% TEST_CLIENT  End-to-end verification for the Predictive Maintenance AI pipeline.
%
% Tests the full chain:
%   MATLAB (api_wrapper) → WebSocket → FastAPI backend → Deep Learning models → MATLAB
%
% IMPORTANT: api_wrapper maintains its OWN persistent WebSocket client internally.
% This script does NOT create a separate client — doing so would be redundant and
% misleading, because the two clients are independent.
%
% USAGE:
%   1. Start the Python server:
%        cd <project_root>
%        python backend/run.py
%   2. Run this script in MATLAB Command Window:
%        run test_client.m
%   3. Review the diagnostics printed below.
%
% Requires: api_wrapper.m, PredictiveMaintenanceClient.m (on MATLAB path)

clear; clc;

%% ── Configuration ──────────────────────────────────────────────────────────
SERVER_URL   = 'http://127.0.0.1:8000';   % <-- Port 8000 (NOT 8001)
MACHINE_ID   = 'TEST-UNIT-001';            % Diagnostic client ID
N_SAMPLES    = 2048;                       % Ring-buffer length (matches gateway)

fprintf('╔══════════════════════════════════════════════════╗\n');
fprintf('║   PREDICTIVE MAINTENANCE DIGITAL TWIN — TEST    ║\n');
fprintf('╚══════════════════════════════════════════════════╝\n');
fprintf('  Target server : %s\n', SERVER_URL);
fprintf('  Machine ID    : %s\n', MACHINE_ID);
fprintf('  Date/Time     : %s\n', char(datetime('now')));
fprintf('\n');

%% ── Step 1: HTTP Health Check (verify server is reachable) ─────────────────
fprintf('[STEP 1] HTTP health check → %s/health\n', SERVER_URL);
try
    opts   = weboptions('Timeout', 8, 'ContentType', 'json');
    health = webread([SERVER_URL, '/health'], opts);
    fprintf('  ✓ Server alive  — status: %s  uptime: %.1f s\n', ...
            health.status, health.uptime_s);
catch ME
    fprintf('  ✗ HEALTH CHECK FAILED: %s\n', ME.message);
    fprintf('\n  ACTION REQUIRED:\n');
    fprintf('    • Start the server:   python backend/run.py\n');
    fprintf('    • Check port (must be 8000, not 8001)\n');
    fprintf('    • Check firewall / antivirus is not blocking port 8000\n');
    return;
end
fprintf('\n');

%% ── Step 2: Build synthetic sensor payload ──────────────────────────────────
fprintf('[STEP 2] Building synthetic sensor payload (%d samples)...\n', N_SAMPLES);
t        = linspace(0, 1, N_SAMPLES);
fs       = 12000;    % Hz — standard for this project

% Vibration: 50 Hz fundamental + bearing-fault harmonic at 157 Hz + noise
vib_col  = (sin(2*pi*50*t) + 0.3*sin(2*pi*157*t) + 0.05*randn(size(t)))';

% Current: 3-phase balanced 50 Hz + slight asymmetry (stator fault simulation)
Ia = (sqrt(2) * sin(2*pi*50*t + 0))';
Ib = (sqrt(2) * sin(2*pi*50*t - 2*pi/3))';
Ic = (sqrt(2) * sin(2*pi*50*t + 2*pi/3) + 0.02*randn(size(t)))';  % slight noise
curr_mat = [Ia, Ib, Ic];   % [2048 × 3]

% Scalar operating point: [RPM; Torque_Nm; TempMotor_°C; TempAmb_°C]
scalars  = [1480; 48; 72; 24];

fprintf('  Vibration  : [%d × 1] col vector, RMS = %.4f g\n', ...
        numel(vib_col), sqrt(mean(vib_col.^2)));
fprintf('  Current    : [%d × 3] matrix, Ia_RMS = %.4f A\n', ...
        size(curr_mat,1), sqrt(mean(curr_mat(:,1).^2)));
fprintf('  Scalars    : RPM=%.0f  Torque=%.0f Nm  TempM=%.0f°C  TempA=%.0f°C\n', ...
        scalars(1), scalars(2), scalars(3), scalars(4));
fprintf('\n');

%% ── Step 3: Call api_wrapper (manages its own WebSocket client internally) ──
fprintf('[STEP 3] Calling api_wrapper → ws://127.0.0.1:8000/ws/simulink/...\n');
fprintf('  (api_wrapper creates and caches its own persistent WebSocket client)\n');

t_call = tic;
try
    [Health, Fault, Conf, Acc, RUL, Therm] = ...
        api_wrapper(vib_col, curr_mat, scalars, [], false);
    elapsed_ms = toc(t_call) * 1000;

    fprintf('\n');
    fprintf('┌────────────────────────────────────────────────┐\n');
    fprintf('│              AI DIAGNOSIS RESULTS              │\n');
    fprintf('├────────────────────────────────────────────────┤\n');

    health_labels = {'0-Unknown', '1-Normal', '2-Warning', '3-Critical'};
    if Health >= 0 && Health <= 3
        h_lbl = health_labels{Health + 1};
    else
        h_lbl = num2str(Health);
    end

    fault_labels = {'0-None', '1-Bearing', '2-Stator', '3-Rotor', '4-Tool', '5-Thermal'};
    if Fault >= 0 && Fault <= 5
        f_lbl = fault_labels{Fault + 1};
    else
        f_lbl = num2str(Fault);
    end

    fprintf('│  Health State  : %-30s │\n', h_lbl);
    fprintf('│  Fault Type    : %-30s │\n', f_lbl);
    fprintf('│  Confidence    : %-5.1f %%                        │\n', Conf);
    fprintf('│  Accuracy      : %-5.1f %%                        │\n', Acc);
    if RUL >= 0
        fprintf('│  RUL Forecast  : %-7.1f h                      │\n', RUL);
    else
        fprintf('│  RUL Forecast  : Not yet determined             │\n');
    end
    fprintf('│  Thermal Status: %-30s │\n', num2str(Therm));
    fprintf('│  Round-trip    : %-7.1f ms                      │\n', elapsed_ms);
    fprintf('└────────────────────────────────────────────────┘\n');

    %% ── Step 4: Pass/Fail Assessment ────────────────────────────────────────
    fprintf('\n[STEP 4] Assessment\n');
    all_ok = true;

    if Health == 0 && Conf == 0
        fprintf('  ⚠  Health=0 and Conf=0 — likely a timeout or no server response.\n');
        fprintf('     Check: backend console for errors, ensure models are loaded.\n');
        all_ok = false;
    else
        fprintf('  ✓ Non-zero Health and Confidence received from backend.\n');
    end

    if RUL == -1
        fprintf('  ℹ  RUL=-1 (not yet determined) — normal on first call.\n');
    else
        fprintf('  ✓ RUL = %.1f h\n', RUL);
    end

    if elapsed_ms > 10000
        fprintf('  ⚠  Round-trip > 10 s — possible model loading delay or timeout.\n');
        all_ok = false;
    else
        fprintf('  ✓ Round-trip within expected range (%.1f ms)\n', elapsed_ms);
    end

    if all_ok
        fprintf('\n  ══ ALL CHECKS PASSED — Simulink block is ready. ══\n\n');
    else
        fprintf('\n  ══ SOME CHECKS FAILED — review warnings above.  ══\n\n');
    end

catch ME
    fprintf('\n  ✗ api_wrapper THREW AN EXCEPTION:\n');
    fprintf('    %s\n', ME.message);
    if ~isempty(ME.stack)
        fprintf('    File: %s  Line: %d\n', ME.stack(1).file, ME.stack(1).line);
    end
    fprintf('\n  Possible causes:\n');
    fprintf('    • Server not running (start with: python backend/run.py)\n');
    fprintf('    • Wrong port (must be 8000)\n');
    fprintf('    • MATLAB R2022a+ required for websocket() support\n');
    fprintf('    • api_wrapper.m not on the MATLAB path\n');
end
