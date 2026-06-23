function start_ai_server()
    % START_AI_SERVER: Automatically launch the Python AI backend
    % This script should be added to the Simulink InitFcn callback.
    
    SERVER_PORT = 8001;
    fprintf('\n[AUTO-START] Checking for AI Server on port %d...\n', SERVER_PORT);
    
    % 1. Check if server is already running (Windows specific)
    [~, result] = system(sprintf('netstat -ano | findstr :%d', SERVER_PORT));
    
    if ~isempty(result)
        fprintf('[INFO] Server is already running. Ready for simulation.\n');
        return;
    end
    
    % 2. Robust Path Discovery: Search for "Matlab_Project codes" folder
    current_file = mfilename('fullpath');
    current_dir = fileparts(current_file);
    
    python_exe = '';
    search_dir = current_dir;
    
    % Search up to 3 levels up for the sibling project folder
    for i = 1:3
        % Option A: Sibling folder "Matlab_Project codes"
        check_dir = fullfile(search_dir, 'Matlab_Project codes');
        check_exe = fullfile(check_dir, '.venv', 'Scripts', 'python.exe');
        
        % Option B: We are already inside "Matlab_Project codes"
        self_check = fullfile(search_dir, '.venv', 'Scripts', 'python.exe');
        
        if exist(check_exe, 'file')
            python_exe = check_exe;
            project_root = check_dir;
            break;
        elseif exist(self_check, 'file')
            python_exe = self_check;
            project_root = search_dir;
            break;
        end
        search_dir = fileparts(search_dir); % Move up one level
    end
    
    if isempty(python_exe)
        warning('Could not find AI Backend in "Matlab_Project codes" or current folder.');
        fprintf('[MANUAL] Please ensure your Python folder and Simulink folder are next to each other.\n');
        return;
    end
    
    % Use short names or wrap in double quotes to handle spaces
    python_exe_quoted = sprintf('"%s"', python_exe);
    project_root_quoted = sprintf('"%s"', project_root);
    
    % 4. Construct the start command
    % Use 'start /B' to run in background
    % Explicitly call run_server.py since it handles absolute pathing correctly
    cmd = sprintf('cd /d %s && start /B "" %s run_server.py', ...
                  project_root_quoted, python_exe_quoted);
    
    fprintf('[EXECUTE] Launching Python FastAPI Backend...\n');
    [status, cmd_out] = system(cmd);
    
    if status == 0
        fprintf('[SUCCESS] Server launch sequence initiated.\n');
        fprintf('[WAIT] Initializing models (Attention, CNN, LSTM)... Please wait 10s.\n');
        pause(10); % Give TensorFlow time to load weights
        fprintf('[READY] AI Models Loaded. Starting simulation...\n\n');
    else
        warning('Failed to launch server automatically: %s', cmd_out);
        fprintf('[MANUAL] Please run: .\\.venv\\Scripts\\python.exe -m uvicorn backend.app.main:app manually.\n');
    end
end
