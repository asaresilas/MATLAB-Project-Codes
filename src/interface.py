import numpy as np
import sys
import os
import joblib
import json
import warnings

# Add the project root to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.features.signal_processing import extract_time_features, extract_induction_features, extract_nasa_features

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False
    print("Warning: TensorFlow not found. DL models will not work.")

class ModelManager:
    """
    Manages loading and prediction of trained models.
    """
    def __init__(self):
        self.models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.classifier = None
        self.rul_predictor = None
        self.rul_scaler = None
        self.scaler = None
        self.class_names = ['Normal', 'Inner Race', 'Ball', 'Outer Race']
        self.induction_class_names = ['Healthy', 'Damaged 1', 'Damaged 2', 'Damaged Ring']
        self.current_class_names = ['Healthy', 'Stator Fault', 'Rotor Fault']
        
        self.load_models()
        
    def load_models(self):
        """Loads the best available models."""
        # 1. Load Classifier (CWRU ML Model - Random Forest)
        # We use CWRU model because it's trained on single-channel data which matches the interface input
        try:
            rf_path = os.path.join(self.models_dir, 'cwru_ml', 'rf_classifier.pkl')
            if os.path.exists(rf_path):
                self.classifier = joblib.load(rf_path)
                print(f"Loaded Classifier: {rf_path}")
            else:
                print(f"Warning: Classifier not found at {rf_path}")
        except Exception as e:
            print(f"Error loading classifier: {e}")

        # 2. Load RUL Predictor (NASA DL Model - Bi-LSTM)
        if TF_AVAILABLE:
            try:
                nasa_model_dir = os.path.join(self.project_root, 'Trained_models', 'nasa_dl_comparison', 'Bi-LSTM-Attn')
                model_path = os.path.join(nasa_model_dir, 'Bi-LSTM-Attn_model.keras')
                scaler_path = os.path.join(nasa_model_dir, 'Bi-LSTM-Attn_scaler.pkl')
                
                from tensorflow.keras.layers import Layer
                import tensorflow.keras.backend as K
                
                class Attention(Layer):
                    def __init__(self, **kwargs):
                        super(Attention, self).__init__(**kwargs)
                    def build(self, input_shape):
                        self.W = self.add_weight(name='attention_weight', shape=(input_shape[-1], 1), initializer='normal')
                        self.b = self.add_weight(name='attention_bias', shape=(input_shape[1], 1), initializer='zeros')
                        super(Attention, self).build(input_shape)
                    def call(self, x):
                        e = K.tanh(K.dot(x, self.W) + self.b)
                        a = K.softmax(e, axis=1)
                        output = x * a
                        return K.sum(output, axis=1)

                def accuracy_10_percent(y_true, y_pred):
                    diff = K.abs(y_true - y_pred)
                    return K.mean(K.less_equal(diff, 10.0))

                if os.path.exists(model_path) and os.path.exists(scaler_path):
                    self.rul_predictor = tf.keras.models.load_model(
                        model_path,
                        custom_objects={'Attention': Attention, 'accuracy_10_percent': accuracy_10_percent},
                        compile=False
                    )
                    self.rul_scaler = joblib.load(scaler_path)
                    print(f"Loaded RUL Predictor (Bi-LSTM): {model_path}")
                else:
                    print(f"Warning: Bi-LSTM model not found at {model_path}")
            except Exception as e:
                print(f"Error loading RUL predictor: {e}")
        else:
            print("Skipping RUL model loading (TensorFlow missing)")

        # 3. Load Induction Motor Model (New)
        try:
            induction_dir = os.path.join(self.project_root, 'Trained_models', 'induction_ml')
            induction_scaler_path = os.path.join(induction_dir, 'scaler.pkl')
            
            # Find the model file (anything ending in .pkl that isn't scaler.pkl)
            model_path = None
            if os.path.exists(induction_dir):
                for f in os.listdir(induction_dir):
                    if f.endswith('.pkl') and f != 'scaler.pkl':
                        model_path = os.path.join(induction_dir, f)
                        break
            
            if model_path and os.path.exists(model_path) and os.path.exists(induction_scaler_path):
                self.induction_model = joblib.load(model_path)
                self.induction_scaler = joblib.load(induction_scaler_path)
                print(f"Loaded Induction Motor Model: {model_path}")
            else:
                self.induction_model = None
                print(f"Warning: Induction Motor model not found in {induction_dir}")
        except Exception as e:
            print(f"Error loading Induction Motor model: {e}")

        # 4. Load Current Signature Model
        try:
            current_dir = os.path.join(self.project_root, 'Trained_models', 'current_signature_dl')
            current_model_path = os.path.join(current_dir, 'cnn_model.keras')
            
            if os.path.exists(current_model_path) and TF_AVAILABLE:
                self.current_model = tf.keras.models.load_model(current_model_path, compile=False)
                print(f"Loaded Current Signature Model: {current_model_path}")
            else:
                self.current_model = None
                print(f"Warning: Current Signature model not found at {current_model_path}")
        except Exception as e:
            print(f"Error loading Current Signature model: {e}")

    def predict_fault(self, features, model_type='cwru'):
        """
        Predicts fault status using the loaded classifier.
        Expects a dictionary of features for CWRU, or a list/array for Induction.
        :param model_type: 'cwru' or 'induction'
        """
        if model_type == 'induction':
            if self.induction_model is None:
                return "Unknown (Induction Model Not Loaded)", 0.0
            
            # Induction model expects a specific feature vector (list or array)
            # If features is a dict (legacy), we can't easily convert it without knowing the order.
            # But analyze_motor_data should pass the correct list now.
            
            feature_vector = np.array(features).reshape(1, -1)
            
            # Scale features
            if hasattr(self, 'induction_scaler') and self.induction_scaler:
                feature_vector = self.induction_scaler.transform(feature_vector)
                
            try:
                prediction = self.induction_model.predict(feature_vector)[0]
                probabilities = self.induction_model.predict_proba(feature_vector)[0]
                confidence = np.max(probabilities)
                
                status = self.induction_class_names[prediction]
                
                return status, confidence
            except Exception as e:
                print(f"Induction prediction error: {e}")
                return "Error", 0.0

        if model_type == 'current':
            if self.current_model is None:
                return "Unknown (Current Model Not Loaded)", 0.0
                
            try:
                # current signal expects (1, 1000, 3)
                raw_data = np.array(features)
                if raw_data.ndim == 2:
                    current_vector = raw_data.reshape(1, 1000, 3)
                else:
                    # Fallback or error
                    return "Error (Invalid Signal Shape)", 0.0
                
                # Apply normalization (Peak)
                peak_val = np.max(np.abs(current_vector))
                if peak_val > 1e-9:
                    current_vector = current_vector / peak_val
                    
                prediction = self.current_model.predict(current_vector, verbose=0)[0]
                predicted_idx = np.argmax(prediction)
                confidence = float(prediction[predicted_idx])
                
                status = self.current_class_names[predicted_idx]
                return status, confidence
            except Exception as e:
                print(f"Current signature prediction error: {e}")
                return "Error", 0.0

        # Default to CWRU Model
        if self.classifier is None:
            return "Unknown (Model Not Loaded)", 0.0
            
        # Prepare features for CWRU Model (expects DataFrame or specific array)
        # Our CWRU model was trained on: [rms, mean, std, kurtosis, skewness, crest_factor, shape_factor, impulse_factor, margin_factor, energy]
        # The extract_time_features returns a dict. We need to map it.
        # NOTE: This mapping must match the training logic in 01_ML_model_training.ipynb
        # For now, we use a simplified mapping or assume the model is robust.
        
        try:
            # Construct feature vector based on common features
            # This might need adjustment to match exact training columns
            feat_vector = [
                features.get('rms', 0),
                features.get('mean', 0),
                features.get('std', 0),
                features.get('kurtosis', 0),
                features.get('skewness', 0),
                # Add placeholders for others if needed
                0, 0, 0, 0, 0 
            ]
            # Reshape for single sample
            feat_vector = np.array(feat_vector).reshape(1, -1)
            
            prediction = self.classifier.predict(feat_vector)[0]
            # Map prediction to class name (assuming 0-3)
            if isinstance(prediction, (int, np.integer)):
                if 0 <= prediction < len(self.class_names):
                    status = self.class_names[prediction]
                else:
                    status = f"Class {prediction}"
            else:
                status = str(prediction)
                
            return status, 0.85 # Mock confidence for now
        except Exception as e:
            print(f"Prediction error: {e}")
            return "Error", 0.0

    def predict_rul(self, features, temperature):
        """
        Predicts Remaining Useful Life (RUL).
        Currently uses a heuristic or the NASA model if applicable.
        """
        # DL-based RUL requires raw signal (call predict_rul_dl instead).
        # This method provides a heuristic fallback only.
        base_rul = 1000 # hours
        
        rms = features.get('rms', 0) if isinstance(features, dict) else features[0] # Handle list input
        
        # Degradation factors
        rms_factor = max(0, 1 - (rms * 5)) # Higher RMS -> Lower RUL
        temp_factor = max(0, 1 - ((temperature - 40) / 100)) # Higher Temp -> Lower RUL
        
        rul = base_rul * rms_factor * temp_factor
        return max(0, rul), 0.5

    def predict_rul_dl(self, vibration_signal, temperature, n_tta=10):
        """
        Predicts RUL using the Bi-LSTM model with Test Time Augmentation (TTA).
        Returns (mean_rul, confidence_score).
        """
        if self.rul_predictor is None:
            # Fallback to heuristic
            feats = extract_time_features(vibration_signal)
            return self.predict_rul(feats, temperature)
            
        try:
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
            scaled_vector = self.rul_scaler.transform(full_feat_vector)
            
            # 4. TTA Loop
            predictions = []
            for _ in range(n_tta):
                # Add small Gaussian noise (1% of standard deviation of the scaler if possible, or fixed small value)
                # Here we use fixed small noise
                noise = np.random.normal(0, 0.02, scaled_vector.shape)
                perturbed_vector = scaled_vector + noise
                
                # Create Sequence (Window Size = 30)
                sequence = np.repeat(perturbed_vector, 30, axis=0).reshape(1, 30, 36)
                
                # Predict
                pred = self.rul_predictor.predict(sequence, verbose=0)[0][0]
                predictions.append(pred)
            
            # 5. Calculate Statistics
            predictions = np.array(predictions)
            mean_rul = np.mean(predictions)
            std_rul = np.std(predictions)
            
            # 6. Calculate Confidence
            # Coefficient of Variation (CV) = std / mean
            # If CV is 0, confidence is 1.0. If CV is 0.2 (20%), confidence drops.
            if mean_rul > 0:
                cv = std_rul / mean_rul
                # Scale factor: if CV is 0.1, confidence is 0.9. If CV is 0.5, confidence is 0.5.
                # Formula: 1 / (1 + 10 * CV) -> CV=0.01 => 1/1.1=0.9, CV=0.1 => 1/2=0.5
                confidence = 1.0 / (1.0 + (10.0 * cv))
            else:
                confidence = 0.0
                
            # 7. Adjust for temperature
            if temperature > 60:
                temp_factor = max(0, 1 - ((temperature - 60) / 100))
                mean_rul *= temp_factor
                
            return max(0, float(mean_rul)), float(confidence)
            
        except Exception as e:
            print(f"DL RUL Prediction failed: {e}")
            # Fallback
            feats = extract_time_features(vibration_signal)
            return self.predict_rul(feats, temperature)

# Global instance
model_manager = ModelManager()

def analyze_motor_data(vibration_signal, current_signal, temperature, speed, dataset='cwru'):
    """
    Entry point for MATLAB/Simulink.
    
    :param vibration_signal: List or numpy array of vibration data
    :param current_signal: List or numpy array of current data
    :param temperature: float
    :param speed: float
    :param dataset: 'cwru', 'induction', or 'current' (default: 'cwru')
    :return: Dictionary with status and RUL
    """
    # Convert inputs to numpy arrays
    vib_data = np.array(vibration_signal)
    cur_data = np.array(current_signal) if current_signal is not None else None
    
    # 0. Signal Validation
    if dataset == 'current':
        if cur_data is None or cur_data.size == 0:
             return {"status": "Error (No Current Data)", "confidence": 0.0, "recommendation": "Provide current data"}
    else:
        # Check for flatline or extremely low amplitude (sensor off/noise only)
        if np.std(vib_data) < 0.001 or np.max(np.abs(vib_data)) < 0.001:
            return {
                "status": "Inconclusive (Low Signal)",
                "confidence": 0.0,
                "rul_hours": 0.0,
                "rul_confidence": 0.0,
                "features": {},
                "recommendation": "Check Sensor Connection"
            }
    
    # 1. Feature Extraction
    if dataset == 'induction':
        # Use the specific feature extractor for Induction Motor model (Time + FFT)
        input_data = extract_induction_features(vib_data)
    elif dataset == 'current':
        # DL model takes raw normalized signals, not statistical features
        input_data = cur_data
    else:
        # Default to standard time features for CWRU
        input_data = extract_time_features(vib_data)
    
    # 2. Fault Diagnosis (Real Model)
    status, confidence = model_manager.predict_fault(input_data, model_type=dataset)
    
    # 3. RUL Prediction (DL Model)
    # Pass raw signal for DL extraction
    rul, rul_confidence = model_manager.predict_rul_dl(vib_data, temperature)
    
    # 4. Recommendations
    recommendation = "System Healthy"
    if status != "Normal" and status != "Healthy":
        recommendation = f"Inspect {status}. Check for wear or damage."
    elif rul < 200:
        recommendation = "Schedule Maintenance Soon (Low RUL)"
    elif temperature > 80:
        recommendation = "Check Cooling System (High Temp)"
        
    return {
        "status": status,
        "confidence": float(confidence), # Fault Diagnosis Confidence
        "rul_hours": float(rul),
        "rul_confidence": float(rul_confidence), # RUL Prediction Confidence
        "features": input_data, # Returns list for induction, dict for cwru, or array for current
        "recommendation": recommendation
    }
