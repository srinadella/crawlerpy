"""Crawler execution module using Scrapy."""

import logging
import subprocess
import json
import os
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime
from urllib.parse import urlparse

from app.models import SessionLocal, CrawlJob, CrawlerConfig, IndexDocument
from app.config import settings


logger = logging.getLogger(__name__)


class CrawlerExecutor:
    """Execute Scrapy crawlers for web crawling jobs."""
    
    def __init__(self, config: Dict[str, Any], job_id: int):
        """
        Initialize crawler executor.
        
        Args:
            config: Crawler configuration from database
            job_id: Job ID for tracking
        """
        self.config = config
        self.job_id = job_id
        self.logger = logger
        
    def execute(self) -> Dict[str, Any]:
        """
        Execute the crawler job using Scrapy.
        
        Returns:
            Dictionary with execution results
        """
        db = SessionLocal()
        
        try:
            # Prepare spider arguments
            spider_name = 'sitemap' if self.config.get('use_sitemap', True) else 'generic'
            
            # Create config JSON for spider
            config_data = {
                'seed_urls': self.config.get('seed_urls', []),
                'allow_domains': self.config.get('allowed_domains', []),
                'url_patterns_include': self.config.get('url_patterns_include', []),
                'url_patterns_exclude': self.config.get('url_patterns_exclude', []),
                'max_depth': self.config.get('max_depth', 2),
                'extract_pdfs': self.config.get('extract_pdfs', True),
                'extract_docx': self.config.get('extract_docx', True),
                'opensearch_index': self.config.get('opensearch_index_name', 'documents'),
                'job_id': self.job_id,
                'concurrent_requests': self.config.get('concurrent_requests', 16),
                'download_delay': self.config.get('download_delay', 1),
            }
            
            # Collection filename for this crawl
            timestamp = datetime.utcnow().isoformat().replace(':', '-')
            collection_filename = f"crawl_{timestamp}.jsonl"
            
            # Build scrapy command using the runner script
            cmd = [
                sys.executable,
                'app/scrapy_runner.py',
                spider_name,
                json.dumps(config_data),
                str(self.job_id),
                f'{settings.COLLECTIONS_PATH}/{collection_filename}'
            ]
            
            # Set environment for Scrapy
            env = os.environ.copy()
            env['PYTHONPATH'] = '/Users/sri/data/crawler:' + env.get('PYTHONPATH', '')
            
            # Update job status to running
            job = db.query(CrawlJob).filter(CrawlJob.id == self.job_id).first()
            if job:
                job.status = "running"
                job.progress = 10
                db.commit()
            
            # Execute crawler
            self.logger.info(f"Starting crawl job {self.job_id} with spider: {spider_name}")
            result = subprocess.run(
                cmd,
                cwd='/Users/sri/data/crawler',
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                error_msg = result.stderr or result.stdout or "Unknown error"
                self.logger.error(f"Scrapy crawl failed: {error_msg}")
                
                job = db.query(CrawlJob).filter(CrawlJob.id == self.job_id).first()
                if job:
                    job.status = "failed"
                    job.completed_at = datetime.utcnow()
                    job.error_details = {"error": error_msg}
                    db.commit()
                
                return {
                    "status": "failed",
                    "error": error_msg
                }
            
            # Parse logs to get statistics
            lines = result.stderr.split('\n') if result.stderr else []
            urls_crawled = 0
            documents_indexed = 0
            
            for line in lines:
                if 'Scraped' in line or 'items' in line.lower():
                    # Try to extract counts from Scrapy logs
                    try:
                        if 'Scraped' in line:
                            # Extract number: "Scraped 123 items"
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'Scraped' and i + 1 < len(parts):
                                    urls_crawled = int(parts[i + 1])
                    except (ValueError, IndexError):
                        pass
            
            # Count documents in collection file
            collection_path = f'{settings.COLLECTIONS_PATH}/{collection_filename}'
            if os.path.exists(collection_path):
                with open(collection_path, 'r') as f:
                    documents_indexed = sum(1 for _ in f)
            
            # Update job with results
            job = db.query(CrawlJob).filter(CrawlJob.id == self.job_id).first()
            if job:
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                job.urls_crawled = urls_crawled if urls_crawled > 0 else documents_indexed
                job.documents_indexed = documents_indexed
                job.progress = 100
                job.logs = f"Successfully crawled {urls_crawled or documents_indexed} URLs, indexed {documents_indexed} documents"
                db.commit()
            
            self.logger.info(f"Crawl job {self.job_id} completed: {documents_indexed} documents indexed")
            
            return {
                "status": "completed",
                "urls_crawled": urls_crawled or documents_indexed,
                "documents_indexed": documents_indexed,
                "collection": collection_filename
            }
            
        except subprocess.TimeoutExpired:
            self.logger.error(f"Crawler execution timeout for job {self.job_id}")
            job = db.query(CrawlJob).filter(CrawlJob.id == self.job_id).first()
            if job:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                job.error_details = {"error": "Crawl timeout (>1 hour)"}
                db.commit()
            return {"status": "failed", "error": "Timeout"}
            
        except Exception as e:
            self.logger.error(f"Crawler execution error for job {self.job_id}: {e}")
            job = db.query(CrawlJob).filter(CrawlJob.id == self.job_id).first()
            if job:
                job.status = "failed"
                job.completed_at = datetime.utcnow()
                job.error_details = {"error": str(e)}
                db.commit()
            return {"status": "failed", "error": str(e)}
        
        finally:
            db.close()
