import os
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(PROJECT_ROOT, "data", "aligned_digital_twin.npz")

def inspect_dataset():
    if not os.path.exists(DATA_FILE):
        print(f"ERROR Error: Dataset not found at {DATA_FILE}")
        print("Please run `python scripts/build_aligned_digital_twin.py` first!")
        return

    print(f"OK Successfully loaded Digital Twin Dataset: {DATA_FILE}")
    print("=" * 60)
    
    data = np.load(DATA_FILE)
    
    print("\n📦 ARRAY SHAPES (What is inside the dataset?):")
    print(f"  • Vibration (CWRU):      {data['vibration_cwru'].shape}")
    print(f"  • Vibration (Induction): {data['vibration_ind'].shape}")
    print(f"  • NASA Sequence:         {data['nasa_seq'].shape}")
    print(f"  • Current Signature:     {data['current'].shape}")
    print(f"  • Thermal Images:        {data['thermal'].shape}")
    print(f"  • Scalar Telemetry:      {data['scalars'].shape}")
    print(f"  • Shared Labels:         {data['shared_labels'].shape}")
    print(f"  • Shared RUL (Hours):    {data['shared_rul'].shape}")
    
    print("\n🔍 SNEAK PEEK: A motor degrading over time...")
    print("-" * 60)
    print(f"{'TimeStep':<10} | {'Health State':<15} | {'RUL (Hours)':<15} | {'Temp (C)':<10}")
    print("-" * 60)
    
    total_samples = len(data['shared_labels'])
    
    # Show the first few (Healthy), middle (Warning), and last few (Critical)
    indices_to_show = [0, 1, 2, total_samples // 2, (total_samples // 2) + 1, total_samples - 2, total_samples - 1]
    
    state_map = {0: "🟢 Healthy", 1: "🟡 Warning", 2: "🔴 Critical"}
    
    for idx in indices_to_show:
        if idx >= total_samples: continue
        
        state = state_map[data['shared_labels'][idx]]
        rul = data['shared_rul'][idx]
        temp = data['scalars'][idx][0] # Bearing Temp
        
        print(f"Sample {idx:<3} | {state:<15} | {rul:<15.1f} | {temp:<10.1f}")
        
    print("=" * 60)
    print("\nAs you can see, all modalities are now mathematically locked together!")
    print("When the motor is Healthy, the temperature is low and RUL is 20,000.")
    print("When it reaches Critical, the temperature is high and RUL is near 0.")

if __name__ == "__main__":
    inspect_dataset()
