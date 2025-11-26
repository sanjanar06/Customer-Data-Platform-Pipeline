import argparse
import json
import time
from typing import List, Dict, Any
from confluent_kafka import Producer
from config import settings
from config.logging_config import setup_logging, get_logger
from src.python.producer.event_generator import (
    get_demo_events, get_fuzzy_events,get_large_scale_events
)

# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

class EventKafkaProducer:
    def __init__(self, bootstrap_servers: str, topic: str):
        self.topic = topic
        conf = {
            'bootstrap.servers': bootstrap_servers,
            'client.id': 'cdp-producer',
            'queue.buffering.max.messages': 100000,
            # --- PERFORMANCE TUNING ---
            'queue.buffering.max.messages': 100000, # Large buffer
            'batch.num.messages': 5000,             # Send big batches
            'linger.ms': 100,                       # Wait up to 100ms to fill a batch
            'compression.type': 'lz4'               # Fast compression
        }
        self.producer = Producer(conf)
        logger.info(f"Kafka Producer initialized: {bootstrap_servers} -> {topic}")

    def delivery_report(self, err, msg):
        """Callback for delivery reports"""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        # else:
        #     logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")

    def send_events(self, events: List[Dict[str, Any]], interval: float, loop: bool = False) -> None:
        """Send events to Kafka topic."""
        logger.info(f"Sending {len(events)} events to topic '{self.topic}' (interval: {interval}s, loop: {loop})")
        
        try:
            iteration = 0
            while True:
                iteration += 1
                logger.info(f"Iteration {iteration} - Sending batch...")
                
                for idx, event_template in enumerate(events, 1):
                    # Generate timestamped event
                    event = event_template.copy()
                    event["timestamp"] = int(time.time())
                    event["sequence"] = idx
                    if "description" in event:
                        desc = event.pop("description")
                    else:
                        desc = f"Event {idx}"

                    # Send to Kafka
                    try:
                        self.producer.produce(
                            self.topic,
                            key=None, # Or use profile_id as key for ordering
                            value=json.dumps(event).encode('utf-8'),
                            callback=self.delivery_report
                        )
                        # Trigger callback
                        self.producer.poll(0)
                        
                        logger.info(f"[{idx}/{len(events)}] Sent: {desc}")
                        time.sleep(interval)
                        
                    except BufferError:
                        logger.warning("Queue full, waiting...")
                        self.producer.flush()
                
                self.producer.flush() # Ensure all messages are sent
                
                if not loop:
                    logger.info("Batch complete.")
                    break
                else:
                    logger.info("Looping...")
                    time.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.warning("Stopped by user")
        finally:
            self.producer.flush()
    
    def send_hairball_events(self, interval: float) -> None:
        """Send infinite hairball events with incrementing email addresses."""
        logger.info(f"Sending infinite hairball events to topic '{self.topic}' (interval: {interval}s)")
        
        shared_device = "device_HAIRBALL_01"
        counter = 0
        
        try:
            while True:
                counter += 1
                
                event = {
                    "event_type": "login",
                    "identities": {
                        "deviceID": shared_device,
                        "email": f"victim_{counter}@bad-merge.com"
                    },
                    "properties": {"risk": "high"},
                    "timestamp": int(time.time()),
                    "sequence": counter
                }
                
                # Send to Kafka
                try:
                    self.producer.produce(
                        self.topic,
                        key=None,
                        value=json.dumps(event).encode('utf-8'),
                        callback=self.delivery_report
                    )
                    self.producer.poll(0)
                    
                    logger.info(f"[{counter}] Sent: Hairball Event victim_{counter}@bad-merge.com")
                    time.sleep(interval)
                    
                except BufferError:
                    logger.warning("Queue full, waiting...")
                    self.producer.flush()
                    
        except KeyboardInterrupt:
            logger.warning("Stopped by user")
        finally:
            self.producer.flush()

def main() -> None:
    parser = argparse.ArgumentParser(description="CDP Event Producer (Kafka)")
    parser.add_argument("--interval", type=float, default=settings.PRODUCER_INTERVAL, help="Seconds between events")
    parser.add_argument("--mode", choices=["demo", "random", "hairball", "fuzzy","stress"], default="demo", help="demo: sequential, stress: 100+ mixed events")
    parser.add_argument("--loop", action="store_true", help="Loop continuously")
    
    args = parser.parse_args()
    
    # Define Kafka Settings (Hardcoded for now or from settings)
    KAFKA_BROKER = settings.KAFKA_BROKER # External port for host machine
    TOPIC = settings.KAFKA_TOPIC
    
    logger.info("=" * 60)
    logger.info(f"CDP Kafka Producer v3.0")
    logger.info(f"Broker: {KAFKA_BROKER}")
    logger.info(f"Topic:  {TOPIC}")
    logger.info(f"Mode:   {args.mode}")
    logger.info("=" * 60)
    
    # Start Producer
    producer = EventKafkaProducer(KAFKA_BROKER, TOPIC)
    
    # Select Event Source and send
    if args.mode == "demo":
        events = get_demo_events()
        loop = args.loop  # Demo mode respects --loop flag
        producer.send_events(events, args.interval, loop)
    elif args.mode == "stress":
        events = get_large_scale_events(num_profiles=25)
        loop = args.loop  # Stress mode respects --loop flag
        producer.send_events(events, args.interval, loop)
    elif args.mode == "hairball":
        # Hairball mode sends infinite events with incrementing emails
        producer.send_hairball_events(args.interval)
    elif args.mode == "fuzzy":
        events = get_fuzzy_events()
        loop = args.loop  # Fuzzy mode respects --loop flag
        producer.send_events(events, args.interval, loop)
    else:
        logger.error("Random mode not yet implemented for Kafka producer")
        return

if __name__ == "__main__":
    main()