"""PDF content extraction."""

from typing import Dict, Any, Optional
import pdfplumber
import io


class PDFExtractor:
    """Extract text and metadata from PDF files."""
    
    @staticmethod
    def extract_from_path(file_path: str, url: str) -> Dict[str, Any]:
        """
        Extract text and metadata from PDF file.
        
        Args:
            file_path: Path to PDF file
            url: Source URL
            
        Returns:
            Dictionary with extracted data
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                return PDFExtractor._extract_from_pdf(pdf, url, file_path)
        except Exception as e:
            return {
                'title': 'Error extracting PDF',
                'content': '',
                'metadata': {'error': str(e), 'url': url, 'file_path': file_path},
                'content_type': 'pdf'
            }
    
    @staticmethod
    def extract_from_bytes(pdf_bytes: bytes, url: str, filename: str = 'document.pdf') -> Dict[str, Any]:
        """
        Extract text and metadata from PDF bytes.
        
        Args:
            pdf_bytes: PDF file content as bytes
            url: Source URL
            filename: Original filename
            
        Returns:
            Dictionary with extracted data
        """
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            with pdfplumber.open(pdf_file) as pdf:
                return PDFExtractor._extract_from_pdf(pdf, url, filename)
        except Exception as e:
            return {
                'title': 'Error extracting PDF',
                'content': '',
                'metadata': {'error': str(e), 'url': url, 'filename': filename},
                'content_type': 'pdf'
            }
    
    @staticmethod
    def _extract_from_pdf(pdf, url: str, filename: str) -> Dict[str, Any]:
        """Extract from pdfplumber PDF object."""
        # Extract text from all pages
        text_content = []
        tables = []
        
        for page_num, page in enumerate(pdf.pages, 1):
            page_text = page.extract_text()
            if page_text:
                text_content.append(page_text)
            
            # Extract tables if present
            page_tables = page.extract_tables()
            if page_tables:
                for table in page_tables:
                    tables.append({
                        'page': page_num,
                        'data': table
                    })
        
        # Get metadata
        metadata = PDFExtractor._extract_metadata(pdf)
        metadata['url'] = url
        metadata['page_count'] = len(pdf.pages)
        metadata['has_tables'] = len(tables) > 0
        
        # Extract title from metadata or filename
        title = metadata.get('title', '')
        if not title:
            title = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
        
        return {
            'title': title or 'Untitled PDF',
            'content': '\n\n'.join(text_content),
            'metadata': metadata,
            'content_type': 'pdf',
            'tables': tables
        }
    
    @staticmethod
    def _extract_metadata(pdf) -> Dict[str, Any]:
        """Extract metadata from PDF."""
        metadata = {}
        
        if pdf.metadata:
            pdf_meta = pdf.metadata
            if pdf_meta.get('Title'):
                metadata['title'] = pdf_meta['Title']
            if pdf_meta.get('Author'):
                metadata['author'] = pdf_meta['Author']
            if pdf_meta.get('Subject'):
                metadata['subject'] = pdf_meta['Subject']
            if pdf_meta.get('Keywords'):
                metadata['keywords'] = pdf_meta['Keywords']
            if pdf_meta.get('Creator'):
                metadata['creator'] = pdf_meta['Creator']
            if pdf_meta.get('Producer'):
                metadata['producer'] = pdf_meta['Producer']
        
        return metadata
