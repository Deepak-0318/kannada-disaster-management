"""
Utility functions for the dataset pipeline
"""
import json
import hashlib
import time
import random
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import requests
from fake_useragent import UserAgent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pipeline.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class PoliteCrawler:
    """Base class for polite web crawling with rate limiting"""
    
    def __init__(self, delay: float = 2.0, max_retries: int = 3):
        self.delay = delay
        self.max_retries = max_retries
        self.ua = UserAgent(fallback='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36')
        self.last_request_time = 0
        
    def get_headers(self) -> Dict[str, str]:
        """Generate realistic headers"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def polite_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a polite request with rate limiting and retries"""
        # Rate limiting
        elapsed = time.time() - self.last_request_time
        if elapsed < self.delay:
            time.sleep(self.delay - elapsed)
            
        for attempt in range(self.max_retries):
            try:
                headers = self.get_headers()
                response = requests.get(
                    url, 
                    headers=headers, 
                    timeout=30,
                    **kwargs
                )
                self.last_request_time = time.time()
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    logger.warning(f"Rate limited on {url}, backing off...")
                    time.sleep(60 * (attempt + 1))
                else:
                    logger.warning(f"Status {response.status_code} for {url}")
                    
            except Exception as e:
                logger.error(f"Request error (attempt {attempt+1}): {e}")
                time.sleep(2 ** attempt)
                
        return None

def save_json(data: Any, filepath: Path, indent: int = 2):
    """Save data to JSON file"""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    logger.info(f"Saved {len(data) if isinstance(data, list) else 1} records to {filepath}")

def load_json(filepath: Path) -> Any:
    """Load data from JSON file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def generate_id(text: str) -> str:
    """Generate unique ID from text"""
    return hashlib.md5(text.encode('utf-8')).hexdigest()[:12]

def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> List[str]:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - overlap
    return chunks