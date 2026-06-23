function [h_out, f_out, c_out, a_out, r_out, t_out] = api_wrapper(vib_mag, current_matrix, scalars, Thermal_Matrix, has_thermal)
% API_WRAPPER  Extrinsic helper called from simulink_predictive_gateway.m
%
% Runs in the MATLAB base workspace (not compiled by Simulink Coder).
% Maintains a persistent PredictiveMaintenanceClient and sends the
% 2048-point ring-buffer windows to the FastAPI backend via WebSocket.
%
% OUTPUTS (all numeric scalars for Simulink ports):
%   h_out  - Health state:   0=Unknown, 1=Normal, 2=Warning, 3=Critical
%   f_out  - Fault type:     0=None, 1=Bearing, 2=Stator, 3=Rotor, 4=Tool, 5=Thermal
%   c_out  - Confidence      [0–100 %]
%   a_out  - Accuracy/certainty (1 – uncertainty) [0–100 %]
%   r_out  - Remaining Useful Life (hours, from NASA Bi-LSTM or class approximation)
%   t_out  - Thermal fault:  0=None/OK, 1=Fault, 2=Fan fault

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
        client = PredictiveMaintenanceClient('ws://127.0.0.1:8000', 'MOTOR-3D-TWIN');
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
    payload = struct();
    payload.vibration = double(vib_mag(:));          % column vector → JSON array
    payload.current   = double(current_matrix);      % Nx3 matrix  → JSON array-of-arrays
    payload.scalars   = double(scalars(:)');          % row vector   → JSON array [RPM,T,Tm,Ta]

    % --- Main prediction ---
    res = client.predict(payload);

    % --- Thermal image (optional, independent WebSocket call) ---
    t_res_exists = false;
    t_res = struct('alert_level', 'NORMAL', 'predicted_class', '');
    if has_thermal
        try
            t_res = client.predict_thermal(Thermal_Matrix);
            t_res_exists = true;
            if ~strcmp(t_res.alert_level, 'NORMAL')
                t_out = 1;
                if isfield(t_res, 'predicted_class') && contains(t_res.predicted_class, 'Fan')
                    t_out = 2;
                end
            end
        catch
            % Thermal path not available — leave t_out = 0
        end
    end

    % --- Health state (h_out): worst of main + thermal ---
    h_out = 1;  % Normal until proven otherwise
    if strcmp(res.alert_level, 'CRITICAL') || (t_res_exists && strcmp(t_res.alert_level, 'CRITICAL'))
        h_out = 3;
    elseif strcmp(res.alert_level, 'WARNING') || (t_res_exists && strcmp(t_res.alert_level, 'WARNING'))
        h_out = 2;
    end

    % --- Fault type (f_out): use explicit fault_code from backend ---
    % 0=None/Unknown  1=Bearing  2=Stator  3=Rotor  4=Tool/Industrial  5=Thermal
    % fault_code is set by the backend prediction engine and never relies on
    % string parsing, so it is robust to any changes in model_used formatting.
    f_out = 0;
    if isfield(res, 'fault_code') && ~isempty(res.fault_code)
        f_out = double(res.fault_code);
    end
    % Thermal fault always overrides when thermal sensor independently detects a fault
    if t_out > 0 && h_out > 1
        f_out = 5;
    end

    % --- Confidence & certainty ---
    if isfield(res, 'confidence'),  c_out = res.confidence * 100; end
    if isfield(res, 'uncertainty'), a_out = (1.0 - res.uncertainty) * 100; end

    % --- RUL (hours) ---
    % The backend now returns rul_hours directly (real NASA Bi-LSTM output or
    % class-based approximation). Use it; never derive from 'prediction' field.
    if isfield(res, 'rul_hours') && ~isempty(res.rul_hours) && res.rul_hours >= 0
        r_out = res.rul_hours;
    else
        % Fallback if old backend version doesn't send rul_hours:
        % prediction field = class_index/2 (0=Normal, 0.5=Warning, 1.0=Critical)
        % Invert: remaining life ≈ (1 – prediction) × 20000 h MOL
        if isfield(res, 'prediction')
            r_out = (1.0 - res.prediction) * 20000;
        end
    end

catch ME
    fprintf('[API_WRAPPER] Error: %s\n', ME.message);
    % Keep neutral defaults — do NOT output fake-healthy values on error
end

end
