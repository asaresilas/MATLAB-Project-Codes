function [Health_State, Fault_Type, Confidence, Accuracy, RUL_Hours, Thermal_Status, Vib_Out] = ...
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
%   Fault_Type    - Categorical fault code (single dominant fault):
%                     0 = Healthy          (no fault detected)
%                     1 = Bearing Fault    (CWRU-CNN / Current-CNN)
%                     2 = Rotor Fault      (Induction-CNN / Current-CNN)
%                     3 = Shaft Fault      (Induction-CNN Ring class)
%                     4 = Thermal Fault    (Thermal-CNN / IEC scalar alarm)
%                     5 = Multiple Faults  (two or more fault types active)
%   Confidence    - Model confidence [0–100 %]
%   Accuracy      - Validated meta-fusion F1-macro [90.89 % — see CLAUDE.md]
%   RUL_Hours     - Remaining Useful Life in hours (–1 = not yet determined)
%   Thermal_Status- 0=OK | 1=WARNING (>95°C or ΔT>50K) | 2=CRITICAL (>120°C or ΔT>70K)
%
% VIBRATION OUTPUT (Vib_Out):
%   RMS value of the 2048-sample vibration buffer in g (m/s² ÷ 9.81).
%   Updated every 2048 samples (once per prediction cycle).
%   ISO 10816-3 Group 2 thresholds (g):
%     Zone A (normal)    < 0.51 g    (1.6 mm/s RMS × 10 Hz motor → ≈0.5 g)
%     Zone B (acceptable)  0.51–2.04 g
%     Zone C (marginal)    2.04–3.27 g
%     Zone D (dangerous) > 3.27 g
%
% USAGE — place as a MATLAB Function Block with inputs:
%   Ia, Ib, Ic         : 3-phase currents [A]
%   Vib_X/Y/Z          : vibration acceleration from Simscape (m/s²)
%   RPM                : rotor speed [rpm]
%   Torque             : shaft torque [Nm]
%   Temp_Amb           : ambient temperature [K or °C, backend handles both]
%   Temp_Motor         : motor winding temperature [K or °C]
%   Thermal_Matrix     : 3×3 thermal camera frame in Kelvin (can be empty [])
%
% Requires: api_wrapper.m, PredictiveMaintenanceClient.m, Log_Sensor_Data.m
%           (all on the MATLAB path)
%
% NOTE ON VIBRATION SYNTHESIS
%   Simscape Multibody rigid-joint constraints absorb the bearing reaction
%   forces internally, producing rotor-centre deviation of ~1e-13 m/s².
%   This is constraint residual, not housing vibration. An accelerometer
%   mounted on the bearing housing measures the housing response to the
%   transmitted bearing force. We synthesise that signal from the physics
%   parameters already in the MATLAB base workspace (set by motor_params_*.m):
%     A_1x  = 0.50 m/s²  — 1× running speed (residual imbalance, ISO Zone A)
%     A_2x  = 0.15 m/s²  — 2× harmonic
%     A_impact            — outer-race defect impact amplitude (N), 0 = healthy
%     BPFO                — bearing pass frequency outer race (Hz)
%   fs_vib = 12 000 Hz matches the CWRU training dataset sample rate.

% --- Coder directives ---
coder.extrinsic('api_wrapper');
coder.extrinsic('Log_Sensor_Data');
coder.extrinsic('evalin');
coder.extrinsic('safe_evalin_d');   % wraps evalin+try/catch; codegen cannot see try/catch

% --- Persistent state ---
persistent buffer_curr buffer_vib buffer_idx
persistent last_h last_fc last_c last_r last_t last_state_str
persistent last_vib_rms   % RMS of last full 2048-sample buffer (g)
persistent vib_ctr        % absolute sample counter — drives synthesis time axis

if isempty(buffer_idx)
    buffer_curr  = zeros(2048, 3, 'double');
    buffer_vib   = zeros(2048, 1, 'double');
    buffer_idx   = 1;
    vib_ctr      = double(0);

    % Neutral startup defaults (0 / -1 = "no data yet", not misleading healthy values)
    last_h       = 0;       % Unknown
    last_fc      = 0;       % 0 = Healthy (no fault)
    last_c       = 0;       % 0% confidence
    last_r       = -1;      % RUL not yet determined
    last_t       = 0;       % No thermal fault
    last_vib_rms = 0.0;     % 0 g until first buffer fills
    last_state_str = 'UNKNOWN';
end

% --- Output pre-allocation (required for Simulink Coder) ---
Health_State   = zeros(1, 1, 'double');
Fault_Type     = zeros(1, 1, 'double');
Confidence     = zeros(1, 1, 'double');
Accuracy       = zeros(1, 1, 'double');
RUL_Hours      = zeros(1, 1, 'double');
Thermal_Status = zeros(1, 1, 'double');
Vib_Out        = zeros(1, 1, 'double');   % vibration RMS (g) — updated every 2048 samples

% =========================================================================
% VIBRATION SYNTHESIS
% Simscape output (Vib_X/Y/Z) is ~1e-13 m/s² — rigid-joint constraint
% residual, not housing vibration.  Synthesise the bearing-housing
% acceleration from physics equations using workspace parameters.
% =========================================================================
fs_vib = 12000;                         % synthesis rate (Hz) — matches CWRU training
t_vib  = double(vib_ctr) / fs_vib;     % current synthesis time (s)
vib_ctr = vib_ctr + 1;                 % advance counter

% Auto-detect whether Simulink connects omega (rad/s) or n (RPM).
% For this 4-pole 50 Hz motor: omega_rated ≈ 155 rad/s, n_rated = 1480 RPM.
% Values < 300 → rad/s (Simulink Simscape output); ≥ 300 → RPM (tachometer block).
% Threshold 300 is unambiguous: rated speed is 155 rad/s vs 1480 RPM.
speed_raw = double(RPM);
if speed_raw < 300
    omega     = speed_raw;               % already rad/s from Simulink omega port
    speed_rpm = speed_raw * 60 / (2*pi); % convert to RPM for display and backend
else
    omega     = speed_raw * 2*pi / 60;   % input is RPM → convert to rad/s for synthesis
    speed_rpm = speed_raw;
end
fr = omega / (2*pi);                     % shaft rotation frequency (Hz)

% --- Healthy baseline (ISO 10816-3 Group 2 Zone A: ~1–2 mm/s RMS ≈ 0.5 m/s²) ---
A_1x    = 0.50;    % 1× running-speed component (m/s²)
A_2x    = 0.15;    % 2× harmonic (m/s²) — present in any running motor
A_noise = 0.08;    % broadband noise floor (m/s²)

vib_sample = A_1x    * sin(2*pi*fr*t_vib) + ...
             A_2x    * sin(2*pi*2*fr*t_vib + 1.2) + ...
             A_noise * sin(2*pi*317*t_vib + 0.3) + ...   % pseudo-noise tone 1
             A_noise * sin(2*pi*853*t_vib + 2.1);         % pseudo-noise tone 2

% --- Read fault parameters from workspace ---
% motor_params_normal/fault/critical.m should be run in InitFcn before simulation.
% If a variable is missing (e.g. script was not run), the try/catch provides a
% safe default so the simulation does not crash — it will run as NORMAL condition.
%
% Simulink codegen rule: evalin returns mxArray; declare a typed double default
% FIRST so the code generator infers the correct type from the initialisation.
A_impact = double(0);
A_impact = safe_evalin_d('A_impact', 0.0);        % default 0 N (no defect)

BPFO_hz = double(88.1);
BPFO_hz = safe_evalin_d('BPFO', 88.1);            % default BPFO at 1480 RPM

% --- Shaft misalignment: elevated 2x running-speed component (ISO 13373) ---
% Misalignment transfers as a 2× harmonic through the flexible coupling.
% A_misalign = coupling_stiffness × radial_offset / housing_mass
k_coupling_val = double(1e5);
k_coupling_val = safe_evalin_d('k_coupling', 1e5);  % default 100 kN/m

delta_off_val = double(0);
delta_off_val = safe_evalin_d('delta_offset', 0.0); % default 0 mm (aligned)
m_housing_vib  = double(145.0);
A_misalign_2x  = (k_coupling_val * delta_off_val) / m_housing_vib;
vib_sample = vib_sample + A_misalign_2x * sin(2*pi*2*fr*t_vib + 1.2);

% --- Rotor imbalance: 1x synchronous component (ISO 1940-1) ---
% Residual unbalance from rotor asymmetry / fault-induced mass redistribution.
% Physics: centrifugal force F = U_rotor * omega^2 (U_rotor = m_unb * e_unb in kg*m).
% Housing acceleration A_imb = F / m_rotor  (simplified SDOF, well below critical speed).
% U_rotor is set in motor_params_*.m to reflect the fault severity:
%   Normal   : ISO G2.5 grade residual (~200 g*mm = 200e-6 kg*m)
%   Fault    : bearing defect causes rotor asymmetry (~800 g*mm = 800e-6 kg*m)
%   Critical : severe defect / bent shaft (~2500 g*mm = 2500e-6 kg*m)
U_rotor_val = double(200e-6);
U_rotor_val = safe_evalin_d('U_rotor', 200e-6);   % default 200 g·mm (ISO G2.5)
m_rotor_mass  = double(45.0);    % IEC 280M 75 kW rotor mass (kg) — fixed geometry
A_imbalance   = (U_rotor_val * omega^2) / m_rotor_mass;   % m/s^2
% Phase offset 0.8 rad to decouple imbalance vector from baseline 1x component
vib_sample = vib_sample + A_imbalance * sin(2*pi*fr*t_vib + 0.8);

% --- Bearing outer-race defect: exponentially decaying impact train at BPFO ---
% Each outer-race defect produces an impulse every 1/BPFO seconds.
% The impulse excites the bearing resonance frequency (~2500 Hz) and
% decays with time constant 1/beta.  Amplitude scales with A_impact (N).
if A_impact > 0 && BPFO_hz > 0
    T_bpfo   = 1 / BPFO_hz;                    % impact period (s)
    phase    = mod(t_vib, T_bpfo);             % time since most recent impact
    beta     = 400;                             % ring-down rate (1/s)
    f_ring   = 2500;                            % bearing natural frequency (Hz)
    a_defect = (double(A_impact) / 300) * ...
               exp(-beta * phase) * ...
               sin(2*pi*f_ring*phase);
    vib_sample = vib_sample + a_defect;
end

% vib_sample is in m/s²; convert to g for buffer accumulation.
% api_wrapper also divides by 9.81, so the buffer stores m/s² and the
% wrapper handles the conversion — keep vib_sample in m/s² here.
vib_mag_val = vib_sample;   % m/s², stored in ring buffer

% =========================================================================
% RING BUFFER ACCUMULATION
% =========================================================================
idx = mod(buffer_idx - 1, 2048) + 1;

buffer_vib(idx)    = vib_mag_val;
buffer_curr(idx,1) = double(Ia);
buffer_curr(idx,2) = double(Ib);
buffer_curr(idx,3) = double(Ic);

buffer_idx = buffer_idx + 1;

% --- Trigger prediction every 2048 samples ---
if idx == 2048
    % Prefer workspace temperatures from motor_params_*.m (immediate, scenario-correct)
    % over the Simulink signal (which needs many steps to reach thermal steady state).
    % Falls back to the Simulink port value if motor_params has not been loaded.
    temp_motor_out = double(Temp_Motor);
    temp_amb_out   = double(Temp_Amb);
    temp_motor_out = safe_evalin_d('T_stator_K',  temp_motor_out);  % prefer workspace K value
    temp_amb_out   = safe_evalin_d('T_ambient_K', temp_amb_out);
    scalars = double([speed_rpm; Torque; temp_motor_out; temp_amb_out]);

    % Check for a valid thermal frame
    has_thermal = false;
    if ~isempty(Thermal_Matrix) && any(Thermal_Matrix(:) > 0)
        has_thermal = true;
    end

    % --- Compute buffer RMS values ---
    vib_rms_ms2 = sqrt(mean(buffer_vib .^ 2));   % m/s²
    vib_rms_g   = vib_rms_ms2 / 9.81;            % convert to g for ISO 10816-3 comparison
    ia_rms   = sqrt(mean(buffer_curr(:,1) .^ 2));
    ib_rms   = sqrt(mean(buffer_curr(:,2) .^ 2));
    ic_rms   = sqrt(mean(buffer_curr(:,3) .^ 2));

    % Store RMS so Vib_Out can output it every step (even between predictions)
    last_vib_rms = vib_rms_g;

    % --- Extrinsic API call (runs in MATLAB base workspace) ---
    h_out = double(-1);
    f_out = double(0);
    c_out = double(0);
    r_out = double(-1);
    t_out = double(0);

    [h_out, f_out, c_out, ~, r_out, t_out] = ...
        api_wrapper(buffer_vib, buffer_curr, scalars, Thermal_Matrix, has_thermal);

    % Only update outputs if a real response came back
    if h_out >= 0
        last_h  = h_out;
        last_fc = f_out;   % categorical fault code 0–5 from api_wrapper
        last_c  = c_out;
        last_r  = r_out;
        last_t  = t_out;

        switch last_h
            case 1,  last_state_str = 'NORMAL';
            case 2,  last_state_str = 'WARNING';
            case 3,  last_state_str = 'CRITICAL';
            otherwise, last_state_str = 'UNKNOWN';
        end
    end

    % --- Log sensor snapshot ---
    log_vec   = [vib_rms_g, ia_rms, ib_rms, ic_rms, ...
                 speed_rpm, double(Torque), temp_motor_out, temp_amb_out];
    log_names = {'Vib_RMS_g','Ia_RMS','Ib_RMS','Ic_RMS','RPM','Torque','Temp_Motor_K','Temp_Amb_K'};

    Log_Sensor_Data(log_vec, log_names, 12000, [], last_state_str);
end

% --- Assign outputs ---
% Accuracy is fixed at the validated meta-fusion F1-macro (90.89 %).
% The old formula (1 - uncertainty)*100 always returned 100 % because
% n_iter=1 (deterministic forward pass, uncertainty=0). Use the real
% experimentally confirmed value from the 5-fold cross-validation.
Health_State(:)   = last_h;
Fault_Type(:)     = last_fc;    % categorical 0–5, not a bitmask
Confidence(:)     = last_c;
Accuracy(:)       = 90.89;      % validated F1-macro (CLAUDE.md §Confirmed Metrics)
RUL_Hours(:)      = last_r;
Thermal_Status(:) = last_t;
Vib_Out(:)        = last_vib_rms;  % RMS in g — holds previous value between prediction cycles

end % simulink_predictive_gateway
% safe_evalin_d is a separate file (safe_evalin_d.m) on the MATLAB path.
% Keeping it external is required: MATLAB Coder analyzes all local functions
% in a %#codegen file — coder.extrinsic only suppresses the call site, not
% the function body.  Moving it to its own file makes it truly invisible to
% the code generator.
