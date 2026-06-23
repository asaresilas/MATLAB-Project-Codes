import os
import sys
import numpy as np
import joblib

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SOURCE_CACHE = os.path.join(DATA_DIR, "fusion_test_cache.npz")
OUTPUT_FILE = os.path.join(DATA_DIR, "aligned_digital_twin.npz")

np.random.seed(42)

def build_aligned_digital_twin():
    print(" Initializing High-Rigor Digital Twin Alignment...")
    
    if not os.path.exists(SOURCE_CACHE):
        print(f"Error: Could not find source cache at {SOURCE_CACHE}")
        sys.exit(1)
        
    print(f"Loading modality pools from {SOURCE_CACHE}...")
    cache = np.load(SOURCE_CACHE)
    
    # Extract Raw Modalities
    raw_Xs = {
        'vibration_cwru': cache['cwru_x'],
        'vibration_ind': cache['ind_x'],
        'nasa_seq': cache['nasa_x'],
        'current': cache['curr_x'],
        'thermal': cache['therm_x']
    }
    
    raw_ys = {
        'vibration_cwru': cache['cwru_y'],
        'vibration_ind': cache['ind_y'],
        'nasa_seq': cache['nasa_y'],
        'current': cache['curr_y'],
        'thermal': cache['therm_y']
    }
    raw_rul = {
        'nasa_seq': cache['nasa_rul'] if 'nasa_rul' in cache.files else None
    }
    
    # 1. Use NASA as the Master Backbone
    # We take a continuous sequence from NASA to represent a "real" trajectory
    print("\nExtracting NASA Backbone (Master State Evolution)...")
    X_N = raw_Xs['nasa_seq']
    y_N = raw_ys['nasa_seq']
    rul_N = raw_rul['nasa_seq']
    
    # We'll take the first 100 samples of NASA to simulate a degradation run
    # (In a real scenario, this would be a single unit's run-to-failure)
    n_trajectory = min(150, len(X_N))
    trajectory_indices = np.arange(n_trajectory)
    
    master_y = y_N[trajectory_indices]
    master_rul_pct = rul_N[trajectory_indices] if rul_N is not None else None
    
    print(f"  Backbone length: {n_trajectory} time-steps")
    
    # 2. Synchronize other modalities with probabilistic disagreement
    print("Aligning Modal Experts to Master State (Introducing Sensor Conflict)...")
    aligned_data = {mod: [] for mod in raw_Xs.keys()}
    aligned_data['nasa_seq'] = X_N[trajectory_indices]
    
    for i in range(n_trajectory):
        master_state = master_y[i]
        
        for mod_name in ['vibration_cwru', 'vibration_ind', 'current', 'thermal']:
            pool_X = raw_Xs[mod_name]
            pool_y = raw_ys[mod_name]
            
            # SCIENTIFIC HARDENING: Introduce State Disagreement
            # 85% Correct, 10% Neighboring State (Lag/Lead), 5% Random (Noise)
            rand = np.random.random()
            if rand < 0.85:
                target_state = master_state
            elif rand < 0.95:
                # Neighboring state (Lag or Lead)
                target_state = np.clip(master_state + np.random.choice([-1, 1]), 0, 2)
            else:
                # Random noise / sensor malfunction
                target_state = np.random.randint(0, 3)
            
            # Find all indices in this modality pool that match the (possibly shifted) target state
            matching_indices = np.where(pool_y == target_state)[0]
            
            if len(matching_indices) == 0:
                idx = np.random.randint(0, len(pool_X))
            else:
                # Using deterministic randomness based on i to keep trajectory stable
                idx = matching_indices[(i + i//10) % len(matching_indices)]
                
            aligned_data[mod_name].append(pool_X[idx])
            
    # Convert lists to arrays
    final_data = {}
    for mod_name, data_list in aligned_data.items():
        if isinstance(data_list, list):
            final_data[mod_name] = np.array(data_list)
        else:
            final_data[mod_name] = data_list
            
    # 3. Generate Shared RUL Target (NASA-Grounded)
    print("\nGenerating Physically-Grounded RUL Trajectory...")
    max_hours = 20000.0
    if master_rul_pct is not None:
        shared_rul_pct = master_rul_pct.astype(np.float32)
        shared_rul = ((shared_rul_pct / 100.0) * max_hours).astype(np.float32)
        progress = 1.0 - np.clip(shared_rul_pct / 100.0, 0.0, 1.0)
    else:
        print("  [!] NASA RUL target missing in source cache. Falling back to simulated trajectory.")
        progress = np.linspace(0, 1, n_trajectory)
        shared_rul = (max_hours * (1.0 - progress**1.5)).astype(np.float32)
        shared_rul_pct = ((shared_rul / max_hours) * 100.0).astype(np.float32)
    
    # 4. Synthesize Scalar Telemetry (mapped to Master State)
    print("Synthesizing Coherent Scalar Telemetry...")
    scalars = np.zeros((n_trajectory, 9), dtype=np.float32)
    for i in range(n_trajectory):
        p = progress[i]
        # Temperature rises non-linearly
        temp = 40.0 + (p**2 * 55.0) + np.random.normal(0, 1.5)
        scalars[i, 0] = temp # Bearing Temp
        scalars[i, 1] = temp + 8.0 # Stator Temp
        scalars[i, 2] = 0.5 + (p**3 * 10.0) # RMS Vibration (Exponential rise)
        scalars[i, 3] = 1750.0 - (p**2 * 40.0) # RPM Slip
        scalars[i, 4:] = np.random.normal(100, 2, 5) # Stable auxiliary metrics
        
    # 5. Save the Hardened Dataset
    print(f"\nSaving Aligned Digital Twin Archive to {OUTPUT_FILE}...")
    np.savez_compressed(
        OUTPUT_FILE,
        vibration_cwru=final_data['vibration_cwru'],
        vibration_ind=final_data['vibration_ind'],
        nasa_seq=final_data['nasa_seq'],
        current=final_data['current'],
        thermal=final_data['thermal'],
        scalars=scalars,
        shared_labels=master_y,
        shared_rul=shared_rul,
        shared_rul_pct=shared_rul_pct
    )
    
    print("\nOK SUCCESS: Physically-Coherent Aligned Dataset Generated!")
    print("This dataset simulates a single motor lifecycle from Healthy to Critical state.")

if __name__ == "__main__":
    build_aligned_digital_twin()
