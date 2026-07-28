% APPLY_GATEWAY_FIX  Patches the MATLAB Function block inside
%                   Centrifugal_and_Motor_Assemble_2.slx with the
%                   try/catch evalin fix for U_rotor and the other
%                   four workspace variables.
%
% Run once from the MATLAB Command Window:
%   run('apply_gateway_fix.m')
%
% The script:
%   1. Opens Centrifugal_and_Motor_Assemble_2.slx (without simulating)
%   2. Finds the embedded MATLAB Function block using Stateflow API
%   3. Replaces its source with simulink_predictive_gateway.m
%   4. Saves the model
%
% After running this script the old crash is gone and you can simulate
% normally.  You do NOT need to run it again unless you overwrite
% simulink_predictive_gateway.m.

fprintf('=== apply_gateway_fix: starting ===\n');

% ── 1. Locate files ─────────────────────────────────────────────────────────
script_dir = fileparts(mfilename('fullpath'));   % .../matlab_client/
gateway_m  = fullfile(script_dir, 'simulink_predictive_gateway.m');

% Model is one folder up (Project work/Simulink Simulation/)
sim_dir    = fullfile(fileparts(script_dir), '..', ...
             'Simulink Simulation');
model_file = fullfile(sim_dir, 'Centrifugal_and_Motor_Assemble_2.slx');

% Normalise path (resolve '..')
model_file = char(java.io.File(model_file).getCanonicalPath());

if ~isfile(gateway_m)
    error('apply_gateway_fix: cannot find %s', gateway_m);
end
if ~isfile(model_file)
    error('apply_gateway_fix: cannot find model at\n  %s', model_file);
end
fprintf('Gateway source : %s\n', gateway_m);
fprintf('Simulink model : %s\n', model_file);

% ── 2. Read the fixed gateway code ──────────────────────────────────────────
new_code = fileread(gateway_m);
fprintf('Gateway code read: %d chars\n', numel(new_code));

% Quick sanity check: both critical fixes must be present
if ~contains(new_code, 'try; U_rotor_val')
    error(['apply_gateway_fix: simulink_predictive_gateway.m is missing the ' ...
           'U_rotor try/catch fix.\nExpected "try; U_rotor_val = ..." near line 151.\n' ...
           'Check that the file was saved correctly.']);
end
if ~contains(new_code, 'T_stator_K')
    error(['apply_gateway_fix: simulink_predictive_gateway.m is missing the ' ...
           'workspace temperature fix.\nExpected "T_stator_K" near the scalars line.\n' ...
           'Check that the file was saved correctly.']);
end
fprintf('try/catch fix and workspace temperature fix verified in source.\n');

% ── 3. Open the model ────────────────────────────────────────────────────────
model_name = 'Centrifugal_and_Motor_Assemble_2';
if ~bdIsLoaded(model_name)
    fprintf('Loading model (this may take a moment)...\n');
    load_system(model_file);
else
    fprintf('Model already loaded.\n');
end

% ── 4. Find the MATLAB Function block via Stateflow API ─────────────────────
rt     = sfroot;
charts = rt.find('-isa', 'Stateflow.EMChart');

target_chart = [];
for k = 1 : numel(charts)
    try
        p = charts(k).Path;
        if contains(p, model_name) && contains(p, 'MATLAB Function')
            target_chart = charts(k);
            fprintf('Found chart: %s\n', p);
            break
        end
    catch
        % skip charts with inaccessible paths
    end
end

if isempty(target_chart)
    % Fallback: look for any EMChart in the model that has the gateway signature
    for k = 1 : numel(charts)
        try
            scr = charts(k).Script;
            if contains(scr, 'simulink_predictive_gateway') || ...
               contains(scr, 'U_rotor_val')
                target_chart = charts(k);
                fprintf('Found chart by content: %s\n', charts(k).Path);
                break
            end
        catch
        end
    end
end

if isempty(target_chart)
    error(['apply_gateway_fix: could not find the MATLAB Function block.\n' ...
           'Make sure the model contains a block named "MATLAB Function".\n' ...
           'Available charts:\n%s'], ...
          strjoin(arrayfun(@(c) c.Path, charts, 'UniformOutput', false), '\n'));
end

% ── 5. Replace the embedded code ─────────────────────────────────────────────
fprintf('Patching MATLAB Function block...\n');
target_chart.Script = new_code;
fprintf('Code replaced (%d chars).\n', numel(new_code));

% ── 6. Save the model ────────────────────────────────────────────────────────
fprintf('Saving model...\n');
save_system(model_name);
fprintf('Model saved: %s\n', model_file);

fprintf('=== apply_gateway_fix: DONE ===\n');
fprintf('You can now run motor_params_normal.m and then simulate.\n');
