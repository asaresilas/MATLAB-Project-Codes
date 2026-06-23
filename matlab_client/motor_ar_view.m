% AR Overlay Visualization for Digital Twin
% This script creates a 3D visualization of the motor and updates its color
% based on the API diagnosis result.

function motor_ar_view(result)
% Creates or updates a 3D motor view
% Usage: motor_ar_view(api_result_struct)

persistent fig_handle motor_body bearing_housing

if isempty(fig_handle) || ~isvalid(fig_handle)
    fig_handle = figure('Name', 'Digital Twin AR Overlay', 'Color', 'w');
    axis equal; grid on; hold on;
    view(3);
    xlabel('X'); ylabel('Y'); zlabel('Z');
    title('Motor Health Status (Real-Time)');
    
    % Draw Motor Body (Cylinder)
    [X, Y, Z] = cylinder(0.5, 20);
    Z = Z * 2; % Scale length
    motor_body = surf(X, Y, Z, 'FaceColor', 'gray', 'EdgeColor', 'none', 'FaceAlpha', 0.5);
    
    % Draw Bearing Housing (Ring)
    [Xb, Yb, Zb] = cylinder(0.55, 20);
    Zb = Zb * 0.2 + 2; % Position at end
    bearing_housing = surf(Xb, Yb, Zb, 'FaceColor', 'blue', 'EdgeColor', 'none');
    
    % Lighting
    camlight; lighting gouraud;
end

figure(fig_handle); % Bring to focus

% Update Colors based on Result

% 1. Bearing Status
fault = result.bearing_analysis.fault_type;
if contains(fault, 'Normal')
    set(bearing_housing, 'FaceColor', 'g'); % Green
elseif contains(fault, 'Outer') || contains(fault, 'Inner') || contains(fault, 'Ball')
    set(bearing_housing, 'FaceColor', 'r'); % Red (Fault)
else
    set(bearing_housing, 'FaceColor', 'y'); % Yellow (Unknown/Warning)
end

% 2. Overall Motor Health
health = result.overall_health;
switch health
    case 'Healthy'
        set(motor_body, 'FaceColor', [0.8 0.8 0.8]); % Light Gray
        title('Motor Health: HEALTHY', 'Color', 'g');
    case 'Warning'
        set(motor_body, 'FaceColor', [1 1 0]); % Yellow Tint
        title('Motor Health: WARNING', 'Color', [0.8 0.6 0]);
    case 'Critical'
        set(motor_body, 'FaceColor', [1 0 0]); % Red Tint
        title('Motor Health: CRITICAL', 'Color', 'r');
end

drawnow;
end
