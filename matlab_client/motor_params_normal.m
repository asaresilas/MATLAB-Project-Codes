% MOTOR_PARAMS_NORMAL  Healthy operating parameters for the 75 kW IEC 280M SCIM.
%
% Run this script in the Simulink InitFcn callback (Model Properties > Callbacks)
% BEFORE calling start_ai_server() to ensure parameters are in the base workspace
% when simulink_predictive_gateway.m reads them via evalin('base', ...).
%
% Motor: 75 kW, 400 V, 50 Hz, 4-pole, IEC 280M squirrel-cage induction motor
% Operating state: HEALTHY (Zone A per ISO 10816-3)
%
% IEC 60034-1 Class F insulation absolute temperature limits:
%   Stator winding warning : 95 °C (368.15 K)
%   Stator winding critical: 120 °C (393.15 K)
%
% Vibration reference (ISO 10816-3 Group 2, 75 kW rigid mount):
%   Zone A (new/normal) : RMS < 1.6 mm/s ≈ 0.51 g @ 25 Hz
%   Zone B (acceptable) : 1.6–2.5 mm/s
%   Zone C (marginal)   : 2.5–4.0 mm/s
%   Zone D (dangerous)  : > 4.0 mm/s

% ── Bearing geometry (SKF 6316 deep-groove, typical IEC 280M drive-end) ──────
% Values from SKF bearing catalogue; n_balls=9 for 6316.
n_balls    = 9;           % number of rolling elements
d_ball     = 25.4e-3;     % ball diameter (m)
D_pitch    = 120.65e-3;   % pitch circle diameter (m)
alpha_c    = 0;           % contact angle (°) — radial bearing
fr_nominal = 1480/60;     % shaft frequency at 1480 rpm (Hz)

% Bearing pass frequency — outer race (BPFO):
%   BPFO = (n/2) × fr × (1 − d_ball/D_pitch × cos(alpha_c))
BPFO = (n_balls / 2) * fr_nominal * (1 - (d_ball / D_pitch) * cosd(alpha_c));

% ── Fault synthesis parameters (healthy — no defect) ─────────────────────────
A_impact    = 0;        % outer-race defect impact amplitude (N) — 0 = no defect

% ── Shaft coupling stiffness and offset (healthy alignment) ──────────────────
k_coupling   = 1e5;     % coupling torsional stiffness (N/m) — IEC-rated coupling
delta_offset = 0;       % radial misalignment (m) — zero for aligned shaft

% ── Rotor imbalance (ISO 1940-1 Grade G2.5) ──────────────────────────────────
% Max specific unbalance for G2.5 at 1480 RPM: e = 9549*G/N = 16 g·mm/kg
% For a 45 kg rotor: max U = 16 * 45 = 720 g·mm.  Healthy motor is well within
% this limit — using 200 g·mm (28 % of max) as a nominal well-balanced state.
% U_rotor = m_unbalance * e_unbalance  (product in kg·m)
U_rotor = 200e-6;       % 200 g·mm = 200e-6 kg·m — ISO G2.5 residual imbalance

% ── Electrical operating point ────────────────────────────────────────────────
% Full-load rated current for 75 kW, 400 V, η=0.94, pf=0.87, 3-phase:
%   I_line = P / (√3 × V × η × pf) = 75000 / (1.732 × 400 × 0.94 × 0.87) ≈ 129 A
% At no-load or light load, stator current ≈ 60–70 % of rated → 85 A typical.
I_a_rms    = 85.0;      % Phase A RMS current (A) — approx. 65 % load
RPM_nom    = 1480;      % Nominal rotor speed (rpm) at healthy full load
Torque_nom = 484.0;     % Rated shaft torque (N·m) = P/(ω) = 75000/(2π×1480/60)

% ── Thermal operating point ───────────────────────────────────────────────────
% IEC 60034-1 Class F: max winding temperature rise = 105 K above 40 °C ambient.
% Healthy motor at 65 % load: winding ~60 °C above ambient (40 °C) → 100 °C.
% We use 60 °C winding (333.15 K) to represent a lightly loaded healthy state.
T_ambient_K = 313.15;   % 40 °C ambient → 313.15 K
T_stator_K  = 333.15;   % 60 °C stator winding (healthy, lightly loaded) → 333.15 K

fprintf('[PARAMS] State: NORMAL | Vib impact: %.0f N | T_stator: %.1f °C | Ia: %.0f A | RPM: %.0f\n', ...
    A_impact, T_stator_K - 273.15, I_a_rms, RPM_nom);
