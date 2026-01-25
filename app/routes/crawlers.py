"""Crawler configuration routes."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List
from app.models import CrawlerConfig, get_db
from app.schemas import CrawlerConfigCreate, CrawlerConfigUpdate, CrawlerConfigResponse
from app.auth import require_editor, get_current_user
from app.models import User
from app.audit import log_action

router = APIRouter()


@router.get("/", response_model=List[CrawlerConfigResponse])
@router.get("", response_model=List[CrawlerConfigResponse])
async def list_crawlers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all crawler configurations.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        List of crawler configs
    """
    crawlers = db.query(CrawlerConfig).all()
    return [CrawlerConfigResponse.from_orm(c) for c in crawlers]


@router.get("/{crawler_id}", response_model=CrawlerConfigResponse)
async def get_crawler(
    crawler_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific crawler configuration.
    
    Args:
        crawler_id: Crawler ID
        db: Database session
        current_user: Current user
        
    Returns:
        Crawler configuration
    """
    crawler = db.query(CrawlerConfig).filter(CrawlerConfig.id == crawler_id).first()
    if not crawler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return CrawlerConfigResponse.from_orm(crawler)


@router.post("/", response_model=CrawlerConfigResponse, status_code=status.HTTP_201_CREATED)
@router.post("", response_model=CrawlerConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_crawler(
    config: CrawlerConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Create new crawler configuration (editor+ only).
    
    Args:
        config: Crawler configuration
        db: Database session
        current_user: Current user
        
    Returns:
        Created crawler
    """
    # Check for duplicate name
    existing = db.query(CrawlerConfig).filter(CrawlerConfig.name == config.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crawler name already exists"
        )
    
    # Create default index name if not provided
    index_name = config.opensearch_index_name or f"crawler_{config.name.lower().replace(' ', '_')}"
    
    crawler = CrawlerConfig(
        name=config.name,
        description=config.description,
        enabled=config.enabled,
        seed_urls=config.seed_urls,
        allow_domains=config.allow_domains,
        url_patterns_include=config.url_patterns_include,
        url_patterns_exclude=config.url_patterns_exclude,
        follow_sitemap=config.follow_sitemap,
        respect_robots_txt=config.respect_robots_txt,
        max_depth=config.max_depth,
        download_timeout=config.download_timeout,
        concurrent_requests=config.concurrent_requests,
        concurrent_requests_per_domain=config.concurrent_requests_per_domain,
        download_delay=config.download_delay,
        extract_pdfs=config.extract_pdfs,
        extract_docx=config.extract_docx,
        opensearch_index_name=index_name,
        enable_indexing=config.enable_indexing,
        create_json_collection=config.create_json_collection
    )
    
    db.add(crawler)
    db.commit()
    db.refresh(crawler)
    
    # Log the action
    try:
        log_action(
            user_id=current_user.id,
            username=current_user.username,
            action="crawler_created",
            resource_type="crawler",
            resource_id=str(crawler.id),
            resource_name=crawler.name,
            details={
                "seed_urls": crawler.seed_urls,
                "max_depth": crawler.max_depth,
                "enabled": crawler.enabled
            },
            status="success"
        )
    except Exception as e:
        # Don't fail the request if audit logging fails
        print(f"Audit log error: {e}")
    
    return CrawlerConfigResponse.from_orm(crawler)


@router.put("/{crawler_id}", response_model=CrawlerConfigResponse)
async def update_crawler(
    crawler_id: int,
    config_update: CrawlerConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Update crawler configuration (editor+ only).
    
    Args:
        crawler_id: Crawler ID
        config_update: Updated configuration
        db: Database session
        current_user: Current user
        
    Returns:
        Updated crawler
    """
    crawler = db.query(CrawlerConfig).filter(CrawlerConfig.id == crawler_id).first()
    if not crawler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    # Update fields if provided
    update_data = config_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(crawler, field, value)
    
    db.commit()
    db.refresh(crawler)
    
    return CrawlerConfigResponse.from_orm(crawler)


@router.delete("/{crawler_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_crawler(
    crawler_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Delete crawler configuration (editor+ only).
    
    Args:
        crawler_id: Crawler ID
        db: Database session
        current_user: Current user
    """
    crawler = db.query(CrawlerConfig).filter(CrawlerConfig.id == crawler_id).first()
    if not crawler:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    db.delete(crawler)
    db.commit()
    
    # Log the action
    try:
        log_action(
            user_id=current_user.id,
            username=current_user.username,
            action="crawler_deleted",
            resource_type="crawler",
            resource_id=str(crawler_id),
            resource_name=crawler.name,
            details={
                "seed_urls": crawler.seed_urls
            },
            status="success"
        )
    except Exception as e:
        # Don't fail the request if audit logging fails
        print(f"Audit log error: {e}")
