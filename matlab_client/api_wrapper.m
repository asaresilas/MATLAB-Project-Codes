function [h_out, f_out, c_out, a_out, r_out, t_out] = api_wrapper(vib_mag, current_matrix, scalars, Thermal_Matrix, has_thermal)
% API_WRAPPER  Extrinsic helper called from simulink_predictive_gateway.m
%
% Runs in the MATLAB base workspace (not compiled by Simulink Coder).
% Maintains a persistent PredictiveMaintenanceClient and sends the
% 2048-point ring-buffer windows to the FastAPI backend via WebSocket.
%
% OUTPUTS (all numeric scalars for Simulink ports):
%   h_out  - Health state:   0=Unknown, 1=Normal, 2=Warning, 3=Critical
%   f_out  - Categorical fault code (single dominant fault):
%              0 = Healthy          4 = Thermal Fault
%              1 = Bearing Fault    5 = Multiple Faults
%              2 = Rotor Fault
%              3 = Shaft Fault
%            Read from backend field 'fault_code' (not 'fault_flags' bitmask).
%   c_out  - Confidence [0–100 %]
%   a_out  - Validated meta-fusion F1-macro accuracy [90.89 % — fixed constant]
%   r_out  - Remaining Useful Life (hours, from NASA Bi-LSTM or class approximation)
%   t_out  - Thermal severity: 0=OK, 1=WARNING (>95°C or ΔT>50K), 2=CRITICAL (>120°C or ΔT>70K)

persistent client last_connect_attempt;

% --- Neutral defaults (0 = "no data yet", not false confidence) ---
h_out = 0;   % 0 = Unknown, not Normal — prevents misleading "healthy" before first AI response
f_out = 0;   % No fault identified yet
c_out = 0;   % 0% confidence until AI responds
a_out = 0;   % 0% certainty until AI responds
r_out = -1;  % -1 = RUL not yet determined (distinct from 0 h = imminent failure)
t_out = 0;   % No thermal fault

try
    % --- Initialise persistent client on first call ---
    if isempty(client)
        % SERVER_URL priority:
        %   1. MOTORGUARD_SERVER env var (set in MATLAB Command Window)
        %   2. HF Spaces cloud URL (production default)
        %   3. localhost (automatic fallback when env var is empty string)
        %
        % Switch to local:  setenv('MOTORGUARD_SERVER','http://127.0.0.1:8000')
        % Switch to cloud:  setenv('MOTORGUARD_SERVER','')
        SERVER_URL = getenv('MOTORGUARD_SERVER');
        if isempty(SERVER_URL)
            SERVER_URL = 'https://YOUR-HF-USERNAME-motorguard.hf.space';
        end
        client = PredictiveMaintenanceClient(SERVER_URL, 'MOTOR-3D-TWIN');
        last_connect_attempt = -inf;
    end

    % --- Re-connect if dropped (auto-reconnect guard) ---
    if ~client.isConnected()
        now_s = now * 86400; % MATLAB datenum -> seconds
        if isempty(last_connect_attempt) || (now_s - last_connect_attempt) >= 5
            fprintf('[API_WRAPPER] Reconnecting...\n');
            last_connect_attempt = now_s;
            client.connect();
        end
        if ~client.isConnected()
            return;  % Still not connected — keep neutral defaults
        end
    end

    % --- Build structured payload matching PredictionEngine.predict() dict path ---
    % Keys: vibration (Nx1), current (Nx3), scalars ([RPM; Torque; MotorTemp; AmbTemp])
    % thermal_image (3x3 Kelvin matrix) is included directly so the backend's
    % predict_from_matrix() handles normalise → jet colormap → CNN internally.
    payload = struct();
    % Transform Sensor outputs m/s²; CWRU-CNN was trained in g → convert here.
    payload.vibration = double(vib_mag(:)) / 9.81;   % m/s² → g, column vector → JSON array
    payload.current   = double(current_matrix);      % Nx3 matrix  → JSON array-of-arrays
    payload.scalars   = double(scalars(:)');          % row vector   → JSON array [RPM,T,Tm,Ta]
    if has_thermal
        payload.thermal_image = double(Thermal_Matrix);  % 3x3 Kelvin → JSON array-of-arrays
    end

    % --- Main prediction (includes thermal when available) ---
    res = client.predict(payload);

    % --- Health state from main response (thermal now embedded in meta-fusion) ---
    h_out = 1;  % Normal until proven otherwise
    if strcmp(res.alert_level, 'CRITICAL')
        h_out = 3;
    elseif strcmp(res.alert_level, 'WARNING')
        h_out = 2;
    end

    % --- Thermal output: read standalone thermal_status field ---
    % thermal_status is independent of fault_code — fires on high temperature
    % OR Thermal-CNN alarm even when a bearing/current fault_code was assigned.
    %   0 = No thermal alarm
    %   1 = Thermal WARNING  (motor_temp > 95 degC or dT > 50 K)
    %   2 = Thermal CRITICAL (motor_temp > 120 degC or dT > 70 K)
    % Legacy fallback: if backend is old version without thermal_status field,
    % use fault_code == 5 as before.
    t_out = 0;
    if isfield(res, 'thermal_status') && ~isempty(res.thermal_status)
        t_out = double(res.thermal_status);
    elseif isfield(res, 'fault_code') && res.fault_code == 5
        t_out = 1;
    end

    % --- Fault code (f_out): categorical 0–5 from backend ---
    % Backend now returns 'fault_code' as a single integer (0=Healthy … 5=Multiple).
    % This is simpler and unambiguous compared to the old bitmask 'fault_flags'.
    f_out = 0;
    if isfield(res, 'fault_code') && ~isempty(res.fault_code)
        f_out = double(res.fault_code);
    end

    % Read human-readable fault name for the fprintf log below
    fault_name = 'Healthy';
    if isfield(res, 'fault_type_name') && ~isempty(res.fault_type_name)
        fault_name = res.fault_type_name;
    end

    % --- Confidence ---
    % a_out is the validated meta-fusion F1-macro (90.89 %) — a fixed constant.
    % The old formula (1 - uncertainty)*100 always returned 100 % because the
    % backend uses n_iter=1 (deterministic), making uncertainty=0 always.
    % Hardcode to the experimentally confirmed value from 5-fold CV (CLAUDE.md).
    if isfield(res, 'confidence'),  c_out = res.confidence * 100; end
    a_out = 90.89;   % validated F1-macro; NOT (1-uncertainty)*100

    % --- RUL (hours) ---
    if isfield(res, 'rul_hours') && ~isempty(res.rul_hours) && res.rul_hours >= 0
        r_out = res.rul_hours;
    else
        if isfield(res, 'prediction')
            r_out = (1.0 - res.prediction) * 20000;
        end
    end

    % --- Informative console log (once per prediction cycle) ---
    health_labels = {'UNKNOWN','NORMAL','WARNING','CRITICAL'};
    h_label = health_labels{min(h_out + 1, 4)};
    vib_rms_g = sqrt(mean(double(vib_mag) .^ 2)) / 9.81;
    fprintf('[AI] Health: %-8s | Fault: %-16s | Code: %d | Conf: %5.1f%% | RUL: ', ...
        h_label, fault_name, f_out, c_out);
    if r_out >= 0
        fprintf('%6.1f h\n', r_out);
    else
        fprintf('  N/A\n');
    end
    fprintf('     Vib RMS: %.3f g | Thermal: %d\n', vib_rms_g, t_out);

catch ME
    fprintf('[API_WRAPPER] Error: %s\n', ME.message);
    % Keep neutral defaults — do NOT output fake-healthy values on error
end

end
