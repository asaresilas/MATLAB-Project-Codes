function [Health_State, Fault_Type, Confidence, Accuracy, RUL_Hours, Thermal_Status] = ...
    simulink_predictive_gateway(Ia, Ib, Ic, Vib_X, Vib_Y, Vib_Z, RPM, Torque, Temp_Amb, Temp_Motor, Thermal_Matrix) %#codegen
% SIMULINK_PREDICTIVE_GATEWAY  Real-time AI bridge for the SCIM Digital Twin.
%
% Accumulates a 2048-sample ring buffer per simulation step, then calls the
% FastAPI backend (via api_wrapper) every time the buffer fills.
%
% All outputs are scalar doubles so Simulink can route them to displays,
% scopes, and Goto blocks without conversion:
%
%   Health_State  - 0=Unknown | 1=Normal | 2=Warning | 3=Critical
%   Fault_Type    - 0=None | 1=Bearing | 2=Stator | 3=Rotor | 4=Tool | 5=Thermal
%   Confidence    - Model confidence [0–100 %]
%   Accuracy      - (1 – uncertainty) [0–100 %]
%   RUL_Hours     - Remaining Useful Life in hours (–1 = not yet determined)
%   Thermal_Status- 0=OK/unavailable | 1=Fault | 2=Fan fault
%
% USAGE — place as a MATLAB Function Block with inputs:
%   Ia, Ib, Ic         : 3-phase currents [A]
%   Vib_X/Y/Z          : vibration acceleration [g]
%   RPM                : rotor speed [rpm]
%   Torque             : shaft torque [Nm]
%   Temp_Amb           : ambient temperature [°C]
%   Temp_Motor         : motor winding temperature [°C]
%   Thermal_Matrix     : thermal camera frame (can be empty [])
%
% Requires: api_wrapper.m, PredictiveMaintenanceClient.m, Log_Sensor_Data.m
%           (all on the MATLAB path)

% --- Coder directives ---
coder.extrinsic('api_wrapper');
coder.extrinsic('Log_Sensor_Data');

% --- Persistent ring buffers ---
persistent buffer_curr buffer_vib buffer_idx
persistent last_h last_f last_c last_a last_r last_t last_state_str

if isempty(buffer_idx)
    buffer_curr  = zeros(2048, 3, 'double');
    buffer_vib   = zeros(2048, 1, 'double');
    buffer_idx   = 1;

    % Neutral startup defaults (0 / -1 = "no data yet", not misleading healthy values)
    last_h = 0;    % Unknown
    last_f = 0;    % No fault
    last_c = 0;    % 0% confidence
    last_a = 0;    % 0% certainty
    last_r = -1;   % RUL not yet determined
    last_t = 0;    % No thermal fault
    last_state_str = 'UNKNOWN';
end

% --- Output pre-allocation (required for Simulink Coder) ---
Health_State   = zeros(1, 1, 'double');
Fault_Type     = zeros(1, 1, 'double');
Confidence     = zeros(1, 1, 'double');
Accuracy       = zeros(1, 1, 'double');
RUL_Hours      = zeros(1, 1, 'double');
Thermal_Status = zeros(1, 1, 'double');

% --- Accumulate ring buffer ---
vib_mag_val = sqrt(double(Vib_X)^2 + double(Vib_Y)^2 + double(Vib_Z)^2);
idx = mod(buffer_idx - 1, 2048) + 1;

buffer_vib(idx)    = vib_mag_val;
buffer_curr(idx,1) = double(Ia);
buffer_curr(idx,2) = double(Ib);
buffer_curr(idx,3) = double(Ic);

buffer_idx = buffer_idx + 1;

% --- Trigger prediction every 2048 samples ---
if idx == 2048
    scalars = double([RPM; Torque; Temp_Motor; Temp_Amb]);

    % Check for a valid thermal frame
    has_thermal = false;
    if ~isempty(Thermal_Matrix) && any(Thermal_Matrix(:) > 0)
        has_thermal = true;
    end

    % --- Extrinsic API call (runs in MATLAB base workspace) ---
    % Predeclare outputs as typed scalars so Simulink Coder does not treat
    % them as raw mxArray values inside expressions.
    h_out = double(-1);
    f_out = double(0);
    c_out = double(0);
    a_out = double(0);
    r_out = double(-1);
    t_out = double(0);

    [h_out, f_out, c_out, a_out, r_out, t_out] = ...
        api_wrapper(buffer_vib, buffer_curr, scalars, Thermal_Matrix, has_thermal);

    % Only update outputs if a real response came back
    if h_out >= 0   % api_wrapper returns 0 = Unknown, never negative on success
        last_h = h_out;
        last_f = f_out;
        last_c = c_out;
        last_a = a_out;
        last_r = r_out;
        last_t = t_out;

        % Map numeric health state to label string for Log_Sensor_Data
        switch last_h
            case 1,  last_state_str = 'NORMAL';
            case 2,  last_state_str = 'WARNING';
            case 3,  last_state_str = 'CRITICAL';
            otherwise, last_state_str = 'UNKNOWN';
        end
    end

    % --- Log sensor snapshot + health state to CSV (non-blocking file I/O) ---
    % Build a compact sensor vector: [vib_rms, Ia_rms, Ib_rms, Ic_rms, RPM, Torque, Temp_Motor, Temp_Amb]
    vib_rms = sqrt(mean(buffer_vib .^ 2));
    ia_rms  = sqrt(mean(buffer_curr(:,1) .^ 2));
    ib_rms  = sqrt(mean(buffer_curr(:,2) .^ 2));
    ic_rms  = sqrt(mean(buffer_curr(:,3) .^ 2));
    log_vec  = [vib_rms, ia_rms, ib_rms, ic_rms, ...
                double(RPM), double(Torque), double(Temp_Motor), double(Temp_Amb)];
    log_names = {'Vib_RMS','Ia_RMS','Ib_RMS','Ic_RMS','RPM','Torque','Temp_Motor','Temp_Amb'};

    Log_Sensor_Data(log_vec, log_names, 12000, [], last_state_str);
end

% --- Assign outputs ---
Health_State(:)   = last_h;
Fault_Type(:)     = last_f;
Confidence(:)     = last_c;
Accuracy(:)       = last_a;
RUL_Hours(:)      = last_r;
Thermal_Status(:) = last_t;

end
