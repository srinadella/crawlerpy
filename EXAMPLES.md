# Example Usage Guide

## Using the Web Crawler Application

This guide walks through common workflows in the Web Crawler Admin UI and API.

---

## Workflow 1: Create and Run Your First Crawler

### Step 1: Login
1. Open `http://localhost:8000`
2. Enter credentials:
   - Username: `admin`
   - Password: `admin123`
3. Click **Login**

### Step 2: Create a Crawler Configuration
1. Click **Crawlers** in the navigation
2. Click **+ New Crawler**
3. Fill in the form:
   ```
   Name: My First Crawler
   Description: Testing crawler on example.com
   Seed URLs: https://example.com
   Allowed Domains: example.com
   Max Depth: 2
   ```
4. Keep checkboxes checked for PDF/DOCX extraction
5. Click **Save**

### Step 3: Start the Crawl
1. In Crawlers list, click **Start** button
2. Job will be created and run in background
3. Go to **Jobs** tab to monitor progress

### Step 4: Search Results
1. After crawl completes, go to **Search**
2. Enter search terms: `example`
3. See indexed documents from your crawl

---

## Workflow 2: Manage Multiple Crawlers

### Create a Documentation Site Crawler
```
Name: Product Docs
Description: Crawl documentation site
Seed URLs: 
  https://docs.product.com
  https://docs.product.com/api
Allowed Domains: docs.product.com
URL Patterns Include: .*docs.*
Max Depth: 3
Extract PDFs: Yes
Extract DOCX: Yes
```

### Create a Blog Crawler
```
Name: Company Blog
Description: Index all blog posts
Seed URLs: https://blog.company.com
Allowed Domains: blog.company.com
URL Patterns Include: /blog/.*
URL Patterns Exclude: /blog/draft.*
Max Depth: 1
```

---

## Workflow 3: Using the API Directly

### Login and Get Token
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { ... }
}
```

### Create a Crawler via API
```bash
TOKEN="your_access_token"

curl -X POST http://localhost:8000/api/crawlers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Created Crawler",
    "description": "Created via API",
    "enabled": true,
    "seed_urls": ["https://example.com"],
    "allow_domains": ["example.com"],
    "max_depth": 2,
    "extract_pdfs": true,
    "extract_docx": true,
    "follow_sitemap": true
  }'
```

### Start a Crawl Job
```bash
CRAWLER_ID=1
TOKEN="your_access_token"

curl -X POST "http://localhost:8000/api/jobs/$CRAWLER_ID/start" \
  -H "Authorization: Bearer $TOKEN"
```

### Search Documents
```bash
TOKEN="your_access_token"

curl -X POST http://localhost:8000/api/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "q": "example",
    "content_type": "",
    "domain": "",
    "limit": 10,
    "offset": 0
  }'
```

---

## Workflow 4: Admin Tasks

### View System Statistics
1. Click **Admin** in navigation
2. System tab shows:
   - Number of crawlers
   - Number of jobs
   - Number of users
   - Storage used
   - OpenSearch connection status

### Manage Users
1. Admin → Users tab
2. Click **+ New User**
3. Fill form:
   ```
   Username: john
   Email: john@company.com
   Password: secure_password
   Roles: editor, viewer
   ```
4. User can now login

### View Indices
1. Admin → Indices tab
2. Shows all OpenSearch indices with:
   - Document count
   - Index size
   - Options to reindex or delete

### Export Collection
1. Admin → Collections tab
2. Shows JSON Lines files from crawls
3. Download for offline analysis or archival

---

## Advanced: Custom Crawler Configuration

### Example 1: E-commerce Site Crawling
```
Name: E-commerce Catalog
Seed URLs:
  https://shop.example.com/products
  https://shop.example.com/categories
Allowed Domains: shop.example.com
URL Patterns Include:
  /products/.*
  /categories/.*
URL Patterns Exclude:
  /admin.*
  /checkout.*
  /account/.*
Max Depth: 3
Concurrent Requests: 32
Download Delay: 0.5 seconds
```

### Example 2: Blog Archive Crawling
```
Name: Blog Archive 2025
Seed URLs: https://blog.example.com/archive
Allowed Domains: blog.example.com
URL Patterns Include: /blog/2025/.*
URL Patterns Exclude: /draft.*
Max Depth: 2
Concurrent Requests: 8
Download Delay: 2 seconds (be respectful)
```

### Example 3: Documentation Crawling
```
Name: SDK Documentation
Seed URLs: https://developer.example.com
Allowed Domains: developer.example.com
URL Patterns Include: /docs/.*
URL Patterns Exclude: /docs/beta.*
Max Depth: 4
Concurrent Requests: 16
Download Delay: 1 second
Extract PDFs: Yes (for guides)
Extract DOCX: Yes (for templates)
```

---

## Workflow 5: Scheduled Crawling

### Manual Job Management
Currently crawls run on-demand. For production scheduling:

```python
# Example: Add to crontab or use Celery Beat
from app.models import CrawlerConfig, CrawlJob, SessionLocal
from app.routes.jobs import execute_crawl_job
from datetime import datetime

db = SessionLocal()
crawler = db.query(CrawlerConfig).filter(CrawlerConfig.id == 1).first()

job = CrawlJob(
    config_id=crawler.id,
    status='running',
    started_at=datetime.utcnow()
)
db.add(job)
db.commit()

# Execute crawl (background task)
```

### Future: Celery Scheduled Tasks
```python
from celery import Celery
from celery.schedules import crontab

app = Celery('crawler')

@app.task
def scheduled_crawl(crawler_id):
    execute_crawl_job(job_id, crawler_id)

app.conf.beat_schedule = {
    'daily-crawl': {
        'task': 'app.tasks.scheduled_crawl',
        'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
        'args': (1,)  # crawler_id
    }
}
```

---

## Workflow 6: Data Analysis

### Export Results to CSV
```bash
TOKEN="your_token"

# Get search results as JSON
curl -X POST http://localhost:8000/api/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"q":"*","limit":10000}' \
  > search_results.json

# Convert to CSV (Python)
python3 -c "
import json
import csv

with open('search_results.json') as f:
    data = json.load(f)

with open('results.csv', 'w') as f:
    writer = csv.DictWriter(f, ['url', 'title', 'content_type'])
    writer.writeheader()
    writer.writerows([
        {'url': r['url'], 'title': r['title'], 'content_type': r['content_type']}
        for r in data['results']
    ])
"
```

### Analyze Collections Locally
```python
import json
from collections import Counter

# Read collection file
docs = []
with open('storage/collections/crawl_2026-01-25T10-30-45.jsonl') as f:
    for line in f:
        docs.append(json.loads(line))

# Statistics
print(f"Total documents: {len(docs)}")

# Content type distribution
types = Counter(d['content_type'] for d in docs)
print(f"By type: {dict(types)}")

# Domains
domains = Counter(d['domain'] for d in docs)
print(f"Top domains: {domains.most_common(5)}")

# Average content length
avg_len = sum(len(d.get('content', '')) for d in docs) / len(docs)
print(f"Average content length: {avg_len:.0f} chars")
```

---

## Workflow 7: Debugging and Troubleshooting

### View Crawl Job Logs
1. Admin → Click job ID
2. See:
   - Detailed logs
   - Error details
   - Performance metrics

### Check OpenSearch
```bash
# Cluster health
curl http://localhost:9200/_cluster/health

# Index stats
curl http://localhost:9200/crawler_*/_stats

# Sample documents
curl http://localhost:9200/crawler_example_site/_search?size=1 | jq .
```

### Enable Debug Mode
```bash
API_DEBUG=true bash run.sh
```

Then visit `http://localhost:8000/docs` for interactive API testing.

---

## Workflow 8: Production Deployment

### Pre-deployment Checklist
```bash
# 1. Update environment
cp .env.example .env
# Edit .env with production values

# 2. Test with PostgreSQL
docker-compose up postgres -d
# Update DATABASE_URL in .env

# 3. Run migrations (if any)
python3 init_db.py

# 4. Test crawling
# Create test crawler and verify indexing works

# 5. Setup OpenSearch for HA
# Configure replication and sharding

# 6. Setup SSL
# Use nginx/caddy reverse proxy with HTTPS

# 7. Configure firewall
# Restrict port access appropriately
```

### Deploy Script Example
```bash
#!/bin/bash
set -e

# Pull latest code
git pull origin main

# Update dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Restart application
systemctl restart crawler

# Verify health
curl -f http://localhost:8000/api/health
```

---

## Performance Tuning

### Crawler Configuration
```
For fast crawling (many pages):
- Concurrent Requests: 32
- Download Delay: 0.1 seconds
- Max Depth: 1

For respectful crawling (default):
- Concurrent Requests: 16
- Download Delay: 1 second
- Max Depth: 2

For slow/restricted sites:
- Concurrent Requests: 4
- Download Delay: 5 seconds
- Max Depth: 1
```

### OpenSearch Tuning
```bash
# Increase heap size
export ES_JAVA_OPTS="-Xms2g -Xmx2g"

# Adjust refresh interval for faster indexing
curl -X PUT http://localhost:9200/crawler_*/_settings \
  -H "Content-Type: application/json" \
  -d '{"index": {"refresh_interval": "5s"}}'

# Revert after indexing
curl -X PUT http://localhost:9200/crawler_*/_settings \
  -H "Content-Type: application/json" \
  -d '{"index": {"refresh_interval": "30s"}}'
```

---

## Troubleshooting Examples

### Issue: Crawl is very slow
**Solution:** Increase concurrent requests and lower download delay
```
Crawlers → Edit → Max Depth: 1, Concurrent Requests: 32
```

### Issue: OpenSearch out of memory
**Solution:** Refresh frequently, limit batch size, add more RAM
```python
# In pipelines.py, reduce batch_size
self.batch_size = 100  # Instead of 500
```

### Issue: Duplicate documents being indexed
**Solution:** Deduplication is automatic, but check:
```bash
curl http://localhost:9200/crawler_docs/_search?q=checksum:value
```

### Issue: PDFs not extracting text
**Solution:** Check file format and PDF type
```bash
# Verify PDF is text-based (not image-based)
pdfplumber.open('file.pdf').pages[0].extract_text()
```

---

## Real-World Examples

### Example 1: Index Your Company Knowledge Base
```
1. Create crawler with:
   - Seed URL: https://knowledge.company.com
   - Max Depth: 5
   - Enable PDF/DOCX extraction

2. Run crawl

3. Configure OpenSearch Dashboards:
   - Create index pattern "crawler_*"
   - Build dashboards for company wiki

4. Share dashboard with team
```

### Example 2: Archive Website Before Migration
```
1. Create crawler named "Website Archive"
   - Seed: https://old-site.com
   - Max Depth: 10

2. Run crawl

3. Export JSON collection:
   - storage/collections/crawl_2026-01-25T10-30-45.jsonl

4. Store as version-controlled artifact

5. Can restore to OpenSearch anytime without re-crawling
```

### Example 3: Monitor Competitor Website Changes
```
1. Create crawler: "Competitor Monitor"
   - Seed: https://competitor.com
   - Max Depth: 2

2. Schedule daily via cron:
   ```bash
   0 2 * * * curl -X POST http://localhost:8000/api/jobs/1/start \
     -H "Authorization: Bearer $TOKEN"
   ```

3. Compare collections over time:
   - New pages added?
   - Content changed?
   - Pricing updates?
```

---

## Next Steps

1. **Setup your first crawler** - Follow Workflow 1
2. **Explore the UI** - Familiarize with all sections
3. **Check API documentation** - Visit `/docs`
4. **Configure OpenSearch Dashboards** - Advanced visualization
5. **Plan production deployment** - Review deployment checklist
6. **Customize for your needs** - Extend extractors, add crawlers

Happy crawling! 🕷️
