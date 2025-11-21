import json
import psycopg2
from psycopg2.extras import Json
from pymongo import MongoClient
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

class DataIngestor:
    def __init__(self, mongo_client: MongoClient):
        self.mongo_db = mongo_client[settings.MONGO_DB]
        self.pg_conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            dbname=settings.POSTGRES_DB
        )
        self.pg_conn.autocommit = True

    def ingest_profiles(self):
        """
        Extracts profiles from MongoDB and loads them into PostgreSQL 'profiles_raw' table.
        """
        logger.info("Starting data ingestion: MongoDB -> PostgreSQL")
        
        # 1. Fetch data from MongoDB
        profiles = list(self.mongo_db["profiles"].find({}))
        count = len(profiles)
        logger.info(f"Extracted {count} profiles from MongoDB")

        if count == 0:
            logger.warning("No data to ingest.")
            return

        # 2. Prepare PostgreSQL Table (profiles_raw)
        # We drop and recreate to simulate a full refresh "Raw" landing zone
        with self.pg_conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS profiles_raw CASCADE;")
            cur.execute("""
                CREATE TABLE profiles_raw (
                    master_profile_id TEXT PRIMARY KEY,
                    identities JSONB,
                    attributes JSONB,
                    event_history JSONB,
                    created_at TIMESTAMP,
                    updated_at TIMESTAMP
                );
            """)
            logger.info("Recreated table: profiles_raw")

            # 3. Insert Data
            insert_query = """
                INSERT INTO profiles_raw 
                (master_profile_id, identities, attributes, event_history, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            for p in profiles:
                cur.execute(insert_query, (
                    p.get("master_profile_id"),
                    Json(p.get("identities", {})),
                    Json(p.get("attributes", {})),
                    Json(p.get("event_history", [])),
                    p.get("created_at"),
                    p.get("updated_at")
                ))
            
            logger.info(f"Loaded {count} rows into PostgreSQL")

    def close(self):
        if self.pg_conn:
            self.pg_conn.close()