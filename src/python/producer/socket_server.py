import socket
import json
import time
from typing import List, Dict, Any, Optional
from config.logging_config import get_logger
from .event_generator import generate_event_with_timestamp

logger = get_logger(__name__)

class EventSocketServer:
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
    
    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((self.host, self.port))
        self.socket.listen(1)
        logger.info(f"Socket server started on {self.host}:{self.port}")
    
    def send_events(
        self,
        events: List[Dict[str, Any]],
        interval: float,
        loop: bool = False
    ) -> None:
        """
        Send events to connected clients.
        
        Args:
            events: List of event templates to send
            interval: Seconds between events
            loop: Whether to loop the sequence continuously
        """
        if not self.socket:
            raise RuntimeError("Server not started. Call start() first.")
        
        logger.info(f"Sending {len(events)} events (interval: {interval}s, loop: {loop})")
        logger.info("Waiting for Flink to connect...")
        
        try:
            while True:
                conn, addr = self.socket.accept()
                logger.info(f"Client connected from {addr}")
                
                try:
                    iteration = 0
                    while True:
                        iteration += 1
                        logger.info(f"Iteration {iteration} - Sending {len(events)} events")
                        
                        for idx, event_template in enumerate(events, 1):
                            event = generate_event_with_timestamp(event_template, idx)
                    
                            line = json.dumps(event) + "\n"
                            try:
                                conn.sendall(line.encode("utf-8"))
                                logger.info(f"[{idx}/{len(events)}] {event.get('description', 'No description')}")
                                logger.debug(f"Sent: {json.dumps(event, indent=2)}")
                            except (BrokenPipeError, ConnectionResetError):
                                logger.warning("Client disconnected")
                                raise
                            
                            time.sleep(interval)
                        
                        if not loop:
                            logger.info(f"All {len(events)} events sent successfully")
                            logger.info("Check Neo4j Browser: http://localhost:7474")
                            logger.info("Query: MATCH (p:Profile)-[r:HAS_IDENTITY]->(i:Identity) RETURN p, r, i")
                            break
                        else:
                            logger.info("Looping... (Ctrl+C to stop)")
                            time.sleep(interval * 2)
                
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    if not loop:
                        logger.info("Demo complete. Shutting down producer.")
                        break
                    else:
                        logger.info("Waiting for next client connection...")
        
        except KeyboardInterrupt:
            logger.warning("Interrupted by user. Shutting down...")
        finally:
            self.stop()
    
    def stop(self):
        if self.socket:
            try:
                self.socket.close()
                logger.info("Socket server stopped")
            except Exception as e:
                logger.error(f"Error closing socket: {e}")
    
    def send_random_events(self, interval: float) -> None:
        """
        Send random test events (original behavior).
        
        Args:
            interval: Seconds between events
        """
        import random
        
        if not self.socket:
            raise RuntimeError("Server not started. Call start() first.")
        
        logger.info(f"Random event generator started (interval: {interval}s)")
        
        try:
            while True:
                conn, addr = self.socket.accept()
                logger.info(f"Client connected from {addr}")
                
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
                            logger.warning("Client disconnected")
                            break
                        i += 1
                        time.sleep(interval)
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass
                    logger.info("Waiting for next client...")
        
        except KeyboardInterrupt:
            logger.warning("Shutting down random generator")
        finally:
            self.stop()
