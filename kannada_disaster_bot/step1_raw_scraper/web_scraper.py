"""
Web scraping module for disaster management content
"""
import json
import time
import re
from pathlib import Path
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import PoliteCrawler, save_json, logger
from config import RAW_DATA_DIR, DATA_SOURCES, SCRAPING_CONFIG

class WebScraper(PoliteCrawler):
    """Scraper for disaster management websites"""
    
    def __init__(self):
        super().__init__(
            delay=SCRAPING_CONFIG["delay_between_requests"],
            max_retries=SCRAPING_CONFIG["max_retries"]
        )
        self.driver = None
        
    def init_selenium(self):
        """Initialize Selenium WebDriver for JS-heavy pages"""
        if self.driver is None:
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Selenium WebDriver initialized")
            
    def close_selenium(self):
        """Close Selenium WebDriver"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            
    def scrape_static_page(self, url: str) -> Optional[str]:
        """Scrape static HTML page"""
        response = self.polite_request(url)
        if response:
            return response.text
        return None
        
    def scrape_dynamic_page(self, url: str, wait_for: str = "body", timeout: int = 10) -> Optional[str]:
        """Scrape JavaScript-rendered page using Selenium"""
        try:
            self.init_selenium()
            self.driver.get(url)
            
            # Wait for element to load
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, wait_for)))
            
            # Additional wait for dynamic content
            time.sleep(2)
            
            return self.driver.page_source
            
        except Exception as e:
            logger.error(f"Selenium error for {url}: {e}")
            return None
            
    def extract_text_from_html(self, html: str, source_name: str) -> str:
        """Extract clean text from HTML"""
        soup = BeautifulSoup(html, 'lxml')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
            
        # Try to find main content
        main_content = None
        
        # Common content selectors
        content_selectors = [
            'main', 'article', '.content', '#content',
            '.main-content', '.entry-content', '.post-content',
            '[role="main"]', '.container .row .col'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content and len(main_content.get_text(strip=True)) > 500:
                break
                
        if not main_content:
            main_content = soup.body or soup
            
        # Extract text
        text = main_content.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        
        return text.strip()
        
    def scrape_ndma(self) -> List[Dict]:
        """Scrape NDMA website"""
        results = []
        source_config = DATA_SOURCES["ndma"]
        
        for disaster_type, url in source_config["disaster_urls"].items():
            logger.info(f"Scraping NDMA {disaster_type}: {url}")
            
            html = self.scrape_static_page(url)
            if html:
                text = self.extract_text_from_html(html, "ndma")
                
                record = {
                    "id": f"ndma_{disaster_type}_{int(time.time())}",
                    "source_name": "NDMA",
                    "source_url": url,
                    "disaster_type": disaster_type,
                    "content_type": "web",
                    "raw_text": text,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "language": "en"  # NDMA is primarily English
                }
                results.append(record)
                
                # Save immediately
                save_dir = RAW_DATA_DIR / "ndma" / disaster_type
                save_json([record], save_dir / "raw_text.json")
                
        return results
        
    def scrape_ksdma(self) -> List[Dict]:
        """Scrape Karnataka State Disaster Management Authority"""
        results = []
        source_config = DATA_SOURCES["ksdma"]
        
        for disaster_type, url in source_config["disaster_urls"].items():
            logger.info(f"Scraping KSDMA {disaster_type}: {url}")
            
            # Try static first, then dynamic if needed
            html = self.scrape_static_page(url)
            if not html or len(html) < 1000:
                html = self.scrape_dynamic_page(url)
                
            if html:
                text = self.extract_text_from_html(html, "ksdma")
                
                record = {
                    "id": f"ksdma_{disaster_type}_{int(time.time())}",
                    "source_name": "KSDMA",
                    "source_url": url,
                    "disaster_type": disaster_type,
                    "content_type": "web",
                    "raw_text": text,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "language": "en"
                }
                results.append(record)
                
                save_dir = RAW_DATA_DIR / "ksdma" / disaster_type
                save_json([record], save_dir / "raw_text.json")
                
        return results
        
    def scrape_imd(self) -> List[Dict]:
        """Scrape Indian Meteorological Department"""
        results = []
        source_config = DATA_SOURCES["imd"]
        
        for disaster_type, url in source_config["disaster_urls"].items():
            logger.info(f"Scraping IMD {disaster_type}: {url}")
            
            html = self.scrape_static_page(url)
            if html:
                text = self.extract_text_from_html(html, "imd")
                
                record = {
                    "id": f"imd_{disaster_type}_{int(time.time())}",
                    "source_name": "IMD",
                    "source_url": url,
                    "disaster_type": disaster_type,
                    "content_type": "web",
                    "raw_text": text,
                    "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "language": "en"
                }
                results.append(record)
                
                save_dir = RAW_DATA_DIR / "imd" / disaster_type
                save_json([record], save_dir / "raw_text.json")
                
        return results
        
    def scrape_news_articles(self, keywords: List[str], max_articles: int = 50) -> List[Dict]:
        """
        Scrape disaster-related news from The Hindu and Indian Express
        Note: This uses their search/archive pages
        """
        results = []
        
        # The Hindu search URL pattern
        hindu_search_urls = [
            f"https://www.thehindu.com/search/?q={'+'.join(keywords)}&order=DESC&sort=publishdate",
        ]
        
        # Indian Express search
        ie_search_urls = [
            f"https://indianexpress.com/?s={'+'.join(keywords)}",
        ]
        
        for url in hindu_search_urls + ie_search_urls:
            logger.info(f"Searching news: {url}")
            
            html = self.scrape_static_page(url)
            if not html:
                continue
                
            soup = BeautifulSoup(html, 'lxml')
            
            # Find article links
            article_links = []
            
            # The Hindu article selectors
            for link in soup.select('a[href*="/article"]'):
                href = link.get('href')
                if href and '/article' in href:
                    article_links.append(urljoin(url, href))
                    
            # Indian Express selectors
            for link in soup.select('.title a, .story a'):
                href = link.get('href')
                if href:
                    article_links.append(urljoin(url, href))
                    
            # Deduplicate and limit
            article_links = list(set(article_links))[:max_articles]
            
            for article_url in article_links:
                logger.info(f"Scraping article: {article_url}")
                
                article_html = self.scrape_static_page(article_url)
                if article_html:
                    text = self.extract_text_from_html(article_html, "news")
                    
                    # Determine disaster type from content
                    disaster_type = self._detect_disaster_type(text)
                    
                    record = {
                        "id": f"news_{int(time.time())}_{hash(article_url) % 10000}",
                        "source_name": "The_Hindu" if "thehindu" in url else "Indian_Express",
                        "source_url": article_url,
                        "disaster_type": disaster_type or "general",
                        "content_type": "article",
                        "raw_text": text,
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "language": "en"
                    }
                    results.append(record)
                    
                    save_dir = RAW_DATA_DIR / "news" / (disaster_type or "general")
                    existing = []
                    if (save_dir / "raw_text.json").exists():
                        existing = json.loads((save_dir / "raw_text.json").read_text(encoding='utf-8'))
                    existing.append(record)
                    save_json(existing, save_dir / "raw_text.json")
                    
        return results
        
    def _detect_disaster_type(self, text: str) -> Optional[str]:
        """Detect disaster type from text content"""
        text_lower = text.lower()
        
        disaster_keywords = {
            "flood": ["flood", "flooding", "inundation"],
            "urban_flood": ["urban flood", "city flood", "bangalore flood", "mumbai flood"],
            "earthquake": ["earthquake", "tremor", "seismic"],
            "cyclone": ["cyclone", "hurricane", "typhoon", "storm"],
            "landslide": ["landslide", "mudslide", "debris flow"],
            "fire_accident": ["fire", "blaze", "inferno", "wildfire"],
            "heatwave": ["heat wave", "heatwave", "extreme heat"],
            "lightning": ["lightning", "thunderstorm", "thunder"],
            "pandemic": ["pandemic", "covid", "outbreak", "epidemic"]
        }
        
        for disaster, keywords in disaster_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return disaster
        return None
        
    def run_all_scrapers(self) -> Dict[str, List[Dict]]:
        """Run all web scrapers"""
        all_results = {}
        
        try:
            all_results["ndma"] = self.scrape_ndma()
            all_results["ksdma"] = self.scrape_ksdma()
            all_results["imd"] = self.scrape_imd()
            
            # Scrape news for each disaster type
            for disaster in ["flood", "earthquake", "cyclone", "landslide", "fire", "covid"]:
                news_results = self.scrape_news_articles([disaster, "disaster", "karnataka"], max_articles=20)
                all_results[f"news_{disaster}"] = news_results
                
        finally:
            self.close_selenium()
            
        return all_results

if __name__ == "__main__":
    scraper = WebScraper()
    results = scraper.run_all_scrapers()
    logger.info(f"Scraping complete. Total sources: {len(results)}")