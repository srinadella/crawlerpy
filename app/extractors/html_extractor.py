"""HTML content extraction from web pages."""

from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
import re


class HTMLExtractor:
    """Extract text and metadata from HTML content."""
    
    @staticmethod
    def extract(html_content: str, url: str) -> Dict[str, Any]:
        """
        Extract title, text, and metadata from HTML.
        
        Args:
            html_content: Raw HTML string
            url: Source URL
            
        Returns:
            Dictionary with extracted data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            
            # Extract title
            title = None
            if soup.title:
                title = soup.title.string
            if not title:
                h1 = soup.find('h1')
                if h1:
                    title = h1.get_text(strip=True)
            
            # Extract main content
            text = soup.get_text(separator='\n', strip=True)
            
            # Extract metadata
            metadata = HTMLExtractor._extract_metadata(soup)
            metadata['url'] = url
            
            return {
                'title': title or 'Untitled',
                'content': text,
                'metadata': metadata,
                'content_type': 'html'
            }
        except Exception as e:
            return {
                'title': 'Error extracting HTML',
                'content': '',
                'metadata': {'error': str(e), 'url': url},
                'content_type': 'html'
            }
    
    @staticmethod
    def _extract_metadata(soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML head."""
        metadata = {}
        
        # Extract description
        desc = soup.find('meta', attrs={'name': 'description'})
        if desc:
            metadata['description'] = desc.get('content', '')
        
        # Extract keywords
        keywords = soup.find('meta', attrs={'name': 'keywords'})
        if keywords:
            metadata['keywords'] = keywords.get('content', '').split(',')
        
        # Extract author
        author = soup.find('meta', attrs={'name': 'author'})
        if author:
            metadata['author'] = author.get('content', '')
        
        # Extract language
        lang = soup.find('html')
        if lang:
            metadata['language'] = lang.get('lang', '')
        
        # Extract images and links count
        metadata['images_count'] = len(soup.find_all('img'))
        metadata['links_count'] = len(soup.find_all('a'))
        
        return metadata
