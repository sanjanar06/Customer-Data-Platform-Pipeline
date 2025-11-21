import sys
import os
import time
import json
import socket

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings

def send_event(event):
    """Send raw JSON event to Flink socket"""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((settings.PRODUCER_HOST, settings.PRODUCER_PORT))
            s.sendall((json.dumps(event) + "\n").encode('utf-8'))
            print(f"Sent: {event['identities']['email']} on SHARED_DEVICE")
            time.sleep(0.5) # Small delay to let Flink process
    except Exception as e:
        print(f"Error: {e}")

def main():
    print("⚠️  SIMULATING HAIRBALL SCENARIO ⚠️")
    print("sending 10 different users from ONE device...")
    
    shared_device_id = "device_PUBLIC_LIBRARY_01"
    
    for i in range(1, 11):
        event = {
            "event_type": "login",
            "timestamp": int(time.time()),
            "identities": {
                "deviceID": shared_device_id,
                "email": f"visitor_{i}@library.com"
            },
            "properties": {
                "location": "Public Library"
            }
        }
        send_event(event)

    print("\n✅ Done! Check http://localhost:8000/api/graph/anomalies")

if __name__ == "__main__":
    main()