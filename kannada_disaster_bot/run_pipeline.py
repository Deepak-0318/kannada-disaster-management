"""
Main orchestrator for the complete Kannada Disaster Management Dataset Pipeline
"""
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from step1_raw_scraper.main_scraper import run_raw_scraping_pipeline
from step2_cleaning.text_cleaner import run_cleaning_pipeline
from step3_qa_generation.qa_generator import run_qa_generation_pipeline
from utils.helpers import logger

def run_full_pipeline():
    """Execute complete end-to-end pipeline"""
    start_time = time.time()
    
    logger.info("=" * 70)
    logger.info("KANNADA DISASTER MANAGEMENT CHATBOT - DATASET PIPELINE")
    logger.info("Target: ~10,000 Kannada Q&A pairs")
    logger.info("=" * 70)
    
    try:
        # Step 1: Raw Data Scraping
        logger.info("\n" + "=" * 70)
        logger.info("STEP 1: RAW DATA SCRAPING")
        logger.info("=" * 70)
        raw_results = run_raw_scraping_pipeline()
        
        # Step 2: Data Cleaning
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2: DATA CLEANING & NORMALIZATION")
        logger.info("=" * 70)
        cleaned_data = run_cleaning_pipeline()
        
        # Step 3: Q&A Generation
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3: Q&A GENERATION")
        logger.info("=" * 70)
        final_dataset = run_qa_generation_pipeline()
        
        # Final Summary
        elapsed = time.time() - start_time
        logger.info("\n" + "=" * 70)
        logger.info("PIPELINE COMPLETION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total execution time: {elapsed:.2f} seconds ({elapsed/60:.2f} minutes)")
        logger.info(f"Final dataset location: final_dataset/")
        logger.info(f"  - kannada_disaster_qa_dataset.json")
        logger.info(f"  - kannada_disaster_qa_dataset.csv")
        logger.info(f"  - dataset_statistics.json")
        logger.info("=" * 70)
        
        return final_dataset
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    run_full_pipeline()