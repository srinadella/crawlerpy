#!/usr/bin/env python3
"""Quick reference for testing the real crawler implementation."""

"""
=== QUICK START: TESTING THE REAL CRAWLER ===

1. PREREQUISITE
   - Application running at http://localhost:8000
   - At least one crawler configuration in the database
   
2. START A CRAWL VIA API
   ```bash
   curl -X POST http://localhost:8000/api/jobs/{crawler_id}/start \
     -H "Authorization: Bearer <your_jwt_token>"
   ```
   
   Response:
   {
     "id": 3,
     "config_id": 1,
     "status": "running",
     "progress": 5,
     "urls_crawled": 0,
     "documents_indexed": 0,
     "started_at": "2026-01-25T...",
     "created_by_id": 1
   }

3. CHECK JOB STATUS
   ```bash
   curl http://localhost:8000/api/jobs/detail/{job_id} \
     -H "Authorization: Bearer <token>"
   ```
   
   Look for:
   - status: "running" → "completed" or "failed"
   - progress: 0-100%
   - urls_crawled: number of pages downloaded
   - documents_indexed: number of documents indexed

4. AUTOMATED TEST
   ```bash
   cd /Users/sri/data/crawler
   python3 test_crawler_execution.py
   ```
   
   This will:
   - Log in with sample credentials
   - Get first crawler config
   - Start a crawl job
   - Monitor for 30 seconds
   - Show final results

=== WHAT'S HAPPENING BEHIND THE SCENES ===

When you start a crawl:

1. Job record created with status "running"
2. Background task spawns subprocess:
   python3 app/scrapy_runner.py <spider_name> <config> <job_id> <output>

3. Scrapy spider executes:
   - Downloads pages from seed URLs
   - Follows links up to max_depth
   - Applies URL patterns (include/exclude)
   - Respects robots.txt
   - Applies download delays
   - Extracts HTML/PDF/DOCX content
   - Deduplicates based on checksums
   - Indexes to OpenSearch
   - Saves to collection file

4. Results collected:
   - Subprocess completes
   - Collection file parsed for count
   - Job record updated with final stats

=== UNDERSTANDING SPIDER TYPES ===

SITEMAP SPIDER (use_sitemap = True)
- Discovers sitemap.xml at seed URL
- Parses URLs from sitemap
- Also crawls seed URL directly
- Best for well-structured sites

GENERIC SPIDER (use_sitemap = False)
- Starts from seed URLs
- Follows links in HTML
- Applies same depth/pattern filters
- Best for sites without sitemap

=== CONFIGURATION EXAMPLE ===

To create a crawler for example.com:

{
  "name": "Example Site",
  "seed_urls": ["https://example.com"],
  "allowed_domains": ["example.com"],
  "follow_sitemap": true,
  "max_depth": 2,
  "concurrent_requests": 16,
  "download_delay": 1,
  "extract_pdfs": true,
  "extract_docx": true,
  "opensearch_index_name": "example_documents"
}

=== OUTPUT AND STORAGE ===

Collection File:
  storage/collections/crawl_2026-01-25T18-30-45.jsonl
  
  Each line is a JSON document:
  {
    "url": "https://example.com/page",
    "title": "Page Title",
    "content": "Extracted text...",
    "content_type": "html",
    "metadata": {...},
    "checksum": "sha256_hash"
  }

OpenSearch Index:
  - Index name from config (e.g., "documents")
  - Full-text searchable
  - Can be queried via Search API

=== MONITORING IN REAL-TIME ===

Watch the terminal running the FastAPI server:
  - INFO logs show Scrapy progress
  - Document counts as they're indexed
  - Timing information

Database Tables:
  - CrawlJob: job status, progress, final counts
  - IndexDocument: documents in OpenSearch (if tracking)

=== TROUBLESHOOTING ===

Job stays in "running" state:
  → Check if subprocess is still executing
  → Check /Users/sri/data/crawler/server.log for errors
  → Check if max_depth is too high (infinite loops possible)

No documents indexed:
  → Check seed_urls are accessible
  → Check allowed_domains filter isn't too restrictive
  → Check url_patterns_exclude doesn't block everything
  → Try increasing max_depth

OpenSearch connection error:
  → Check AWS credentials in .env
  → Verify domain policy allows access
  → Check OPENSEARCH_HOST and OPENSEARCH_PORT

=== FILES INVOLVED ===

Execution:
  - app/routes/jobs.py (entry point)
  - app/crawler_executor.py (orchestration)
  - app/scrapy_runner.py (subprocess)

Spiders:
  - app/spiders/web_spider.py (SitemapSpider, GenericSpider)

Processing:
  - app/pipelines.py (extraction, deduplication, indexing)
  - app/extractors/ (HTML, PDF, DOCX extraction)

Storage:
  - storage/collections/ (JSONL files)
  - storage/logs/ (crawl logs)

Database:
  - crawler.db (job records, configs)
  - audit.db (audit trail)

=== SUCCESS INDICATORS ===

Successful crawl shows:
✓ Job status changes from "running" to "completed"
✓ urls_crawled > 0
✓ documents_indexed > 0
✓ Collection file created in storage/collections/
✓ Documents searchable via /api/search
✓ Index shows in /api/search/indices
"""

if __name__ == "__main__":
    import sys
    print(__doc__)
