"""Pydantic schemas for API request/response validation."""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# User schemas
class UserBase(BaseModel):
    username: str
    email: Optional[EmailStr] = None
    roles: List[str] = ["viewer"]


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    roles: Optional[List[str]] = None


class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


# Crawler config schemas
class CrawlerConfigBase(BaseModel):
    name: str
    description: Optional[str] = None
    enabled: bool = True
    
    seed_urls: List[str] = []
    allow_domains: List[str] = []
    url_patterns_include: List[str] = []
    url_patterns_exclude: List[str] = []
    
    follow_sitemap: bool = True
    respect_robots_txt: bool = True
    
    max_depth: int = 2
    download_timeout: int = 30
    concurrent_requests: int = 16
    concurrent_requests_per_domain: int = 8
    download_delay: int = 1
    
    extract_pdfs: bool = True
    extract_docx: bool = True
    
    opensearch_index_name: Optional[str] = None
    enable_indexing: bool = True
    create_json_collection: bool = True


class CrawlerConfigCreate(CrawlerConfigBase):
    pass


class CrawlerConfigUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None
    seed_urls: Optional[List[str]] = None
    allow_domains: Optional[List[str]] = None
    url_patterns_include: Optional[List[str]] = None
    url_patterns_exclude: Optional[List[str]] = None
    follow_sitemap: Optional[bool] = None
    respect_robots_txt: Optional[bool] = None
    max_depth: Optional[int] = None
    download_timeout: Optional[int] = None
    concurrent_requests: Optional[int] = None
    concurrent_requests_per_domain: Optional[int] = None
    download_delay: Optional[int] = None
    extract_pdfs: Optional[bool] = None
    extract_docx: Optional[bool] = None
    opensearch_index_name: Optional[str] = None
    enable_indexing: Optional[bool] = None
    create_json_collection: Optional[bool] = None


class CrawlerConfigResponse(CrawlerConfigBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Crawl job schemas
class CrawlJobBase(BaseModel):
    status: str = "pending"
    progress: int = 0


class CrawlJobResponse(CrawlJobBase):
    id: int
    config_id: int
    urls_crawled: int
    documents_indexed: int
    errors_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class CrawlJobDetailResponse(CrawlJobResponse):
    logs: str
    error_details: Dict[str, Any]
    config: CrawlerConfigResponse


# Index document schemas
class IndexDocumentResponse(BaseModel):
    id: int
    document_id: str
    url: str
    title: Optional[str] = None
    content_type: str
    opensearch_indexed: bool
    indexed_at: Optional[datetime] = None
    metadata: Dict[str, Any]
    
    class Config:
        from_attributes = True


# OpenSearch document schema
class OpenSearchDocument(BaseModel):
    url: str
    title: Optional[str] = None
    content: str
    content_type: str  # html, pdf, docx
    domain: str
    crawled_at: datetime = Field(default_factory=datetime.utcnow)
    source_filename: Optional[str] = None
    checksum: str
    metadata: Dict[str, Any] = {}


# Search schemas
class SearchQuery(BaseModel):
    q: str
    content_type: Optional[str] = None
    domain: Optional[str] = None
    limit: int = 10
    offset: int = 0


class SearchResult(BaseModel):
    id: str
    url: str
    title: Optional[str] = None
    content_snippet: str
    content_type: str
    score: float
    
    class Config:
        from_attributes = True
