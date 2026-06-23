% matlab_phase1_test.m
% Quick test script to verify `PredictiveMaintenanceClient` connects and gets a prediction.

try
    client = PredictiveMaintenanceClient();
    client.connect();
    disp('[INFO] Connected to server.');

    % Create a sample sensor vector matching recommended 15 sensors
    sensor_vector = randn(1,15); % replace with realistic samples in real test
    sensor_names = { 'Vib_X','Vib_Y','Vib_Z', 'Vib_Fan', 'I_A','I_B','I_C', 'Temp_1', 'Temp_2', 'Speed', 'Pressure', 'Thermal_1', 'Thermal_2', 'Extra_1', 'Extra_2' };
    sample_rate_hz = 10000; % example
    tstamp = posixtime(datetime('now'));

    % If PredictiveMaintenanceClient provides predict(sensor_data, sensor_names)
    try
        resp = client.predict(sensor_vector, sensor_names);
        disp('[INFO] Prediction response:');
        disp(resp);
    catch predErr
        warning(sprintf('Prediction call failed: %s', predErr.message));
    end

    % Optional: send ground-truth example
    % client.sendGroundTruth(0, 999, 'none');

    client.close();
    disp('[INFO] Connection closed.');
catch ME
    disp('[ERROR] Phase1 test failed:');
    disp(getReport(ME));
end
