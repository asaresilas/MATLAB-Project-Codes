"""
Comprehensive API Test Suite
Tests all models and endpoints for functionality
"""

import requests
import numpy as np
import json
import time
from datetime import datetime
from pathlib import Path

class APITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "url": base_url,
            "tests": {},
            "summary": {}
        }
        self.token = None
        
    def log_result(self, test_name, status, details=""):
        """Log test result"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        symbol = "✓" if status == "PASS" else "✗" if status == "FAIL" else "⚠"
        print(f"{symbol} {test_name}: {status}")
        if details:
            print(f"  └─ {details}")
    
    def test_health_check(self):
        """Test 1: Health Check"""
        try:
            r = requests.get(f"{self.base_url}/health", timeout=5)
            if r.status_code == 200:
                self.log_result("Health Check", "PASS", f"Status: {r.json()['status']}")
                return True
            else:
                self.log_result("Health Check", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("Health Check", "FAIL", str(e))
            return False
    
    def test_models_endpoint(self):
        """Test 2: List all loaded models"""
        try:
            r = requests.get(f"{self.base_url}/api/v1/models", timeout=5)
            if r.status_code == 200:
                data = r.json()
                models = data.get('loaded_models', [])
                configs = data.get('configs', {})
                
                # Expected models
                expected = ['CIA1', 'NASA', 'CWRU', 'Induction_Motor', 'Current_Signature', 'Thermal']
                loaded = set(models)
                expected_set = set(expected)
                
                missing = expected_set - loaded
                found = loaded & expected_set
                
                status = "PASS" if len(missing) == 0 else "PARTIAL" if len(found) > 0 else "FAIL"
                details = f"Loaded: {len(models)}/6 models - {', '.join(sorted(models))}"
                if missing:
                    details += f" | Missing: {', '.join(sorted(missing))}"
                
                self.log_result("Models Endpoint", status, details)
                return status in ["PASS", "PARTIAL"]
            else:
                self.log_result("Models Endpoint", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("Models Endpoint", "FAIL", str(e))
            return False
    
    def test_authentication(self):
        """Test 3: Authentication"""
        try:
            r = requests.post(
                f"{self.base_url}/api/v1/auth/token",
                data={'username': 'admin', 'password': os.getenv('ADMIN_PASSWORD', '')},
                timeout=5
            )
            if r.status_code == 200:
                data = r.json()
                self.token = data.get('access_token')
                expires = data.get('expires_in', 'unknown')
                self.log_result("Authentication", "PASS", f"Token obtained, expires in {expires}s")
                return True
            else:
                self.log_result("Authentication", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("Authentication", "FAIL", str(e))
            return False
    
    def test_cia1_model(self):
        """Test 4: CIA1 Model Prediction"""
        if not self.token:
            self.log_result("CIA1 Model", "SKIP", "No authentication token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            payload = {
                "air_temperature": 298,
                "process_temperature": 308,
                "rpm": 1500,
                "torque": 40,
                "tool_wear": 0,
                "type": "M"
            }
            r = requests.post(
                f"{self.base_url}/api/v1/predict/cia1",
                headers=headers,
                json=payload,
                timeout=10
            )
            if r.status_code == 200:
                result = r.json()
                self.log_result("CIA1 Model", "PASS", f"Prediction: {result.get('prediction')}")
                return True
            else:
                self.log_result("CIA1 Model", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("CIA1 Model", "FAIL", str(e))
            return False
    
    def test_cwru_model(self):
        """Test 5: CWRU Model (Bearing Fault Classification)"""
        if not self.token:
            self.log_result("CWRU Model", "SKIP", "No authentication token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            # Generate 1000 samples of vibration signal
            signal = np.random.randn(1000).tolist()
            payload = {"signal": signal}
            
            r = requests.post(
                f"{self.base_url}/api/v1/predict/cwru",
                headers=headers,
                json=payload,
                timeout=10
            )
            if r.status_code == 200:
                result = r.json()
                fault = result.get('fault_type', 'Unknown')
                confidence = result.get('confidence', 0)
                self.log_result("CWRU Model", "PASS", f"Fault: {fault} (conf: {confidence:.2%})")
                return True
            else:
                self.log_result("CWRU Model", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("CWRU Model", "FAIL", str(e))
            return False
    
    def test_nasa_model(self):
        """Test 6: NASA Model (RUL Prediction)"""
        if not self.token:
            self.log_result("NASA Model", "SKIP", "No authentication token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            # Generate 9 features x N samples (NASA expects features)
            signal = np.random.randn(100, 9).tolist()  # 100 samples, 9 features
            payload = {"features": signal}
            
            r = requests.post(
                f"{self.base_url}/api/v1/predict/nasa",
                headers=headers,
                json=payload,
                timeout=10
            )
            if r.status_code == 200:
                result = r.json()
                rul = result.get('rul_hours', 0)
                conf = result.get('confidence', 0)
                self.log_result("NASA Model", "PASS", f"RUL: {rul:.1f} hours (conf: {conf:.2%})")
                return True
            else:
                self.log_result("NASA Model", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("NASA Model", "FAIL", str(e))
            return False
    
    def test_induction_motor_model(self):
        """Test 7: Induction Motor Model"""
        if not self.token:
            self.log_result("Induction Motor Model", "SKIP", "No authentication token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            signal = np.random.randn(1000).tolist()
            payload = {"signal": signal}
            
            r = requests.post(
                f"{self.base_url}/api/v1/predict/induction",
                headers=headers,
                json=payload,
                timeout=10
            )
            if r.status_code == 200:
                result = r.json()
                status = result.get('status', 'Unknown')
                self.log_result("Induction Motor Model", "PASS", f"Status: {status}")
                return True
            else:
                self.log_result("Induction Motor Model", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("Induction Motor Model", "FAIL", str(e))
            return False
    
    def test_comprehensive_diagnosis(self):
        """Test 8: Comprehensive Diagnosis (All Models Combined)"""
        if not self.token:
            self.log_result("Comprehensive Diagnosis", "SKIP", "No authentication token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {self.token}'}
            # Realistic signal generation
            t = np.linspace(0, 1, 12000)
            vibration = (0.5 * np.sin(2 * np.pi * 60 * t)).tolist()
            current = np.random.randn(1000, 3).tolist()
            
            payload = {
                "vibration_signal": vibration,
                "current_signal": current,
                "temperature": 75.0,
                "speed": 1050
            }
            
            print("  Sending comprehensive diagnosis request...")
            start = time.time()
            r = requests.post(
                f"{self.base_url}/api/v1/diagnose/comprehensive",
                headers=headers,
                json=payload,
                timeout=60
            )
            elapsed = time.time() - start
            
            if r.status_code == 200:
                result = r.json()
                rul = result.get('rul_hours', 0)
                health = result.get('overall_health', 'Unknown')
                faults = len(result.get('fault_locations', []))
                self.log_result("Comprehensive Diagnosis", "PASS", 
                               f"RUL: {rul:.1f}h, Health: {health}, Faults: {faults} ({elapsed:.1f}s)")
                return True
            else:
                self.log_result("Comprehensive Diagnosis", "FAIL", f"Status code: {r.status_code}")
                return False
        except Exception as e:
            self.log_result("Comprehensive Diagnosis", "FAIL", str(e))
            return False
    
    def save_results(self, filename=None):
        """Save test results to JSON file"""
        if filename is None:
            filename = f"api_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = Path(__file__).parent / filename
        
        # Calculate summary
        passed = sum(1 for t in self.results["tests"].values() if t["status"] == "PASS")
        failed = sum(1 for t in self.results["tests"].values() if t["status"] == "FAIL")
        skipped = sum(1 for t in self.results["tests"].values() if t["status"] == "SKIP")
        
        self.results["summary"] = {
            "total": len(self.results["tests"]),
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "success_rate": f"{passed / (len(self.results['tests']) - skipped) * 100:.1f}%" if (len(self.results["tests"]) - skipped) > 0 else "N/A"
        }
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        summary = self.results["summary"]
        print(f"Total Tests: {summary['total']}")
        print(f"Passed: {summary['passed']}")
        print(f"Failed: {summary['failed']}")
        print(f"Skipped: {summary['skipped']}")
        print(f"Success Rate: {summary['success_rate']}")
        
        print("="*70)
    
    def run_all_tests(self):
        """Run all tests"""
        print("\n" + "="*70)
        print("PREDICTIVE MAINTENANCE API TEST SUITE")
        print("="*70)
        print(f"Testing: {self.base_url}\n")
        
        # Run tests
        self.test_health_check()
        self.test_models_endpoint()
        self.test_authentication()
        
        if self.token:
            self.test_cia1_model()
            self.test_cwru_model()
            self.test_nasa_model()
            self.test_induction_motor_model()
            self.test_comprehensive_diagnosis()
        
        self.print_summary()
        filepath = self.save_results()
        print(f"\nResults saved to: {filepath}")

if __name__ == "__main__":
    import sys
    
    # Get base URL from command line or use default
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
    
    tester = APITester(base_url)
    tester.run_all_tests()
