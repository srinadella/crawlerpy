"""Search routes for querying indexed documents."""

from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from app.models import get_db
from app.schemas import SearchQuery, SearchResult
from app.auth import get_current_user
from app.models import User
from app.opensearch_client import get_opensearch_client
from app.audit import log_action

router = APIRouter()


@router.post("", response_model=Dict[str, Any])
@router.post("/", response_model=Dict[str, Any])
async def search_documents(
    search_query: SearchQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Search indexed documents across all indices.
    
    Args:
        search_query: Search parameters
        db: Database session
        current_user: Current user
        
    Returns:
        Search results
    """
    if not search_query.q:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Query cannot be empty")
    
    opensearch = get_opensearch_client()
    
    # Search across all crawler indices
    try:
        results = opensearch.search(
            index_name="crawler_*",
            query=search_query.q,
            content_type=search_query.content_type,
            domain=search_query.domain,
            limit=search_query.limit,
            offset=search_query.offset
        )
        
        # Convert to search result format
        search_results = []
        for doc in results:
            # Truncate content for snippet
            content = doc.get('content', '')
            snippet = content[:200] + "..." if len(content) > 200 else content
            
            search_results.append({
                "id": doc.get('_id', ''),
                "url": doc.get('url', ''),
                "title": doc.get('title', ''),
                "content_snippet": snippet,
                "content_type": doc.get('content_type', ''),
                "score": doc.get('_score', 0)
            })
        
        return {
            "query": search_query.q,
            "total": len(search_results),
            "results": search_results,
            "limit": search_query.limit,
            "offset": search_query.offset
        }
    
    except Exception as e:
        # Log failed search
        try:
            log_action(
                user_id=current_user.id,
                username=current_user.username,
                action="search_executed",
                resource_type="search",
                resource_id="",
                details={
                    "query": search_query.q,
                    "content_type": search_query.content_type
                },
                status="error",
                error_message=str(e)
            )
        except:
            pass
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search error: {str(e)}"
        )


@router.get("/document/{doc_id}")
async def get_document(
    doc_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get full document content by ID.
    
    Args:
        doc_id: Document ID
        db: Database session
        current_user: Current user
        
    Returns:
        Full document
    """
    opensearch = get_opensearch_client()
    
    try:
        # Try to fetch from any crawler index
        response = opensearch.client.get(index="crawler_*", id=doc_id)
        return response['_source']
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )


@router.get("/indices")
async def get_indices(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all crawler indices and their statistics.
    
    Args:
        db: Database session
        current_user: Current user
        
    Returns:
        List of indices with stats
    """
    opensearch = get_opensearch_client()
    
    try:
        indices_info = []
        
        # Get all crawler indices
        response = opensearch.client.indices.get(index="crawler_*")
        
        for index_name in response.keys():
            stats = opensearch.get_index_stats(index_name)
            indices_info.append({
                "name": index_name,
                "document_count": stats.get('doc_count', 0),
                "size_bytes": stats.get('size_bytes', 0),
                "size_mb": round(stats.get('size_bytes', 0) / (1024 * 1024), 2)
            })
        
        return {
            "total_indices": len(indices_info),
            "indices": indices_info
        }
    
    except Exception as e:
        return {
            "total_indices": 0,
            "indices": []
        }
