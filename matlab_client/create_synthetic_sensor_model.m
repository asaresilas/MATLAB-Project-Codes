% create_synthetic_sensor_model.m
% Automatically builds the synthetic_sensor_test.slx Simulink model
% MATLAB 2025b Compatible Version

clear all; close all; clc;

% Print MATLAB version
v = version;
disp(['[INFO] MATLAB Version: ' v]);

model_name = 'synthetic_sensor_test';
model_path = fullfile(pwd, [model_name '.slx']);

% Check if model already exists, close it
try
    close_system(model_name, 0);
catch
end

% Delete any existing file
if isfile(model_path)
    delete(model_path);
    disp('[INFO] Deleted existing model file');
end

% Create a new model
new_system(model_name);
open_system(model_name);

% Set model parameters (compatible with 2025b)
try
    set_param(model_name, 'SolverType', 'Fixed-step');
    set_param(model_name, 'Solver', 'FixedStepDiscrete');
    set_param(model_name, 'FixedStep', '0.001');
    set_param(model_name, 'StopTime', '60');
catch err
    warning('[WARNING] Could not set all solver params');
end

disp(['[INFO] Created model: ' model_name]);
disp('[INFO] Running on MATLAB 2025b');
disp('[INFO] Adding 15 blocks...');

% 1. Clock
add_block('simulink/Sources/Clock', [model_name '/Clock'], 'Position', [50, 50, 80, 80]);
disp('  Clock added');

% 2. Sine Wave 1 (Vib_X)
add_block('simulink/Sources/Sine Wave', [model_name '/Sine_X'], 'Position', [50, 120, 130, 150]);
set_param([model_name '/Sine_X'], 'Frequency', '10', 'Amplitude', '0.5', 'Phase', '0');
disp('  Sine_X added');

% 3. Sine Wave 2 (Vib_Y)
add_block('simulink/Sources/Sine Wave', [model_name '/Sine_Y'], 'Position', [50, 180, 130, 210]);
set_param([model_name '/Sine_Y'], 'Frequency', '10', 'Amplitude', '0.5', 'Phase', '2.094');
disp('  Sine_Y added');

% 4. Sine Wave 3 (Vib_Z)
add_block('simulink/Sources/Sine Wave', [model_name '/Sine_Z'], 'Position', [50, 240, 130, 270]);
set_param([model_name '/Sine_Z'], 'Frequency', '10', 'Amplitude', '0.5', 'Phase', '4.189');
disp('  Sine_Z added');

% 5. Ramp
add_block('simulink/Sources/Ramp', [model_name '/Ramp_Temp'], 'Position', [50, 300, 130, 330]);
set_param([model_name '/Ramp_Temp'], 'Slope', '0.1', 'Start time', '0', 'InitialOutput', '0');
disp('  Ramp_Temp added');

% 6. Constant Speed
add_block('simulink/Sources/Constant', [model_name '/Const_Speed'], 'Position', [50, 360, 130, 390]);
set_param([model_name '/Const_Speed'], 'Value', '1500');
disp('  Const_Speed added');

% 7. Constant Current
add_block('simulink/Sources/Constant', [model_name '/Const_Current'], 'Position', [50, 420, 130, 450]);
set_param([model_name '/Const_Current'], 'Value', '10');
disp('  Const_Current added');

% 8. Constant Temperature
add_block('simulink/Sources/Constant', [model_name '/Const_Temp'], 'Position', [50, 480, 130, 510]);
set_param([model_name '/Const_Temp'], 'Value', '35');
disp('  Const_Temp added');

% 9. Constant Extra
add_block('simulink/Sources/Constant', [model_name '/Const_Extra'], 'Position', [50, 540, 130, 570]);
set_param([model_name '/Const_Extra'], 'Value', '0');
disp('  Const_Extra added');

% 10. Mux
add_block('simulink/Signal Routing/Mux', [model_name '/Mux_Sensors'], 'Position', [250, 200, 280, 480]);
set_param([model_name '/Mux_Sensors'], 'Inputs', '8');
disp('  Mux_Sensors added');

% 11. Rate Transition
add_block('simulink/Signal Attributes/Rate Transition', [model_name '/RateTransition_1Hz'], 'Position', [350, 330, 410, 360]);
set_param([model_name '/RateTransition_1Hz'], 'OutputPortSampleTime', '1');
disp('  RateTransition_1Hz added');

% 12. MATLAB Function
add_block('simulink/User-Defined Functions/MATLAB Function', [model_name '/predict_maintenance'], 'Position', [500, 320, 600, 370]);
disp('  predict_maintenance added');

% 13. Display
add_block('simulink/Sinks/Display', [model_name '/Display_Prediction'], 'Position', [680, 330, 760, 360]);
disp('  Display_Prediction added');

% 14. To File
add_block('simulink/Sinks/To File', [model_name '/ToFile_Sensors'], 'Position', [350, 420, 420, 450]);
set_param([model_name '/ToFile_Sensors'], 'VariableName', 'sensor_data', 'SaveFormat', 'Structure with time');
disp('  ToFile_Sensors added');

% 15. To Workspace
add_block('simulink/Sinks/To Workspace', [model_name '/ToWorkspace_Predictions'], 'Position', [680, 420, 760, 450]);
set_param([model_name '/ToWorkspace_Predictions'], 'VariableName', 'predictions_log', 'SaveFormat', 'Array');
disp('  ToWorkspace_Predictions added');

disp('[INFO] All 15 blocks created');
disp('[INFO] Now wiring blocks...');

% CONNECT BLOCKS
try
    add_line(model_name, 'Sine_X/1', 'Mux_Sensors/1', 'autorouting', 'on');
    add_line(model_name, 'Sine_Y/1', 'Mux_Sensors/2', 'autorouting', 'on');
    add_line(model_name, 'Sine_Z/1', 'Mux_Sensors/3', 'autorouting', 'on');
    add_line(model_name, 'Const_Speed/1', 'Mux_Sensors/4', 'autorouting', 'on');
    add_line(model_name, 'Const_Current/1', 'Mux_Sensors/5', 'autorouting', 'on');
    add_line(model_name, 'Const_Temp/1', 'Mux_Sensors/6', 'autorouting', 'on');
    add_line(model_name, 'Ramp_Temp/1', 'Mux_Sensors/7', 'autorouting', 'on');
    add_line(model_name, 'Const_Extra/1', 'Mux_Sensors/8', 'autorouting', 'on');
    add_line(model_name, 'Mux_Sensors/1', 'RateTransition_1Hz/1', 'autorouting', 'on');
    add_line(model_name, 'RateTransition_1Hz/1', 'predict_maintenance/1', 'autorouting', 'on');
    add_line(model_name, 'RateTransition_1Hz/1', 'ToFile_Sensors/1', 'autorouting', 'on');
    add_line(model_name, 'predict_maintenance/1', 'Display_Prediction/1', 'autorouting', 'on');
    add_line(model_name, 'predict_maintenance/1', 'ToWorkspace_Predictions/1', 'autorouting', 'on');
    disp('[INFO] All connections made');
catch err
    warning('[WARNING] Some connections failed');
end

% Create sim_logs folder
sim_logs_dir = fullfile(pwd, 'sim_logs');
if not(exist(sim_logs_dir, 'dir'))
    mkdir(sim_logs_dir);
    disp('[INFO] Created folder: sim_logs');
end

% Save model
save_system(model_name, model_path);
disp(['[INFO] Model saved: ' model_path]);

% Display summary
disp(' ');
disp('====================================================================');
disp('Success! Simulink Model Created');
disp('====================================================================');
fprintf('Model: %s\n', model_name);
fprintf('Path: %s\n', model_path);
fprintf('Blocks: 15 total\n');
fprintf('Sensors: 8\n');
disp(' ');
disp('NEXT STEP:');
disp('1. Double-click predict_maintenance block');
disp('2. Copy code from: predict_maintenance_fcn.txt');
disp('3. Paste into MATLAB Function block');
disp('4. Click Run to simulate');
disp('====================================================================');
disp(' ');

close_system(model_name, 0);
open_system(model_name);
disp('[INFO] Model ready. Block diagram now open in Simulink.');
