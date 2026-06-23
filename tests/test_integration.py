import unittest
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.interface import analyze_motor_data
from src.models.classifiers import FaultDiagnosisModel
from src.models.rul import RULModel

class TestDigitalTwinPipeline(unittest.TestCase):
    def test_interface_structure(self):
        """Test if the main interface returns the expected dictionary structure."""
        # Mock inputs
        vibration = np.random.normal(0, 1, 1000) # 1000 data points
        current = np.random.normal(0, 1, 1000)
        temp = 75.0
        speed = 1750.0
        
        result = analyze_motor_data(vibration, current, temp, speed)
        
        self.assertIn('status', result)
        self.assertIn('rul_hours', result)
        self.assertIn('features', result)
        self.assertIn('rms', result['features'])
        print("\nInterface Test Passed: Output structure is correct.")

    def test_classifier_training(self):
        """Test if the classifier can train on dummy data."""
        X = np.random.rand(100, 10) # 100 samples, 10 features
        y = np.random.randint(0, 2, 100) # Binary classification
        
        model = FaultDiagnosisModel(model_type='rf')
        try:
            model.train(X, y)
            print("\nClassifier Training Test Passed.")
        except Exception as e:
            self.fail(f"Classifier training failed: {e}")

    def test_rul_model_build(self):
        """Test if the RUL model builds correctly."""
        input_shape = (50, 5) # 50 time steps, 5 features
        try:
            model = RULModel(input_shape)
            print("\nRUL Model Build Test Passed.")
        except ImportError:
            print("\nSkipping RUL Model test (TensorFlow not installed).")
        except Exception as e:
            self.fail(f"RUL model build failed: {e}")

if __name__ == '__main__':
    unittest.main()
