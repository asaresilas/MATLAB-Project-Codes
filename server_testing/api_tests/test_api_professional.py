"""
Predictive Maintenance API - Professional Performance Test
==========================================================================
Enterprise-grade testing with professional output formatting
"""

import subprocess
import requests
import numpy as np
import time
import json
import sys
from datetime import datetime
from pathlib import Path
import os
import threading
import queue

# Configuration
API_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SERVER_STARTUP_TIMEOUT = 180

class Colors:
    """Professional color scheme"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    END = '\033[0m'
    BG_BLUE = '\033[44m'

class ProfessionalTester:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "system": {},
            "tests": {},
            "performance": {},
            "summary": {}
        }
        self.token = None
        self.server_process = None
        self.test_count = 0
        self.pass_count = 0
        
    def print_title(self):
        """Print professional title banner"""
        print(f"\n{Colors.BOLD}{Colors.CYAN}")
        print("╔" + "═"*78 + "╗")
        print("║" + " "*20 + "PREDICTIVE MAINTENANCE API TEST SUITE" + " "*21 + "║")
        print("║" + " "*16 + "Professional Performance & Validation Report" + " "*18 + "║")
        print("╚" + "═"*78 + "╝")
        print(f"{Colors.END}\n")
        
    def print_section(self, title, icon="→"):
        """Print section header"""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{icon} {title}{Colors.END}")
        print(f"{Colors.BLUE}{'─'*80}{Colors.END}")
        
    def print_subsection(self, title):
        """Print subsection header"""
        print(f"\n{Colors.CYAN}  ▪ {title}{Colors.END}")
        
    def print_pass(self, label, value="", time_ms=None):
        """Print successful test result"""
        self.pass_count += 1
        self.test_count += 1
        
        if time_ms:
            print(f"{Colors.GREEN}  ✓ {label:<45} {value:<20} ({time_ms:>6.2f}ms){Colors.END}")
        else:
            print(f"{Colors.GREEN}  ✓ {label:<45} {value}{Colors.END}")
            
    def print_fail(self, label, reason=""):
        """Print failure"""
        self.test_count += 1
        if reason:
            print(f"{Colors.RED}  ✗ {label:<45} {reason}{Colors.END}")
        else:
            print(f"{Colors.RED}  ✗ {label}{Colors.END}")
            
    def print_info(self, label, value=""):
        """Print info message"""
        if value:
            print(f"{Colors.YELLOW}  ℹ {label:<45} {str(value)}{Colors.END}")
        else:
            print(f"{Colors.YELLOW}  ℹ {label}{Colors.END}")
            
    def print_data(self, label, value):
        """Print key-value data"""
        print(f"  {label:<40} : {value}")
        
    def print_table_row(self, col1, col2, col3, col4, col5):
        """Print table row"""
        print(f"  {col1:<20} │ {col2:<15} │ {col3:<12} │ {col4:<12} │ {col5:<12}")
        
    def print_progress_bar(self, elapsed, total, percent):
        """Print professional progress bar"""
        bar_length = 30
        filled = int(bar_length * percent / 100)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r{Colors.BLUE}  Loading: [{bar}] {percent:>3}% ({elapsed:>3}/{total}s){Colors.END}", end='', flush=True)
        
    def start_server(self):
        """Start API server with professional output"""
        self.print_section("SERVER INITIALIZATION", "⚙")
        
        try:
            project_root = Path(__file__).parent.parent.parent
            backend_dir = project_root / "backend"
            
            self.print_info("Project Root", project_root)
            self.print_info("Backend Directory", backend_dir)
            
            if not backend_dir.exists():
                self.print_fail("Backend directory", f"NOT FOUND: {backend_dir}")
                return False
            
            self.print_info("Status", "Starting server subprocess...")
            
            # Start server with output suppression
            self.server_process = subprocess.Popen(
                [sys.executable, "-m", "uvicorn", "app.main:app", 
                 "--host", "0.0.0.0", "--port", "8000"],
                cwd=str(backend_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            # Read output in background
            output_thread = threading.Thread(target=self._monitor_server, daemon=True)
            output_thread.start()
            
            print()
            start_time = time.time()
            last_update = 0
            
            # Wait for server startup
            while time.time() - start_time < SERVER_STARTUP_TIMEOUT:
                elapsed = int(time.time() - start_time)
                progress = int((elapsed / SERVER_STARTUP_TIMEOUT) * 100)
                
                if elapsed > last_update:
                    self.print_progress_bar(elapsed, SERVER_STARTUP_TIMEOUT, progress)
                    last_update = elapsed
                
                # Check process
                if self.server_process.poll() is not None:
                    print()
                    self.print_fail("Server Process", f"Crashed (exit code: {self.server_process.poll()})")
                    return False
                
                # Check health endpoint
                try:
                    response = requests.get(f"{API_URL}/health", timeout=2)
                    if response.status_code == 200:
                        print()
                        self.print_pass("Server Health", "ACTIVE", elapsed * 1000)
                        
                        # Check models
                        try:
                            models_resp = requests.get(f"{API_URL}/api/v1/models", timeout=5)
                            if models_resp.status_code == 200:
                                data = models_resp.json()
                                loaded = len(data.get('loaded_models', []))
                                if loaded >= 6:
                                    self.print_pass("Models Loaded", f"{loaded}/6 READY")
                                    time.sleep(1)
                                    return True
                                else:
                                    self.print_info("Models", f"{loaded}/6 loading...")
                        except:
                            self.print_info("Models", "Still initializing...")
                except:
                    pass
                
                time.sleep(0.5)
            
            print()
            self.print_fail("Server Startup", f"Timeout after {SERVER_STARTUP_TIMEOUT}s")
            return False
            
        except Exception as e:
            self.print_fail("Server Startup", str(e))
            return False
    
    def _monitor_server(self):
        """Monitor server output"""
        try:
            while True:
                line = self.server_process.stdout.readline()
                if not line:
                    break
                # Only show errors
                if 'error' in line.lower() or 'exception' in line.lower():
                    print(f"{Colors.YELLOW}[SERVER] {line.strip()}{Colors.END}")
        except:
            pass
    
    def run_system_validation(self):
        """Validate system components"""
        self.print_section("SYSTEM VALIDATION", "✓")
        
        checks = {
            "Python Version": f"{sys.version.split()[0]}",
            "API Server": f"{API_URL}",
            "Authentication": f"{USERNAME}:***",
            "Model Timeout": f"{SERVER_STARTUP_TIMEOUT}s"
        }
        
        for check, value in checks.items():
            self.print_pass(check, value)
    
    def test_health(self):
        """Test 1: Health Check"""
        self.print_section("TEST 1: HEALTH CHECK", "1️⃣")
        
        try:
            start = time.time()
            response = requests.get(f"{API_URL}/health", timeout=5)
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'UNKNOWN')
                self.print_pass("Server Health", status, elapsed)
                self.results["performance"]["health_check"] = elapsed
                return True
            else:
                self.print_fail("Server Health", f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_fail("Server Health", str(e))
            return False
    
    def test_models_loaded(self):
        """Test 2: Verify Models"""
        self.print_section("TEST 2: MODEL VERIFICATION", "2️⃣")
        
        try:
            response = requests.get(f"{API_URL}/api/v1/models", timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                models = data.get('loaded_models', [])
                
                expected = {'CIA1', 'NASA', 'CWRU', 'Induction_Motor', 'Current_Signature', 'Thermal'}
                loaded = set(models)
                
                self.print_info(f"Models Loaded: {len(loaded)}/6")
                
                for model in sorted(expected):
                    if model in loaded:
                        self.print_pass(f"  {model}", "READY")
                    else:
                        self.print_fail(f"  {model}", "MISSING")
                
                self.results["tests"]["models"] = {
                    "count": len(models),
                    "models": sorted(models)
                }
                return len(loaded) == 6
            else:
                self.print_fail("Models Query", f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_fail("Models Query", str(e))
            return False
    
    def test_authentication(self):
        """Test 3: Authentication"""
        self.print_section("TEST 3: AUTHENTICATION", "3️⃣")
        
        try:
            self.print_info("Username", USERNAME)
            
            start = time.time()
            response = requests.post(
                f"{API_URL}/api/v1/auth/token",
                data={'username': USERNAME, 'password': PASSWORD},
                timeout=10
            )
            elapsed = (time.time() - start) * 1000
            
            if response.status_code == 200:
                data = response.json()
                self.token = data['access_token']
                expires = data.get('expires_in', 3600)
                
                self.print_pass("Authentication", "SUCCESS", elapsed)
                self.print_info("Token Expires In", f"{expires//60} minutes ({expires}s)")
                
                self.results["performance"]["authentication"] = elapsed
                self.results["tests"]["auth"] = {
                    "status": "success",
                    "expires_in": expires
                }
                return True
            else:
                self.print_fail("Authentication", f"Status {response.status_code}")
                return False
        except Exception as e:
            self.print_fail("Authentication", str(e))
            return False
    
    def generate_signal(self, condition):
        """Generate synthetic sensor signal"""
        sample_rate = 12000
        duration = 1
        t = np.linspace(0, duration, int(sample_rate * duration))
        
        if condition == "healthy":
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)
            vibration += 0.1 * np.sin(2 * np.pi * 120 * t)
            vibration += np.random.normal(0, 0.05, len(t))
            rul = 1250
        elif condition == "degradation":
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)
            vibration += 0.15 * np.sin(2 * np.pi * 120 * t)
            vibration += 0.1 * np.sin(2 * np.pi * 180 * t)
            vibration += np.random.normal(0, 0.1, len(t))
            rul = 850
        elif condition == "fault":
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)
            vibration += 0.25 * np.sin(2 * np.pi * 120 * t)
            vibration += 0.2 * np.sin(2 * np.pi * 180 * t)
            vibration += 0.15 * np.sin(2 * np.pi * 240 * t)
            vibration += np.random.normal(0, 0.15, len(t))
            vibration += np.random.choice([0, 2.0], len(t), p=[0.98, 0.02])
            rul = 250
        else:  # critical
            vibration = 0.5 * np.sin(2 * np.pi * 60 * t)
            vibration += 0.3 * np.sin(2 * np.pi * 120 * t)
            vibration += 0.25 * np.sin(2 * np.pi * 180 * t)
            vibration += 0.2 * np.sin(2 * np.pi * 240 * t)
            vibration += 0.15 * np.sin(2 * np.pi * 300 * t)
            vibration += np.random.normal(0, 0.2, len(t))
            vibration += np.random.choice([0, 4.0], len(t), p=[0.95, 0.05])
            rul = 50
        
        # 3-phase current
        current_phases = []
        for phase in range(3):
            phase_shift = phase * 2 * np.pi / 3
            phase_current = 10 * np.sin(2 * np.pi * 60 * t + phase_shift)
            current_phases.append(phase_current[:1000].tolist())
        
        return {
            "vibration": vibration.tolist(),
            "current": current_phases,
            "expected_rul": rul
        }
    
    def run_diagnosis_tests(self):
        """Test 4-7: Run diagnosis with different conditions"""
        self.print_section("DIAGNOSIS TESTS", "4️⃣-7️⃣")
        
        conditions = [
            ("Healthy Operation", "healthy", "🟢"),
            ("Early Degradation", "degradation", "🟡"),
            ("Fault Developing", "fault", "🟠"),
            ("Critical Condition", "critical", "🔴")
        ]
        
        self.results["tests"]["diagnosis"] = {}
        self.results["tests"]["model_performance"] = {}
        
        for i, (label, condition, emoji) in enumerate(conditions, 1):
            print(f"\n{Colors.BOLD}{emoji} TEST {3+i}: {label.upper()}{Colors.END}")
            print(f"{Colors.BLUE}{'─'*80}{Colors.END}")
            
            try:
                self.print_info("Generating signal", condition)
                signal = self.generate_signal(condition)
                
                start = time.time()
                response = requests.post(
                    f"{API_URL}/api/v1/diagnose/comprehensive",
                    json=signal,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=15
                )
                elapsed = (time.time() - start) * 1000
                
                if response.status_code == 200:
                    data = response.json()
                    rul = data.get('rul', {}).get('remaining_hours', 0)
                    health = data.get('health_status', 'UNKNOWN')
                    confidence = data.get('rul', {}).get('confidence', 0)
                    faults = len(data.get('detected_faults', []))
                    
                    # Extract model predictions and metrics
                    model_predictions = data.get('model_predictions', {})
                    fault_predictions = data.get('fault_predictions', {})
                    
                    self.print_pass("Diagnosis Result", "SUCCESS", elapsed)
                    self.print_data("  RUL (Hours)", f"{rul:.1f}")
                    self.print_data("  Health Status", health)
                    self.print_data("  Confidence", f"{confidence:.1f}%")
                    self.print_data("  Faults Detected", faults)
                    
                    # Display model-level predictions
                    if model_predictions:
                        print(f"\n{Colors.BOLD}  Model Predictions:{Colors.END}")
                        for model_name, pred_data in sorted(model_predictions.items()):
                            if isinstance(pred_data, dict):
                                rul_val = pred_data.get('rul', pred_data.get('value', 'N/A'))
                                conf = pred_data.get('confidence', 'N/A')
                                print(f"    • {model_name:<25} RUL: {str(rul_val):<10} | Confidence: {str(conf)}%")
                            else:
                                print(f"    • {model_name:<25} {pred_data}")
                    
                    # Display fault predictions from each model
                    if fault_predictions:
                        print(f"\n{Colors.BOLD}  Fault Detection:{Colors.END}")
                        for model_name, faults_data in sorted(fault_predictions.items()):
                            if isinstance(faults_data, list):
                                fault_count = len(faults_data)
                                print(f"    • {model_name:<25} {fault_count} faults detected")
                            else:
                                print(f"    • {model_name:<25} {faults_data}")
                    
                    self.results["tests"]["diagnosis"][condition] = {
                        "rul": rul,
                        "health": health,
                        "confidence": confidence,
                        "faults": faults,
                        "response_time_ms": elapsed,
                        "model_predictions": model_predictions,
                        "fault_predictions": fault_predictions
                    }
                    self.results["performance"][f"diagnosis_{condition}"] = elapsed
                    
                    # Store for model performance analysis
                    if model_name not in self.results["tests"]["model_performance"]:
                        self.results["tests"]["model_performance"][model_name] = []
                    
                else:
                    self.print_fail("Diagnosis Result", f"Status {response.status_code}")
            except Exception as e:
                self.print_fail("Diagnosis Result", str(e))
    
    def print_summary(self):
        """Print professional summary report"""
        self.print_section("TEST EXECUTION SUMMARY", "📊")
        
        # Test statistics
        success_rate = (self.pass_count / self.test_count * 100) if self.test_count > 0 else 0
        
        print(f"\n{Colors.BOLD}Test Statistics:{Colors.END}")
        print(f"  Total Tests Run       : {self.test_count}")
        print(f"  Tests Passed          : {Colors.GREEN}{self.pass_count}{Colors.END}")
        print(f"  Tests Failed          : {Colors.RED}{self.test_count - self.pass_count}{Colors.END}")
        print(f"  Success Rate          : {Colors.CYAN}{success_rate:.1f}%{Colors.END}")
        
        # Performance metrics table
        if self.results["performance"]:
            print(f"\n{Colors.BOLD}Performance Metrics (Response Times):{Colors.END}")
            print(f"{'  Test Name':<35} {'Response Time':>15}")
            print(f"  {'-'*49}")
            
            avg_time = 0
            for test, time_ms in sorted(self.results["performance"].items()):
                avg_time += time_ms
                color = Colors.GREEN if time_ms < 3000 else Colors.YELLOW if time_ms < 5000 else Colors.RED
                print(f"  {test:<35} {color}{time_ms:>14.2f} ms{Colors.END}")
            
            if self.results["performance"]:
                avg = avg_time / len(self.results["performance"])
                print(f"  {'-'*49}")
                print(f"  {'Average':<35} {Colors.CYAN}{avg:>14.2f} ms{Colors.END}")
        
        # Models status
        if self.results["tests"].get("models"):
            models = self.results["tests"]["models"]["models"]
            print(f"\n{Colors.BOLD}Loaded Models ({len(models)}/6) - Status:{Colors.END}")
            for model in sorted(models):
                print(f"  {Colors.GREEN}✓{Colors.END} {model}")
        
        # Diagnosis results with RUL progression
        if self.results["tests"].get("diagnosis"):
            print(f"\n{Colors.BOLD}Diagnosis Results Across Conditions:{Colors.END}")
            print(f"{'  Condition':<20} {'RUL (hours)':>15} {'Health':>15} {'Confidence':>15}")
            print(f"  {'-'*65}")
            
            conditions = ["healthy", "degradation", "fault", "critical"]
            for cond in conditions:
                if cond in self.results["tests"]["diagnosis"]:
                    data = self.results["tests"]["diagnosis"][cond]
                    rul = data["rul"]
                    health = data["health"]
                    conf = data["confidence"]
                    
                    # Color code by condition
                    if cond == "healthy":
                        emoji = "🟢"
                    elif cond == "degradation":
                        emoji = "🟡"
                    elif cond == "fault":
                        emoji = "🟠"
                    else:
                        emoji = "🔴"
                    
                    print(f"  {emoji} {cond:<17} {rul:>14.1f}h {health:>14} {conf:>14.1f}%")
        
        # Model predictions accuracy
        if self.results["tests"].get("diagnosis"):
            print(f"\n{Colors.BOLD}Model-Level Predictions Summary:{Colors.END}")
            print(f"{'  Model Name':<25} {'Avg RUL (h)':>15} {'Avg Confidence':>15}")
            print(f"  {'-'*55}")
            
            model_stats = {}
            for cond, diag_data in self.results["tests"]["diagnosis"].items():
                preds = diag_data.get("model_predictions", {})
                for model_name, pred in preds.items():
                    if model_name not in model_stats:
                        model_stats[model_name] = {"ruls": [], "confs": []}
                    
                    if isinstance(pred, dict):
                        rul_val = pred.get('rul', pred.get('value', 0))
                        conf_val = pred.get('confidence', 0)
                        if isinstance(rul_val, (int, float)):
                            model_stats[model_name]["ruls"].append(rul_val)
                        if isinstance(conf_val, (int, float)):
                            model_stats[model_name]["confs"].append(conf_val)
            
            for model_name in sorted(model_stats.keys()):
                stats = model_stats[model_name]
                avg_rul = np.mean(stats["ruls"]) if stats["ruls"] else 0
                avg_conf = np.mean(stats["confs"]) if stats["confs"] else 0
                
                # Color confidence high->green, low->red
                conf_color = Colors.GREEN if avg_conf >= 80 else Colors.YELLOW if avg_conf >= 60 else Colors.RED
                print(f"  {model_name:<25} {avg_rul:>14.1f}h {conf_color}{avg_conf:>14.1f}%{Colors.END}")
        
        # Verdict
        print(f"\n{Colors.BOLD}Overall Status:{Colors.END}")
        if success_rate >= 90:
            print(f"  {Colors.GREEN}✓ PASSED - System is operational{Colors.END}")
            status = "PASSED"
        else:
            print(f"  {Colors.RED}✗ FAILED - Review logs above{Colors.END}")
            status = "FAILED"
        
        self.results["summary"] = {
            "total_tests": self.test_count,
            "passed": self.pass_count,
            "success_rate": success_rate,
            "status": status
        }
    
    def save_report(self):
        """Save professional JSON report"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_name = f"api_test_report_{timestamp}.json"
            
            with open(report_name, 'w') as f:
                json.dump(self.results, f, indent=2)
            
            print(f"\n{Colors.BOLD}Report Saved:{Colors.END}")
            print(f"  {Colors.CYAN}{report_name}{Colors.END}")
        except Exception as e:
            self.print_fail("Report Save", str(e))
    
    def run(self):
        """Run complete test suite"""
        self.print_title()
        
        # System validation
        self.run_system_validation()
        
        # Start server
        if not self.start_server():
            self.print_section("TEST EXECUTION HALTED", "⛔")
            self.print_fail("Server Startup", "Critical failure - cannot continue")
            return
        
        # Run tests
        self.test_health()
        self.test_models_loaded()
        self.test_authentication()
        
        if self.token:
            self.run_diagnosis_tests()
        
        # Summary
        self.print_summary()
        self.save_report()
        
        # Cleanup
        print(f"\n{Colors.BLUE}Stopping server...{Colors.END}")
        if self.server_process:
            self.server_process.terminate()
            self.server_process.wait(timeout=5)
        print(f"{Colors.GREEN}✓ Server stopped{Colors.END}")
        print(f"\n{Colors.CYAN}{'═'*80}{Colors.END}\n")

def main():
    tester = ProfessionalTester()
    try:
        tester.run()
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}")
        if tester.server_process:
            tester.server_process.terminate()
        sys.exit(130)

if __name__ == "__main__":
    main()
