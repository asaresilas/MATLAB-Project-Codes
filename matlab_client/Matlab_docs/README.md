MATLAB Client Docs
===================

This folder contains all MATLAB client files and documentation for using the Predictive Maintenance API.

Files copied here:
- README.md (client quick-start)
- example_usage.m
- PredictiveMaintenanceClient.m
- PredictiveMaintenanceAPI.m
- motor_ar_view.m
- time_travel_prognostics.m

Quick verification:
1. Start API server: `python backend/run.py`
2. Run Python test: `python test_matlab_integration.py`
3. In MATLAB, cd to this folder and run `example_usage.m` or create a MATLAB Function block to use `PredictiveMaintenanceClient`.

Notes:
- I copied the files into this folder so all MATLAB implementation information is centralized.
- I cannot execute MATLAB here; please run MATLAB tests locally (instructions above).
