import psycopg2
from psycopg2.extras import RealDictCursor
from pymongo import MongoClient, UpdateOne
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

class MetricSyncer:
    def __init__(self, mongo_client: MongoClient):
        self.mongo_coll = mongo_client[settings.MONGO_DB]["profiles"]
        self.pg_conn = psycopg2.connect(
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            dbname=settings.POSTGRES_DB
        )

    def sync_computed_attributes(self):
        """
        Reads ALL computed metrics from dbt marts and updates MongoDB.
        """
        logger.info("Starting Full Reverse ETL: PostgreSQL -> MongoDB")
        
        try:
            # Use RealDictCursor to get column names automatically
            with self.pg_conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM public_marts.mart_computed_attributes")
                rows = cur.fetchall()
                
                if not rows:
                    logger.warning("No computed attributes found in PostgreSQL.")
                    return

                operations = []
                for row in rows:
                    # Build the nested object for MongoDB
                    computed_attributes = {
                        "lifetime_value": float(row['lifetime_value']),
                        "engagement_score": int(row['engagement_score']),
                        "event_metrics": {
                            "total_events": int(row['total_events']),
                            "unique_event_types": int(row['unique_event_types'])
                        },
                        "time_metrics": {
                            "days_since_last_event": float(row['days_since_last_event']),
                            "customer_lifetime_days": float(row['customer_lifetime_days'])
                        },
                        "product_metrics": {
                            "products_purchased_count": int(row['products_purchased_count'] or 0)
                        }
                    }
                    
                    # Create Upsert Operation
                    op = UpdateOne(
                        {"master_profile_id": row['master_profile_id']},
                        {"$set": {"computed_attributes": computed_attributes}}
                    )
                    operations.append(op)

                if operations:
                    result = self.mongo_coll.bulk_write(operations)
                    logger.info(f"✅ Synced full attributes for {result.modified_count} profiles.")
                    
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            raise

    def close(self):
        if self.pg_conn:
            self.pg_conn.close()