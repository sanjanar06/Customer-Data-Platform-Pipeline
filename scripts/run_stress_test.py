#!/usr/bin/env python3
import multiprocessing
import subprocess
import time
import sys
import signal

def run_producer(process_id):
    """Runs a single producer instance in stress mode"""
    print(f"🚀 Starting Producer Process #{process_id}")
    # Calls your existing producer in 'stress' mode which generates random events
    subprocess.run([sys.executable, "scripts/run_producer.py", "--mode", "stress", "--loop", "--interval", "0"])

def main():
    # Number of parallel processes (Adjust based on your CPU cores)
    NUM_PROCESSES = 8 
    
    print("="*60)
    print(f"🔥 CDP STRESS TEST: Launching {NUM_PROCESSES} Parallel Producers")
    print("Target: 10,000+ Events/Second")
    print("="*60)

    processes = []
    try:
        for i in range(NUM_PROCESSES):
            p = multiprocessing.Process(target=run_producer, args=(i,))
            p.start()
            processes.append(p)
            time.sleep(0.5) # Stagger start

        print(f"\n✅ All {NUM_PROCESSES} processes running. Check Grafana!")
        
        # Keep main process alive
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping Stress Test...")
        for p in processes:
            p.terminate()
        print("Clean shutdown complete.")

if __name__ == "__main__":
    main()