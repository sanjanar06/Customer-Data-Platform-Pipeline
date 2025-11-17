from typing import Optional
from pymongo import MongoClient
from neo4j import GraphDatabase, Driver
from config import settings
from config.logging_config import get_logger

logger = get_logger(__name__)

def get_mongodb_client(timeout_ms: int = 5000) -> MongoClient:
    try:
        client = MongoClient(
            settings.MONGO_URI,
            serverSelectionTimeoutMS=timeout_ms
        )
        # Validate connection
        client.admin.command('ping')
        logger.info(f"Connected to MongoDB at {settings.MONGO_HOST}:{settings.MONGO_PORT}")
        return client
    except Exception as e:
        logger.error(f"MongoDB connection failed: {e}")
        raise ConnectionError(f"Failed to connect to MongoDB: {e}")


def get_neo4j_driver() -> Driver:
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        # Validate connection
        driver.verify_connectivity()
        logger.info(f"Connected to Neo4j at {settings.NEO4J_URI}")
        return driver
    except Exception as e:
        logger.error(f"Neo4j connection failed: {e}")
        raise ConnectionError(f"Failed to connect to Neo4j: {e}")


class MongoDBContext:
    def __init__(self, timeout_ms: int = 5000):
        self.timeout_ms = timeout_ms
        self.client: Optional[MongoClient] = None
    
    def __enter__(self) -> MongoClient:
        self.client = get_mongodb_client(self.timeout_ms)
        return self.client
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()
            logger.debug("MongoDB connection closed")


class Neo4jContext:
    def __init__(self):
        self.driver: Optional[Driver] = None
    
    def __enter__(self) -> Driver:
        self.driver = get_neo4j_driver()
        return self.driver
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.driver:
            self.driver.close()
            logger.debug("Neo4j connection closed")
