import numpy as np
import sys
import os
from collections import deque
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.interface import analyze_motor_data

class RealTimeAnalyzer:
    """
    Handles real-time processing of motor data using a sliding window approach.
    """
    def __init__(self, window_size=2048, overlap_percent=0.5):
        """
        Initialize the RealTimeAnalyzer.

        :param window_size: Number of data points to accumulate before analysis (default: 2048)
        :param overlap_percent: Percentage of overlap between consecutive windows (0.0 to 1.0)
        """
        self.window_size = window_size
        self.step_size = int(window_size * (1 - overlap_percent))
        
        # Buffers for signal data
        self.vib_buffer = deque(maxlen=window_size)
        self.curr_buffer = deque(maxlen=window_size)
        
        # Store latest scalar values
        self.latest_temp = 0.0
        self.latest_speed = 0.0
        
        # State tracking
        self.samples_since_last_analysis = 0
        self.analysis_history = []

    def push_data(self, vibration, current, temperature, speed):
        """
        Push new data points into the analyzer.
        
        :param vibration: Single float or list of vibration values
        :param current: Single float or list of current values
        :param temperature: Current temperature
        :param speed: Current speed
        :return: Analysis result dict if a window is completed, else None
        """
        # Handle both single values and chunks
        if np.isscalar(vibration):
            vibration = [vibration]
            current = [current]
            
        # Update scalars
        self.latest_temp = temperature
        self.latest_speed = speed
        
        results = []
        
        for v, c in zip(vibration, current):
            self.vib_buffer.append(v)
            self.curr_buffer.append(c)
            self.samples_since_last_analysis += 1
            
            # Check if we have enough data and it's time to analyze
            if len(self.vib_buffer) == self.window_size and \
               self.samples_since_last_analysis >= self.step_size:
                
                # Perform Analysis
                result = self._analyze_window()
                results.append(result)
                
                # Reset counter for step size
                self.samples_since_last_analysis = 0
                
        return results if results else None

    def _analyze_window(self):
        """Internal method to trigger analysis on the current buffer."""
        # Convert buffers to numpy arrays
        vib_data = np.array(self.vib_buffer)
        curr_data = np.array(self.curr_buffer)
        
        # Call the main interface function
        # Note: analyze_motor_data expects lists or arrays
        timestamp = datetime.now().isoformat()
        
        try:
            analysis = analyze_motor_data(
                vib_data, 
                curr_data, 
                self.latest_temp, 
                self.latest_speed
            )
            
            # Add metadata
            analysis['timestamp'] = timestamp
            analysis['window_size'] = self.window_size
            
            # Store in history (keep last 100)
            self.analysis_history.append(analysis)
            if len(self.analysis_history) > 100:
                self.analysis_history.pop(0)
                
            return analysis
            
        except Exception as e:
            print(f"Error during real-time analysis: {e}")
            return {
                "timestamp": timestamp,
                "status": "Error",
                "error": str(e)
            }

    def get_history(self):
        """Return the history of analysis results."""
        return self.analysis_history

    def clear_buffers(self):
        """Reset the analyzer state."""
        self.vib_buffer.clear()
        self.curr_buffer.clear()
        self.samples_since_last_analysis = 0
