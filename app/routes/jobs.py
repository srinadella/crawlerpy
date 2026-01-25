"""Crawl job execution and monitoring routes."""

from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app.models import CrawlJob, CrawlerConfig, get_db, SessionLocal
from app.schemas import CrawlJobResponse, CrawlJobDetailResponse
from app.auth import require_editor, get_current_user
from app.models import User
from app.audit import log_action
import asyncio
import threading

router = APIRouter()

# In-memory job tracking (in production, use database)
active_jobs = {}


@router.get("", response_model=List[CrawlJobResponse])
async def list_all_jobs(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all crawl jobs.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        List of all crawl jobs
    """
    jobs = db.query(CrawlJob).order_by(CrawlJob.created_at.desc()).all()
    return [CrawlJobResponse.from_orm(j) for j in jobs]


@router.get("/{config_id}", response_model=List[CrawlJobResponse])
async def list_jobs(
    config_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List crawl jobs for a specific crawler.
    
    Args:
        config_id: Crawler config ID
        db: Database session
        current_user: Current user
        
    Returns:
        List of crawl jobs
    """
    jobs = db.query(CrawlJob).filter(CrawlJob.config_id == config_id).all()
    return [CrawlJobResponse.from_orm(j) for j in jobs]


@router.get("/detail/{job_id}", response_model=CrawlJobDetailResponse)
async def get_job_detail(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed job information.
    
    Args:
        job_id: Job ID
        db: Database session
        current_user: Current user
        
    Returns:
        Detailed job information
    """
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    return CrawlJobDetailResponse.from_orm(job)


@router.post("/{config_id}/start", response_model=CrawlJobResponse, status_code=status.HTTP_201_CREATED)
async def start_crawl_job(
    config_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Start a new crawl job (editor+ only).
    
    Args:
        config_id: Crawler config ID
        background_tasks: FastAPI background tasks
        db: Database session
        current_user: Current user
        
    Returns:
        Created crawl job
    """
    # Get crawler config
    config = db.query(CrawlerConfig).filter(CrawlerConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if not config.enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Crawler is disabled")
    
    # Create job record
    job = CrawlJob(
        config_id=config_id,
        created_by_id=current_user.id,
        status="running",
        started_at=datetime.utcnow()
    )
    
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Log the action
    try:
        log_action(
            user_id=current_user.id,
            username=current_user.username,
            action="crawl_job_started",
            resource_type="crawl_job",
            resource_id=str(job.id),
            resource_name=f"Job for {config.name}",
            details={
                "config_id": config_id,
                "crawler_name": config.name
            },
            status="success"
        )
    except Exception as e:
        # Don't fail the request if audit logging fails
        print(f"Audit log error: {e}")
    
    # Schedule background task
    background_tasks.add_task(execute_crawl_job, job.id, config_id)
    
    return CrawlJobResponse.from_orm(job)


@router.post("/{job_id}/stop", response_model=CrawlJobResponse)
async def stop_crawl_job(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_editor)
):
    """
    Stop a running crawl job (editor+ only).
    
    Args:
        job_id: Job ID
        db: Database session
        current_user: Current user
        
    Returns:
        Updated job
    """
    job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    
    if job.status not in ["running", "pending"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Job is not running")
    
    job.status = "stopped"
    job.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(job)
    
    return CrawlJobResponse.from_orm(job)


async def execute_crawl_job(job_id: int, config_id: int):
    """
    Execute crawl job in background.
    
    Args:
        job_id: Job ID
        config_id: Crawler config ID
    """
    db = SessionLocal()
    job = None
    
    try:
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if not job:
            return
        
        config = db.query(CrawlerConfig).filter(CrawlerConfig.id == config_id).first()
        if not config:
            if job:
                job.status = "failed"
                job.error_details = {"error": "Config not found"}
                db.commit()
            return
        
        # Mock crawl execution
        # In production, this would execute the Scrapy crawler
        job.progress = 50
        job.urls_crawled = 100
        job.status = "running"
        db.commit()
        
        # Simulate crawling with sleep
        import time
        time.sleep(2)
        
        # Refresh job from database
        job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
        if job:
            job.progress = 100
            job.documents_indexed = 100
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            job.logs = "Crawl completed successfully"
            db.commit()
        
    except Exception as e:
        try:
            job = db.query(CrawlJob).filter(CrawlJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_details = {"error": str(e)}
                job.completed_at = datetime.utcnow()
                db.commit()
        except:
            pass
    
    finally:
        try:
            db.close()
        except:
            pass
