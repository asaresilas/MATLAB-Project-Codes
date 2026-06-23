"""
Comparison Test: Heuristic vs Deep Learning RUL Prediction

This script demonstrates the difference between the old heuristic approach
and the new Bi-LSTM Deep Learning model for RUL prediction.
"""

import sys
import os
import numpy as np
import matplotlib.pyplot as plt

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features.signal_processing import extract_time_features, extract_nasa_features

def heuristic_rul(vibration_signal, temperature):
    """Original heuristic-based RUL calculation"""
    features = extract_time_features(vibration_signal)
    rms = features['rms']
    
    base_rul = 1000  # hours
    rms_factor = max(0, 1 - (rms * 5))
    temp_factor = max(0, 1 - ((temperature - 40) / 100))
    
    rul = base_rul * rms_factor * temp_factor
    return max(0, rul)

def dl_rul(vibration_signal, temperature, model, scaler):
    """Deep Learning-based RUL prediction"""
    # 1. Extract 9 NASA features
    nasa_feats = extract_nasa_features(vibration_signal)
    
    # 2. Create 36-feature vector (Replicate 4 times)
    feat_values = [
        nasa_feats['rms'], nasa_feats['mean'], nasa_feats['std'],
        nasa_feats['max'], nasa_feats['min'], nasa_feats['kurtosis'],
        nasa_feats['skewness'], nasa_feats['peak_to_peak'], nasa_feats['crest_factor']
    ]
    full_feat_vector = np.array(feat_values * 4).reshape(1, -1)
    
    # 3. Scale features
    scaled_vector = scaler.transform(full_feat_vector)
    
    # 4. Create Sequence (Window Size = 10)
    sequence = np.repeat(scaled_vector, 10, axis=0).reshape(1, 10, 36)
    
    # 5. Predict
    rul_pred = model.predict(sequence, verbose=0)[0][0]
    
    # 6. Adjust for temperature
    if temperature > 60:
        temp_factor = max(0, 1 - ((temperature - 60) / 100))
        rul_pred *= temp_factor
        
    return max(0, float(rul_pred))

def generate_test_signals():
    """Generate various test signals representing different degradation levels"""
    fs = 12000
    t = np.linspace(0, 1, fs)
    
    signals = {
        'Healthy': {
            'signal': 0.1 * np.sin(2 * np.pi * 100 * t) + 0.02 * np.random.randn(fs),
            'temp': 40,
            'description': 'Low vibration, normal temperature'
        },
        'Early Wear': {
            'signal': 0.3 * np.sin(2 * np.pi * 100 * t) + 0.05 * np.random.randn(fs),
            'temp': 50,
            'description': 'Moderate vibration, slightly elevated temp'
        },
        'Moderate Degradation': {
            'signal': 0.6 * np.sin(2 * np.pi * 100 * t) + 0.1 * np.random.randn(fs),
            'temp': 65,
            'description': 'High vibration, elevated temperature'
        },
        'Severe Degradation': {
            'signal': 1.2 * np.sin(2 * np.pi * 100 * t) + 0.2 * np.random.randn(fs),
            'temp': 80,
            'description': 'Very high vibration, high temperature'
        },
        'Near Failure': {
            'signal': 2.0 * np.sin(2 * np.pi * 100 * t) + 0.5 * np.random.randn(fs),
            'temp': 95,
            'description': 'Extreme vibration and temperature'
        }
    }
    
    return signals

def main():
    print("=" * 70)
    print("RUL PREDICTION COMPARISON: Heuristic vs Deep Learning")
    print("=" * 70)
    
    # Load DL model
    print("\nLoading Bi-LSTM model...")
    try:
        import tensorflow as tf
        import joblib
        
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        model_dir = os.path.join(project_root, 'Trained_models', 'nasa_dl_comparison', 'Bi-LSTM')
        
        model = tf.keras.models.load_model(os.path.join(model_dir, 'Bi-LSTM_model.keras'))
        scaler = joblib.load(os.path.join(model_dir, 'Bi-LSTM_scaler.pkl'))
        print("✓ Model loaded successfully\n")
        
    except Exception as e:
        print(f"✗ Failed to load model: {e}")
        print("Running heuristic-only comparison...\n")
        model = None
        scaler = None
    
    # Generate test signals
    test_signals = generate_test_signals()
    
    # Run comparison
    results = []
    print(f"{'Condition':<25} {'Heuristic RUL':<15} {'DL RUL':<15} {'Difference':<15}")
    print("-" * 70)
    
    for condition, data in test_signals.items():
        signal = data['signal']
        temp = data['temp']
        
        # Heuristic prediction
        rul_heuristic = heuristic_rul(signal, temp)
        
        # DL prediction
        if model is not None:
            rul_dl = dl_rul(signal, temp, model, scaler)
            diff = rul_dl - rul_heuristic
            diff_str = f"{diff:+.1f} hrs"
        else:
            rul_dl = None
            diff_str = "N/A"
        
        results.append({
            'condition': condition,
            'heuristic': rul_heuristic,
            'dl': rul_dl,
            'temp': temp,
            'description': data['description']
        })
        
        dl_str = f"{rul_dl:.1f} hrs" if rul_dl is not None else "N/A"
        print(f"{condition:<25} {rul_heuristic:>10.1f} hrs   {dl_str:>12}   {diff_str:>12}")
    
    # Visualization
    if model is not None:
        print("\n" + "=" * 70)
        print("Generating comparison chart...")
        
        conditions = [r['condition'] for r in results]
        heuristic_vals = [r['heuristic'] for r in results]
        dl_vals = [r['dl'] for r in results]
        
        x = np.arange(len(conditions))
        width = 0.35
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar chart comparison
        bars1 = ax1.bar(x - width/2, heuristic_vals, width, label='Heuristic', alpha=0.8, color='#FF6B6B')
        bars2 = ax1.bar(x + width/2, dl_vals, width, label='Deep Learning', alpha=0.8, color='#4ECDC4')
        
        ax1.set_xlabel('Bearing Condition', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Predicted RUL (hours)', fontsize=12, fontweight='bold')
        ax1.set_title('RUL Prediction Comparison', fontsize=14, fontweight='bold')
        ax1.set_xticks(x)
        ax1.set_xticklabels(conditions, rotation=45, ha='right')
        ax1.legend()
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax1.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.0f}',
                        ha='center', va='bottom', fontsize=9)
        
        # Difference chart
        differences = [dl - h for dl, h in zip(dl_vals, heuristic_vals)]
        colors = ['green' if d > 0 else 'red' for d in differences]
        
        ax2.bar(x, differences, color=colors, alpha=0.7)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax2.set_xlabel('Bearing Condition', fontsize=12, fontweight='bold')
        ax2.set_ylabel('Difference (DL - Heuristic) hours', fontsize=12, fontweight='bold')
        ax2.set_title('Prediction Differences', fontsize=14, fontweight='bold')
        ax2.set_xticks(x)
        ax2.set_xticklabels(conditions, rotation=45, ha='right')
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels
        for i, (xi, diff) in enumerate(zip(x, differences)):
            ax2.text(xi, diff, f'{diff:+.0f}',
                    ha='center', va='bottom' if diff > 0 else 'top', fontsize=9)
        
        plt.tight_layout()
        
        # Save figure
        output_path = os.path.join(os.path.dirname(__file__), 'rul_comparison_chart.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        print(f"✓ Chart saved to: {output_path}")
        
        plt.show()
    
    # Summary
    print("\n" + "=" * 70)
    print("ANALYSIS SUMMARY")
    print("=" * 70)
    print("\nKey Observations:")
    print("1. Heuristic uses simple RMS × Temperature formula")
    print("2. DL model analyzes 9 features and learned patterns from real failures")
    print("3. DL predictions are based on actual NASA bearing failure data")
    print("4. Differences show where DL model has learned non-linear relationships")
    print("\nRecommendation: Use DL predictions for production systems")
    print("=" * 70)

if __name__ == "__main__":
    main()
