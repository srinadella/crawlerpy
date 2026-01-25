"""Database models for crawler configuration, jobs, and users."""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from app.config import settings

Base = declarative_base()
engine = create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """User account with RBAC roles."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True)
    hashed_password = Column(String(255), nullable=False)
    roles = Column(JSON, default=["viewer"])  # List of role names
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    crawl_jobs = relationship("CrawlJob", back_populates="created_by_user")


class CrawlerConfig(Base):
    """Crawler configuration and settings."""
    __tablename__ = "crawler_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, index=True, nullable=False)
    description = Column(Text)
    enabled = Column(Boolean, default=True)
    
    # Crawler settings
    seed_urls = Column(JSON, default=[])  # List of starting URLs
    allow_domains = Column(JSON, default=[])  # List of allowed domains
    url_patterns_include = Column(JSON, default=[])  # Regex patterns to include
    url_patterns_exclude = Column(JSON, default=[])  # Regex patterns to exclude
    follow_sitemap = Column(Boolean, default=True)
    respect_robots_txt = Column(Boolean, default=True)
    
    # Download settings
    max_depth = Column(Integer, default=2)
    download_timeout = Column(Integer, default=30)
    concurrent_requests = Column(Integer, default=16)
    concurrent_requests_per_domain = Column(Integer, default=8)
    download_delay = Column(Integer, default=1)
    
    # Content extraction
    extract_pdfs = Column(Boolean, default=True)
    extract_docx = Column(Boolean, default=True)
    
    # Index settings
    opensearch_index_name = Column(String(255))
    enable_indexing = Column(Boolean, default=True)
    
    # Storage
    create_json_collection = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    crawl_jobs = relationship("CrawlJob", back_populates="config", cascade="all, delete-orphan")


class CrawlJob(Base):
    """Individual crawl job execution record."""
    __tablename__ = "crawl_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("crawler_configs.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    
    status = Column(String(50), default="pending")  # pending, running, completed, failed, stopped
    progress = Column(Integer, default=0)  # 0-100
    
    urls_crawled = Column(Integer, default=0)
    documents_indexed = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)
    
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    logs = Column(Text, default="")  # Job logs
    error_details = Column(JSON, default={})  # Detailed error information
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    config = relationship("CrawlerConfig", back_populates="crawl_jobs")
    created_by_user = relationship("User", back_populates="crawl_jobs")


class IndexDocument(Base):
    """Indexed document metadata."""
    __tablename__ = "index_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("crawler_configs.id"))
    
    document_id = Column(String(255), unique=True, index=True)  # OpenSearch doc ID
    url = Column(String(2048), index=True)
    title = Column(String(255))
    content_type = Column(String(50))  # html, pdf, docx
    content_hash = Column(String(64))  # SHA256 hash for deduplication
    
    opensearch_indexed = Column(Boolean, default=False)
    indexed_at = Column(DateTime)
    
    doc_metadata = Column(JSON, default={})  # Author, page count, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    """Database session dependency for FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
