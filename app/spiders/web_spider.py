"""Scrapy spiders for crawling websites."""

import scrapy
from scrapy.http import HtmlResponse
from urllib.parse import urljoin, urlparse
from typing import Optional, List
import xml.etree.ElementTree as ET


class SitemapSpider(scrapy.Spider):
    """
    Spider that crawls URLs from sitemap.xml files.
    Discovers sitemaps and extracts all URLs for crawling.
    """
    name = 'sitemap'
    allowed_domains = []
    
    def __init__(self, config: dict, *args, **kwargs):
        """
        Initialize spider with crawler configuration.
        
        Args:
            config: Crawler configuration dict with seed_urls, allowed_domains, etc.
        """
        super().__init__(*args, **kwargs)
        self.config = config
        self.allowed_domains = config.get('allow_domains', [])
        self.seed_urls = config.get('seed_urls', [])
        self.max_depth = config.get('max_depth', 2)
        self.current_depth = 0
    
    def start_requests(self):
        """Generate initial requests for sitemap discovery."""
        for seed_url in self.seed_urls:
            domain = urlparse(seed_url).netloc
            
            # Try common sitemap locations
            sitemap_urls = [
                urljoin(seed_url, '/sitemap.xml'),
                urljoin(seed_url, '/sitemap_index.xml'),
            ]
            
            for sitemap_url in sitemap_urls:
                yield scrapy.Request(
                    sitemap_url,
                    callback=self.parse_sitemap,
                    meta={'depth': 0},
                    dont_filter=True
                )
            
            # Also crawl seed URL directly
            yield scrapy.Request(
                seed_url,
                callback=self.parse,
                meta={'depth': 1}
            )
    
    def parse_sitemap(self, response):
        """Parse sitemap.xml and extract URLs."""
        try:
            root = ET.fromstring(response.body)
            
            # Handle sitemap index
            namespace = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
            
            # Check if this is a sitemap index
            sitemaps = root.findall('.//sm:sitemap/sm:loc', namespace)
            if sitemaps:
                for sitemap in sitemaps:
                    sitemap_url = sitemap.text
                    yield scrapy.Request(
                        sitemap_url,
                        callback=self.parse_sitemap,
                        meta={'depth': response.meta['depth']},
                        dont_filter=True
                    )
            
            # Extract URLs from sitemap
            urls = root.findall('.//sm:url/sm:loc', namespace)
            for url_elem in urls:
                url = url_elem.text
                if self._is_allowed_url(url):
                    yield scrapy.Request(
                        url,
                        callback=self.parse,
                        meta={'depth': response.meta['depth'] + 1}
                    )
        except Exception as e:
            self.logger.error(f"Error parsing sitemap {response.url}: {e}")
    
    def parse(self, response):
        """Parse web page and extract content."""
        # Meta information about the request
        depth = response.meta.get('depth', 0)
        
        # Skip if depth exceeded
        if depth > self.max_depth:
            return
        
        # Yield the response for pipeline processing
        yield {
            'url': response.url,
            'html': response.text,
            'content_type': 'html',
            'depth': depth
        }
        
        # Extract and follow links
        if depth < self.max_depth:
            for href in response.css('a::attr(href)').getall():
                absolute_url = response.urljoin(href)
                if self._is_allowed_url(absolute_url):
                    yield scrapy.Request(
                        absolute_url,
                        callback=self.parse,
                        meta={'depth': depth + 1},
                        dont_filter=False
                    )
    
    def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is allowed based on configuration."""
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Check against allowed domains
        if self.allowed_domains:
            if not any(domain.endswith(ad) or domain == ad for ad in self.allowed_domains):
                return False
        
        # Check URL patterns
        include_patterns = self.config.get('url_patterns_include', [])
        exclude_patterns = self.config.get('url_patterns_exclude', [])
        
        if include_patterns:
            import re
            if not any(re.search(pattern, url) for pattern in include_patterns):
                return False
        
        if exclude_patterns:
            import re
            if any(re.search(pattern, url) for pattern in exclude_patterns):
                return False
        
        return True


class GenericSpider(scrapy.Spider):
    """Generic spider for crawling websites without sitemap."""
    name = 'generic'
    allowed_domains = []
    
    def __init__(self, config: dict, *args, **kwargs):
        """Initialize spider with configuration."""
        super().__init__(*args, **kwargs)
        self.config = config
        self.allowed_domains = config.get('allow_domains', [])
        self.seed_urls = config.get('seed_urls', [])
        self.max_depth = config.get('max_depth', 2)
    
    def start_requests(self):
        """Generate initial requests."""
        for url in self.seed_urls:
            yield scrapy.Request(
                url,
                callback=self.parse,
                meta={'depth': 0}
            )
    
    def parse(self, response):
        """Parse web page."""
        depth = response.meta.get('depth', 0)
        
        if depth > self.max_depth:
            return
        
        # Yield for pipeline processing
        yield {
            'url': response.url,
            'html': response.text,
            'content_type': 'html',
            'depth': depth
        }
        
        # Follow links
        if depth < self.max_depth:
            for href in response.css('a::attr(href)').getall():
                absolute_url = response.urljoin(href)
                parsed = urlparse(absolute_url)
                
                # Check domain restriction
                if self.allowed_domains:
                    if any(parsed.netloc.endswith(ad) or parsed.netloc == ad for ad in self.allowed_domains):
                        yield scrapy.Request(
                            absolute_url,
                            callback=self.parse,
                            meta={'depth': depth + 1},
                            dont_filter=False
                        )
