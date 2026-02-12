"""
PDF text extraction module
"""
import os
import logging
from typing import List, Dict
import PyPDF2
import pdfplumber

logger = logging.getLogger(__name__)


class PDFExtractor:
    """Extracts text from PDF files"""
    
    def __init__(self, config: dict):
        self.config = config
    
    def extract_with_pypdf2(self, pdf_path: str) -> str:
        """Extract text using PyPDF2"""
        try:
            text = ""
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"PyPDF2 extraction failed for {pdf_path}: {str(e)}")
            return ""
    
    def extract_with_pdfplumber(self, pdf_path: str) -> str:
        """Extract text using pdfplumber (better for complex layouts)"""
        try:
            text = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            logger.error(f"pdfplumber extraction failed for {pdf_path}: {str(e)}")
            return ""
    
    def extract_from_pdf(self, pdf_path: str) -> Dict[str, str]:
        """
        Extract text from a PDF file
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with filename and extracted text
        """
        logger.info(f"Extracting text from: {pdf_path}")
        
        # Try pdfplumber first (better for complex layouts)
        text = self.extract_with_pdfplumber(pdf_path)
        
        # Fallback to PyPDF2 if pdfplumber fails
        if not text or len(text.strip()) < 100:
            text = self.extract_with_pypdf2(pdf_path)
        
        return {
            'filename': os.path.basename(pdf_path),
            'path': pdf_path,
            'text': text,
            'status': 'success' if text else 'error'
        }
    
    def extract_from_directory(self, pdf_dir: str) -> List[Dict[str, str]]:
        """
        Extract text from all PDFs in a directory
        
        Args:
            pdf_dir: Directory containing PDF files
            
        Returns:
            List of dictionaries with extracted content
        """
        results = []
        
        if not os.path.exists(pdf_dir):
            logger.error(f"Directory not found: {pdf_dir}")
            return results
        
        pdf_files = [f for f in os.listdir(pdf_dir) if f.lower().endswith('.pdf')]
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        for pdf_file in pdf_files:
            pdf_path = os.path.join(pdf_dir, pdf_file)
            result = self.extract_from_pdf(pdf_path)
            results.append(result)
        
        return results
    
    def save_results(self, results: List[Dict[str, str]], output_dir: str):
        """Save extracted text to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        for result in results:
            if result['status'] == 'success' and result['text']:
                filename = os.path.splitext(result['filename'])[0] + '.txt'
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"Source PDF: {result['filename']}\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(result['text'])
                
                logger.info(f"Saved: {filepath}")
