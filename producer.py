#!/usr/bin/env python3
"""
Day 7: CDP Event Producer
Sends realistic CDP events with identities for testing identity stitching.

Demo Sequence:
1. Anonymous visitor (deviceID only)
2. User logs in (deviceID + email) - Should stitch to same profile
3. User from different device (different deviceID + same email) - Should merge profiles
"""

import argparse
import socket
import time
import json
import sys

# Demo event sequence for Day 8-9
DEMO_EVENTS = [
    {
        "event_type": "page_view",
        "identities": {
            "deviceID": "device_abc123"
        },
        "properties": {
            "page": "/home",
            "referrer": "google.com",
            "user_agent": "Mozilla/5.0"
        },
        "description": "📱 Event 1: Anonymous visitor (device_abc123)"
    },
    {
        "event_type": "login",
        "identities": {
            "deviceID": "device_abc123",
            "email": "user@example.com"
        },
        "properties": {
            "login_method": "password",
            "login_success": True
        },
        "description": "🔑 Event 2: User logs in (links email)"
    },
    {
        "event_type": "page_view",
        "identities": {
            "deviceID": "device_abc123",
            "email": "user@example.com"
        },
        "properties": {
            "page": "/products/laptop",
            "category": "electronics",
            "product_name": "MacBook Pro"
        },
        "description": "👀 Event 3: Views product"
    },
    {
        "event_type": "add_to_cart",
        "identities": {
            "deviceID": "device_abc123",
            "email": "user@example.com"
        },
        "properties": {
            "product_id": "laptop_001",
            "product_name": "MacBook Pro",
            "price": 1299.99,
            "quantity": 1
        },
        "description": "🛒 Event 4: Adds to cart"
    },
    {
        "event_type": "page_view",
        "identities": {
            "deviceID": "device_xyz789"
        },
        "properties": {
            "page": "/home",
            "user_agent": "Mobile Safari"
        },
        "description": "📱 Event 5: Different device (creates 2nd profile)"
    },
    {
        "event_type": "login",
        "identities": {
            "deviceID": "device_xyz789",
            "email": "user@example.com"
        },
        "properties": {
            "login_method": "password",
            "login_success": True
        },
        "description": "🔗 Event 6: THE MERGE! (same email, profiles merge)"
    },
    {
        "event_type": "purchase",
        "identities": {
            "deviceID": "device_xyz789",
            "email": "user@example.com"
        },
        "properties": {
            "order_id": "ORDER_12345",
            "total": 1299.99,
            "items": ["laptop_001"],
            "payment_method": "credit_card",
            "shipping_address": "123 Main St"
        },
        "description": "💰 Event 7: Purchase complete"
    }
]

def serve_demo(host: str, port: int, interval: float, loop: bool = False):
    """
    Serve the demo event sequence to connected Flink clients.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    
    print(f"🚀 CDP Event Producer started on {host}:{port}", file=sys.stderr)
    print(f"📝 Sending {len(DEMO_EVENTS)} demo events (interval: {interval}s, loop: {loop})", file=sys.stderr)
    print(f"⏳ Waiting for Flink to connect...\n", file=sys.stderr)

    try:
        while True:
            conn, addr = sock.accept()
            print(f"✅ Flink connected from {addr}\n", file=sys.stderr)
            
            try:
                iteration = 0
                while True:
                    iteration += 1
                    print(f"{'='*60}", file=sys.stderr)
                    print(f"Iteration {iteration} - Sending {len(DEMO_EVENTS)} events:", file=sys.stderr)
                    print(f"{'='*60}\n", file=sys.stderr)
                    
                    for idx, event_template in enumerate(DEMO_EVENTS, 1):
                        # Create a copy and add timestamp
                        event = event_template.copy()
                        event["timestamp"] = int(time.time())
                        event["sequence"] = idx
                        
                        # Remove description before sending (it's just for console)
                        description = event.pop("description", "")
                        
                        # Send to Flink
                        line = json.dumps(event) + "\n"
                        try:
                            conn.sendall(line.encode("utf-8"))
                            print(f"[{idx}/{len(DEMO_EVENTS)}] {description}", file=sys.stderr)
                            print(f"     Sent: {json.dumps(event, indent=2)}\n", file=sys.stderr)
                        except (BrokenPipeError, ConnectionResetError):
                            print("⚠️ Flink disconnected", file=sys.stderr)
                            raise
                        
                        time.sleep(interval)
                    
                    if not loop:
                        print(f"\n{'='*60}", file=sys.stderr)
                        print(f"✅ All {len(DEMO_EVENTS)} events sent!", file=sys.stderr)
                        print(f"{'='*60}", file=sys.stderr)
                        print(f"\n📊 Check Neo4j Browser to see the identity graph:", file=sys.stderr)
                        print(f"   http://localhost:7474", file=sys.stderr)
                        print(f"   Run: MATCH (p:Profile)-[r:HAS_IDENTITY]->(i:Identity) RETURN p, r, i\n", file=sys.stderr)
                        break
                    else:
                        print(f"\n🔄 Looping... (Ctrl+C to stop)\n", file=sys.stderr)
                        time.sleep(interval * 2)  # Pause between loops
                        
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
                if not loop:
                    print("\n👋 Demo complete. Shutting down producer.", file=sys.stderr)
                    break
                else:
                    print("\n⏳ Waiting for next Flink connection...\n", file=sys.stderr)
                    
    except KeyboardInterrupt:
        print("\n\n⚠️ Interrupted by user. Shutting down...", file=sys.stderr)
    finally:
        try:
            sock.close()
        except Exception:
            pass

def serve_random(host: str, port: int, interval: float):
    """
    Original random data generator (from Day 4).
    """
    import random
    
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(1)
    print(f"🎲 Random producer listening on {host}:{port}", file=sys.stderr)

    try:
        while True:
            conn, addr = sock.accept()
            print(f"✅ Client connected from {addr}", file=sys.stderr)
            try:
                i = 0
                while True:
                    msg = {
                        "ts": int(time.time()),
                        "id": random.randint(1, 1000000),
                        "value": random.random(),
                        "seq": i
                    }
                    line = json.dumps(msg) + "\n"
                    try:
                        conn.sendall(line.encode("utf-8"))
                    except (BrokenPipeError, ConnectionResetError):
                        print("⚠️ Client disconnected", file=sys.stderr)
                        break
                    i += 1
                    time.sleep(interval)
            finally:
                try:
                    conn.close()
                except Exception:
                    pass
                print("⏳ Waiting for next client...", file=sys.stderr)
    except KeyboardInterrupt:
        print("\n⚠️ Shutting down", file=sys.stderr)
    finally:
        try:
            sock.close()
        except Exception:
            pass

if __name__ == "__main__":
    p = argparse.ArgumentParser(description="CDP Event Producer for Flink")
    p.add_argument("--host", default="0.0.0.0", help="Host to bind (default: 0.0.0.0)")
    p.add_argument("--port", type=int, default=9001, help="Port to bind (default: 9001)")
    p.add_argument("--interval", type=float, default=2.0, help="Seconds between events (default: 2.0)")
    p.add_argument("--mode", choices=["demo", "random"], default="demo", 
                   help="demo: send CDP event sequence, random: send random data (default: demo)")
    p.add_argument("--loop", action="store_true", help="Loop the demo sequence continuously")
    
    args = p.parse_args()
    
    if args.mode == "demo":
        serve_demo(args.host, args.port, args.interval, args.loop)
    else:
        serve_random(args.host, args.port, args.interval)