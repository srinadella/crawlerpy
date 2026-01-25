"""Scrapy project configuration."""

BOT_NAME = 'crawler_bot'

SPIDER_MODULES = ['app.spiders']
NEWSPIDER_MODULE = 'app.spiders'

# Crawl settings
ROBOTSTXT_OBEY = True
CONCURRENT_REQUESTS = 16
CONCURRENT_REQUESTS_PER_DOMAIN = 8
DOWNLOAD_DELAY = 1
DOWNLOAD_TIMEOUT = 30

# User agent
USER_AGENT = 'Mozilla/5.0 (compatible; CrawlerBot/1.0; +http://crawler.local/bot)'

# Middleware
DOWNLOADER_MIDDLEWARES = {
    'scrapy.downloadermiddlewares.useragent.UserAgentMiddleware': None,
    'scrapy.downloadermiddlewares.httpproxy.HttpProxyMiddleware': 543,
}

# Pipelines
ITEM_PIPELINES = {
    'app.pipelines.DocumentExtractionPipeline': 300,
    'app.pipelines.DeduplicationPipeline': 310,
    'app.pipelines.IndexingPipeline': 320,
    'app.pipelines.CollectionPipeline': 330,
}

# Logging
LOG_LEVEL = 'INFO'

# Memory usage
MEMDEBUG_ENABLED = False
TELNETCONSOLE_ENABLED = False

# Allow relative redirects
REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 20
