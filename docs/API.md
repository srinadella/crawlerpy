# API Documentation

## Overview

The Web Crawler API provides comprehensive endpoints for crawler management, document indexing, searching, and administration. Authentication uses JWT tokens obtained via login.

## Authentication

All API endpoints (except `/api/auth/login` and `/api/auth/register`) require JWT authentication.

### Login

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=admin&password=admin123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "username": "admin",
    "email": "admin@crawler.local",
    "roles": ["admin", "editor", "viewer"],
    "is_active": true,
    "created_at": "2026-01-25T10:00:00",
    "updated_at": "2026-01-25T10:00:00"
  }
}
```

### Using the Token

Include the token in the `Authorization` header:

```http
GET /api/crawlers
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Authentication Endpoints

### Register User
`POST /api/auth/register`

**Request:**
```json
{
  "username": "newuser",
  "email": "newuser@example.com",
  "password": "secure_password",
  "roles": ["viewer"]
}
```

**Response:** User object (201 Created)

### Get Current User
`GET /api/auth/me`

**Response:**
```json
{
  "id": 1,
  "username": "admin",
  "email": "admin@crawler.local",
  "roles": ["admin", "editor", "viewer"],
  "is_active": true,
  "created_at": "2026-01-25T10:00:00",
  "updated_at": "2026-01-25T10:00:00"
}
```

### List Users (Admin)
`GET /api/auth/users`

**Response:** Array of user objects

### Update User
`PUT /api/auth/users/{user_id}`

**Request:**
```json
{
  "email": "newemail@example.com",
  "roles": ["editor"]
}
```

## Crawler Endpoints

### List Crawlers
`GET /api/crawlers`

**Response:**
```json
[
  {
    "id": 1,
    "name": "Example Site",
    "description": "Example website crawler",
    "enabled": true,
    "seed_urls": ["https://example.com"],
    "allow_domains": ["example.com"],
    "url_patterns_include": [],
    "url_patterns_exclude": [".*login.*"],
    "follow_sitemap": true,
    "respect_robots_txt": true,
    "max_depth": 2,
    "download_timeout": 30,
    "concurrent_requests": 16,
    "concurrent_requests_per_domain": 8,
    "download_delay": 1,
    "extract_pdfs": true,
    "extract_docx": true,
    "opensearch_index_name": "crawler_example_site",
    "enable_indexing": true,
    "create_json_collection": true,
    "created_at": "2026-01-25T10:00:00",
    "updated_at": "2026-01-25T10:00:00"
  }
]
```

### Get Crawler
`GET /api/crawlers/{crawler_id}`

**Response:** Single crawler object

### Create Crawler (Editor+)
`POST /api/crawlers`

**Request:**
```json
{
  "name": "New Crawler",
  "description": "Crawls example.com",
  "enabled": true,
  "seed_urls": ["https://example.com"],
  "allow_domains": ["example.com"],
  "url_patterns_include": [],
  "url_patterns_exclude": [],
  "follow_sitemap": true,
  "respect_robots_txt": true,
  "max_depth": 3,
  "download_timeout": 30,
  "concurrent_requests": 16,
  "concurrent_requests_per_domain": 8,
  "download_delay": 1,
  "extract_pdfs": true,
  "extract_docx": true,
  "opensearch_index_name": "crawler_new",
  "enable_indexing": true,
  "create_json_collection": true
}
```

**Response:** Created crawler object (201 Created)

### Update Crawler (Editor+)
`PUT /api/crawlers/{crawler_id}`

**Request:** Partial crawler object with fields to update

**Response:** Updated crawler object

### Delete Crawler (Editor+)
`DELETE /api/crawlers/{crawler_id}`

**Response:** 204 No Content

## Job Endpoints

### List Jobs for Crawler
`GET /api/jobs/{config_id}`

**Response:**
```json
[
  {
    "id": 1,
    "config_id": 1,
    "status": "completed",
    "progress": 100,
    "urls_crawled": 150,
    "documents_indexed": 150,
    "errors_count": 0,
    "started_at": "2026-01-25T10:00:00",
    "completed_at": "2026-01-25T10:30:00",
    "created_at": "2026-01-25T10:00:00"
  }
]
```

### Get Job Detail
`GET /api/jobs/detail/{job_id}`

**Response:**
```json
{
  "id": 1,
  "config_id": 1,
  "status": "completed",
  "progress": 100,
  "urls_crawled": 150,
  "documents_indexed": 150,
  "errors_count": 0,
  "started_at": "2026-01-25T10:00:00",
  "completed_at": "2026-01-25T10:30:00",
  "logs": "Crawl job log entries...",
  "error_details": {},
  "created_at": "2026-01-25T10:00:00",
  "config": { ... }
}
```

### Start Crawl Job (Editor+)
`POST /api/jobs/{config_id}/start`

**Response:** Created job object (201 Created)

### Stop Crawl Job (Editor+)
`POST /api/jobs/{job_id}/stop`

**Response:** Updated job object with status "stopped"

## Search Endpoints

### Search Documents
`POST /api/search`

**Request:**
```json
{
  "q": "search terms",
  "content_type": "html",
  "domain": "example.com",
  "limit": 10,
  "offset": 0
}
```

**Response:**
```json
{
  "query": "search terms",
  "total": 25,
  "limit": 10,
  "offset": 0,
  "results": [
    {
      "id": "doc_id_123",
      "url": "https://example.com/page1",
      "title": "Page Title",
      "content_snippet": "Snippet of matching content...",
      "content_type": "html",
      "score": 4.5
    }
  ]
}
```

### Get Document
`GET /api/search/document/{doc_id}`

**Response:** Full document object

### List Indices
`GET /api/search/indices`

**Response:**
```json
{
  "total_indices": 2,
  "indices": [
    {
      "name": "crawler_example_site",
      "document_count": 150,
      "size_bytes": 2048000,
      "size_mb": 1.95
    }
  ]
}
```

## Admin Endpoints (Admin Only)

### System Statistics
`GET /api/admin/stats`

**Response:**
```json
{
  "opensearch_connected": true,
  "crawler_count": 2,
  "job_count": 5,
  "user_count": 3,
  "storage_used_mb": 50.25
}
```

### OpenSearch Health
`GET /api/admin/opensearch/health`

**Response:**
```json
{
  "status": "ok",
  "version": "2.10.0"
}
```

### Reindex Documents
`POST /api/admin/indices/{index_name}/reindex`

**Response:**
```json
{
  "status": "success",
  "indexed": 150,
  "errors": 0
}
```

### Delete Index
`DELETE /api/admin/indices/{index_name}`

**Response:**
```json
{
  "status": "success",
  "message": "Index crawler_example_site deleted"
}
```

### List Collections
`GET /api/admin/collections`

**Response:**
```json
{
  "total": 1,
  "collections": [
    {
      "name": "crawl_2026-01-25T10-30-45",
      "path": "/path/to/storage/collections/crawl_2026-01-25T10-30-45.jsonl",
      "document_count": 150,
      "file_size_bytes": 2048000,
      "created": "2026-01-25T10:30:45"
    }
  ]
}
```

### Delete Collection
`DELETE /api/admin/collections/{collection_name}`

**Response:**
```json
{
  "status": "success",
  "message": "Collection crawl_2026-01-25T10-30-45 deleted"
}
```

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

### Common Status Codes

- `200 OK` - Successful GET request
- `201 Created` - Successful POST request
- `204 No Content` - Successful DELETE request
- `400 Bad Request` - Invalid request format or validation error
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - Authenticated but insufficient permissions
- `404 Not Found` - Resource does not exist
- `409 Conflict` - Resource already exists (e.g., duplicate crawler name)
- `500 Internal Server Error` - Server-side error

## Rate Limiting

Currently, no rate limiting is enforced. In production, implement rate limiting per user/IP:

```python
@app.get("/api/crawlers")
@rate_limit(calls=100, period=3600)
async def list_crawlers(...):
    ...
```

## Batch Operations

For bulk document import from local collections:

1. Prepare JSON Lines file with documents
2. Call reindex endpoint: `POST /api/admin/indices/{index}/reindex`
3. Monitor progress via `/api/jobs` endpoints

## OpenSearch Query Syntax

The search endpoint supports OpenSearch query syntax:

- **Phrase search**: `"exact phrase"`
- **Wildcard**: `test*` or `te?t`
- **Boolean operators**: `AND`, `OR`, `NOT`
- **Range**: `page_count:[1 TO 10]`
- **Field search**: `title:"main title"`

Example:
```json
{
  "q": "title:\"Getting Started\" AND content_type:pdf",
  "limit": 20
}
```

## Webhooks (Future)

Planned for future versions:
- Job completion notifications
- Crawl error alerts
- Index update triggers
