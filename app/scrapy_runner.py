#!/usr/bin/env python3
"""Script to run Scrapy spiders from command line."""

import sys
import os

# Add project root to path so app module can be found
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Ensure PYTHONPATH is set for subprocesses
os.environ['PYTHONPATH'] = project_root

import json
from scrapy.crawler import CrawlerProcess

# Import spiders first to verify they're accessible
try:
    from app.spiders.web_spider import SitemapSpider, GenericSpider
    from app import pipelines  # Pre-import pipelines to ensure they're loaded
except ImportError as e:
    print(f"Import error: {e}", file=sys.stderr)
    print(f"Project root: {project_root}", file=sys.stderr)
    print(f"sys.path: {sys.path}", file=sys.stderr)
    sys.exit(1)

def run_spider(spider_name: str, config: dict, job_id: int, output_file: str):
    """
    Run a Scrapy spider with the given configuration.
    
    Args:
        spider_name: Name of the spider ('sitemap' or 'generic')
        config: Configuration dict
        job_id: Job ID
        output_file: Output file for results
    """
    
    # Select spider class
    if spider_name == 'sitemap':
        spider_cls = SitemapSpider
    else:
        spider_cls = GenericSpider
    
    # Scrapy settings
    settings_dict = {
        'BOT_NAME': 'crawler_bot',
        'SPIDER_MODULES': ['app.spiders'],
        'NEWSPIDER_MODULE': 'app.spiders',
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': config.get('concurrent_requests', 16),
        'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        'DOWNLOAD_DELAY': config.get('download_delay', 1),
        'DOWNLOAD_TIMEOUT': 30,
        'USER_AGENT': 'Mozilla/5.0 (compatible; CrawlerBot/1.0; +http://crawler.local/bot)',
        'LOG_LEVEL': 'INFO',
        'ITEM_PIPELINES': {
            'app.pipelines.DocumentExtractionPipeline': 300,
            'app.pipelines.DeduplicationPipeline': 310,
            'app.pipelines.IndexingPipeline': 320,
            'app.pipelines.CollectionPipeline': 330,
        },
        'FEEDS': {
            output_file: {
                'format': 'jsonlines',
                'indent': None,
            }
        }
    }
    
    # Initialize crawler process
    process = CrawlerProcess(settings_dict)
    
    # Add spider with arguments
    process.crawl(
        spider_cls,
        config=json.dumps(config),
        job_id=job_id
    )
    
    # Run crawler
    try:
        process.start()
    except Exception as e:
        print(f"Error running crawler: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python3 scrapy_runner.py <spider_name> <config_json> <job_id> <output_file>")
        sys.exit(1)
    
    spider_name = sys.argv[1]
    config_json = sys.argv[2]
    job_id = int(sys.argv[3])
    output_file = sys.argv[4]
    
    try:
        config = json.loads(config_json)
    except json.JSONDecodeError as e:
        print(f"Invalid config JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    run_spider(spider_name, config, job_id, output_file)
