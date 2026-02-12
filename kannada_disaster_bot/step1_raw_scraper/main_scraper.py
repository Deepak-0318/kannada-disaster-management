"""
Main orchestrator for raw data scraping
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))
from web_scraper import WebScraper
from pdf_extractor import PDFExtractor
from utils.helpers import logger

def run_raw_scraping_pipeline():
    """Execute complete raw data scraping"""
    logger.info("=" * 60)
    logger.info("STARTING RAW DATA SCRAPING PIPELINE")
    logger.info("=" * 60)
    
    # Step 1: Web scraping
    logger.info("\n--- Phase 1: Web Scraping ---")
    web_scraper = WebScraper()
    web_results = web_scraper.run_all_scrapers()
    
    total_web_records = sum(len(v) for v in web_results.values())
    logger.info(f"Web scraping complete: {total_web_records} records")
    
    # Step 2: PDF extraction
    logger.info("\n--- Phase 2: PDF Extraction ---")
    pdf_extractor = PDFExtractor()
    pdf_results = pdf_extractor.process_all_pdfs()
    
    logger.info(f"PDF extraction complete: {len(pdf_results)} documents")
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("RAW SCRAPING SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Web records: {total_web_records}")
    logger.info(f"PDF records: {len(pdf_results)}")
    logger.info(f"Total raw records: {total_web_records + len(pdf_results)}")
    
    return {
        "web": web_results,
        "pdf": pdf_results
    }

if __name__ == "__main__":
    run_raw_scraping_pipeline()