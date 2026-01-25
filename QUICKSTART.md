# Quick Start Guide

## Fastest Way to Get Running (5 minutes)

### Option 1: With Docker Compose (Recommended)

```bash
# 1. Start infrastructure (OpenSearch, Redis, PostgreSQL)
docker-compose up -d

# 2. Create virtual environment and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Initialize database with sample data
python3 init_db.py

# 4. Start the application
bash run.sh
```

The app will be available at `http://localhost:8000`

OpenSearch Dashboards: `http://localhost:5601`

### Option 2: Local Development (SQLite + OpenSearch)

If you have OpenSearch running locally on default settings:

```bash
# 1. Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Initialize
python3 init_db.py

# 3. Run
bash run.sh
```

### Option 3: Minimal Setup (no OpenSearch)

The API will still work, but indexing features will fail:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 init_db.py
bash run.sh
```

## Login

Visit `http://localhost:8000` and use:

- **Username:** admin
- **Password:** admin123

Other test accounts: `editor/editor123`, `viewer/viewer123`

## First Steps in the UI

### 1. Create a Crawler

1. Navigate to **Crawlers** → Click **+ New Crawler**
2. Configure:
   - **Name:** "My Test Crawler"
   - **Seed URLs:** `https://example.com`
   - **Allowed Domains:** `example.com`
   - **Max Depth:** 2
   - Click **Save**

### 2. Start a Crawl Job

1. Navigate to **Crawlers**
2. Click **Start** on your crawler
3. Job will run in background

### 3. Search Results

1. Navigate to **Search**
2. Enter search terms
3. Browse indexed documents

### 4. Monitor System

1. Navigate to **Dashboard** - see statistics
2. Navigate to **Admin** → **Indices** - view OpenSearch indices
3. Navigate to **Admin** → **Collections** - view local JSON snapshots

## Environment Configuration

Edit `.env` for custom settings:

```bash
cp .env.example .env
nano .env  # Edit as needed
```

Key settings:
- `OPENSEARCH_HOST` - OpenSearch server address
- `DATABASE_URL` - Database connection string
- `JWT_SECRET_KEY` - Change in production!

## Development Tips

### Enable Debug Mode
```bash
API_DEBUG=true bash run.sh
```

### Watch for Changes
The `--reload` flag in `run.sh` will auto-restart on code changes.

### Database Reset
```bash
rm crawler.db  # Remove SQLite file
python3 init_db.py  # Reinitialize
```

### Check OpenSearch Connection
```bash
curl http://localhost:9200
```

### API Documentation
Visit `http://localhost:8000/docs` for interactive Swagger documentation.

## Troubleshooting

### Port Already in Use
```bash
# Change port in .env or via environment variable
API_PORT=8001 bash run.sh

# Or kill the process using port 8000
lsof -i :8000
kill -9 <PID>
```

### OpenSearch Not Connecting
```bash
# Verify OpenSearch is running
curl http://localhost:9200

# Or start with Docker Compose
docker-compose up opensearch -d
```

### Database Lock Error
SQLite doesn't support concurrent writes. If you see lock errors:
1. Close other connections/terminals
2. Use PostgreSQL in production: `docker-compose up postgres -d`
3. Update `DATABASE_URL` in `.env`

### Slow Crawling
Increase concurrent requests in crawler config:
- `concurrent_requests`: 32 (max)
- `concurrent_requests_per_domain`: 16 (max)
- Lower `download_delay` (minimum 0.1)

## Next Steps

1. **Configure a Real Website**
   - Update seed URLs and allowed domains
   - Test with your website's sitemap.xml

2. **Enable PDF/DOCX Extraction**
   - Crawlers will automatically extract from PDFs and Word documents
   - Check **Admin** → **Collections** for extracted documents

3. **Setup Production Database**
   - Update `DATABASE_URL` in `.env` to use PostgreSQL
   - Run migrations if needed

4. **Integrate with OpenSearch**
   - Use OpenSearch Dashboards to visualize indexed data
   - Create custom analyzers and mappings

5. **Deploy to Production**
   - Use environment-specific `.env` files
   - Set `API_DEBUG=false`
   - Change `JWT_SECRET_KEY` to a strong random value
   - Use PostgreSQL instead of SQLite
   - Setup HTTPS with reverse proxy (nginx/caddy)

## Common Tasks

### Create Users Programmatically
```python
from app.models import User, SessionLocal
from app.auth import hash_password

db = SessionLocal()
user = User(
    username="john",
    email="john@example.com",
    hashed_password=hash_password("secure_pass"),
    roles=["editor"]
)
db.add(user)
db.commit()
```

### Export Search Results
Navigate to Search, search, then download via API:
```bash
curl -H "Authorization: Bearer TOKEN" \
  -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"q":"search term","limit":1000}' > results.json
```

### Backup Collections
```bash
tar -czf collections_backup.tar.gz storage/collections/
```

### Monitor Crawl Progress
Visit **Jobs** tab and refresh to see real-time updates:
- URLs crawled
- Documents indexed
- Current progress percentage
- Error count

## Performance Notes

- **First crawl may be slow** - rate limiting and politeness delays
- **Large PDFs/DOCX take time** - extraction and indexing overhead
- **Search performance** - depends on OpenSearch index size
- **Deduplication** - uses content hash, adds minimal overhead

## Getting Help

1. Check **API.md** for endpoint documentation
2. Check **README.md** for architecture details
3. Review logs: `storage/logs/`
4. Check OpenSearch Dashboards: `http://localhost:5601`
5. Enable `API_DEBUG=true` for verbose logging

---

**Happy crawling! 🕷️**
