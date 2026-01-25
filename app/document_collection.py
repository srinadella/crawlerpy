"""Utilities for managing document collections and local snapshots."""

from typing import Dict, Any, List, Optional, TextIO
import json
import os
from datetime import datetime
from app.config import settings
import hashlib


class DocumentCollection:
    """Manage JSON Lines collection files for static document storage."""
    
    def __init__(self, collection_name: str):
        """
        Initialize collection manager.
        
        Args:
            collection_name: Name of the collection
        """
        self.collection_name = collection_name
        self.collection_dir = settings.COLLECTIONS_PATH
        os.makedirs(self.collection_dir, exist_ok=True)
        self.file_path = os.path.join(self.collection_dir, f"{collection_name}.jsonl")
    
    def add_document(self, document: Dict[str, Any]) -> bool:
        """
        Add a document to the collection.
        
        Args:
            document: Document to add
            
        Returns:
            True if successful
        """
        try:
            with open(self.file_path, 'a') as f:
                f.write(json.dumps(document) + '\n')
            return True
        except Exception as e:
            print(f"Error adding document to collection: {e}")
            return False
    
    def add_documents_batch(self, documents: List[Dict[str, Any]]) -> int:
        """
        Add multiple documents to collection.
        
        Args:
            documents: List of documents
            
        Returns:
            Number of documents added
        """
        count = 0
        try:
            with open(self.file_path, 'a') as f:
                for doc in documents:
                    f.write(json.dumps(doc) + '\n')
                    count += 1
        except Exception as e:
            print(f"Error adding batch to collection: {e}")
        
        return count
    
    def read_documents(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Read documents from collection.
        
        Args:
            limit: Maximum number of documents to read
            
        Returns:
            List of documents
        """
        documents = []
        try:
            if not os.path.exists(self.file_path):
                return documents
            
            with open(self.file_path, 'r') as f:
                for i, line in enumerate(f):
                    if limit and i >= limit:
                        break
                    try:
                        doc = json.loads(line.strip())
                        documents.append(doc)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            print(f"Error reading collection: {e}")
        
        return documents
    
    def count_documents(self) -> int:
        """Count documents in collection."""
        if not os.path.exists(self.file_path):
            return 0
        
        count = 0
        try:
            with open(self.file_path, 'r') as f:
                count = sum(1 for _ in f)
        except Exception as e:
            print(f"Error counting documents: {e}")
        
        return count
    
    def clear(self) -> bool:
        """Clear all documents from collection."""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
            return True
        except Exception as e:
            print(f"Error clearing collection: {e}")
            return False
    
    def export_to_opensearch_bulk(self, index_name: str) -> List[Dict[str, Any]]:
        """
        Export collection to OpenSearch bulk format.
        
        Args:
            index_name: Target OpenSearch index name
            
        Returns:
            List of bulk operation dicts
        """
        bulk_actions = []
        
        for doc in self.read_documents():
            doc_id = hashlib.sha256(doc.get('url', '').encode()).hexdigest()
            
            # Index action
            bulk_actions.append({
                "index": {
                    "_index": index_name,
                    "_id": doc_id
                }
            })
            
            # Document
            bulk_actions.append(doc)
        
        return bulk_actions
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get collection metadata."""
        return {
            "name": self.collection_name,
            "path": self.file_path,
            "document_count": self.count_documents(),
            "file_size_bytes": os.path.getsize(self.file_path) if os.path.exists(self.file_path) else 0,
            "created": self._get_file_creation_time()
        }
    
    def _get_file_creation_time(self) -> Optional[str]:
        """Get file creation time."""
        if os.path.exists(self.file_path):
            mtime = os.path.getmtime(self.file_path)
            return datetime.fromtimestamp(mtime).isoformat()
        return None


def create_opensearch_document(url: str, title: str, content: str, content_type: str,
                              domain: str, source_filename: Optional[str] = None,
                              metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Create a document in OpenSearch format.
    
    Args:
        url: Source URL
        title: Document title
        content: Document content
        content_type: Type of content (html, pdf, docx)
        domain: Domain of origin
        source_filename: Original filename if applicable
        metadata: Additional metadata
        
    Returns:
        Document in OpenSearch format
    """
    if metadata is None:
        metadata = {}
    
    # Create checksum for deduplication
    checksum = hashlib.sha256((url + content).encode()).hexdigest()
    
    return {
        "url": url,
        "title": title,
        "content": content,
        "content_type": content_type,
        "domain": domain,
        "crawled_at": datetime.utcnow().isoformat(),
        "source_filename": source_filename,
        "checksum": checksum,
        "metadata": metadata
    }
