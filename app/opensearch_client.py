"""OpenSearch client wrapper and index management."""

from typing import Dict, Any, List, Optional
from opensearchpy import OpenSearch, helpers
from app.config import settings
import hashlib
import json
from datetime import datetime
import os


class OpenSearchClient:
    """Wrapper around OpenSearch client for indexing operations."""
    
    def __init__(self):
        """Initialize OpenSearch connection."""
        auth = None
        
        # Check if master user credentials are provided (preferred for AWS OpenSearch)
        if settings.OPENSEARCH_USER and settings.OPENSEARCH_PASSWORD:
            # Use basic auth with master user credentials
            auth = (settings.OPENSEARCH_USER, settings.OPENSEARCH_PASSWORD)
            
            self.client = OpenSearch(
                hosts=[{
                    'host': settings.OPENSEARCH_HOST,
                    'port': settings.OPENSEARCH_PORT,
                    'scheme': settings.OPENSEARCH_SCHEME
                }],
                http_auth=auth,
                use_ssl=True,
                verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
                ssl_show_warn=False
            )
        else:
            # No credentials provided, try AWS Signature Version 4 authentication
            use_aws_auth = (
                'search-' in settings.OPENSEARCH_HOST and 
                '.es.amazonaws.com' in settings.OPENSEARCH_HOST
            )
            
            if use_aws_auth:
                # Use AWS Signature Version 4 authentication for AWS OpenSearch
                try:
                    from opensearchpy import AWSV4SignerAuth
                    import boto3
                    
                    # Use default AWS credentials from environment/IAM role
                    credentials = boto3.Session().get_credentials()
                    region = settings.OPENSEARCH_HOST.split('.')[2]  # Extract region from hostname
                    
                    auth = AWSV4SignerAuth(credentials, region, 'es')
                    
                    self.client = OpenSearch(
                        hosts=[{
                            'host': settings.OPENSEARCH_HOST,
                            'port': settings.OPENSEARCH_PORT,
                            'scheme': settings.OPENSEARCH_SCHEME
                        }],
                        auth=auth,
                        verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
                        ssl_show_warn=False
                    )
                except (ImportError, Exception):
                    # Fallback to connection without auth if AWS auth fails
                    self.client = OpenSearch(
                        hosts=[{
                            'host': settings.OPENSEARCH_HOST,
                            'port': settings.OPENSEARCH_PORT,
                            'scheme': settings.OPENSEARCH_SCHEME
                        }],
                        use_ssl=True,
                        verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
                        ssl_show_warn=False
                    )
            else:
                # Local OpenSearch without auth
                self.client = OpenSearch(
                    hosts=[{
                        'host': settings.OPENSEARCH_HOST,
                        'port': settings.OPENSEARCH_PORT,
                        'scheme': settings.OPENSEARCH_SCHEME
                    }],
                    verify_certs=settings.OPENSEARCH_VERIFY_CERTS,
                    ssl_show_warn=False
            )
    
    def create_index(self, index_name: str, force: bool = False) -> bool:
        """
        Create index with appropriate mappings.
        
        Args:
            index_name: Name of the index
            force: Delete existing index if it exists
            
        Returns:
            True if successful
        """
        if self.client.indices.exists(index=index_name):
            if force:
                self.client.indices.delete(index=index_name)
            else:
                return False
        
        mappings = {
            "properties": {
                "url": {
                    "type": "keyword"
                },
                "title": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "content": {
                    "type": "text",
                    "analyzer": "standard"
                },
                "content_type": {
                    "type": "keyword"
                },
                "domain": {
                    "type": "keyword"
                },
                "crawled_at": {
                    "type": "date"
                },
                "source_filename": {
                    "type": "keyword"
                },
                "checksum": {
                    "type": "keyword"
                },
                "metadata": {
                    "type": "object",
                    "enabled": True
                }
            }
        }
        
        settings_config = {
            "number_of_shards": 1,
            "number_of_replicas": 0,
            "refresh_interval": "30s"
        }
        
        try:
            self.client.indices.create(
                index=index_name,
                body={
                    "settings": settings_config,
                    "mappings": mappings
                }
            )
            return True
        except Exception as e:
            print(f"Error creating index: {e}")
            return False
    
    def index_document(self, index_name: str, document: Dict[str, Any], doc_id: Optional[str] = None) -> str:
        """
        Index a single document.
        
        Args:
            index_name: Index name
            document: Document to index
            doc_id: Optional document ID
            
        Returns:
            Document ID
        """
        if not doc_id:
            doc_id = hashlib.sha256(document['url'].encode()).hexdigest()
        
        response = self.client.index(
            index=index_name,
            id=doc_id,
            body=document
        )
        return response['_id']
    
    def bulk_index(self, index_name: str, documents: List[Dict[str, Any]], batch_size: int = 500) -> Dict[str, Any]:
        """
        Bulk index documents.
        
        Args:
            index_name: Index name
            documents: List of documents to index
            batch_size: Batch size for bulk operations
            
        Returns:
            Bulk operation results
        """
        actions = []
        for doc in documents:
            doc_id = hashlib.sha256(doc['url'].encode()).hexdigest()
            actions.append({
                "_index": index_name,
                "_id": doc_id,
                "_source": doc
            })
        
        # Use chunk to avoid memory issues with large datasets
        success_count = 0
        error_count = 0
        errors = []
        
        for success, info in helpers.parallel_bulk(self.client, actions, chunk_size=batch_size):
            if success:
                success_count += 1
            else:
                error_count += 1
                errors.append(info)
        
        return {
            "success": success_count,
            "errors": error_count,
            "error_details": errors
        }
    
    def search(self, index_name: str, query: str, content_type: Optional[str] = None, 
               domain: Optional[str] = None, limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Search documents.
        
        Args:
            index_name: Index name
            query: Search query
            content_type: Filter by content type
            domain: Filter by domain
            limit: Number of results
            offset: Offset for pagination
            
        Returns:
            List of search results
        """
        must_clauses = [
            {
                "multi_match": {
                    "query": query,
                    "fields": ["title^2", "content"]
                }
            }
        ]
        
        filter_clauses = []
        if content_type:
            filter_clauses.append({"term": {"content_type": content_type}})
        if domain:
            filter_clauses.append({"term": {"domain": domain}})
        
        body = {
            "query": {
                "bool": {
                    "must": must_clauses,
                    "filter": filter_clauses if filter_clauses else None
                }
            },
            "from": offset,
            "size": limit
        }
        
        try:
            response = self.client.search(index=index_name, body=body)
            results = []
            for hit in response['hits']['hits']:
                result = hit['_source']
                result['_id'] = hit['_id']
                result['_score'] = hit['_score']
                results.append(result)
            return results
        except Exception as e:
            print(f"Error searching: {e}")
            return []
    
    def get_index_stats(self, index_name: str) -> Dict[str, Any]:
        """Get index statistics."""
        try:
            stats = self.client.indices.stats(index=index_name)
            docs = stats['indices'][index_name]['primaries']['docs']
            store = stats['indices'][index_name]['primaries']['store']
            
            return {
                "doc_count": docs['count'],
                "deleted_count": docs['deleted'],
                "size_bytes": store['size_in_bytes']
            }
        except Exception as e:
            print(f"Error getting index stats: {e}")
            return {}
    
    def delete_index(self, index_name: str) -> bool:
        """Delete an index."""
        try:
            self.client.indices.delete(index=index_name)
            return True
        except Exception as e:
            print(f"Error deleting index: {e}")
            return False
    
    def check_connection(self) -> bool:
        """Check if connected to OpenSearch."""
        try:
            self.client.info()
            return True
        except Exception as e:
            print(f"OpenSearch connection error: {e}")
            return False


# Global client instance
_opensearch_client = None


def get_opensearch_client() -> OpenSearchClient:
    """Get or create OpenSearch client instance."""
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = OpenSearchClient()
    return _opensearch_client
