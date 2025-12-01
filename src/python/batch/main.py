#!/usr/bin/env python3

import subprocess
import os
from src.python.batch.syncer import MetricSyncer
from src.python.common.database import get_mongodb_client
from src.python.batch.ingestor import DataIngestor
from config import settings
from config.logging_config import setup_logging, get_logger


# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)


def run_dbt():
    """Execute dbt transformations using subprocess."""
    logger.info("Starting dbt transformations...")

    dbt_dir = os.path.abspath("analytics/cdp_dbt_project")
    try:
        result = subprocess.run(
            ["dbt", "run"],
            cwd=dbt_dir,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(result.stdout)
        logger.info(f"dbt run complete!")
    except subprocess.CalledProcessError as e:
        # Check if dbt actually succeeded despite protobuf error
        if "Done. PASS=" in e.stdout and "ERROR=0" in e.stdout:
            logger.warning("dbt completed successfully but exited with error code due to protobuf logging issue (Python 3.13 compatibility)")
            logger.info(e.stdout)
            return
        logger.error(f"dbt transformations failed: {e.stderr}")
        logger.error(e.stdout)
        raise

def main() -> None:
    logger.info("=" * 60)
    logger.info("CDP BATCH JOB - ELT Pipeline")
    logger.info("=" * 60)
    
    try:
        # 1. Connect to Mongo
        mongo_client = get_mongodb_client()
        
        # 2. Run Ingestion (MongoDB -> Postgres)
        logger.info("\n--- STEP 1: INGESTION ---")
        ingestor = DataIngestor(mongo_client)
        ingestor.ingest_profiles()
        ingestor.close()
        
        # 3. Run dbt (Postgres Raw -> Postgres Marts)
        logger.info("\n--- STEP 2: TRANSFORMATION ---")
        run_dbt()
        
        # 4. Sync metrics back to MongoDB (Postgres Marts -> MongoDB)
        logger.info("\n--- STEP 4: REVERSE ETL (SYNC) ---")
        syncer = MetricSyncer(mongo_client)
        syncer.sync_computed_attributes()
        syncer.close() 
        
        
    except Exception as e:
        logger.error(f"Batch job failed: {e}", exc_info=True)
        raise
    finally:
        if mongo_client:
            mongo_client.close()
        logger.info("\nBatch job finished.\n")


if __name__ == "__main__":
    main()
