"""
Quick script to run web scraper and generate dataset
"""

from web_scraper import KannadaDisasterScraper
import os

def main():
    print("=" * 70)
    print("Kannada Disaster Management Dataset Generator")
    print("=" * 70)
    
    # Create output directory
    output_dir = "disaster_dataset"
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize scraper
    print("\n[1/4] Initializing web scraper...")
    scraper = KannadaDisasterScraper(output_dir=output_dir)
    
    # Scrape all targets
    print("\n[2/4] Scraping data from sources...")
    print("-" * 70)
    scraper.scrape_all_targets()
    
    # Save raw data
    print("\n[3/4] Saving raw scraped data...")
    scraper.save_raw_data()
    
    # Generate statistics
    print("\n[4/4] Generating statistics...")
    stats = scraper.generate_statistics()
    
    # Create and save Q&A dataset
    print("\n" + "-" * 70)
    print("Creating Q&A dataset...")
    qa_pairs = scraper.create_qa_dataset()
    json_file, jsonl_file, alpaca_file = scraper.save_qa_dataset(qa_pairs)
    
    # Print summary
    print("\n" + "=" * 70)
    print("DATASET GENERATION COMPLETE!")
    print("=" * 70)
    print(f"\n📁 Output Directory: {output_dir}/")
    print(f"📊 Total Q&A Pairs: {len(qa_pairs)}")
    print(f"\n📄 Generated Files:")
    print(f"   - Raw Data: {output_dir}/raw_scraped_data.json")
    print(f"   - Q&A JSON: {json_file}")
    print(f"   - Q&A JSONL: {jsonl_file}")
    print(f"   - Alpaca Format: {alpaca_file}")
    
    # Show sample data
    print("\n📋 Sample Q&A Pairs:")
    print("-" * 70)
    for i, qa in enumerate(qa_pairs[:3], 1):
        print(f"\n{i}. [{qa['language'].upper()}] {qa['disaster_type']}")
        print(f"   Q: {qa['instruction'][:80]}...")
        print(f"   A: {qa['output'][:80]}...")
    
    print("\n" + "=" * 70)
    print("Next steps:")
    print("  1. Review the generated dataset")
    print("  2. Run training: python train_model.py --train")
    print("  3. Start web app: python app.py")
    print("=" * 70)

if __name__ == "__main__":
    main()
