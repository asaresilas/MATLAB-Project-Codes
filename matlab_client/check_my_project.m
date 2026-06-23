% CHECK_MY_PROJECT: Diagnostic script for the Digital Twin
% Run this if you are having connection issues.

clc; clear;
fprintf('--- DIGITAL TWIN DIAGNOSTIC (MATLAB %s) ---\n', version);

%% 1. Check Directory Structure
current_file = mfilename('fullpath');
current_dir = fileparts(current_file);
fprintf('Current Script Location: %s\n', current_dir);

%% 2. Find Python Virtual Environment
found_venv = false;
search_dir = current_dir;
python_exe = '';

for i = 1:4
    fprintf('Searching in: %s...\n', search_dir);
    % Check root or sibling for Matlab_Project codes
    options = {
        fullfile(search_dir, '.venv', 'Scripts', 'python.exe'), ...
        fullfile(search_dir, 'Matlab_Project codes', '.venv', 'Scripts', 'python.exe')
    };
    
    for j = 1:length(options)
        if exist(options{j}, 'file')
            python_exe = options{j};
            found_venv = true;
            break;
        end
    end
    if found_venv, break; end
    search_dir = fileparts(search_dir);
end

if ~found_venv
    error('CRITICAL: Cannot find the folder ".venv". Are you sure you are in the project folder?');
else
    fprintf('[SUCCESS] Found Python at: %s\n', python_exe);
end

%% 3. Check Port 8002
[~, res] = system('netstat -ano | findstr :8002');
if ~isempty(res)
    fprintf('[INFO] Port 8002 is ALREADY ACTIVE. No need to restart.\n');
else
    fprintf('[ACTION] Port 8002 is idle. Attempting to start server...\n');
    % Force start in a NEW window so you can see the errors
    % We need to go 3 levels up from python.exe (Scripts -> .venv -> Matlab_Project codes)
    project_root = fileparts(fileparts(fileparts(python_exe))); 
    cmd = sprintf('cd /d "%s" && start cmd /k ""%s" run_server.py"', ...
                  project_root, python_exe);
    system(cmd);
    fprintf('[WAIT] A black window should have opened. Wait for "Application startup complete".\n');
end

%% 4. Verify AI Class
if exist('PredictiveMaintenanceClient', 'class')
    fprintf('[SUCCESS] PredictiveMaintenanceClient class is on the path.\n');
else
    warning('PredictiveMaintenanceClient is NOT on the path. Add the "matlab_client" folder to your MATLAB path.');
end

fprintf('\n--- DIAGNOSTIC COMPLETE ---\n');
fprintf('Now run test_client.m and see if it works!\n');
