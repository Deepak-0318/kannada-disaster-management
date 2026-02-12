"""
Configuration for Kannada Disaster Management Dataset Pipeline
"""
import os
from pathlib import Path

# Base paths
BASE_DIR = Path(__file__).parent
RAW_DATA_DIR = BASE_DIR / "raw_data"
CLEANED_DATA_DIR = BASE_DIR / "cleaned_data"
QA_DATA_DIR = BASE_DIR / "qa_data"
FINAL_DATA_DIR = BASE_DIR / "final_dataset"

# Create directories
for dir_path in [RAW_DATA_DIR, CLEANED_DATA_DIR, QA_DATA_DIR, FINAL_DATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Disaster types to cover
DISASTER_TYPES = [
    "flood",
    "urban_flood", 
    "earthquake",
    "cyclone",
    "landslide",
    "fire_accident",
    "heatwave",
    "lightning",
    "pandemic"
]

# Categories for Q&A
QA_CATEGORIES = [
    "general_awareness",
    "before_disaster",
    "during_disaster", 
    "after_disaster",
    "dos_donts",
    "emergency_response",
    "helpline",
    "evacuation",
    "first_aid",
    "myth_vs_fact",
    "short_voice_query",
    "government_sop"
]

# Data sources configuration
DATA_SOURCES = {
    "ndma": {
        "base_url": "https://ndma.gov.in",
        "disaster_urls": {
            "flood": "https://ndma.gov.in/Natural-Hazards/Floods",
            "earthquake": "https://ndma.gov.in/Natural-Hazards/Earthquakes",
            "cyclone": "https://ndma.gov.in/Natural-Hazards/Cyclones",
            "landslide": "https://ndma.gov.in/Natural-Hazards/Landslides",
            "heatwave": "https://ndma.gov.in/Natural-Hazards/Heat-Wave",
            "lightning": "https://ndma.gov.in/Natural-Hazards/Thunderstorm-Lightning",
            "urban_flood": "https://ndma.gov.in/Natural-Hazards/Floods",
            "fire_accident": "https://ndma.gov.in/Natural-Hazards/Fire",
        },
        "type": "web"
    },
    "ksdma": {
        "base_url": "https://ksdma.karnataka.gov.in",
        "disaster_urls": {
            "flood": "https://ksdma.karnataka.gov.in/flood",
            "cyclone": "https://ksdma.karnataka.gov.in/cyclone",
            "drought": "https://ksdma.karnataka.gov.in/drought",
            "pandemic": "https://ksdma.karnataka.gov.in/health-emergency",
        },
        "type": "web"
    },
    "imd": {
        "base_url": "https://mausam.imd.gov.in",
        "disaster_urls": {
            "cyclone": "https://mausam.imd.gov.in/imd_latest/contents/cyclone.php",
            "heatwave": "https://mausam.imd.gov.in/imd_latest/contents/heatwave.php",
        },
        "type": "web"
    },
    "who": {
        "base_url": "https://www.who.int",
        "disaster_urls": {
            "pandemic": "https://www.who.int/emergencies/disease-outbreak-news",
        },
        "type": "web"
    },
    "red_cross": {
        "base_url": "https://www.indianredcross.org",
        "disaster_urls": {
            "first_aid": "https://www.indianredcross.org/first-aid",
        },
        "type": "web"
    }
}

# PDF sources (government documents)
PDF_SOURCES = [
    {
        "name": "NDMA_Flood_Guidelines",
        "url": "https://ndma.gov.in/sites/default/files/PDF/GUIDELINES/Floods%20Guidelines.pdf",
        "disaster_type": "flood"
    },
    {
        "name": "NDMA_Earthquake_Guidelines",
        "url": "https://ndma.gov.in/sites/default/files/PDF/GUIDELINES/earthquake.pdf",
        "disaster_type": "earthquake"
    },
    {
        "name": "NDMA_Cyclone_Guidelines", 
        "url": "https://ndma.gov.in/sites/default/files/PDF/GUIDELINES/cyclone.pdf",
        "disaster_type": "cyclone"
    }
]

# Scraping settings
SCRAPING_CONFIG = {
    "delay_between_requests": 2,  # seconds
    "timeout": 30,
    "max_retries": 3,
    "user_agents": [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ],
    "respect_robots_txt": True
}

# Kannada-specific settings
KANNADA_CONFIG = {
    "unicode_range": r'[\u0C80-\u0CFF]',  # Kannada Unicode block
    "common_garbage_patterns": [
        r'https?://\S+',
        r'www\.\S+',
        r'\[edit\]',
        r'\[citation needed\]',
        r'\d+\s*comments',
        r'Share\s*this',
        r'Print\s*this',
        r'Advertisement',
    ]
}

# Target dataset size
TARGET_QA_PAIRS = 10000