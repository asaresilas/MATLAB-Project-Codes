#!/usr/bin/env python
"""
API Diagnostic Tool
Checks the setup and configuration of the Predictive Maintenance API
"""

import os
import sys
import json
from pathlib import Path

class APIDiagnostic:
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.success = []
        
    def check_project_structure(self):
        """Check if folder structure is correct"""
        print("\n" + "="*70)
        print("CHECKING PROJECT STRUCTURE")
        print("="*70)
        
        required_dirs = [
            "server_setup/backend",
            "server_testing/api_tests",
            "utility_scripts",
            "Trained_models",
            "models",
            "matlab_client",
            "src",
            ".venv"
        ]
        
        for dir_path in required_dirs:
            full_path = Path(dir_path)
            if full_path.exists():
                print(f"✓ {dir_path}")
                self.success.append(f"Directory: {dir_path}")
            else:
                print(f"✗ MISSING: {dir_path}")
                self.issues.append(f"Directory not found: {dir_path}")
    
    def check_server_files(self):
        """Check if server files exist"""
        print("\n" + "="*70)
        print("CHECKING SERVER FILES")
        print("="*70)
        
        server_files = {
            "server_setup/backend/app/main.py": "API entry point",
            "server_setup/backend/deployment_config.json": "Model configuration",
            "server_setup/START_API_SERVER.bat": "Server startup (Windows)",
            "server_setup/START_API_SERVER.ps1": "Server startup (PowerShell)",
            "server_setup/backend/app/services/model_registry.py": "Model loader",
            "server_setup/backend/app/api/comprehensive.py": "Comprehensive endpoint",
            "server_setup/backend/app/api/endpoints.py": "API endpoints",
        }
        
        for file_path, description in server_files.items():
            if os.path.exists(file_path):
                print(f"✓ {Path(file_path).name:30} ({description})")
                self.success.append(f"Server file: {file_path}")
            else:
                print(f"✗ MISSING: {file_path}")
                self.issues.append(f"Server file not found: {file_path}")
    
    def check_test_files(self):
        """Check if test files exist"""
        print("\n" + "="*70)
        print("CHECKING TEST FILES")
        print("="*70)
        
        test_files = {
            "server_testing/api_tests/test_all_models.py": "Comprehensive test suite",
            "server_testing/api_tests/test_api_simple.py": "Simple tests",
            "server_testing/README_TESTING.md": "Testing documentation",
        }
        
        for file_path, description in test_files.items():
            if os.path.exists(file_path):
                print(f"✓ {Path(file_path).name:30} ({description})")
                self.success.append(f"Test file: {file_path}")
            else:
                print(f"✗ MISSING: {file_path}")
                self.issues.append(f"Test file not found: {file_path}")
    
    def check_models(self):
        """Check if AI models exist"""
        print("\n" + "="*70)
        print("CHECKING AI MODELS")
        print("="*70)
        
        # Load deployment config
        config_path = "server_setup/backend/deployment_config.json"
        if not os.path.exists(config_path):
            print(f"✗ deployment_config.json not found at {config_path}")
            self.issues.append("Configuration file missing")
            return
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        for model_name, model_config in config.items():
            model_path = model_config.get("model_path")
            if model_path:
                if os.path.exists(model_path):
                    print(f"✓ {model_name:20} {model_path}")
                    self.success.append(f"Model loaded: {model_name}")
                else:
                    print(f"✗ {model_name:20} MISSING: {model_path}")
                    self.issues.append(f"Model not found: {model_name}")
            
            # Check scaler if specified
            scaler_path = model_config.get("scaler_path")
            if scaler_path:
                if os.path.exists(scaler_path):
                    print(f"  └─ Scaler: ✓ {Path(scaler_path).name}")
                else:
                    print(f"  └─ Scaler: ✗ MISSING {Path(scaler_path).name}")
                    self.warnings.append(f"Scaler missing for {model_name}")
    
    def check_python_environment(self):
        """Check Python environment setup"""
        print("\n" + "="*70)
        print("CHECKING PYTHON ENVIRONMENT")
        print("="*70)
        
        venv_path = Path(".venv")
        if venv_path.exists():
            print(f"✓ Virtual environment found: {venv_path}")
            self.success.append("Virtual environment exists")
        else:
            print(f"✗ Virtual environment NOT found: {venv_path}")
            self.issues.append("Virtual environment missing - run: python -m venv .venv")
            return
        
        # Check requirements
        req_files = [
            "requirements.txt",
            "server_setup/backend/requirements.txt"
        ]
        
        print("\nDependencies files:")
        for req_file in req_files:
            if os.path.exists(req_file):
                with open(req_file, 'r') as f:
                    packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                print(f"✓ {req_file} ({len(packages)} packages)")
                self.success.append(f"Requirements found: {req_file}")
            else:
                print(f"✗ MISSING: {req_file}")
    
    def check_documentation(self):
        """Check documentation"""
        print("\n" + "="*70)
        print("CHECKING DOCUMENTATION")
        print("="*70)
        
        docs = {
            "PROJECT_ORGANIZATION.md": "Project organization guide",
            "server_testing/README_TESTING.md": "Testing guide",
            "README.md": "Project README",
            "docs/API_KEY_AUTH.md": "API authentication guide",
        }
        
        for doc_file, description in docs.items():
            if os.path.exists(doc_file):
                size = os.path.getsize(doc_file)
                print(f"✓ {Path(doc_file).name:30} ({size:,} bytes) - {description}")
                self.success.append(f"Documentation: {doc_file}")
            else:
                print(f"⚠ Optional: {doc_file}")
                self.warnings.append(f"Documentation missing: {doc_file}")
    
    def print_summary(self):
        """Print diagnostic summary"""
        print("\n" + "="*70)
        print("DIAGNOSTIC SUMMARY")
        print("="*70)
        
        print(f"\n✓ Success:  {len(self.success)} checks passed")
        print(f"⚠ Warnings: {len(self.warnings)} warnings")
        print(f"✗ Issues:   {len(self.issues)} critical issues")
        
        if self.warnings:
            print("\nWARNINGS:")
            for warning in self.warnings:
                print(f"  ⚠ {warning}")
        
        if self.issues:
            print("\nCRITICAL ISSUES (Must fix):")
            for issue in self.issues:
                print(f"  ✗ {issue}")
        
        if not self.issues:
            print("\n" + "="*70)
            print("✓ ALL CHECKS PASSED - PROJECT IS PROPERLY ORGANIZED")
            print("="*70)
            print("\nYou can now:")
            print("  1. Start API server: cd server_setup && START_API_SERVER.bat")
            print("  2. Test API: python server_testing/api_tests/test_all_models.py")
            print("="*70)
        else:
            print("\n" + "="*70)
            print("✗ FIX ISSUES BEFORE PROCEEDING")
            print("="*70)
    
    def run(self):
        """Run all diagnostics"""
        print("\n" + "="*70)
        print("PREDICTIVE MAINTENANCE API - PROJECT DIAGNOSTIC")
        print("="*70)
        
        self.check_project_structure()
        self.check_server_files()
        self.check_test_files()
        self.check_models()
        self.check_python_environment()
        self.check_documentation()
        
        self.print_summary()
        
        return len(self.issues) == 0

if __name__ == "__main__":
    diagnostic = APIDiagnostic()
    success = diagnostic.run()
    sys.exit(0 if success else 1)
