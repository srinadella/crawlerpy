"""Admin routes for system management and index administration."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.models import get_db, User
from app.auth import require_admin
from app.opensearch_client import get_opensearch_client
from app.document_collection import DocumentCollection
import os
from app.config import settings

router = APIRouter()


@router.get("/stats")
async def get_system_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get system statistics (admin only).
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        System statistics
    """
    opensearch = get_opensearch_client()
    
    # Check OpenSearch connection (non-blocking)
    opensearch_connected = False
    try:
        opensearch_connected = opensearch.check_connection()
    except Exception as os_error:
        opensearch_connected = False
        # Continue with other stats even if OpenSearch fails
    
    # Always count from database regardless of OpenSearch status
    from app.models import CrawlerConfig, CrawlJob
    try:
        crawler_count = db.query(CrawlerConfig).count()
        job_count = db.query(CrawlJob).count()
        user_count = db.query(User).count()
    except Exception as db_error:
        crawler_count = 0
        job_count = 0
        user_count = 0
    
    # Get storage info
    storage_used = 0
    try:
        if os.path.exists(settings.COLLECTIONS_PATH):
            for root, dirs, files in os.walk(settings.COLLECTIONS_PATH):
                for file in files:
                    storage_used += os.path.getsize(os.path.join(root, file))
    except Exception as storage_error:
        storage_used = 0
    
    return {
        "opensearch_connected": opensearch_connected,
        "crawler_count": crawler_count,
        "job_count": job_count,
        "user_count": user_count,
        "storage_used_mb": round(storage_used / (1024 * 1024), 2)
    }


@router.get("/opensearch/health")
async def opensearch_health(
    current_user: User = Depends(require_admin)
):
    """
    Check OpenSearch health (admin only).
    
    Args:
        current_user: Current user
        
    Returns:
        OpenSearch health status
    """
    opensearch = get_opensearch_client()
    
    try:
        if opensearch.check_connection():
            info = opensearch.client.info()
            return {
                "status": "ok",
                "version": info.get('version', {}).get('number', 'unknown')
            }
        else:
            return {
                "status": "error",
                "message": "Cannot connect to OpenSearch"
            }
    
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


@router.post("/indices/{index_name}/reindex")
async def reindex_documents(
    index_name: str,
    current_user: User = Depends(require_admin)
):
    """
    Reindex documents from collection back to OpenSearch (admin only).
    
    Args:
        index_name: Index name
        current_user: Current user
        
    Returns:
        Reindex result
    """
    try:
        opensearch = get_opensearch_client()
        
        # Find collection file matching the index
        collection_files = []
        if os.path.exists(settings.COLLECTIONS_PATH):
            for file in os.listdir(settings.COLLECTIONS_PATH):
                if file.endswith('.jsonl'):
                    collection_files.append(file)
        
        if not collection_files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No collection files found"
            )
        
        # Use first collection (in production, match by crawler name)
        collection = DocumentCollection(collection_files[0].replace('.jsonl', ''))
        documents = collection.read_documents()
        
        if not documents:
            return {
                "status": "success",
                "message": "No documents to reindex",
                "count": 0
            }
        
        # Reindex to OpenSearch
        result = opensearch.bulk_index(index_name, documents)
        
        return {
            "status": "success",
            "indexed": result['success'],
            "errors": result['errors']
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindex error: {str(e)}"
        )


@router.delete("/indices/{index_name}")
async def delete_index(
    index_name: str,
    current_user: User = Depends(require_admin)
):
    """
    Delete an OpenSearch index (admin only).
    
    Args:
        index_name: Index name
        current_user: Current user
        
    Returns:
        Delete result
    """
    try:
        opensearch = get_opensearch_client()
        
        if opensearch.delete_index(index_name):
            return {
                "status": "success",
                "message": f"Index {index_name} deleted"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Index not found"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/collections")
async def list_collections(
    current_user: User = Depends(require_admin)
):
    """
    List all document collections (admin only).
    
    Args:
        current_user: Current user
        
    Returns:
        List of collections with metadata
    """
    collections = []
    
    if os.path.exists(settings.COLLECTIONS_PATH):
        for file in os.listdir(settings.COLLECTIONS_PATH):
            if file.endswith('.jsonl'):
                collection_name = file.replace('.jsonl', '')
                collection = DocumentCollection(collection_name)
                metadata = collection.get_metadata()
                collections.append(metadata)
    
    return {
        "total": len(collections),
        "collections": collections
    }


@router.delete("/collections/{collection_name}")
async def delete_collection(
    collection_name: str,
    current_user: User = Depends(require_admin)
):
    """
    Delete a document collection (admin only).
    
    Args:
        collection_name: Collection name
        current_user: Current user
        
    Returns:
        Delete result
    """
    try:
        collection = DocumentCollection(collection_name)
        
        if collection.clear():
            return {
                "status": "success",
                "message": f"Collection {collection_name} deleted"
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Collection not found"
            )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
