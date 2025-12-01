#!/usr/bin/env python3
"""
Batch Job Scheduler

Runs the CDP batch job (ELT pipeline) on a configurable schedule.
Default: Every 5 minutes
"""

import time
import signal
import sys
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import settings
from config.logging_config import setup_logging, get_logger
from src.python.batch.main import main as run_batch_job

# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Global scheduler instance for graceful shutdown
scheduler = None

def graceful_shutdown(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info(f"\n🛑 Received signal {signum}. Shutting down scheduler...")
    if scheduler:
        scheduler.shutdown(wait=True)
    sys.exit(0)

def scheduled_batch_job():
    """Wrapper function to run the batch job with error handling."""
    logger.info("=" * 80)
    logger.info(f"🔄 SCHEDULED BATCH JOB TRIGGERED - {datetime.now().isoformat()}")
    logger.info("=" * 80)
    
    try:
        run_batch_job()
        logger.info("✅ Scheduled batch job completed successfully")
    except Exception as e:
        logger.error(f"❌ Scheduled batch job failed: {e}", exc_info=True)
        # Don't raise - let scheduler continue running

def main():
    """Main scheduler loop."""
    global scheduler
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)
    signal.signal(signal.SIGTERM, graceful_shutdown)
    
    logger.info("=" * 80)
    logger.info("CDP BATCH JOB SCHEDULER")
    logger.info("=" * 80)
    logger.info(f"Schedule: Every {settings.BATCH_INTERVAL_MINUTES} minutes")
    logger.info(f"First run: Immediate")
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 80)
    
    # Create scheduler
    scheduler = BlockingScheduler()
    
    # Add job with interval trigger
    scheduler.add_job(
        scheduled_batch_job,
        trigger=IntervalTrigger(minutes=settings.BATCH_INTERVAL_MINUTES),
        id='batch_job',
        name='CDP ELT Pipeline',
        max_instances=1,  # Prevent overlapping runs
        coalesce=True,    # If a run is missed, only run once when it catches up
        next_run_time=datetime.now()  # Run immediately on startup
    )
    
    try:
        # Start the scheduler (blocking)
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("\n🛑 Scheduler stopped by user")
        scheduler.shutdown(wait=True)

if __name__ == "__main__":
    main()
