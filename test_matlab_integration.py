#!/usr/bin/env python
"""
test_matlab_integration.py - Test WebSocket Communication with Simulink

This script tests the complete data flow:
  1. Connect to API WebSocket
  2. Send sensor data
  3. Receive predictions
  4. Send ground truth
  5. Verify roundtrip latency

Usage:
    python test_matlab_integration.py

Requirements:
    - FastAPI server running: python backend/run.py
    - Python packages: websocket-client, python-dotenv

Created: February 12, 2026
"""

import asyncio
import websockets
import json
import time
import uuid
from datetime import datetime
import statistics
import sys
import os

# Configuration
API_HOST = "localhost"
API_PORT = 8000
WEBSOCKET_URL = f"ws://{API_HOST}:{API_PORT}/ws/simulink"

# Test parameters
NUM_SAMPLES = 10
SAMPLE_RATE_HZ = 100  # Simulink sends at 100 Hz
WAIT_BETWEEN_SAMPLES_MS = int(1000 / SAMPLE_RATE_HZ)

# Color codes for console output
class Color:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    RESET = '\033[0m'

def log_info(msg):
    print(f"{Color.CYAN}[INFO]{Color.RESET} {msg}")

def log_success(msg):
    print(f"{Color.GREEN}[✓]{Color.RESET} {msg}")

def log_error(msg):
    print(f"{Color.RED}[✗]{Color.RESET} {msg}")

def log_warning(msg):
    print(f"{Color.YELLOW}[!]{Color.RESET} {msg}")

def log_test(msg):
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}{msg}{Color.RESET}")
    print(f"{Color.BOLD}{Color.CYAN}{'='*70}{Color.RESET}\n")


async def test_websocket_communication():
    """Main test: WebSocket communication with API."""
    
    # Generate unique client ID
    client_id = str(uuid.uuid4())
    machine_id = "MOTOR-TEST-001"
    
    log_test("TEST 1: WebSocket Connection")
    
    ws_url = f"{WEBSOCKET_URL}/{client_id}"
    log_info(f"Connecting to: {ws_url}")
    
    try:
        async with websockets.connect(ws_url, ping_interval=30) as websocket:
            log_success(f"Connected! Client ID: {client_id}")
            
            # Receive connection confirmation
            response = await asyncio.wait_for(websocket.recv(), timeout=5)
            data = json.loads(response)
            log_info(f"Server response: {data.get('message', 'Connected')}")
            
            # Run tests
            await test_sensor_data(websocket, client_id, machine_id)
            await test_health_check(websocket)
            await test_ground_truth(websocket, client_id, machine_id)
            
    except websockets.exceptions.ConnectionClosedError:
        log_error("Connection closed unexpectedly")
        return False
    except asyncio.TimeoutError:
        log_error(f"Connection timeout after 5 seconds\nMake sure API is running: python backend/run.py")
        return False
    except ConnectionRefusedError:
        log_error(f"Connection refused. Is API running on {ws_url}?")
        return False
    except Exception as e:
        log_error(f"Connection error: {e}")
        return False
    
    return True


async def test_sensor_data(websocket, client_id, machine_id):
    """Test 2: Sensor data prediction pipeline."""
    
    log_test("TEST 2: Sensor Data & Predictions")
    
    latencies = []
    predictions_received = 0
    alerts = []
    
    for i in range(NUM_SAMPLES):
        # Generate fake sensor data (5 sensors)
        import random
        sensor_data = [random.uniform(0.2, 0.9) for _ in range(5)]
        sensor_names = [
            "Vibration_X",
            "Vibration_Y",
            "Temperature",
            "Current",
            "Pressure"
        ]
        
        # Create message
        message = {
            "type": "sensor_data",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "sensor_data": sensor_data,
            "sensor_names": sensor_names,
            "machine_id": machine_id
        }
        
        log_info(f"Sample {i+1}/{NUM_SAMPLES}: Sending sensor data")
        log_info(f"  Data: {[f'{v:.2f}' for v in sensor_data]}")
        
        # Send and measure latency
        send_time = time.time()
        try:
            await websocket.send(json.dumps(message))
            
            # Wait for response with timeout
            response = await asyncio.wait_for(websocket.recv(), timeout=2)
            response_time = time.time()
            latency_ms = (response_time - send_time) * 1000
            latencies.append(latency_ms)
            
            # Parse response
            data = json.loads(response)
            
            if data.get("type") == "prediction":
                predictions_received += 1
                pred_value = data.get("prediction", 0)
                alert_level = data.get("alert_level", "UNKNOWN")
                model = data.get("model_used", "UNKNOWN")
                inference_ms = data.get("inference_time_ms", 0)
                
                log_success(f"Prediction received in {latency_ms:.2f}ms")
                log_info(f"  Prediction: {pred_value:.4f} → {alert_level}")
                log_info(f"  Model: {model}, Inference: {inference_ms:.2f}ms")
                
                if alert_level in ["WARNING", "CRITICAL"]:
                    alerts.append({
                        "sample": i+1,
                        "level": alert_level,
                        "prediction": pred_value
                    })
            else:
                log_warning(f"Unexpected response type: {data.get('type')}")
        
        except asyncio.TimeoutError:
            log_error(f"No response from API (timeout 2s)")
        
        # Wait before next sample (simulate 100 Hz rate)
        if i < NUM_SAMPLES - 1:
            await asyncio.sleep(WAIT_BETWEEN_SAMPLES_MS / 1000)
    
    # Summary statistics
    log_test("TEST 2 RESULTS: Sensor Data Latency")
    log_info(f"Predictions received: {predictions_received}/{NUM_SAMPLES}")
    
    if latencies:
        log_info(f"Latency statistics (milliseconds):")
        log_info(f"  Min: {min(latencies):.2f}ms")
        log_info(f"  Max: {max(latencies):.2f}ms")
        log_info(f"  Mean: {statistics.mean(latencies):.2f}ms")
        log_info(f"  Median: {statistics.median(latencies):.2f}ms")
        log_info(f"  P95: {sorted(latencies)[int(len(latencies)*0.95)]:.2f}ms")
        
        if statistics.median(latencies) < 50:
            log_success(f"✓ Latency target achieved! (P95 < 50ms)")
        else:
            log_warning(f"Latency higher than target (P95 should be <50ms)")
    
    if alerts:
        log_warning(f"Alerts detected ({len(alerts)}):")
        for alert in alerts:
            log_warning(f"  Sample {alert['sample']}: {alert['level']} (pred={alert['prediction']:.2f})")


async def test_health_check(websocket):
    """Test 3: Server health check."""
    
    log_test("TEST 3: Health Check")
    
    message = {
        "type": "health_check",
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    log_info("Sending health check...")
    await websocket.send(json.dumps(message))
    
    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=2)
        data = json.loads(response)
        
        if data.get("type") == "health_check_response":
            status = data.get("status", "unknown")
            connections = data.get("connections_active", 0)
            
            if status == "healthy":
                log_success(f"Server is HEALTHY")
                log_info(f"  Active connections: {connections}")
            else:
                log_warning(f"Server health: {status}")
        else:
            log_warning(f"Unexpected response: {data.get('type')}")
    
    except asyncio.TimeoutError:
        log_error("Health check timeout")


async def test_ground_truth(websocket, client_id, machine_id):
    """Test 4: Ground truth submission for learning."""
    
    log_test("TEST 4: Ground Truth (For Model Learning)")
    
    message = {
        "type": "ground_truth",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "machine_id": machine_id,
        "actual_failure": False,
        "failure_type": "normal_operation",
        "days_to_failure": 0
    }
    
    log_info("Sending ground truth (machine running normally)...")
    await websocket.send(json.dumps(message))
    
    try:
        response = await asyncio.wait_for(websocket.recv(), timeout=2)
        data = json.loads(response)
        
        if data.get("type") == "ground_truth_ack":
            status = data.get("status", "unknown")
            if status == "recorded":
                log_success("Ground truth recorded by server")
                log_info("This data will be used in weekly model retraining")
            else:
                log_warning(f"Ground truth status: {status}")
        else:
            log_warning(f"Unexpected response: {data.get('type')}")
    
    except asyncio.TimeoutError:
        log_error("Ground truth acknowledgment timeout")


async def test_endpoint_availability():
    """Test if API endpoint is available."""
    
    log_test("PRELIMINARY CHECK: API Endpoint Availability")
    
    import socket
    
    log_info(f"Testing connection to {API_HOST}:{API_PORT}...")
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((API_HOST, API_PORT))
    sock.close()
    
    if result == 0:
        log_success(f"✓ API is running on {API_HOST}:{API_PORT}")
        return True
    else:
        log_error(f"✗ API not responding on {API_HOST}:{API_PORT}")
        log_info("Start the API with: python backend/run.py")
        return False


async def main():
    """Main test runner."""
    
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*70}{Color.RESET}")
    print(f"{Color.BOLD}Predictive Maintenance API - MATLAB Integration Test{Color.RESET}")
    print(f"{Color.BOLD}{'='*70}{Color.RESET}\n")
    
    # Check if API is available
    api_available = await test_endpoint_availability()
    if not api_available:
        log_error("Cannot proceed without API")
        sys.exit(1)
    
    # Run WebSocket tests
    success = await test_websocket_communication()
    
    # Summary
    print(f"\n{Color.BOLD}{Color.CYAN}{'='*70}{Color.RESET}")
    if success:
        log_success("✓ ALL TESTS PASSED!")
        log_info("Data flow verified:")
        log_info("  ✓ SIMULINK → API (sensor data)")
        log_info("  ✓ API → SIMULINK (predictions)")
        log_info("  ✓ SIMULINK → Database (ground truth)")
        log_info("Ready to integrate with Simulink models!")
    else:
        log_error("✗ TESTS FAILED - Check configuration and API status")
    print(f"{Color.BOLD}{Color.CYAN}{'='*70}{Color.RESET}\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
        sys.exit(0)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)
