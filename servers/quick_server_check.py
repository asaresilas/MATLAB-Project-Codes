"""
Quick server check - minimal test to see if server is responding
"""
import requests
import time

print("Checking if API server is ready...")
max_attempts = 10
for i in range(max_attempts):
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print(f"✓ Server is UP! (attempt {i+1})")
            print(f"Response: {response.json()}")
            break
    except:
        print(f"Waiting... (attempt {i+1}/{max_attempts})")
        time.sleep(3)
else:
    print("✗ Server did not respond after 30 seconds")
