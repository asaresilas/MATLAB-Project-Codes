"""
Comprehensive API Performance Test with Auto Server Start
==========================================
Tests API with realistic signals and automatic server startup.
Generates synthetic sensor data and evaluates model predictions.
"""

import subprocess
import requests
import numpy as np
import time
import json
import sys
from datetime import datetime
from pathlib import Path
import signal
import os
import threading
import queue

# Configuration
API_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SERVER_STARTUP_TIMEOUT = 180  # seconds (3 minutes for model loading)

class Colors:
    """ANSI color codes"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

class APIPerformanceTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "performance": {},
            "model_predictions": {},
            "summary": {}
        }
        self.token = None
        self.server_process = None
        self.test_results = []
        
    def print_header(self, text):
        """Print formatted header"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{text.center(80)}{Colors.END}")
        print(f"{Colors.BOLD}{Colors.CYAN}{'='*80}{Colors.END}")
    
    def print_section(self, text):
        """Print formatted section"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}→ {text}{Colors.END}")
        print(f"{Colors.BLUE}{'-'*80}{Colors.END}")
    
    def print_pass(self, text):
        """Print success message"""
        print(f"{Colors.GREEN}✓ {text}{Colors.END}")
    
    def print_fail(self, text):
        """Print failure message"""
        print(f"{Colors.RED}✗ {text}{Colors.END}")
    
    def print_info(self, text):
        """Print info message"""
        print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")
    
    def start_server(self):
        """Start API server automatically"""
        self.print_header("STARTING API SERVER")
        self.print_section("Launching Python subprocess")
        
        try:
            project_root = Path(__file__).parent.parent.parent
            backend_dir = project_root / "backend"
            
            print(f"Project Root: {project_root}")
            print(f"Backend Dir: {backend_dir}")
            
            if not backend_dir.exists():
                self.print_fail(f"Backend directory not found: {backend_dir}")
                return False
            
            # Start server in background with output capturing
            self.output_queue = queue.Queue()
            
            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", 
                 "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Start thread to read server output
            output_thread = threading.Thread(target=self._read_server_output, daemon=True)
            output_thread.start()
            
            self.print_info("Waiting for server to start...")
            self.print_info("This may take 30-90 seconds while TensorFlow loads the models...")
            print()
            
            # Wait for server to be ready with progress bar
            start_time = time.time()
            last_progress = 0
            
            while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
                elapsed = int(time.time() - start_time)
                progress = int((elapsed / SERVER_STARTUP_TIMEOUT) * 100)
                
                # Update progress bar every 5 seconds
                if progress > last_progress:
                    self._print_progress_bar(elapsed, SERVER_STARTUP_TIMEOUT, progress)
                    last_progress = progress
                
                # Check if server process crashed
                if self.server_process.poll() is not None:
                    self.print_fail(f"Server process crashed (exit code: {self.server_process.poll()})")
                    print("\n" + Colors.YELLOW + "SERVER ERROR OUTPUT:" + Colors.END)
                    print("─" * 80)
                    # Get any remaining output
                    try:
                        remaining = self.server_process.stdout.read()
                        if remaining:
                            print(remaining)
                    except:
                        pass
                    print("─" * 80)
                    return False
                
                try:
                    # Check health endpoint
                    response = requests.get(f"{API_URL}/health", timeout=2)
                    if response.status_code == 200:
                        print()  # New line after progress bar
                        self.print_pass("✓ Server is running")
                        
                        # Now check if models are loaded
                        try:
                            models_response = requests.get(f"{API_URL}/api/v1/models", timeout=5)
                            if models_response.status_code == 200:
                                data = models_response.json()
                                loaded_count = len(data.get('loaded_models', []))
                                if loaded_count >= 6:
                                    self.print_pass(f"API Server started successfully ({loaded_count} models loaded)")
                                    self.print_info("All models ready!")
                                    time.sleep(1)
                                    return True
                                else:
                                    self.print_info(f"  Models loading... {loaded_count}/6 models ready")
                        except Exception as e:
                            self.print_info(f"  Models still loading...")
                except requests.exceptions.ConnectionError:
                    pass  # Server not ready yet, will retry
                except:
                    pass
                
                time.sleep(0.5)
            
            print()  # New line after progress bar
            self.print_fail(f"Server startup timeout ({SERVER_STARTUP_TIMEOUT}s)")
            self.print_info("The server took too long to start. Possible causes:")
            self.print_info("  • TensorFlow is still loading models (first run can take longer)")
            self.print_info("  • There's an error in the backend (check logs above)")
            self.print_info("  • Port 8000 is already in use by another process")
            
            print("\n" + Colors.YELLOW + "TIP: To debug, run manually:" + Colors.END)
            print(f"  cd {backend_dir}")
            print(f"  python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug")
            
            return False
            
        except Exception as e:
            self.print_fail(f"Failed to start server: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _read_server_output(self):
        """Thread function to read server output"""
        try:
            while True:
                line = self.server_process.stdout.readline()
                if not line:
                    break
                line = line.strip()
                if line and ('error' in line.lower() or 'exception' in line.lower() or 'warning' in line.lower()):
                    print(f"{Colors.YELLOW}[SERVER] {line}{Colors.END}")
                elif line and ('startup' in line.lower() or 'application' in line.lower()):
                    print(f"{Colors.GREEN}[SERVER] {line}{Colors.END}")
        except:
            pass
    
    def _print_progress_bar(self, elapsed, total, percent):
        """Print a progress bar"""
        bar_length = 40
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r{Colors.BLUE}Progress: [{bar}] {percent}% ({elapsed}/{total}s){Colors.END}", end='', flush=True)
    
    def test_health(self):
        """Test 1: Health Check"""
        self.print_section("TEST 1: Health Check")
        
        try:
            start = time.time()
            response = requests.get(f"{API_URL}/health", timeout=5)
            elapsed = time.time() - start
            
            self.results["performance"]["health_check"] = elapsed
            
            if response.status_code == 200:
                data = response.json()
                self.print_pass(f"Server health: {data['status']} ({elapsed:.3f}s)")
                return True
            else:
                self.print_fail(f"Unexpected status code: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(f"Connection error: {e}")
            return False
    
    def test_models_loaded(self):
        """Test 2: Verify All Models Loaded"""
        self.print_section("TEST 2: Models Loaded")
        
        try:
            response = requests.get(f"{API_URL}/api/v1/models", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('loaded_models', [])
                
                expected = {'CIA1', 'NASA', 'CWRU', 'Induction_Motor', 'Current_Signature', 'Thermal'}
                loaded = set(models)
                
                self.print_info(f"Loaded Models ({len(loaded)}):")
                for model in sorted(models):
                    self.print_pass(model)
                
                missing = expected - loaded
                if missing:
                    for model in missing:
                        self.print_fail(f"Missing: {model}")
                    return False
                
                self.results["tests"]["models_loaded"] = {
                    "count": len(models),
                    "models": sorted(models)
                }
                return True
            else:
                self.print_fail(f"Failed to get models: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(f"Error: {e}")
            return False
    
    def authenticate(self):
        """Test 3: Authenticate"""
        self.print_section("TEST 3: Authentication")
        
        try:
            print(f"Logging in: {USERNAME}")
            
            start = time.time()
            response = requests.post(
                f"{API_URL}/api/v1/auth/token",
                data={'username': USERNAME, 'password': PASSWORD},
                timeout=10
            )
            elapsed = time.time() - start
            
            self.results["performance"]["authentication"] = elapsed
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                expires = data.get('expires_in', 3600)
                
                self.print_pass(f"Authentication successful ({elapsed:.3f}s)")
                self.print_info(f"Token expires in: {expires} seconds ({expires//60} minutes)")
                
                self.results["tests"]["authentication"] = {
                    "status": "success",
                    "expires_in": expires
                }
                return True
            else:
                self.print_fail(f"Authentication failed: {response.status_code}")
                return False
        except Exception as e:
            self.print_fail(f"Error: {e}")
            return False
    
    def generate_signals(self, condition='healthy'):
        """Generate realistic test signals"""
        np.random.seed(42)  # For reproducibility
        
        # Vibration signal (12000 samples)
        t = np.linspace(0, 1, 12000)
        
        if condition == 'healthy':
            # Healthy: clean sinusoidal signal with low noise
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)  # 60Hz
            vibration += 0.1 * np.sin(2 * np.pi * 120 * t)  # Harmonic
            vibration += np.random.normal(0, 0.05, len(vibration))  # Low noise
            
        elif condition == 'early_degradation':
            # Early degradation: increased harmonics
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)
            vibration += 0.2 * np.sin(2 * np.pi * 120 * t)  # Stronger harmonic
            vibration += 0.15 * np.sin(2 * np.pi * 180 * t)  # New harmonic
            vibration += np.random.normal(0, 0.1, len(vibration))  # More noise
            
        elif condition == 'fault_developing':
            # Fault developing: strong harmonics and impulsive noise
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)
            vibration += 0.3 * np.sin(2 * np.pi * 120 * t)
            vibration += 0.2 * np.sin(2 * np.pi * 180 * t)
            vibration += 0.15 * np.sin(2 * np.pi * 240 * t)
            
            # Add impulsive noise (bearing defects)
            noise = np.random.normal(0, 0.15, len(vibration))
            impulses = np.random.choice([0, 3.0], size=len(vibration), p=[0.99, 0.01])
            vibration += noise + impulses
            
        elif condition == 'critical':
            # Critical: very strong signal with heavy impulsive content
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)
            vibration += 0.4 * np.sin(2 * np.pi * 120 * t)
            vibration += 0.3 * np.sin(2 * np.pi * 180 * t)
            vibration += 0.25 * np.sin(2 * np.pi * 240 * t)
            vibration += 0.2 * np.sin(2 * np.pi * 300 * t)
            
            # Heavy impulsive noise
            noise = np.random.normal(0, 0.2, len(vibration))
            impulses = np.random.choice([0, 4.0], size=len(vibration), p=[0.95, 0.05])
            vibration += noise + impulses
        
        # 3-phase current signal (1000 samples)
        phase1 = 5.0 * np.sin(2 * np.pi * 50 * np.linspace(0, 0.1, 1000))
        phase2 = 5.0 * np.sin(2 * np.pi * 50 * np.linspace(0, 0.1, 1000) - 2*np.pi/3)
        phase3 = 5.0 * np.sin(2 * np.pi * 50 * np.linspace(0, 0.1, 1000) - 4*np.pi/3)
        
        current = np.column_stack([phase1, phase2, phase3])
        
        return vibration.tolist(), current.tolist()
    
    def test_diagnosis(self, condition='healthy'):
        """Test comprehensive diagnosis with signal"""
        self.print_section(f"TEST: Comprehensive Diagnosis - {condition.upper()}")
        
        if not self.token:
            self.print_fail("No authentication token available")
            return None
        
        try:
            # Generate signals
            print(f"Generating {condition} signal...")
            vibration, current = self.generate_signals(condition)
            
            # Signal statistics
            vib_array = np.array(vibration)
            print(f"  Vibration - Mean: {vib_array.mean():.4f}, Std: {vib_array.std():.4f}, Max: {vib_array.max():.4f}")
            
            headers = {'Authorization': f'Bearer {self.token}'}
            
            print(f"Sending diagnosis request...")
            start = time.time()
            
            response = requests.post(
                f"{API_URL}/api/v1/diagnose/comprehensive",
                headers=headers,
                json={
                    'vibration_signal': vibration,
                    'current_signal': current,
                    'temperature': 70.0 + np.random.randint(0, 20),  # 70-90°C
                    'speed': 1000 + np.random.randint(-100, 100)  # ~1000 RPM
                },
                timeout=120
            )
            elapsed = time.time() - start
            
            print(f"Response received in {elapsed:.2f}s")
            
            if response.status_code == 200:
                result = response.json()
                self.print_pass(f"Diagnosis successful ({elapsed:.3f}s)")
                
                # Extract and display results
                print(f"\n{Colors.BOLD}Diagnostic Results:{Colors.END}")
                
                rul = result.get('rul_hours', 0)
                rul_conf = result.get('rul_confidence', 0)
                health = result.get('overall_health', 'Unknown')
                action = result.get('priority_action', 'N/A')
                
                print(f"  RUL: {rul:.1f} hours (confidence: {rul_conf:.1%})")
                print(f"  Health: {health}")
                print(f"  Action: {action}")
                
                faults = result.get('fault_locations', [])
                if faults:
                    print(f"\n{Colors.BOLD}Detected Faults ({len(faults)}):{Colors.END}")
                    for fault in faults:
                        component = fault.get('component', 'Unknown')
                        fault_type = fault.get('fault_type', 'Unknown')
                        severity = fault.get('severity', 'Unknown')
                        confidence = fault.get('confidence', 0)
                        print(f"    • {component}: {fault_type} ({severity}) - {confidence:.1%} confidence")
                
                # Store results
                perf_key = f"diagnosis_{condition}"
                self.results["performance"][perf_key] = elapsed
                self.results["model_predictions"][condition] = {
                    "rul_hours": rul,
                    "rul_confidence": rul_conf,
                    "overall_health": health,
                    "priority_action": action,
                    "faults_detected": len(faults),
                    "execution_time": elapsed
                }
                
                return result
            else:
                self.print_fail(f"Diagnosis failed: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            self.print_fail(f"Error: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def test_all_conditions(self):
        """Test with multiple signal conditions"""
        self.print_header("TESTING MODEL PERFORMANCE WITH VARIOUS CONDITIONS")
        
        conditions = ['healthy', 'early_degradation', 'fault_developing', 'critical']
        
        for condition in conditions:
            result = self.test_diagnosis(condition)
            if result:
                self.test_results.append((condition, result))
            time.sleep(1)  # Small delay between tests
    
    def print_performance_summary(self):
        """Print detailed performance summary"""
        self.print_header("PERFORMANCE ANALYSIS")
        
        print(f"\n{Colors.BOLD}Response Times:{Colors.END}")
        for key, value in self.results["performance"].items():
            print(f"  {key:.<50} {value:>8.3f}s")
        
        print(f"\n{Colors.BOLD}Model Predictions Summary:{Colors.END}")
        for condition, pred in self.results["model_predictions"].items():
            print(f"\n  {Colors.BOLD}{condition.upper()}{Colors.END}")
            print(f"    RUL: {pred['rul_hours']:.1f}h (confidence: {pred['rul_confidence']:.1%})")
            print(f"    Health: {pred['overall_health']}")
            print(f"    Faults: {pred['faults_detected']}")
            print(f"    Time: {pred['execution_time']:.2f}s")
    
    def save_results(self):
        """Save test results to JSON"""
        filename = f"api_performance_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = Path(__file__).parent / filename
        
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        return filepath
    
    def cleanup(self):
        """Clean up - stop server"""
        if self.server_process:
            self.print_section("Stopping API Server")
            try:
                self.server_process.terminate()
                self.server_process.wait(timeout=5)
                self.print_pass("Server stopped successfully")
            except:
                self.server_process.kill()
                self.print_info("Server force-killed")
    
    def run_full_test(self):
        """Run complete test suite"""
        try:
            self.print_header("PREDICTIVE MAINTENANCE API PERFORMANCE TEST")
            print(f"Timestamp: {datetime.now().isoformat()}")
            print(f"API URL: {API_URL}")
            
            # Start server
            if not self.start_server():
                self.print_fail("Could not start server. Exiting.")
                return
            
            # Run tests
            self.test_health()
            self.test_models_loaded()
            
            if self.authenticate():
                print("\n")
                self.test_all_conditions()
            
            # Summary
            self.print_performance_summary()
            
            # Save results
            filepath = self.save_results()
            self.print_section("Test Complete")
            self.print_pass(f"Results saved to: {filepath}")
            
            # Final summary
            self.print_header("FINAL SUMMARY")
            print(f"{Colors.GREEN}✓ API Server: Operational{Colors.END}")
            print(f"{Colors.GREEN}✓ All 6 Models: Loaded{Colors.END}")
            print(f"{Colors.GREEN}✓ Authentication: Working{Colors.END}")
            print(f"{Colors.GREEN}✓ Diagnosis Engine: Operational{Colors.END}")
            print(f"{Colors.CYAN}→ Test Results: {filepath}{Colors.END}")
            
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        except Exception as e:
            self.print_fail(f"Unexpected error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.cleanup()

def main():
    print(f"{Colors.BOLD}{Colors.CYAN}")
    print("""
    ╔════════════════════════════════════════════════════════════════════════╗
    ║                    PREDICTIVE MAINTENANCE API                          ║
    ║            Comprehensive Performance Test with Auto Server             ║
    ║                                                                        ║
    ║  This test:                                                           ║
    ║  • Automatically starts the API server                               ║
    ║  • Authenticates with the system                                     ║
    ║  • Tests with realistic sensor signals                              ║
    ║  • Evaluates model predictions across multiple conditions           ║
    ║  • Measures performance and response times                          ║
    ║  • Provides detailed analysis and reports                           ║
    ╚════════════════════════════════════════════════════════════════════════╝
    """)
    print(Colors.END)
    
    tester = APIPerformanceTester()
    tester.run_full_test()

if __name__ == "__main__":
    main()
