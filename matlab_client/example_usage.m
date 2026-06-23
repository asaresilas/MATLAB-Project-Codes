% Advanced Usage Script for Predictive Maintenance API
% Demonstrates Circuit Breaker, Dashboard, and Robustness

% 1. Setup
addpath(genpath(pwd));
baseUrl = 'http://localhost:8002/api/v1';
api = PredictiveMaintenanceAPI(baseUrl);

% 2. Start Dashboard
api.show_dashboard();
fprintf('Dashboard launched.\n');

% 3. Authenticate
if api.login('admin', 'admin123')
    
    % Enable Logging
    api.enable_logging('my_simulation_log.mat');
    
    % 4. Simulate Real-Time Loop
    fprintf('Starting Real-Time Simulation Loop (Press Ctrl+C to stop)...\n');
    
    fs = 10000;
    t_step = 0.5; % Call every 0.5 seconds
    
    for i = 1:20
        % Generate Data (varying signal health)
        t = (0:1/fs:1)';
        
        if i < 10
            % Healthy
            s = 0.01 * randn(size(t));
        else
            % Degrading
            s = (i/20) * 0.5 * sin(2*pi*60*t) + 0.1 * randn(size(t));
        end
        
        temp = 45 + (i * 0.5);
        
        % CALL API
        res = api.diagnose_comprehensive(s, temp, 1750);
        
        fprintf('[Step %d] RUL: %.1f h | Health: %s | Status: %s\n', ...
            i, res.rul_hours, res.overall_health, ...
            res.bearing_analysis.fault_type);
        
        pause(t_step);
    end
    
else
    fprintf('Authentication Failed.\n');
end
