#!/usr/bin/env python
"""
Quick Launcher for API Performance Test with Auto Server Start
Run this script and it will:
1. Start the API server automatically
2. Wait for models to load
3. Run comprehensive tests with realistic signals
4. Display results and save reports
"""

import subprocess
import sys
from pathlib import Path

def main():
    # Get test script path
    test_script = Path(__file__).parent / "server_testing" / "api_tests" / "test_api_professional.py"
    
    if not test_script.exists():
        print(f"ERROR: Test script not found at {test_script}")
        sys.exit(1)
    
    print("\n" + "="*80)
    print("PREDICTIVE MAINTENANCE API - PROFESSIONAL PERFORMANCE TEST")
    print("="*80)
    print(f"\nExecuting: {test_script}")
    print("\nThis will:")
    print("  ✓ Validate system configuration")
    print("  ✓ Start the API server automatically")
    print("  ✓ Load and verify all 6 AI models")
    print("  ✓ Authenticate with security system")
    print("  ✓ Run 4 diagnostic tests with realistic signals")
    print("  ✓ Measure performance & response times")
    print("  ✓ Generate professional report")
    print("\n" + "="*80 + "\n")
    
    # Run the test
    try:
        result = subprocess.run([sys.executable, str(test_script)], cwd=Path(__file__).parent)
        sys.exit(result.returncode)
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
