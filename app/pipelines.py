"""Scrapy pipelines for processing crawled items."""

import hashlib
import requests
from typing import Dict, Any
from app.extractors.html_extractor import HTMLExtractor
from app.extractors.pdf_extractor import PDFExtractor
from app.extractors.docx_extractor import DOCXExtractor
from app.document_collection import DocumentCollection, create_opensearch_document
from app.opensearch_client import get_opensearch_client
from app.models import SessionLocal, IndexDocument
from urllib.parse import urlparse
from datetime import datetime
import io
import os


class DocumentExtractionPipeline:
    """Extract content from HTML, PDF, and DOCX documents."""
    
    def process_item(self, item: Dict[str, Any], spider):
        """Process item and extract content."""
        url = item.get('url', '')
        content_type = item.get('content_type', 'html')
        
        extracted = None
        
        if content_type == 'html' and 'html' in item:
            # Extract from HTML
            extracted = HTMLExtractor.extract(item['html'], url)
        
        elif content_type == 'pdf':
            # Extract from PDF bytes or file
            if 'pdf_bytes' in item:
                extracted = PDFExtractor.extract_from_bytes(item['pdf_bytes'], url, item.get('filename', 'document.pdf'))
            elif 'file_path' in item:
                extracted = PDFExtractor.extract_from_path(item['file_path'], url)
        
        elif content_type == 'docx':
            # Extract from DOCX bytes or file
            if 'docx_bytes' in item:
                extracted = DOCXExtractor.extract_from_bytes(item['docx_bytes'], url, item.get('filename', 'document.docx'))
            elif 'file_path' in item:
                extracted = DOCXExtractor.extract_from_path(item['file_path'], url)
        
        if extracted:
            item['title'] = extracted.get('title')
            item['content'] = extracted.get('content')
            item['metadata'] = extracted.get('metadata', {})
            item['content_type'] = extracted.get('content_type', content_type)
        
        return item


class DeduplicationPipeline:
    """Remove duplicate documents based on content hash."""
    
    def __init__(self):
        """Initialize deduplication tracking."""
        self.seen_hashes = set()
        self.db = SessionLocal()
    
    def process_item(self, item: Dict[str, Any], spider):
        """Check and track content hash for deduplication."""
        url = item.get('url', '')
        content = item.get('content', '')
        
        # Calculate checksum
        checksum = hashlib.sha256((url + content).encode()).hexdigest()
        item['checksum'] = checksum
        
        # Check if already indexed
        existing = self.db.query(IndexDocument).filter(
            IndexDocument.content_hash == checksum
        ).first()
        
        if existing:
            raise scrapy.exceptions.DropItem(f"Duplicate content found: {url}")
        
        self.seen_hashes.add(checksum)
        return item
    
    def close_spider(self, spider):
        """Close database connection."""
        self.db.close()


class IndexingPipeline:
    """Index documents to OpenSearch."""
    
    def __init__(self):
        """Initialize indexing pipeline."""
        self.opensearch = get_opensearch_client()
        self.db = SessionLocal()
        self.batch = []
        self.batch_size = 50
        self.index_name = None
    
    def open_spider(self, spider):
        """Open spider and prepare for indexing."""
        # Get index name from spider config
        if hasattr(spider, 'config'):
            self.index_name = spider.config.get('opensearch_index_name', 'crawler_documents')
        
        if self.opensearch.check_connection():
            # Create index if it doesn't exist
            self.opensearch.create_index(self.index_name)
    
    def process_item(self, item: Dict[str, Any], spider):
        """Process and add item to indexing batch."""
        if not item.get('content') or not item.get('title'):
            raise scrapy.exceptions.DropItem(f"Missing required fields: {item.get('url')}")
        
        # Parse domain from URL
        parsed_url = urlparse(item['url'])
        domain = parsed_url.netloc
        
        # Create OpenSearch document
        doc = create_opensearch_document(
            url=item['url'],
            title=item['title'],
            content=item['content'],
            content_type=item['content_type'],
            domain=domain,
            source_filename=item.get('filename'),
            metadata=item.get('metadata', {})
        )
        
        self.batch.append(doc)
        
        # Flush batch if size exceeded
        if len(self.batch) >= self.batch_size:
            self.flush_batch(spider)
        
        # Store in database
        try:
            doc_id = hashlib.sha256(item['url'].encode()).hexdigest()
            index_doc = IndexDocument(
                config_id=item.get('config_id'),
                document_id=doc_id,
                url=item['url'],
                title=item['title'],
                content_type=item['content_type'],
                content_hash=item['checksum'],
                metadata=item.get('metadata', {}),
                opensearch_indexed=False
            )
            self.db.add(index_doc)
            self.db.commit()
        except Exception as e:
            self.db.rollback()
            spider.logger.error(f"Error storing document in DB: {e}")
        
        return item
    
    def flush_batch(self, spider):
        """Flush accumulated documents to OpenSearch."""
        if not self.batch:
            return
        
        try:
            result = self.opensearch.bulk_index(self.index_name, self.batch)
            spider.logger.info(
                f"Indexed {result['success']} documents, {result['errors']} errors"
            )
            
            # Mark as indexed in database
            try:
                urls = [doc['url'] for doc in self.batch]
                self.db.query(IndexDocument).filter(
                    IndexDocument.url.in_(urls)
                ).update({'opensearch_indexed': True, 'indexed_at': datetime.utcnow()})
                self.db.commit()
            except Exception as e:
                self.db.rollback()
                spider.logger.error(f"Error updating database: {e}")
            
            self.batch = []
        except Exception as e:
            spider.logger.error(f"Error flushing batch to OpenSearch: {e}")
    
    def close_spider(self, spider):
        """Flush remaining batch and close connections."""
        self.flush_batch(spider)
        self.db.close()


class CollectionPipeline:
    """Save documents to local JSON Lines collection."""
    
    def __init__(self):
        """Initialize collection pipeline."""
        self.collection = None
    
    def open_spider(self, spider):
        """Initialize collection for this crawl."""
        collection_name = 'crawl_' + datetime.utcnow().isoformat().replace(':', '-').split('.')[0]
        self.collection = DocumentCollection(collection_name)
        spider.logger.info(f"Saving collection to: {self.collection.file_path}")
    
    def process_item(self, item: Dict[str, Any], spider):
        """Add document to collection."""
        # Parse domain from URL
        parsed_url = urlparse(item['url'])
        domain = parsed_url.netloc
        
        # Create document in OpenSearch format
        doc = create_opensearch_document(
            url=item['url'],
            title=item['title'],
            content=item['content'],
            content_type=item['content_type'],
            domain=domain,
            source_filename=item.get('filename'),
            metadata=item.get('metadata', {})
        )
        
        self.collection.add_document(doc)
        return item
    
    def close_spider(self, spider):
        """Close collection and log statistics."""
        stats = self.collection.get_metadata()
        spider.logger.info(f"Collection complete: {stats['document_count']} documents")
