"""
Kannada text cleaning and normalization module
"""
import re
import json
import unicodedata
from pathlib import Path
from typing import List, Dict, Set, Tuple
from collections import defaultdict

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import save_json, load_json, logger
from config import CLEANED_DATA_DIR, RAW_DATA_DIR, DISASTER_TYPES, KANNADA_CONFIG

class KannadaTextCleaner:
    """Clean and normalize text for Kannada disaster management content"""
    
    def __init__(self):
        self.kannada_pattern = re.compile(KANNADA_CONFIG["unicode_range"])
        self.garbage_patterns = [re.compile(p, re.IGNORECASE) for p in KANNADA_CONFIG["common_garbage_patterns"]]
        
        # Common English disaster terms that should be preserved (may appear in Kannada text)
        self.preserve_english = {
            'ndma', 'ksdma', 'imd', 'who', 'red cross',
            'helpline', 'emergency', 'disaster', 'first aid',
            'covid', 'covid-19', 'corona', 'pandemic',
            'sms', 'gps', 'app', 'url', 'website'
        }
        
    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode characters"""
        # NFKC normalization for compatibility
        text = unicodedata.normalize('NFKC', text)
        
        # Fix common Kannada encoding issues
        # Replace broken Kannada characters
        text = text.replace('\u200c', '')  # Remove zero-width non-joiner
        text = text.replace('\u200d', '')  # Remove zero-width joiner
        
        return text
        
    def remove_html_artifacts(self, text: str) -> str:
        """Remove HTML tags and entities"""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        text = re.sub(r'&#\d+;', '', text)
        
        return text
        
    def remove_boilerplate(self, text: str) -> str:
        """Remove headers, footers, navigation text"""
        lines = text.split('\n')
        cleaned_lines = []
        
        skip_patterns = [
            r'^home\s*$',
            r'^menu\s*$',
            r'^search\s*$',
            r'^contact\s*$',
            r'^about\s*$',
            r'^login\s*$',
            r'^sign\s*in\s*$',
            r'^\s*click here\s*$',
            r'^\s*read more\s*$',
            r'^\s*share\s*$',
            r'^\s*print\s*$',
            r'copyright',
            r'all rights reserved',
            r'^\s*page \d+ of \d+\s*$',
            r'^\s*\d+\s*$',  # Just numbers
        ]
        
        skip_regex = [re.compile(p, re.IGNORECASE) for p in skip_patterns]
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                continue
                
            # Skip navigation/boilerplate
            if any(pattern.match(line_stripped) for pattern in skip_regex):
                continue
                
            cleaned_lines.append(line)
            
        return '\n'.join(cleaned_lines)
        
    def clean_garbage(self, text: str) -> str:
        """Remove garbage patterns"""
        for pattern in self.garbage_patterns:
            text = pattern.sub('', text)
            
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        
        return text.strip()
        
    def deduplicate_paragraphs(self, text: str) -> str:
        """Remove duplicate paragraphs"""
        paragraphs = text.split('\n\n')
        seen: Set[str] = set()
        unique_paragraphs = []
        
        for para in paragraphs:
            para_clean = para.strip()
            if not para_clean:
                continue
                
            # Normalize for comparison
            para_norm = ' '.join(para_clean.lower().split())
            
            # Check for near-duplicates (first 100 chars)
            para_hash = para_norm[:100]
            
            if para_hash not in seen and len(para_clean) > 20:
                seen.add(para_hash)
                unique_paragraphs.append(para_clean)
                
        return '\n\n'.join(unique_paragraphs)
        
    def filter_relevant_sentences(self, text: str, disaster_type: str) -> str:
        """Filter sentences relevant to disaster management"""
        sentences = re.split(r'(?<=[.!?।])\s+', text)
        
        # Keywords that indicate relevance
        relevance_keywords = {
            "flood": ['ಹೆಚ್ಚು', 'ನೀರು', 'ಮಳೆ', 'ನದಿ', 'inundation', 'flood', 'ಬಂಡಿ', 'rescue'],
            "urban_flood": ['ನಗರ', 'city', 'drainage', 'sewer', 'urban', 'metro', 'bangalore'],
            "earthquake": ['ಭೂಕಂಪ', 'tremor', 'richter', 'seismic', 'magnitude', 'building collapse'],
            "cyclone": ['ಚಂಡಮಾರುತ', 'storm', 'wind', 'rainfall', 'landfall', 'depression'],
            "landslide": ['ಭೂಸ್ಖಲನ', 'mud', 'debris', 'slope', 'hill', 'mountain'],
            "fire_accident": ['ಬೆಂಕಿ', 'fire', 'burn', 'smoke', 'extinguisher', 'short circuit'],
            "heatwave": ['ಬಿಸಿಲು', 'heat', 'temperature', 'dehydration', 'sunstroke', 'summer'],
            "lightning": ['ಮಿಂಚು', 'thunder', 'lightning', 'storm', 'electric', 'cloud'],
            "pandemic": ['ಸಾಂಕ್ರಾಮಿಕ', 'disease', 'virus', 'infection', 'vaccine', 'covid', 'health']
        }
        
        keywords = relevance_keywords.get(disaster_type, [])
        
        relevant_sentences = []
        for sentence in sentences:
            sentence_lower = sentence.lower()
            # Keep sentence if it has disaster keywords or is instructional
            if any(kw in sentence_lower for kw in keywords):
                relevant_sentences.append(sentence)
            elif any(word in sentence_lower for word in ['must', 'should', 'do not', 'don\'t', 'warning', 'alert', 'safety']):
                relevant_sentences.append(sentence)
                
        return ' '.join(relevant_sentences)
        
    def clean_record(self, record: Dict) -> Optional[Dict]:
        """Clean a single raw record"""
        try:
            raw_text = record.get('raw_text', '')
            if not raw_text or len(raw_text) < 50:
                return None
                
            # Apply cleaning steps
            text = self.normalize_unicode(raw_text)
            text = self.remove_html_artifacts(text)
            text = self.remove_boilerplate(text)
            text = self.clean_garbage(text)
            text = self.deduplicate_paragraphs(text)
            text = self.filter_relevant_sentences(text, record.get('disaster_type', 'general'))
            
            # Final cleanup
            text = text.strip()
            
            if len(text) < 100:  # Too short after cleaning
                return None
                
            cleaned_record = {
                "id": record["id"],
                "source_name": record["source_name"],
                "source_url": record["source_url"],
                "disaster_type": record["disaster_type"],
                "content_type": record["content_type"],
                "cleaned_text": text,
                "original_length": len(raw_text),
                "cleaned_length": len(text),
                "cleaned_at": record.get("scraped_at", ""),
                "language": record.get("language", "en")
            }
            
            return cleaned_record
            
        except Exception as e:
            logger.error(f"Error cleaning record {record.get('id', 'unknown')}: {e}")
            return None
            
    def process_raw_data(self):
        """Process all raw data files"""
        total_cleaned = 0
        
        for source_dir in RAW_DATA_DIR.iterdir():
            if not source_dir.is_dir():
                continue
                
            for disaster_dir in source_dir.iterdir():
                if not disaster_dir.is_dir():
                    continue
                    
                raw_file = disaster_dir / "raw_text.json"
                if not raw_file.exists():
                    continue
                    
                logger.info(f"Processing: {raw_file}")
                
                # Load raw data
                raw_records = load_json(raw_file)
                if not isinstance(raw_records, list):
                    raw_records = [raw_records]
                    
                # Clean records
                cleaned_records = []
                for record in raw_records:
                    cleaned = self.clean_record(record)
                    if cleaned:
                        cleaned_records.append(cleaned)
                        
                if cleaned_records:
                    # Save cleaned data
                    save_dir = CLEANED_DATA_DIR / disaster_dir.name
                    save_json(cleaned_records, save_dir / "cleaned_text.json")
                    total_cleaned += len(cleaned_records)
                    
        logger.info(f"Cleaning complete. Total cleaned records: {total_cleaned}")
        return total_cleaned
        
    def merge_and_deduplicate(self):
        """Merge all cleaned data and remove cross-source duplicates"""
        all_texts = []
        
        for disaster_type in DISASTER_TYPES:
            disaster_dir = CLEANED_DATA_DIR / disaster_type
            if not disaster_dir.exists():
                continue
                
            cleaned_file = disaster_dir / "cleaned_text.json"
            if not cleaned_file.exists():
                continue
                
            records = load_json(cleaned_file)
            all_texts.extend(records)
            
        # Remove duplicates across sources
        seen_hashes = set()
        unique_records = []
        
        for record in all_texts:
            text_hash = hash(record["cleaned_text"][:200])  # First 200 chars
            
            if text_hash not in seen_hashes:
                seen_hashes.add(text_hash)
                unique_records.append(record)
                
        logger.info(f"After deduplication: {len(unique_records)} records (removed {len(all_texts) - len(unique_records)} duplicates)")
        
        # Save merged dataset
        save_json(unique_records, CLEANED_DATA_DIR / "all_cleaned_data.json")
        
        return unique_records

def run_cleaning_pipeline():
    """Execute cleaning pipeline"""
    logger.info("=" * 60)
    logger.info("STARTING DATA CLEANING PIPELINE")
    logger.info("=" * 60)
    
    cleaner = KannadaTextCleaner()
    
    # Process individual files
    cleaner.process_raw_data()
    
    # Merge and deduplicate
    final_data = cleaner.merge_and_deduplicate()
    
    logger.info(f"\nCleaning pipeline complete: {len(final_data)} final records")
    return final_data

if __name__ == "__main__":
    run_cleaning_pipeline()