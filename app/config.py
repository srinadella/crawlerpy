"""Configuration management for the crawler application."""

from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./crawler.db"
    
    # OpenSearch
    OPENSEARCH_HOST: str = "search-srisearch-4cxrdo5pnm4kfyg7c2p3mr3boy.us-east-1.es.amazonaws.com"
    OPENSEARCH_PORT: int = 443
    OPENSEARCH_SCHEME: str = "https"
    OPENSEARCH_USER: Optional[str] = None
    OPENSEARCH_PASSWORD: Optional[str] = None
    OPENSEARCH_VERIFY_CERTS: bool = True
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30
    
    # Crawler
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_RETRY_TIMES: int = 3
    CRAWLER_CONCURRENT_REQUESTS: int = 16
    CRAWLER_CONCURRENT_REQUESTS_PER_DOMAIN: int = 8
    CRAWLER_DOWNLOAD_DELAY: float = 0.5
    
    # File storage
    STORAGE_PATH: str = "./storage"
    COLLECTIONS_PATH: str = "./storage/collections"
    LOGS_PATH: str = "./storage/logs"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
