from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application Settings
    APP_NAME: str = "CDP Prototype"
    ENVIRONMENT: str = "development"  # development, staging, production
    LOG_LEVEL: str = "INFO"
    DEBUG: bool = False
    
    # MongoDB Settings
    MONGO_HOST: str = "localhost"
    MONGO_PORT: int = 27017
    MONGO_USER: str = "admin"
    MONGO_PASSWORD: str = "password123"
    MONGO_DB: str = "cdp"

    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "cdp_user"
    POSTGRES_PASSWORD: str = "cdp_password"
    POSTGRES_DB: str = "cdp_analytics"
    
    @property
    def MONGO_URI(self) -> str:
        """Build MongoDB connection URI."""
        return f"mongodb://{self.MONGO_USER}:{self.MONGO_PASSWORD}@{self.MONGO_HOST}:{self.MONGO_PORT}/"
    
    @property
    def POSTGRES_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Neo4j Settings
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "password123"
    
    # Event Producer Settings
    PRODUCER_HOST: str = "0.0.0.0" # listen on all interfaces
    PRODUCER_PORT: int = 9001
    PRODUCER_INTERVAL: float = 2.0  # Seconds between events
    
    # Flink Settings
    FLINK_JOBMANAGER_HOST: str = "localhost"
    FLINK_JOBMANAGER_PORT: int = 8081
    FLINK_PARALLELISM: int = 2
    
    # AI/Gemini Settings
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    GEMINI_TEMPERATURE: float = 0.7
    GEMINI_MAX_TOKENS: int = 1024
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 1
    API_RELOAD: bool = True  # Hot reload for development
    
    # Batch Job Settings
    BATCH_PROFILE_LIMIT: Optional[int] = None  # None = process all
    BATCH_CHUNK_SIZE: int = 100
    BATCH_INTERVAL_MINUTES: int = 5  # Run batch job every N minutes
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # Ignore extra fields in .env


# Singleton instance
settings = Settings()

# Environment-specific overrides
if settings.ENVIRONMENT == "production":
    settings.DEBUG = False
    settings.LOG_LEVEL = "WARNING"
    settings.API_RELOAD = False
elif settings.ENVIRONMENT == "development":
    settings.DEBUG = True
    settings.LOG_LEVEL = "DEBUG"
    settings.API_RELOAD = True
