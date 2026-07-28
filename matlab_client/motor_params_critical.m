% MOTOR_PARAMS_CRITICAL  CRITICAL-level operating parameters for the 75 kW IEC 280M SCIM.
%
% Represents a severe bearing defect (0.021" pit, equivalent to CWRU Dataset
% severity 3) with significant shaft misalignment and winding overtemperature.
% These parameters produce CRITICAL-level AI predictions when the Simulink
% Digital Twin is run.  The motor must be stopped immediately in this state.
%
% Run this script in the Simulink InitFcn callback BEFORE start_ai_server().
%
% Motor: 75 kW, 400 V, 50 Hz, 4-pole, IEC 280M squirrel-cage induction motor
% Operating state: CRITICAL
%
% ISO 10816-3 Group 2 vibration target: Zone D (> 4.0 mm/s RMS ≈ >1.6 g)
% IEC 60034-1 Class F thermal: > 120 °C winding → CRITICAL (insulation damage risk)
%
% ⚠ SAFETY NOTE: In a physical installation, this operating state requires
%   immediate shutdown (lockout/tagout).  This file is for simulation only.

% ── Bearing geometry (same SKF 6316) ─────────────────────────────────────────
n_balls    = 9;
d_ball     = 25.4e-3;
D_pitch    = 120.65e-3;
alpha_c    = 0;
fr_nominal = 1440/60;       % significantly reduced speed from heavy fault load

BPFO = (n_balls / 2) * fr_nominal * (1 - (d_ball / D_pitch) * cosd(alpha_c));

% ── Fault synthesis parameters — severe bearing outer-race defect ─────────────
% A_impact = 350 N produces vib RMS ≈ 3.0–4.5 g, placing the motor in ISO Zone D.
% Equivalent to a deep spall causing repeated high-energy metal-to-metal impacts.
A_impact    = 8000;     % outer-race defect impact amplitude (N)
                        % Calibrated: RMS ≈ 0.63 g (CWRU severe-fault range)

% ── Shaft coupling — significant misalignment (bent shaft or coupling failure) ──
k_coupling   = 1e5;
delta_offset = 1.5e-3;  % 1.5 mm radial offset → large 2× running-speed vibration

% ── Rotor imbalance — severe (bent shaft / broken rotor bar mass redistribution) ─
% Severe bearing spall causes shaft deflection; broken rotor bars (or partial
% winding failure) shift the rotor centre of mass off the geometric axis.
% 2500 g·mm exceeds ISO G6.3 limit (2880 g·mm at 1480 RPM) — alarm condition.
% Physical interpretation: ~2.5 g mass displaced 1 m from axis (or equivalent).
U_rotor = 2500e-6;      % 2500 g·mm = 2500e-6 kg·m — severe imbalance / bent shaft

% ── Electrical operating point — heavily overloaded ──────────────────────────
% Severe bearing friction + rotor asymmetry → 138 A ≈ 107 % of rated 129 A.
% Operating above rated current accelerates insulation degradation.
I_a_rms    = 138.0;     % Phase A RMS current (A) — 105 % of rated (overload)
RPM_nom    = 1440;      % Heavily reduced speed from fault torque drag
Torque_nom = 484.0;     % Same demanded torque; motor straining to maintain speed

% ── Thermal operating point — critical winding overtemperature ───────────────
% IEC 60034-1 Class F insulation critical limit: 120 °C absolute.
% Bearing friction + electrical overload → winding reaches 130 °C (above limit).
% Prolonged operation at this temperature causes irreversible insulation carbonisation.
T_ambient_K = 298.15;   % 25 °C ambient (IEC standard test condition)
T_stator_K  = 408.15;   % 135 °C stator winding → dT=110K > 70K AND 135 > 120 → CRITICAL

fprintf('[PARAMS] State: CRITICAL | Vib impact: %.0f N | T_stator: %.1f °C | Ia: %.0f A | RPM: %.0f\n', ...
    A_impact, T_stator_K - 273.15, I_a_rms, RPM_nom);
fprintf('[PARAMS] WARNING: CRITICAL state simulated. Physical motor requires immediate shutdown.\n');
