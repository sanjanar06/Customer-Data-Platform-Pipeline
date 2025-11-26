#!/usr/bin/env python3
import sys
import os
import time

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from config import settings
from src.python.common.database import get_neo4j_driver
from config.logging_config import setup_logging, get_logger

setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

def init_neo4j():
    logger.info("🚀 Starting Neo4j Initialization & Constraints...")
    
    driver = None
    try:
        driver = get_neo4j_driver()
        
        # Retry logic for startup (in case Neo4j is still waking up)
        for i in range(30):
            try:
                driver.verify_connectivity()
                break
            except Exception:
                logger.info("Waiting for Neo4j to be ready...")
                time.sleep(2)
        
        with driver.session() as session:
            # 1. CLEANUP: Merge existing duplicates (The "Deduping" Logic)
            logger.info("🧹 Step 1: Cleaning up existing duplicates...")
            dedup_query = """
            MATCH (i:Identity)
            WITH i.type AS type, i.value AS value, collect(i) AS nodes
            WHERE size(nodes) > 1
            WITH head(nodes) AS keeper, tail(nodes) AS duplicates
            UNWIND duplicates AS dupe
            MATCH (dupe)<-[r:HAS_IDENTITY]-(p:Profile)
            MERGE (p)-[:HAS_IDENTITY]->(keeper)
            DELETE r
            DELETE dupe
            """
            session.run(dedup_query)
            logger.info("✅ Cleanup complete.")

            # 2. CONSTRAINT: Create Unique Constraint
            logger.info("🛡️ Step 2: Enforcing Uniqueness Constraint...")
            constraint_query = """
            CREATE CONSTRAINT unique_identity IF NOT EXISTS
            FOR (i:Identity) REQUIRE (i.type, i.value) IS UNIQUE
            """
            session.run(constraint_query)
            logger.info("✅ Constraint 'unique_identity' enforced.")
            
            # 3. INDEX: Ensure Fulltext Index exists (for Fuzzy Matching)
            logger.info("🔍 Step 3: Verifying Fuzzy Match Index...")
            index_query = """
            CREATE FULLTEXT INDEX identity_fuzzy_index IF NOT EXISTS
            FOR (n:Identity) ON EACH [n.value]
            """
            session.run(index_query)
            logger.info("✅ Fulltext index 'identity_fuzzy_index' verified.")

    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        sys.exit(1)
    finally:
        if driver:
            driver.close()
        logger.info("✨ Neo4j Initialization Complete!")

if __name__ == "__main__":
    init_neo4j()