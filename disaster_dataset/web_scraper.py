"""
Kannada Disaster Management Dataset Web Scraper
This script scrapes disaster-related content in Kannada from various sources
to create a training dataset for the AI chatbot.
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import re
from urllib.parse import urljoin, urlparse
import os
from datetime import datetime

class KannadaDisasterScraper:
    def __init__(self, output_dir="scraped_data"):
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.scraped_data = []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Target URLs for scraping
        self.target_urls = {
            # Karnataka Government Disaster Management Pages
            'karnataka_disaster_portal': [
                'https://ksdma.karnataka.gov.in/english',
                'https://revenue.karnataka.gov.in/24/disaster-management/en',
            ],
            
            # District Disaster Management Pages (English with Kannada content)
            'district_dmg_pages': [
                'https://uttarakannada.nic.in/en/disaster-management/',
                'https://kodagu.nic.in/en/disaster-management/',
                'https://raichur.nic.in/en/disaster-management/',
                'https://haveri.nic.in/en/disaster-management/',
                'https://udupi.nic.in/en/ddmp-sample/',
            ],
            
            # Helpline Pages
            'helpline_pages': [
                'https://bangalorerural.nic.in/en/helpline/',
                'https://vijayapura.nic.in/en/helpline/',
                'https://davanagere.nic.in/en/helpline/',
                'https://bengaluruurban.nic.in/en/helpline/',
            ],
            
            # NDMA Resources
            'ndma_resources': [
                'https://ndma.gov.in/sites/default/files/PDF/pocketbook-do-dont.pdf',
                'https://nidm.gov.in/iec.asp',
            ],
            
            # Kannada Wikipedia Pages
            'kannada_wikipedia': [
                'https://kn.wikipedia.org/wiki/%E0%B2%97%E0%B2%BE%E0%B2%B3%E0%B3%80',  # Flood in Kannada
                'https://kn.wikipedia.org/wiki/%E0%B2%AD%E0%B3%82%E0%B2%95%E0%B2%82%E0%B2%AA',  # Earthquake
                'https://kn.wikipedia.org/wiki/%E0%B2%B5%E0%B2%BE%E0%B2%AF%E0%B3%81_%E0%B2%97%E0%B2%BE%E0%B2%B3',  # Cyclone
            ],
        }
        
        # Emergency helpline data in Kannada
        self.helpline_data_kannada = [
            {
                "disaster_type": "general",
                "question_kn": "ಪ್ರಾಕೃತಿಕ ವಿಪತ್ತು ಸಮಯದಲ್ಲಿ ಯಾವ ಹೆಲ್ಪ್‌ಲೈನ್ ಸಂಖ್ಯೆಗೆ ಕರೆ ಮಾಡಬೇಕು?",
                "answer_kn": "ಪ್ರಾಕೃತಿಕ ವಿಪತ್ತು ಸಮಯದಲ್ಲಿ 1077 ಈ ತುರ್ತು ಸಹಾಯವಾಣಿಗೆ ಕರೆ ಮಾಡಿ. ಇದು ಕರ್ನಾಟಕ ರಾಜ್ಯ ವಿಪತ್ತು ನಿರ್ವಹಣಾ ಪ್ರಾಧಿಕಾರದ (KSDMA) ಉಚಿತ ಸಹಾಯವಾಣಿ."
            },
            {
                "disaster_type": "flood",
                "question_kn": "ಪ್ರವಾಹದ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
                "answer_kn": "ಪ್ರವಾಹದ ಸಮಯದಲ್ಲಿ: 1) ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ, 2) ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ವಿಚ್ಛಿನ್ನಗೊಳಿಸಿ, 3) ಶುದ್ಧ ನೀರು ಕುಡಿಯಿರಿ, 4) ರೇಡಿಯೋ/TV ಮೂಲಕ ಅಪ್‌ಡೇಟ್‌ಗಳನ್ನು ಅನುಸರಿಸಿ, 5) 1077 ಗೆ ಕರೆ ಮಾಡಿ."
            },
            {
                "disaster_type": "earthquake",
                "question_kn": "ಭೂಕಂಪದ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
                "answer_kn": "ಭೂಕಂಪದ ಸಮಯದಲ್ಲಿ: 1) ಶಾಂತವಾಗಿರಿ, 2) ಮೇಜು ಅಥವಾ ಬಲವಾದ ವಸ್ತುವಿನ ಕೆಳಗೆ ಅಡಗಿರಿ, 3) ಕಿಟಕಿ, ಕನ್ನಡಿ, ಗೋಡೆಗಳಿಂದ ದೂರವಿರಿ, 4) ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ, 5) ಹೊರಗೆ ಇದ್ದರೆ ಮರಗಳು, ಕಟ್ಟಡಗಳಿಂದ ದೂರವಿರಿ."
            },
            {
                "disaster_type": "cyclone",
                "question_kn": "ಚಂಡಮಾರುತದ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
                "answer_kn": "ಚಂಡಮಾರುತದ ಸಮಯದಲ್ಲಿ: 1) ಭದ್ರವಾದ ಕಟ್ಟಡದಲ್ಲಿ ಇರಿ, 2) ಕಿಟಕಿ, ಬಾಗಿಲುಗಳನ್ನು ಮುಚ್ಚಿರಿ, 3) ರೇಡಿಯೋ ಮೂಲಕ ಮಾಹಿತಿ ಅನುಸರಿಸಿ, 4) ಅಗತ್ಯ ವಸ್ತುಗಳನ್ನು ಸಿದ್ಧವಾಗಿಡಿ, 5) ಭದ್ರತಾ ದಳಗಳ ಸೂಚನೆಯನ್ನು ಅನುಸರಿಸಿ."
            },
            {
                "disaster_type": "fire",
                "question_kn": "ಬೆಂಕಿ ಅಪಾಯದ ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
                "answer_kn": "ಬೆಂಕಿ ಅಪಾಯದ ಸಮಯದಲ್ಲಿ: 1) 101 ಗೆ ಕರೆ ಮಾಡಿ, 2) ವಿದ್ಯುತ್ ಸಂಪರ್ಕ ವಿಚ್ಛಿನ್ನಗೊಳಿಸಿ, 3) ಬೆಂಕಿಯ ವಿರುದ್ಧ ಹೋರಾಡಲು ಶ್ವಾಸಕವಚ ಬಳಸಿ, 4) ತಡೆರಹಿತ ಹಾದಿಯಲ್ಲಿ ಹೊರಹೋಗಿ, 5) ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ."
            },
            {
                "disaster_type": "emergency_numbers",
                "question_kn": "ಕರ್ನಾಟಕದಲ್ಲಿ ತುರ್ತು ಸಹಾಯವಾಣಿ ಸಂಖ್ಯೆಗಳು ಯಾವುವು?",
                "answer_kn": "ಪೊಲೀಸ್ - 100, ಅಗ್ನಿಶಾಮಕ ದಳ - 101, ಆಂಬುಲೆನ್ಸ್ - 102/108, ವಿಪತ್ತು ನಿರ್ವಹಣಾ ಹೆಲ್ಪ್‌ಲೈನ್ - 1077, ರಾಜ್ಯ ತುರ್ತು ಕಾರ್ಯಾಚರಣೆ ಕೇಂದ್ರ - 1070, ಮಹಿಳಾ ಹೆಲ್ಪ್‌ಲೈನ್ - 1091, ಮಕ್ಕಳ ಹೆಲ್ಪ್‌ಲೈನ್ - 1098."
            },
        ]
        
    def scrape_url(self, url, category="general"):
        """Scrape content from a single URL"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract text content
            # Remove script and style elements
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()
            
            # Get text
            text = soup.get_text(separator='\n', strip=True)
            
            # Clean up text
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            text = '\n'.join(lines)
            
            # Extract title
            title = soup.find('title')
            title = title.get_text(strip=True) if title else "No Title"
            
            # Extract all links
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                links.append({
                    'text': link.get_text(strip=True),
                    'url': full_url
                })
            
            data = {
                'url': url,
                'title': title,
                'category': category,
                'content': text,
                'links': links[:20],  # Limit links
                'scraped_at': datetime.now().isoformat()
            }
            
            return data
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None
    
    def scrape_all_targets(self):
        """Scrape all target URLs"""
        all_data = []
        
        for category, urls in self.target_urls.items():
            print(f"\n=== Scraping Category: {category} ===")
            for url in urls:
                data = self.scrape_url(url, category)
                if data:
                    all_data.append(data)
                    self.scraped_data.append(data)
                time.sleep(2)  # Be respectful to servers
        
        return all_data
    
    def save_raw_data(self):
        """Save scraped raw data"""
        output_file = os.path.join(self.output_dir, 'raw_scraped_data.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.scraped_data, f, ensure_ascii=False, indent=2)
        print(f"\nRaw data saved to: {output_file}")
        return output_file
    
    def create_qa_dataset(self):
        """Create Q&A dataset from scraped data and predefined templates"""
        qa_pairs = []
        
        # Add predefined helpline Q&A
        for item in self.helpline_data_kannada:
            qa_pairs.append({
                "instruction": item["question_kn"],
                "input": "",
                "output": item["answer_kn"],
                "disaster_type": item["disaster_type"],
                "language": "kannada",
                "source": "predefined"
            })
        
        # Add English Q&A pairs for bilingual training
        english_qa = [
            {
                "instruction": "What helpline number should I call during a natural disaster in Karnataka?",
                "input": "",
                "output": "During a natural disaster in Karnataka, call 1077, the toll-free Disaster Helpline of Karnataka State Disaster Management Authority (KSDMA).",
                "disaster_type": "general",
                "language": "english",
                "source": "predefined"
            },
            {
                "instruction": "What should I do during a flood?",
                "input": "",
                "output": "During a flood: 1) Move to higher ground, 2) Turn off electricity and gas, 3) Drink clean water, 4) Follow updates on radio/TV, 5) Call 1077 for help.",
                "disaster_type": "flood",
                "language": "english",
                "source": "predefined"
            },
            {
                "instruction": "What should I do during an earthquake?",
                "input": "",
                "output": "During an earthquake: 1) Stay calm, 2) Drop, Cover, and Hold under a sturdy object, 3) Stay away from windows and mirrors, 4) Don't use elevators, 5) If outside, stay away from buildings and trees.",
                "disaster_type": "earthquake",
                "language": "english",
                "source": "predefined"
            },
            {
                "instruction": "What are the emergency helpline numbers in Karnataka?",
                "input": "",
                "output": "Police - 100, Fire - 101, Ambulance - 102/108, Disaster Management Helpline - 1077, State Emergency Operation Centre - 1070, Women Helpline - 1091, Child Helpline - 1098.",
                "disaster_type": "emergency_numbers",
                "language": "english",
                "source": "predefined"
            },
        ]
        
        qa_pairs.extend(english_qa)
        
        # Create bilingual pairs (Kannada-English mixed)
        bilingual_qa = [
            {
                "instruction": "ನಾನು flood ಸಮಯದಲ್ಲಿ ಏನು ಮಾಡಬೇಕು?",
                "input": "",
                "output": "ಪ್ರವಾಹದ ಸಮಯದಲ್ಲಿ, ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ತೆರಳಿ (move to higher ground) ಮತ್ತು 1077 ಗೆ ಕರೆ ಮಾಡಿ. Stay away from flood water.",
                "disaster_type": "flood",
                "language": "bilingual",
                "source": "predefined"
            },
            {
                "instruction": "What is the number for ವಿಪತ್ತು ನಿರ್ವಹಣಾ helpline?",
                "input": "",
                "output": "The Karnataka Disaster Management Helpline (ಕರ್ನಾಟಕ ವಿಪತ್ತು ನಿರ್ವಹಣಾ ಸಹಾಯವಾಣಿ) number is 1077. It is toll-free and available 24/7.",
                "disaster_type": "general",
                "language": "bilingual",
                "source": "predefined"
            },
        ]
        
        qa_pairs.extend(bilingual_qa)
        
        return qa_pairs
    
    def save_qa_dataset(self, qa_pairs):
        """Save Q&A dataset in multiple formats"""
        # Save as JSON
        json_file = os.path.join(self.output_dir, 'kannada_disaster_qa.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        print(f"Q&A dataset saved to: {json_file}")
        
        # Save as JSONL (for training)
        jsonl_file = os.path.join(self.output_dir, 'kannada_disaster_qa.jsonl')
        with open(jsonl_file, 'w', encoding='utf-8') as f:
            for item in qa_pairs:
                f.write(json.dumps(item, ensure_ascii=False) + '\n')
        print(f"Q&A dataset (JSONL) saved to: {jsonl_file}")
        
        # Save in Alpaca format for fine-tuning
        alpaca_format = []
        for item in qa_pairs:
            alpaca_format.append({
                "instruction": item["instruction"],
                "input": item["input"],
                "output": item["output"]
            })
        
        alpaca_file = os.path.join(self.output_dir, 'kannada_disaster_alpaca.json')
        with open(alpaca_file, 'w', encoding='utf-8') as f:
            json.dump(alpaca_format, f, ensure_ascii=False, indent=2)
        print(f"Alpaca format dataset saved to: {alpaca_file}")
        
        return json_file, jsonl_file, alpaca_file
    
    def generate_statistics(self):
        """Generate statistics about the dataset"""
        stats = {
            "total_scraped_urls": len(self.scraped_data),
            "categories": {},
            "total_qa_pairs": 0,
            "language_distribution": {}
        }
        
        for data in self.scraped_data:
            cat = data.get('category', 'unknown')
            stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
        
        print("\n=== Scraping Statistics ===")
        print(f"Total URLs scraped: {stats['total_scraped_urls']}")
        print(f"Categories: {stats['categories']}")
        
        return stats


def main():
    """Main function to run the scraper"""
    print("=" * 60)
    print("Kannada Disaster Management Dataset Scraper")
    print("=" * 60)
    
    # Initialize scraper
    scraper = KannadaDisasterScraper(output_dir="disaster_dataset")
    
    # Scrape all target URLs
    print("\nStarting web scraping...")
    scraper.scrape_all_targets()
    
    # Save raw data
    scraper.save_raw_data()
    
    # Generate statistics
    scraper.generate_statistics()
    
    # Create and save Q&A dataset
    print("\nCreating Q&A dataset...")
    qa_pairs = scraper.create_qa_dataset()
    scraper.save_qa_dataset(qa_pairs)
    
    print("\n" + "=" * 60)
    print("Scraping completed successfully!")
    print(f"Dataset saved in: {scraper.output_dir}/")
    print("=" * 60)
    
    return scraper


if __name__ == "__main__":
    main()
