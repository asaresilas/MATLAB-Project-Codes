import sys
import os
import numpy as np
import time

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.real_time_analyzer import RealTimeAnalyzer

def test_real_time_processing():
    print("Testing Real-Time Analyzer...")
    print("=" * 60)
    
    # Initialize Analyzer
    # Use small window for testing
    WINDOW_SIZE = 100
    OVERLAP = 0.5
    analyzer = RealTimeAnalyzer(window_size=WINDOW_SIZE, overlap_percent=OVERLAP)
    
    print(f"Window Size: {WINDOW_SIZE}")
    print(f"Step Size: {analyzer.step_size}")
    
    # Generate Dummy Stream
    # We'll simulate a stream of 250 points
    # Expected behavior:
    # - Point 0-99: Filling buffer
    # - Point 100: First analysis (Window 0-100)
    # - Point 150: Second analysis (Window 50-150)
    # - Point 200: Third analysis (Window 100-200)
    # - Point 250: Fourth analysis (Window 150-250)
    
    total_points = 250
    stream_vib = np.random.randn(total_points)
    stream_curr = np.random.randn(total_points)
    
    print("\nSimulating Data Stream...")
    analysis_count = 0
    
    for i in range(total_points):
        # Push one point at a time
        result = analyzer.push_data(stream_vib[i], stream_curr[i], 45.0, 1750.0)
        
        if result:
            analysis_count += 1
            print(f"Analysis triggered at point {i+1}")
            for res in result:
                print(f"  Status: {res['status']}")
                print(f"  RUL: {res['rul_hours']:.1f}")
                
    print("\n" + "=" * 60)
    print(f"Total Analyses Triggered: {analysis_count}")
    
    # Expected: 4 analyses (at 100, 150, 200, 250)
    if analysis_count == 4:
        print("SUCCESS: Correct number of analyses triggered.")
    else:
        print(f"FAILURE: Expected 4 analyses, got {analysis_count}.")

if __name__ == "__main__":
    test_real_time_processing()
