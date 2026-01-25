# Web Crawler with OpenSearch Indexing

A production-grade web crawler application that indexes websites (sitemap), PDFs, and Word documents into OpenSearch. Includes a full-featured admin UI with crawler management, real-time job monitoring, and role-based access control (RBAC).

## Features

### Core Crawler
- **Scrapy-based web crawling** with sitemap.xml auto-discovery
- **Sitemap parsing** - automatically discover and crawl from sitemaps
- **PDF extraction** - extract text and metadata from PDF files using pdfplumber
- **DOCX parsing** - extract text and structure from Word documents
- **Content deduplication** - avoid re-indexing identical content using checksums
- **Configurable patterns** - include/exclude URL patterns using regex
- **Rate limiting** - respect robots.txt and throttle requests
- **Concurrent crawling** - configurable concurrent requests and domain-level limits

### Indexing
- **OpenSearch integration** - native support for indexing documents
- **Bulk operations** - efficient batch indexing
- **Local snapshots** - JSON Lines format collections for offline storage and reproducibility
- **Document metadata** - preserve author, creation date, page count, and custom metadata
- **Full-text search** - search across title, content, and metadata

### Administration UI
- **Dashboard** - system statistics and status overview
- **Crawler Management** - create, edit, configure, and delete crawlers
- **Job Control** - start, monitor, and stop crawl jobs in real-time
- **Search Interface** - full-text search across indexed documents
- **Index Administration** - manage OpenSearch indices, reindex, delete
- **Collection Management** - view and manage local document collections
- **User Management** - create users and assign roles

### Security
- **JWT Authentication** - secure token-based API authentication
- **Role-Based Access Control (RBAC)** - three default roles:
  - **Admin** - full system access
  - **Editor** - manage crawlers and index
  - **Viewer** - read-only access
- **Password hashing** - bcrypt-based password security
- **HTTP-only tokens** - prevents XSS attacks

### Audit & Logging
- **Comprehensive audit trail** - all user actions logged to separate database
- **Action tracking** - user actions, login attempts, crawler changes
- **Error logging** - failed operations with error details
- **Application state persistence** - settings survive server restarts
- **CLI audit viewer** - `python3 view_audit_logs.py` to view logs
- See [AUDIT_SYSTEM.md](AUDIT_SYSTEM.md) for complete audit documentation

## Architecture

```
crawler/
├── app/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Configuration management
│   ├── models.py               # Database models (SQLAlchemy)
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── auth.py                 # Authentication and authorization
│   ├── opensearch_client.py    # OpenSearch wrapper
│   ├── document_collection.py  # JSON Lines collection management
│   ├── settings.py             # Scrapy configuration
│   ├── pipelines.py            # Scrapy item processing pipelines
│   ├── extractors/
│   │   ├── html_extractor.py   # BeautifulSoup-based HTML extraction
│   │   ├── pdf_extractor.py    # pdfplumber-based PDF extraction
│   │   └── docx_extractor.py   # python-docx-based Word extraction
│   ├── spiders/
│   │   └── web_spider.py       # Scrapy spiders for crawling
│   └── routes/
│       ├── auth.py             # Authentication endpoints
│       ├── crawlers.py         # Crawler configuration endpoints
│       ├── jobs.py             # Job execution endpoints
│       ├── search.py           # Search endpoints
│       └── admin.py            # Administrative endpoints
├── frontend/
│   └── public/
│       ├── index.html          # Single-page app HTML
│       └── app.js              # Vanilla JavaScript frontend
├── storage/
│   ├── collections/            # JSON Lines document snapshots
│   └── logs/                   # Crawl job logs
├── requirements.txt            # Python dependencies
├── run.sh                      # Start application
└── init_db.py                  # Database initialization with sample data
```

## Installation

### Prerequisites
- Python 3.8+
- OpenSearch 2.0+ (or Elasticsearch 7.0+)
- Redis (optional, for task queues)

### Setup

1. **Clone the repository**
   ```bash
   cd /Users/sri/data/crawler
   ```

2. **Create virtual environment and install dependencies**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

4. **Initialize database**
   ```bash
   python3 init_db.py
   ```

5. **Start the application**
   ```bash
   bash run.sh
   ```

The application will be available at `http://localhost:8000`

## Sample Login Credentials

After initialization, use these credentials to log in:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Admin |
| editor | editor123 | Editor |
| viewer | viewer123 | Viewer |

## API Documentation

Once running, visit `/docs` for interactive Swagger documentation.

### Key Endpoints

**Authentication**
- `POST /api/auth/login` - Login and get JWT token
- `POST /api/auth/register` - Register new user
- `GET /api/auth/me` - Get current user info

**Crawlers**
- `GET /api/crawlers` - List all crawler configurations
- `POST /api/crawlers` - Create new crawler
- `PUT /api/crawlers/{id}` - Update crawler configuration
- `DELETE /api/crawlers/{id}` - Delete crawler

**Jobs**
- `POST /api/jobs/{config_id}/start` - Start crawl job
- `GET /api/jobs/{config_id}` - List jobs for crawler
- `POST /api/jobs/{job_id}/stop` - Stop running job
- `GET /api/jobs/detail/{job_id}` - Get job details

**Search**
- `POST /api/search` - Search indexed documents
- `GET /api/search/indices` - List indices and statistics

**Administration**
- `GET /api/admin/stats` - System statistics
- `GET /api/admin/opensearch/health` - OpenSearch health
- `DELETE /api/admin/indices/{name}` - Delete index
- `POST /api/admin/indices/{name}/reindex` - Reindex from collection
- `GET /api/admin/collections` - List collections

**Audit Logging** (NEW)
- `GET /api/audit` - View all audit logs (admin only)
- `GET /api/audit/user/{user_id}` - View user's audit logs
- `GET /api/audit/actions/summary` - Action statistics (admin only)
- `GET /api/audit/state/{key}` - Get application state
- `POST /api/audit/state/{key}` - Save application state (admin only)

## Configuration

### Crawler Configuration

Create crawlers via the UI or API with:
- **Seed URLs** - starting URLs for crawling
- **Allowed domains** - restrict crawling to specific domains
- **URL patterns** - regex include/exclude patterns
- **Depth limit** - maximum crawl depth
- **Extraction options** - enable/disable PDF and DOCX parsing
- **Rate limiting** - download delay and concurrent request limits

### OpenSearch Setup

For development with OpenSearch using Docker:

```bash
docker run -d \
  -p 9200:9200 \
  -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "DISABLE_SECURITY_PLUGIN=true" \
  opensearchproject/opensearch:latest
```

### Database Options

**Development (SQLite)**
```
DATABASE_URL=sqlite:///./crawler.db
```

**Production (PostgreSQL)**
```
DATABASE_URL=postgresql://user:password@localhost:5432/crawler
```

## Document Collections

Crawled documents are automatically saved to JSON Lines format for offline storage and reproducibility:

```
storage/collections/crawl_2026-01-25T10-30-45.jsonl
```

Each line is a JSON document with:
```json
{
  "url": "https://example.com/page",
  "title": "Page Title",
  "content": "Page content...",
  "content_type": "html",
  "domain": "example.com",
  "crawled_at": "2026-01-25T10:30:45",
  "source_filename": null,
  "checksum": "sha256_hash",
  "metadata": {
    "author": "John Doe",
    "page_count": 5,
    "created": "2026-01-20T00:00:00"
  }
}
```

These collections can be:
- Stored as version-controlled snapshots
- Reindexed into OpenSearch without re-crawling
- Analyzed offline
- Shared across environments

## Role-Based Access Control (RBAC)

### Admin Role
- Manage users and roles
- Create/delete crawlers and indices
- View system statistics
- Manage collections
- Reindex documents

### Editor Role
- Create and configure crawlers
- Start and stop crawl jobs
- View search results
- Manage index mappings

### Viewer Role
- Search indexed documents
- View crawler status
- Download search results
- View system statistics (read-only)

## Scaling and Production

### Future Enhancements

1. **Distributed Crawling**
   - Celery task queue integration
   - Distributed workers across multiple machines
   - Redis-backed job scheduling

2. **Advanced Features**
   - JavaScript rendering (Playwright/Selenium)
   - Proxy rotation
   - CAPTCHA handling
   - Custom authentication for crawled sites

3. **Performance**
   - Elasticsearch/OpenSearch sharding
   - Database indexing optimization
   - Caching layer (Redis)
   - Document deduplication improvements

4. **Monitoring**
   - Prometheus metrics export
   - Log aggregation (ELK stack)
   - Real-time dashboards
   - Alerting system

## Development

### Project Structure
- Backend: FastAPI + SQLAlchemy ORM
- Crawling: Scrapy framework
- Frontend: Vanilla JavaScript (no build step)
- Database: SQLite (dev) / PostgreSQL (prod)
- Search: OpenSearch
- Auth: JWT tokens + Bcrypt

### Adding New Extractors

Create a new extractor in `app/extractors/`:

```python
class CustomExtractor:
    @staticmethod
    def extract(content, url):
        return {
            'title': 'Extracted Title',
            'content': 'Extracted content',
            'metadata': {},
            'content_type': 'custom'
        }
```

Then add processing in `app/pipelines.py`.

### Extending RBAC

Modify role definitions in `app/auth.py` and update role checks in route handlers:

```python
@router.post("/special-feature")
async def special_feature(
    current_user: User = Depends(require_role(['admin']))
):
    ...
```

## Troubleshooting

### OpenSearch Connection Error
- Ensure OpenSearch is running: `http://localhost:9200`
- Check credentials in `.env`
- Verify firewall allows connection

### Database Lock (SQLite)
- SQLite doesn't support concurrent writes
- For production, switch to PostgreSQL
- Close other connections if lock persists

### Large File Handling
- PDFs and DOCX are extracted to memory
- For very large files, consider streaming extraction
- Adjust timeout settings in `.env`

## License

MIT License - see LICENSE file for details

## Support

For issues, questions, or contributions, please submit an issue or pull request.
