import argparse
from config import settings
from config.logging_config import setup_logging, get_logger
from .event_generator import get_demo_events, get_fuzzy_events, get_hairball_events
from .socket_server import EventSocketServer

# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="CDP Event Producer for Flink Stream Processing"
    )
    parser.add_argument(
        "--host",
        default=settings.PRODUCER_HOST,
        help=f"Host to bind (default: {settings.PRODUCER_HOST})"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.PRODUCER_PORT,
        help=f"Port to bind (default: {settings.PRODUCER_PORT})"
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=settings.PRODUCER_INTERVAL,
        help=f"Seconds between events (default: {settings.PRODUCER_INTERVAL})"
    )
    parser.add_argument(
        "--mode",
        choices=["demo", "random", "hairball", "fuzzy"],
        default="demo",
        help="demo: send CDP event sequence, random: send random data (default: demo)"
    )
    parser.add_argument(
        "--loop",
        action="store_true",
        help="Loop the demo sequence continuously"
    )
    
    args = parser.parse_args()
    
    logger.info("CDP Event Producer Starting")
    logger.info(f"Mode: {args.mode}")
    logger.info(f"Host: {args.host}:{args.port}")
    logger.info(f"Interval: {args.interval}s")
    if args.mode == "demo":
        logger.info(f"Loop: {args.loop}")
    logger.info("=" * 60)
    
    # Create and start server
    server = EventSocketServer(args.host, args.port)
    server.start()
    
    # Send events based on mode
    if args.mode == "demo":
        events = get_demo_events()
        server.send_events(events, args.interval, args.loop)
    elif args.mode == "hairball":
        events = get_hairball_events()
        server.send_events(events, args.interval, loop=True)  # Send hairball events continuously
    elif args.mode == "fuzzy":
        events = get_fuzzy_events()
        server.send_events(events, args.interval, loop=False)  # Send fuzzy events continuously
    else:
        server.send_random_events(args.interval)


if __name__ == "__main__":
    main()
