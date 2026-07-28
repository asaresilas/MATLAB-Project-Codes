function start_ai_server()
% START_AI_SERVER  Launch the Python FastAPI backend before the Simulink
%                  simulation runs.  The React frontend is started separately
%                  from a terminal: cd frontend && npm run dev
%
%   Add this to your Simulink model:
%     Model Properties > Callbacks > InitFcn:
%         run('motor_params_normal.m')
%         start_ai_server()
%
%   Server started:
%     Backend  (FastAPI / uvicorn) : http://127.0.0.1:8000
%     API docs                     : http://127.0.0.1:8000/docs

    BACKEND_PORT  = 8000;
    HEALTH_URL    = sprintf('http://127.0.0.1:%d/health', BACKEND_PORT);
    PREDICT_URL   = sprintf('http://127.0.0.1:%d/api/v1/predict/simulink', BACKEND_PORT);

    fprintf('\n');
    fprintf('============================================================\n');
    fprintf('  Predictive Maintenance Digital Twin — Server Startup\n');
    fprintf('============================================================\n');

    % ── 1.  Locate project root ───────────────────────────────────────────
    current_file = mfilename('fullpath');
    current_dir  = fileparts(current_file);

    python_exe   = '';
    project_root = '';
    search_dir   = current_dir;

    for i = 1:4
        sibling_root = fullfile(search_dir, 'Matlab_Project codes');
        sibling_py   = fullfile(sibling_root, '.venv', 'Scripts', 'python.exe');
        self_py      = fullfile(search_dir,   '.venv', 'Scripts', 'python.exe');

        if exist(sibling_py, 'file')
            python_exe   = sibling_py;
            project_root = sibling_root;
            break;
        elseif exist(self_py, 'file')
            python_exe   = self_py;
            project_root = search_dir;
            break;
        end
        search_dir = fileparts(search_dir);
    end

    if isempty(python_exe)
        fprintf('[WARNING] Cannot find virtual environment (.venv/Scripts/python.exe).\n');
        fprintf('          Please start servers manually:\n');
        fprintf('            Backend : cd backend && python run.py\n');
        fprintf('            Frontend: cd frontend && npm run dev\n');
        fprintf('============================================================\n\n');
        return;
    end

    chk_opts     = weboptions('Timeout', 5, 'MediaType', 'application/json');

    % ── 2.  Verify BACKEND via /health (not just netstat) ────────────────
    fprintf('\n[BACKEND]  Checking http://127.0.0.1:%d/health ...\n', BACKEND_PORT);

    backend_ok = false;
    backend_dir = fullfile(project_root, 'backend');
    try
        webread(HEALTH_URL, chk_opts);
        backend_ok = true;
        fprintf('[BACKEND]  Already running and healthy.  (OK)\n');
    catch
        % Not reachable — write a .bat launcher so Python gets a real
        % console window (start /B kills silent processes on some systems).
        fprintf('[BACKEND]  Not running.  Launching FastAPI server ...\n');

        bat_path = fullfile(project_root, '_launch_backend.bat');
        fid = fopen(bat_path, 'w');
        fprintf(fid, '@echo off\r\n');
        fprintf(fid, 'title MotorGuard Backend (port 8000)\r\n');
        fprintf(fid, 'cd /d "%s"\r\n', backend_dir);
        fprintf(fid, '"%s" run.py\r\n', python_exe);
        fprintf(fid, 'echo.\r\n');
        fprintf(fid, 'echo [Backend stopped] Press any key to close.\r\n');
        fprintf(fid, 'pause > nul\r\n');
        fclose(fid);

        % Open a minimised cmd window — survives independently of MATLAB
        be_cmd = sprintf('start "MotorGuard Backend" /MIN "%s"', bat_path);
        [be_status, be_out] = system(be_cmd);

        if be_status == 0
            fprintf('[BACKEND]  Window launched (minimised).  Waiting for models (up to 120 s)...');
            for k = 1:120
                pause(1);
                try
                    webread(HEALTH_URL, chk_opts);
                    backend_ok = true;
                    fprintf(' OK\n');
                    break;
                catch
                    if mod(k, 10) == 0
                        fprintf(' %ds', k);
                    else
                        fprintf('.');
                    end
                end
            end
            if ~backend_ok
                fprintf('\n[WARNING]  Backend did not respond within 120 s.\n');
                fprintf('           Check the "MotorGuard Backend" terminal window for errors.\n');
                fprintf('           Common causes: missing packages (pip install -r requirements.txt)\n');
                fprintf('           or a previous Python process still holding port 8000.\n');
            end
        else
            fprintf('[BACKEND]  Launch FAILED (system error): %s\n', strtrim(be_out));
            fprintf('           Please start manually:\n');
            fprintf('             cd "%s" && python run.py\n', backend_dir);
        end
    end

    % ── 3.  Verify /api/v1/predict/simulink endpoint is registered ────────
    if backend_ok
        try
            % A GET to a POST endpoint returns 405, not 404 — so any non-404
            % response means the route is registered.
            weboptions_head = weboptions('Timeout', 5);
            webread(PREDICT_URL, weboptions_head);
        catch ME
            if contains(ME.message, '405') || contains(ME.message, 'Method')
                fprintf('[BACKEND]  /api/v1/predict/simulink — route confirmed (405 = POST-only OK).\n');
            elseif contains(ME.message, '404') || contains(ME.message, 'Not Found')
                fprintf('[WARNING]  /api/v1/predict/simulink returned 404.\n');
                fprintf('           The running backend may be an old version.\n');
                fprintf('           Please restart it: cd backend && python run.py\n');
                backend_ok = false;
            else
                % Any other error (timeout, auth) — route likely exists
                fprintf('[BACKEND]  /api/v1/predict/simulink reachable.\n');
            end
        end
    end

    % ── 4.  Final status summary ─────────────────────────────────────────
    fprintf('\n');
    fprintf('------------------------------------------------------------\n');
    fprintf('  SERVER STATUS SUMMARY\n');
    fprintf('------------------------------------------------------------\n');
    if backend_ok
        fprintf('  Backend  : RUNNING   http://127.0.0.1:%d\n', BACKEND_PORT);
        fprintf('             API docs : http://127.0.0.1:%d/docs\n', BACKEND_PORT);
    else
        fprintf('  Backend  : NOT READY (port %d) -- simulation may fail\n', BACKEND_PORT);
        fprintf('             >> Restart: cd backend && python run.py\n');
    end
    fprintf('  Frontend : start manually — cd frontend && npm run dev\n');
    fprintf('------------------------------------------------------------\n');
    fprintf('  Starting simulation ...\n');
    fprintf('============================================================\n\n');

    % ── 5.  Warn if backend is not ready (do not block Simulink) ─────────
    if ~backend_ok
        warning('MotorGuard:BackendNotReady', ...
            'Backend not ready on port %d. Predictions will be unavailable.', BACKEND_PORT);
    end
end
