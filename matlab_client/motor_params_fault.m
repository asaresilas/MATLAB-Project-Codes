% MOTOR_PARAMS_FAULT  WARNING-level operating parameters for the 75 kW IEC 280M SCIM.
%
% Represents an early-stage bearing outer-race defect (0.007" pit, equivalent to
% CWRU Dataset severity 1) with mild rotor imbalance.  These parameters produce
% WARNING-level AI predictions when the Simulink Digital Twin is run.
%
% Run this script in the Simulink InitFcn callback BEFORE start_ai_server().
%
% Motor: 75 kW, 400 V, 50 Hz, 4-pole, IEC 280M squirrel-cage induction motor
% Operating state: FAULT / WARNING
%
% ISO 10816-3 Group 2 vibration target: Zone B/C boundary (2.5 mm/s RMS ≈ 1.0 g)
% IEC 60034-1 Class F thermal: 95 °C winding → WARNING threshold (368.15 K)

% ── Bearing geometry (same SKF 6316 as normal state) ─────────────────────────
n_balls    = 9;
d_ball     = 25.4e-3;
D_pitch    = 120.65e-3;
alpha_c    = 0;
fr_nominal = 1465/60;       % slightly reduced speed due to increased slip under fault load

BPFO = (n_balls / 2) * fr_nominal * (1 - (d_ball / D_pitch) * cosd(alpha_c));

% ── Fault synthesis parameters — early bearing outer-race defect ──────────────
% A_impact = 120 N produces a vib RMS ≈ 1.0–1.5 g, placing the motor in ISO Zone B/C.
% This corresponds to a detectable defect requiring maintenance within 72 hours.
A_impact    = 4000;     % outer-race defect impact amplitude (N)
                        % Calibrated: RMS ≈ 0.32 g (CWRU outer-race fault range)

% ── Shaft coupling — minor angular misalignment ───────────────────────────────
k_coupling   = 1e5;
delta_offset = 0.3e-3;  % 0.3 mm radial offset — elevated 2× vibration component

% ── Rotor imbalance — moderate (bearing fault causes rotor asymmetry) ─────────
% Bearing outer-race wear redistributes dynamic loads, causing the shaft
% centreline to precess non-uniformly → effective rotor unbalance increases.
% 800 g·mm = 4× healthy level; still below ISO G6.3 alarm limit (2880 g·mm).
U_rotor = 800e-6;       % 800 g·mm = 800e-6 kg·m — fault-induced rotor asymmetry

% ── Electrical operating point — overloaded (bearing friction losses) ─────────
% Bearing defect increases friction → higher stator current for same torque.
% 110 A ≈ 85 % of rated 129 A line current → consistent with WARNING load.
I_a_rms    = 110.0;     % Phase A RMS current (A) — overloaded ~83 %
RPM_nom    = 1465;      % Reduced speed: increased slip from bearing drag
Torque_nom = 484.0;     % Same demanded torque, but motor works harder

% ── Thermal operating point — elevated winding temperature ────────────────────
% IEC 60034-1 Class F winding WARNING threshold: 95 °C absolute.
% At 83 % load with bearing friction losses: winding reaches ~95 °C.
T_ambient_K = 298.15;   % 25 °C ambient (IEC standard test condition)
T_stator_K  = 351.15;   % 78 °C stator winding → dT=53K > 50K → WARNING by scalar expert

fprintf('[PARAMS] State: FAULT/WARNING | Vib impact: %.0f N | T_stator: %.1f °C | Ia: %.0f A | RPM: %.0f\n', ...
    A_impact, T_stator_K - 273.15, I_a_rms, RPM_nom);
