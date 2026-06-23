classdef PredictiveMaintenanceAPI < handle
    % PredictiveMaintenanceAPI Client for interacting with the Python API
    % Includes: Circuit Breaker, Auto-Relogin, Dashboard, Async, Logging
    
    properties
        BaseURL
        Token
        IsAuthenticated = false
        Options
        Username
        Password
        
        % Robustness Properties (Circuit Breaker)
        FailCount = 0
        Features
        LastFailTime = 0
        CircuitOpen = false
        RetryInterval = 30; % seconds to wait before trying again
        MaxFailures = 3;    % failures before opening circuit
        
        % Logging
        LogEnabled = false
        LogFile = 'maintenance_log.mat';
        
        % Dashboard
        DashboardFig
        DashboardHandles
    end
    
    methods
        function obj = PredictiveMaintenanceAPI(baseUrl)
            % Constructor
            if nargin < 1
                baseUrl = 'http://localhost:8000/api/v1';
            end
            if endsWith(baseUrl, '/')
                baseUrl = baseUrl(1:end-1);
            end
            obj.BaseURL = baseUrl;
            obj.Options = weboptions('ContentType', 'json', 'MediaType', 'application/json', 'Timeout', 10);
        end
        
        function success = start_server(obj, project_path)
            % Attempt to start the Python server
            if nargin < 2
                currentFile = mfilename('fullpath');
                [clientDir, ~, ~] = fileparts(currentFile);
                project_path = fileparts(clientDir);
            end
            
            cmd = sprintf('cd "%s" & start /B uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 &', project_path);
            try
                status = system(cmd);
                success = (status == 0);
            catch
                success = false;
            end
        end
        
        function success = login(obj, username, password)
            url = [obj.BaseURL, '/auth/token'];
            data = struct('username', username, 'password', password);
            try
                authOpts = weboptions('MediaType', 'application/x-www-form-urlencoded', 'Timeout', 5);
                response = webwrite(url, data, authOpts);
                
                obj.Token = response.access_token;
                obj.IsAuthenticated = true;
                obj.Username = username;
                obj.Password = password;
                
                obj.Options = weboptions('ContentType', 'json', 'MediaType', 'application/json', ...
                    'Timeout', 10, 'HeaderFields', {'Authorization', ['Bearer ', obj.Token]});
                
                % Reset Circuit Breaker on successful login
                obj.FailCount = 0;
                obj.CircuitOpen = false;
                success = true;
                disp('PredictiveMaintenanceAPI: Login successful.');
            catch ME
                success = false;
                disp(['PredictiveMaintenanceAPI: Login failed. ', ME.message]);
            end
        end
        
        function enable_logging(obj, filename)
            if nargin > 1; obj.LogFile = filename; end
            obj.LogEnabled = true;
            disp(['Logging enabled to ', obj.LogFile]);
        end
        
        function result = diagnose_comprehensive(obj, vibration, temperature, speed, current)
            % safe_result template for Safe Mode
            safe_result = struct('rul_hours', -1, 'rul_confidence', 0, ...
                'bearing_analysis', struct('fault_type', 'Unknown', 'confidence', 0), ...
                'motor_analysis', struct('status', 'Unknown', 'confidence', 0), ...
                'electrical_analysis', struct('status', 'Unknown'), ...
                'overall_health', 'Connection Error', 'priority_action', 'Check Server');
            
            if nargin < 3; temperature = 25.0; end
            if nargin < 4; speed = 1750.0; end
            if nargin < 5; current = []; end
            
            % 1. Input Validation
            if any(isnan(vibration)) || any(isinf(vibration))
                disp('Warning: Vibration signal contains NaN/Inf. Replacing with zeros.');
                vibration(isnan(vibration)) = 0;
                vibration(isinf(vibration)) = 0;
            end
            
            % 2. Circuit Breaker Check
            if obj.CircuitOpen
                if (now * 86400 - obj.LastFailTime) > obj.RetryInterval
                    disp('Circuit Breaker: Half-Open (Retrying connection...)');
                    % Allow one request to pass (Half-Open)
                else
                    % Circuit still open, return safe result immediately
                    result = safe_result;
                    return;
                end
            end
            
            % Auto-login
            if ~obj.IsAuthenticated && ~isempty(obj.Username)
                obj.login(obj.Username, obj.Password);
            end
            
            url = [obj.BaseURL, '/diagnose/comprehensive'];
            
            % Downsampling for large signals (>10k) to speed up JSON
            if length(vibration) > 10000
                vibration = vibration(1:2:end);
            end
            
            payload = struct();
            if isrow(vibration); vibration = vibration(:); end
            payload.vibration_signal = vibration;
            payload.temperature = temperature;
            payload.speed = speed;
            if ~isempty(current); payload.current_signal = current; end
            
            try
                result = webwrite(url, payload, obj.Options);
                
                % Success! Reset mechanism
                obj.FailCount = 0;
                obj.CircuitOpen = false;
                
                % Update Dashboard if active
                obj.update_dashboard(result);
                
                % Log data
                if obj.LogEnabled
                    obj.log_data(result, temperature, speed);
                end
                
            catch ME
                % Failure Logic
                obj.FailCount = obj.FailCount + 1;
                obj.LastFailTime = now * 86400;
                disp(['API Error: ', ME.message]);
                
                % Check for permanent failure condition
                if obj.FailCount >= obj.MaxFailures
                    obj.CircuitOpen = true;
                    disp('Circuit Breaker: OPEN (Too many failures). Pausing requests for 30s.');
                end
                
                % Try re-auth once if 401, but careful not to loop infinite
                if (contains(ME.message, '401') || contains(ME.message, 'Unauthorized')) && obj.FailCount < 2
                    disp('Token expired. Re-authenticating...');
                    if obj.login(obj.Username, obj.Password)
                        result = obj.diagnose_comprehensive(vibration, temperature, speed, current);
                        return;
                    end
                end
                
                result = safe_result;
            end
        end
        
        function future = diagnose_async(obj, vibration, temperature, speed, current)
            % Asynchronous diagnosis using Parallel Computing Toolbox
            if isempty(ver('parallel')) && isempty(ver('distcomp'))
                error('PredictiveMaintenanceAPI: Async requires Parallel Computing Toolbox.');
            end
            
            % Use parfeval to run in background
            % We pass basic data types, not the 'obj' itself, to avoid serialization issues
            future = parfeval(@bg_wrapper, 1, obj.BaseURL, obj.Token, vibration, temperature, speed, current);
        end
        
        function show_dashboard(obj)
            % Create a MATLAB Dashboard for monitoring
            if isempty(obj.DashboardFig) || ~isvalid(obj.DashboardFig)
                obj.DashboardFig = figure('Name', 'Predictive Maintenance Dashboard', ...
                    'NumberTitle', 'off', 'MenuBar', 'none', 'ToolBar', 'none', ...
                    'Position', [100, 100, 600, 400], 'Color', 'w');
                
                % UI Layout
                layout = uigridlayout(obj.DashboardFig, [2, 3]);
                layout.RowHeight = {'1x', '1x'};
                layout.ColumnWidth = {'1x', '1x', '1x'};
                
                % Panels
                p1 = uipanel(layout, 'Title', 'RUL (Hours)', 'FontSize', 14, 'BackgroundColor', 'w');
                p2 = uipanel(layout, 'Title', 'Confidence', 'FontSize', 14, 'BackgroundColor', 'w');
                p3 = uipanel(layout, 'Title', 'Health Status', 'FontSize', 14, 'BackgroundColor', 'w');
                
                obj.DashboardHandles.lblRUL = uilabel(p1, 'Text', '--', 'FontSize', 36, ...
                    'HorizontalAlignment', 'center', 'Position', [10, 50, 180, 60]);
                
                obj.DashboardHandles.lblConf = uilabel(p2, 'Text', '--%', 'FontSize', 36, ...
                    'HorizontalAlignment', 'center', 'Position', [10, 50, 180, 60]);
                
                obj.DashboardHandles.lampHealth = uilamp(p3, 'Position', [75, 50, 50, 50], 'Color', 'g');
                obj.DashboardHandles.lblHealth = uilabel(p3, 'Text', 'Healthy', 'FontSize', 16, ...
                    'HorizontalAlignment', 'center', 'Position', [10, 10, 180, 30]);
                
            else
                figure(obj.DashboardFig); % Bring to front
            end
        end
        
        function update_dashboard(obj, res)
            if ~isempty(obj.DashboardFig) && isvalid(obj.DashboardFig)
                % Update RUL
                obj.DashboardHandles.lblRUL.Text = sprintf('%.1f', res.rul_hours);
                obj.DashboardHandles.lblConf.Text = sprintf('%.1f%%', res.rul_confidence * 100);
                
                % Update Health Status Lamp
                switch res.overall_health
                    case 'Healthy'
                        obj.DashboardHandles.lampHealth.Color = 'g';
                        obj.DashboardHandles.lblHealth.Text = 'Healthy';
                    case 'Warning'
                        obj.DashboardHandles.lampHealth.Color = 'y';
                        obj.DashboardHandles.lblHealth.Text = 'Warning';
                    otherwise % Critical or other
                        obj.DashboardHandles.lampHealth.Color = 'r';
                        obj.DashboardHandles.lblHealth.Text = 'CRITICAL';
                end
                
                drawnow limitrate;
            end
        end
        
        function log_data(obj, res, temp, speed)
            % Simple persistent logging
            try
                % Load existing or create new
                if exist(obj.LogFile, 'file')
                    data = load(obj.LogFile);
                    log = data.log;
                else
                    log = struct('time', [], 'rul', [], 'health', {});
                end
                
                % Append
                idx = length(log.time) + 1;
                log.time(idx) = now;
                log.rul(idx) = res.rul_hours;
                log.health(idx) = {res.overall_health};
                
                save(obj.LogFile, 'log');
            catch
                % Ignore logging errors to prevent blocking
            end
        end
    end
end

% Wrapper outside of methods block (MATLAB local function)
function res = bg_wrapper(baseUrl, token, vib, temp, spd, curr)
% Create a TEMPORARY api instance for the worker
api_worker = PredictiveMaintenanceAPI(baseUrl);

% Manually set token to avoid re-login network call
api_worker.Token = token;
api_worker.IsAuthenticated = true;
% Update options manually as well
api_worker.Options = weboptions('ContentType', 'json', 'MediaType', 'application/json', ...
    'Timeout', 60, 'HeaderFields', {'Authorization', ['Bearer ', token]});

res = api_worker.diagnose_comprehensive(vib, temp, spd, curr);
end
