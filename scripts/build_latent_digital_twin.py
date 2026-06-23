import os
import sys
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
SOURCE_CACHE = os.path.join(DATA_DIR, "fusion_test_cache.npz")

np.random.seed(42)

def generate_pool(n_samples, filename):
    print(f"Synthesizing {n_samples} latent-linked samples for {filename}...")
    d_trajectory = np.random.uniform(0, 1.0, n_samples)
    
    # Sort for trajectory-like consistency in test set, keep random for train
    if "test" in filename or "digital_twin" in filename:
        d_trajectory = np.sort(d_trajectory)

    cache = np.load(SOURCE_CACHE)
    raw_Xs = {mod: cache[key] for mod, key in zip(['vibration_cwru', 'vibration_ind', 'nasa_seq', 'current', 'thermal'], ['cwru_x', 'ind_x', 'nasa_x', 'curr_x', 'therm_x'])}
    raw_ys = {mod: cache[key] for mod, key in zip(['vibration_cwru', 'vibration_ind', 'nasa_seq', 'current', 'thermal'], ['cwru_y', 'ind_y', 'nasa_y', 'curr_y', 'therm_y'])}

    final_data = {mod: [] for mod in raw_Xs.keys()}
    final_labels = []
    final_rul = []

    for d in d_trajectory:
        true_state = 0 if d < 0.35 else (1 if d < 0.75 else 2)
        for mod in raw_Xs.keys():
            mod_jitter = np.random.normal(0, 0.08)
            mod_d = np.clip(d + mod_jitter, 0, 1)
            mod_state = 0 if mod_d < 0.35 else (1 if mod_d < 0.75 else 2)
            
            pool_X = raw_Xs[mod]; pool_y = raw_ys[mod]
            indices = np.where(pool_y == mod_state)[0]
            idx = indices[np.random.randint(0, len(indices))] if len(indices) > 0 else np.random.randint(0, len(pool_X))
            final_data[mod].append(pool_X[idx])
            
        final_labels.append(true_state)
        final_rul.append(100.0 * (1.0 - d))

    # Scalars
    scalars = np.zeros((n_samples, 9), dtype=np.float32)
    for i, d in enumerate(d_trajectory):
        temp = 40.0 + (d**1.5 * 50.0) + np.random.normal(0, 0.5)
        scalars[i, 0] = temp; scalars[i, 1] = temp + 5.0
        scalars[i, 2] = 0.5 + (np.exp(3*d) * 0.5)
        scalars[i, 3] = 0.01 + (d**3 * 0.1)
        scalars[i, 4:] = np.random.normal(100, 1, 5)

    np.savez_compressed(
        os.path.join(DATA_DIR, filename),
        vibration_cwru=np.array(final_data['vibration_cwru']),
        vibration_ind=np.array(final_data['vibration_ind']),
        nasa_seq=np.array(final_data['nasa_seq']),
        current=np.array(final_data['current']),
        thermal=np.array(final_data['thermal']),
        scalars=scalars,
        shared_labels=np.array(final_labels),
        shared_rul=np.array(final_rul),
        shared_rul_pct=np.array(final_rul)
    )

def build_latent_digital_twin():
    print("Initializing Phase 2: Latent-State Stacking Data Generation...")
    if not os.path.exists(SOURCE_CACHE): return
    
    generate_pool(1500, "latent_train_cache.npz")
    generate_pool(300, "latent_digital_twin.npz")
    
    print(f"OK SUCCESS: Phase 2 Training/Testing Caches Generated.")
    print("  Integrity: All modalities linked to hidden d-variable.")

if __name__ == "__main__":
    build_latent_digital_twin()
