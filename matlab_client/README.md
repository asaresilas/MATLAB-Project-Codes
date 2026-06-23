Predictive Maintenance MATLAB Client
===================================

Location: matlab_client/ (this folder)

Contents:
- PredictiveMaintenanceClient.m — MATLAB client class (connect, predict, sendGroundTruth, close)
- example_usage.m — MATLAB example script
- motor_ar_view.m — (existing project file)
- time_travel_prognostics.m — (existing project file)
- PredictiveMaintenanceAPI.m — (existing API helper file)

Quick Start (MATLAB)
1. Open MATLAB and add this folder to path (Current Folder = matlab_client)
2. Start API server on your machine:
   - In terminal: `python backend/run.py` (ensure server shows "Application startup complete")
3. In MATLAB command window:
   ```matlab
   cd 'd:\Silas Document\UMaT\Year 4\Project work\Matlab_Project codes\matlab_client'
   client = PredictiveMaintenanceClient('ws://localhost:8000', 'MOTOR-TEST-001');
   client.connect();
   sensor_data = [0.5, 0.3, 0.8, 0.2, 0.9];
   sensor_names = {'Vibration_X','Vibration_Y','Temperature','Current','Pressure'};
   prediction = client.predict(sensor_data, sensor_names);
   disp(prediction);
   client.sendGroundTruth(false, 0, 'normal_operation');
   client.close();
   ```

Files & Docs
- For full integration docs and data flow see: ../DATA_FLOW_PATHS.md and ../WEEK1_IMPLEMENTATION_GUIDE.md
- For quick start steps see: ../QUICK_START.md

Verification
1. Run `python test_matlab_integration.py` from project root to validate end-to-end WebSocket flow.
2. In MATLAB, run `example_usage.m` to exercise client methods.

If you want, I can run the Python connectivity test now or open/move any additional docs into this folder.
