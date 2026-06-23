Simulink Phase 1 Wiring Guide

Purpose: create a minimal virtual motor simulation that emits sensor vectors and logs them using `Log_Sensor_Data`.

Blocks (core):
- Clock (Simulink -> Sources)
- Virtual Motor (Subsystem) [SIMULINK BLOCK: user-created subsystem that simulates motor physics]
- Sensor Simulator (Subsystem) [SIMULINK BLOCK: generates vibration/current/temp signals]
- Mux (Simulink -> Signal Routing) to combine signals into a vector
- Buffer (DSP System Toolbox or Signal Processing) optional for batching
- MATLAB Function (User-Defined) -> Place `Log_Sensor_Data` call here [SIMULINK FUNCTION BLOCK REQUIRED]
- To Workspace / To File for backup
- Scope (optional) for live plotting

Connections:
1. Clock -> Virtual Motor subsystem input (time)
2. Virtual Motor -> Sensor Simulator (parameters, states)
3. Sensor Simulator outputs individual signals: Vib_X, Vib_Y, Vib_Z, I_A, I_B, I_C, Temp1, Speed
4. Feed each sensor output into a `Mux` (set number of inputs = N sensors)
5. `Mux` output -> MATLAB Function block input `sensor_vector`
6. MATLAB Function block calls `Log_Sensor_Data(sensor_vector, sensor_names, sample_rate, tstamp)`
7. Optionally duplicate `Mux` output into `To File` or `To Workspace` for post-run analysis

Simulink Function Block details (predict_maintenance vs logging):
- `Log_Sensor_Data` block: only writes one sample per call. If simulation runs at high sample rates (10 kHz), prefer logging inside a `To File` block or downsample to 1000 Hz before writing to CSV.
- `predict_maintenance` block: should operate at a lower rate (e.g., 1 Hz). Use a Rate Transition or a Buffer + Trigger to collect N-samples, then call prediction.

Recommended rates:
- Raw vibration: 10 kHz (keep internal, but log downsampled)
- Prediction: 1 Hz (send a 1024-sample window every second)

Checklist to create model:
- [ ] Create new model `motor_virtual_system.slx`
- [ ] Add `Clock`, `Virtual Motor` subsystem, `Sensor Simulator` subsystem
- [ ] Wire sensors to `Mux` and to `To Workspace` for quick checks
- [ ] Add MATLAB Function block named `Log_Sensor_Data_Block` and paste call to `Log_Sensor_Data`
- [ ] Add second MATLAB Function block `predict_maintenance` (see IMPLEMENTATION_CHECKLIST.txt for code)
- [ ] Run simulation for 60 seconds, trigger fault injection at t=30s in `Virtual Motor` subsystem

Notes:
- Mark blocks that must be user-edited: `Virtual Motor`, `Sensor Simulator`, `predict_maintenance` as [SIMULINK FUNCTION BLOCK REQUIRED] where appropriate.
- If MATLAB Function block file I/O is restricted in your Simulink configuration, use a `To File` block.
