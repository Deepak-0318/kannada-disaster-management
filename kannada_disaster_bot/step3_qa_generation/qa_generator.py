"""
Automatic Q&A generation from cleaned text
"""
import re
import json
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

import sys
sys.path.append(str(Path(__file__).parent.parent))
from utils.helpers import save_json, load_json, logger, chunk_text
from config import CLEANED_DATA_DIR, QA_DATA_DIR, FINAL_DATA_DIR, DISASTER_TYPES, QA_CATEGORIES, TARGET_QA_PAIRS
from templates import (
    QUESTION_TEMPLATES, 
    DISASTER_NAMES_KANNADA, 
    DISASTER_MYTHS,
    HELPLINE_NUMBERS
)

class KannadaQAGenerator:
    """Generate Kannada Q&A pairs from cleaned disaster management text"""
    
    def __init__(self):
        self.qa_pairs = []
        self.category_counts = defaultdict(int)
        
    def extract_key_sentences(self, text: str) -> List[Dict]:
        """Extract key instructional sentences from text"""
        sentences = re.split(r'(?<=[.!?।])\s+', text)
        
        key_patterns = {
            "before": ['ಮುನ್ನ', 'before', 'preparedness', 'siddha', 'ತಯಾರಿ', 'plan'],
            "during": ['ಸಮಯದಲ್ಲಿ', 'during', 'ವೇಳೆ', 'time', 'while'],
            "after": ['ನಂತರ', 'after', 'post', 'recovery', 'punarvasa'],
            "dos": ['ಮಾಡಬೇಕು', 'should', 'must', 'do', 'ಮಾಡಿ'],
            "donts": ['ಮಾಡಬಾರದು', 'should not', 'don\'t', 'avoid', 'ತಪ್ಪಿಸಿ'],
            "emergency": ['ತುರ್ತು', 'emergency', 'rescue', 'ರಕ್ಷಣೆ', 'ಸ್ಪಂದನೆ'],
            "safety": ['ಸುರಕ್ಷತೆ', 'safety', 'secure', 'ಕಾಪಾಡಿಕೊಳ್ಳಿ'],
            "warning": ['ಎಚ್ಚರಿಕೆ', 'warning', 'alert', 'ಅಪಾಯ', 'danger'],
        }
        
        key_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 300:
                continue
                
            detected_categories = []
            for cat, keywords in key_patterns.items():
                if any(kw in sentence.lower() for kw in keywords):
                    detected_categories.append(cat)
                    
            if detected_categories:
                key_sentences.append({
                    "text": sentence,
                    "categories": detected_categories,
                    "length": len(sentence)
                })
                
        return key_sentences
        
    def generate_from_template(self, disaster_type: str, category: str) -> List[Dict]:
        """Generate Q&A using templates"""
        qa_pairs = []
        
        templates = QUESTION_TEMPLATES.get(category, [])
        disaster_name_kn = DISASTER_NAMES_KANNADA.get(disaster_type, disaster_type)
        
        for template in templates:
            # Fill template
            question = template.format(disaster=disaster_name_kn)
            
            # Generate contextual answer based on category
            answer = self._generate_template_answer(disaster_type, category, question)
            
            if answer:
                qa_pairs.append({
                    "question": question,
                    "answer": answer,
                    "disaster_type": disaster_type,
                    "category": category,
                    "source_type": "template_generated",
                    "confidence": "medium"
                })
                
        return qa_pairs
        
    def _generate_template_answer(self, disaster_type: str, category: str, question: str) -> str:
        """Generate answer for template-based question"""
        
        # This would ideally use an LLM, but we'll use rule-based generation
        # with proper Kannada translations of key facts
        
        answers_db = {
            "general_awareness": {
                "flood": "ಪ್ರವಾಹ ಎಂದರೆ ನದಿ, ಕಾಲುವೆ ಅಥವಾ ಸಮುದ್ರದ ನೀರು ಒತ್ತೊತ್ತಾಗಿ ಹರಿದು ನೆಲವನ್ನು ಮುಚ್ಚುವ ಪ್ರಕ್ರಿಯೆ. ಇದು ಭಾರೀ ಮಳೆ, ಡ್ಯಾಂ ಒಡೆತ ಅಥವಾ ಸುನಾಮಿ ಕಾರಣದಿಂದ ಸಂಭವಿಸಬಹುದು.",
                "earthquake": "ಭೂಕಂಪ ಎಂದರೆ ಭೂಮಿಯ ಒಳಗೆ ಶಕ್ತಿಯ ಬಿಡುಗಡೆಯಿಂದ ಭೂಮಿ ಕಂಪಿಸುವ phenomenon. ಇದು ಟೆಕ್ಟೋನಿಕ್ ಪ್ಲೇಟ್‌ಗಳ ಚಲನೆಯಿಂದ ಉಂಟಾಗುತ್ತದೆ.",
                "cyclone": "ಚಂಡಮಾರುತ ಎಂದರೆ ಕಡಲ ಮೇಲೆ ಉಂಟಾಗುವ ಬಲವಾದ ಗಾಳಿ ಮತ್ತು ಮಳೆಯ ವ್ಯವಸ್ಥೆ. ಇದು ಬಿಸಿಲು ತಾಪದಿಂದ ಉಂಟಾಗುವ ವಾಯು ಚಲನೆಯಿಂದ ರೂಪುಗೊಳ್ಳುತ್ತದೆ.",
                "landslide": "ಭೂಸ್ಖಲನ ಎಂದರೆ ಬೆಟ್ಟದ ಭಾಗಗಳು ಕುಸಿದು ಕೆಳಗೆ ಬೀಳುವುದು. ಇದು ಭಾರೀ ಮಳೆ, ಭೂಕಂಪ ಅಥವಾ ಮಾನವ ಕ್ರಿಯೆಗಳಿಂದ ಸಂಭವಿಸಬಹುದು.",
                "fire_accident": "ಬೆಂಕಿ ಅಪಘಾತ ಎಂದರೆ ಅನಿಯಂತ್ರಿತ ಬೆಂಕಿಯಿಂದ ಉಂಟಾಗುವ ನಾಶ. ವಿದ್ಯುತ್ ಕೊಳಲು, ಗ್ಯಾಸ್ ಸೋರಿಕೆ, ಅಥವಾ ಕಾಳಗದಿಂದ ಇದು ಸಂಭವಿಸಬಹುದು.",
                "heatwave": "ಬಿಸಿಲು ತಾಪ ಎಂದರೆ ಸಾಮಾನ್ಯಕ್ಕಿಂತ ಹೆಚ್ಚು ತಾಪಮಾನವಿರುವ ಅವಧಿ. ಇದು ಆರೋಗ್ಯ ಸಮಸ್ಯೆಗಳನ್ನು ಉಂಟುಮಾಡಬಹುದು.",
                "lightning": "ಮಿಂಚು ಎಂದರೆ ಮೇಘಗಳ ಮಧ್ಯೆ ವಿದ್ಯುತ್ ಚಾರ್ಜ್‌ಗಳ ವಿನಿಮಯ. ಇದು ಭೂಮಿಗೆ ಬೀಳಬಹುದು ಮತ್ತು ಅಪಾಯಕಾರಿ.",
                "pandemic": "ಸಾಂಕ್ರಾಮಿಕ ಎಂದರೆ ದೊಡ್ಡ ಪ್ರದೇಶದಲ್ಲಿ ವ್ಯಾಪಕವಾಗಿ ಹರಡುವ ರೋಗ. ಇದು ವೈರಸ್ ಅಥವಾ ಬ್ಯಾಕ್ಟೀರಿಯಾ ಕಾರಣದಿಂದ ಉಂಟಾಗುತ್ತದೆ.",
            },
            
            "before_disaster": {
                "flood": "ಪ್ರವಾಹಕ್ಕೆ ಮುನ್ನ: 1) ಮನೆಯನ್ನು ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ಸ್ಥಳಾಂತರಿಸಿ 2) ಮುಖ್ಯ ದಾಖಲೆಗಳನ್ನು ವಾಟರ್‌ಪ್ರೂಫ್ ಬ್ಯಾಗ್‌ನಲ್ಲಿ ಇಡಿ 3) ತುರ್ತು ಕಿಟ್ ಸಿದ್ಧಪಡಿಸಿ 4) ಬ್ಯಾಟರಿ, ಟಾರ್ಚ್, ಔಷಧಿಗಳನ್ನು ಸಂಗ್ರಹಿಸಿ 5) ಸುದ್ದಿ ಚಾನೆಲ್‌ಗಳನ್ನು ಅನುಸರಿಸಿ.",
                "earthquake": "ಭೂಕಂಪಕ್ಕೆ ಮುನ್ನ: 1) ಮನೆಯನ್ನು earthquake-resistant ಆಗಿ ನಿರ್ಮಿಸಿ 2) ಭಾರೀ ವಸ್ತುಗಳನ್ನು ಗೋಡೆಗೆ ಸ್ಥಿರವಾಗಿ ಕಟ್ಟಿ 3) ತುರ್ತು ಯೋಜನೆ ಕುಟುಂಬದೊಂದಿಗೆ ಚರ್ಚಿಸಿ 4) ತುರ್ತು ಕಿಟ್ ಸಿದ್ಧಪಡಿಸಿ 5) ಗ್ಯಾಸ್, ವಿದ್ಯುತ್ ಸಂಪರ್ಕಗಳನ್ನು ಪರಿಶೀಲಿಸಿ.",
                "cyclone": "ಚಂಡಮಾರುತಕ್ಕೆ ಮುನ್ನ: 1) ಕಿಟಕಿ-ಬಾಗಿಲುಗಳಿಗೆ ಬಲಪಡಿಸುವ ಫಲಕಗಳನ್ನು ಸಿದ್ಧಪಡಿಸಿ 2) ಮನೆಯ ಹೊರಗಿನ ವಸ್ತುಗಳನ್ನು ಒಳಗೆ ತನ್ನಿ 3) ತುರ್ತು ಆಹಾರ, ನೀರು ಸಂಗ್ರಹಿಸಿ 4) ರೇಡಿಯೋ/ಬ್ಯಾಟರಿ ಟಿವಿ ಸಿದ್ಧಪಡಿಸಿ 5) ಸುರಕ್ಷಿತ ಸ್ಥಳಕ್ಕೆ ನಿರ್ಗಮನ ಯೋಜನೆ ಮಾಡಿ.",
                "fire_accident": "ಬೆಂಕಿ ಅಪಘಾತಕ್ಕೆ ಮುನ್ನ: 1) ಮನೆಯಲ್ಲಿ ಅಗ್ನಿಶಾಮಕ ಉಪಕರಣಗಳನ್ನು ಇಡಿ 2) ವಿದ್ಯುತ್ ಸಂಪರ್ಕಗಳನ್ನು ಪರಿಶೀಲಿಸಿ 3) ಬೆಂಕಿ ನಿರ್ಗಮನ ಮಾರ್ಗಗಳನ್ನು ಸ್ಪಷ್ಟವಾಗಿಡಿ 4) ಬೆಂಕಿ ಅಲಾರ್ಮ್ ಅಳವಡಿಸಿ 5) ಕುಟುಂಬದೊಂದಿಗೆ ಬೆಂಕಿ ಡ್ರಿಲ್ ಮಾಡಿ.",
                "pandemic": "ಸಾಂಕ್ರಾಮಿಕಕ್ಕೆ ಮುನ್ನ: 1) ರೋಗ ನಿರೋಧಕ ಲಸಿಕೆಗಳನ್ನು ತೆಗೆದುಕೊಳ್ಳಿ 2) ಮಾಸ್ಕ್, ಸ್ಯಾನಿಟೈಸರ್ ಸಂಗ್ರಹಿಸಿ 3) ಆರೋಗ್ಯ ವಿಮೆ ಪರಿಶೀಲಿಸಿ 4) ಮನೆಯಲ್ಲಿ ಐಸೋಲೇಶನ್ ಸೌಲಭ್ಯ ಸಿದ್ಧಪಡಿಸಿ 5) ಆನ್‌ಲೈನ್ ಸೇವೆಗಳಿಗೆ ಸೈನ್ ಅಪ್ ಮಾಡಿ.",
            },
            
            "during_disaster": {
                "flood": "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ: 1) ಎತ್ತರದ ಸ್ಥಳಕ್ಕೆ ಹೋಗಿ 2) ನೀರು ಹರಿಯುವ ಮಾರ್ಗದಲ್ಲಿ ನಡೆಯಬೇಡಿ 3) ವಿದ್ಯುತ್ ತಾರಗಳಿಗೆ ದೂರವಿರಿ 4) ರೇಡಿಯೋ/ಟಿವಿ ಮಾಹಿತಿ ಅನುಸರಿಸಿ 5) ಸಹಾಯಕ್ಕಾಗಿ ಹೆಲ್ಪ್‌ಲೈನ್‌ಗೆ ಕರೆ ಮಾಡಿ.",
                "earthquake": "ಭೂಕಂಪ ಸಮಯದಲ್ಲಿ: 1) ಮೇಜು ಕೆಳಗೆ ಅಡಗಿ 2) ಕಿಟಕಿ, ಗಾಜು ವಸ್ತುಗಳಿಂದ ದೂರವಿರಿ 3) ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ 4) ಹೊರಗೆ ಇದ್ದರೆ ಓಪನ್ ಸ್ಥಳಕ್ಕೆ ಹೋಗಿ 5) ಕಂಪನ ನಿಂತ ನಂತರವೇ ಹೊರಗೆ ಹೋಗಿ.",
                "cyclone": "ಚಂಡಮಾರುತ ಸಮಯದಲ್ಲಿ: 1) ಮನೆಯ ಒಳಗೆ ಉಳಿಯಿರಿ 2) ಕಿಟಕಿ-ಬಾಗಿಲುಗಳನ್ನು ಮುಚ್ಚಿರಿ 3) ಬಲವಾದ ಗಾಳಿಯಿಂದ ದೂರವಿರಿ 4) ರೇಡಿಯೋ ಮಾಹಿತಿ ಕೇಳಿ 5) ಅಗತ್ಯವಿದ್ದರೆ ಮಾತ್ರ ಹೊರಗೆ ಹೋಗಿ.",
                "fire_accident": "ಬೆಂಕಿ ಅಪಘಾತ ಸಮಯದಲ್ಲಿ: 1) ತಕ್ಷಣ ಹೊರಗೆ ಹೋಗಿ 2) ಅಗ್ನಿಶಾಮಕ ದಳಕ್ಕೆ 101 ಗೆ ಕರೆ ಮಾಡಿ 3) ವಿದ್ಯುತ್ ಬೆಂಕಿಗೆ ನೀರು ಬೇಡ 4) ಹೊಗೆಯಿಂದ ಕೆಳಗೆ ನಡೆಯಿರಿ 5) ಲಿಫ್ಟ್ ಬಳಸಬೇಡಿ.",
                "pandemic": "ಸಾಂಕ್ರಾಮಿಕ ಸಮಯದಲ್ಲಿ: 1) ಮನೆಯಲ್ಲಿ ಉಳಿಯಿರಿ 2) ಮಾಸ್ಕ್ ಧರಿಸಿ 3) ಸಾಮಾಜಿಕ ಅಂತರ ಕಾಪಾಡಿಕೊಳ್ಳಿ 4) ಕೈಗಳನ್ನು ಸೋಪ್‌ನಿಂದ ತೊಳೆಯಿರಿ 5) ಆರೋಗ್ಯ ಸಮಸ್ಯೆ ಇದ್ದರೆ ವೈದ್ಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
            },
            
            "helpline": {
                "flood": "ಪ್ರವಾಹ ಸಮಯದಲ್ಲಿ: ರಾಷ್ಟ್ರೀಯ ತುರ್ತು ಸಂಖ್ಯೆ 112, NDMA 011-26701728, KSDMA 080-22256023, ಪೊಲೀಸ್ 100, ಅಗ್ನಿಶಾಮಕ 101, ಆಂಬುಲೆನ್ಸ್ 108, ವಿಪತ್ತು ನಿರ್ವಹಣೆ 1070.",
                "earthquake": "ಭೂಕಂಪ ಸಮಯದಲ್ಲಿ: ರಾಷ್ಟ್ರೀಯ ತುರ್ತು ಸಂಖ್ಯೆ 112, NDMA 011-26701728, ಪೊಲೀಸ್ 100, ಅಗ್ನಿಶಾಮಕ 101, ಆಂಬುಲೆನ್ಸ್ 108. ಸ್ಥಳೀಯ ತಹಸೀಲ್ದಾರ ಕಚೇರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ.",
                "cyclone": "ಚಂಡಮಾರುತ ಸಮಯದಲ್ಲಿ: IMD ಹವಾಮಾನ ಹೆಲ್ಪ್‌ಲೈನ್ 1800-180-1717, ರಾಷ್ಟ್ರೀಯ ತುರ್ತು 112, NDMA 011-26701728, ಪೊಲೀಸ್ 100, ಅಗ್ನಿಶಾಮಕ 101, ಆಂಬುಲೆನ್ಸ್ 108.",
                "fire_accident": "ಬೆಂಕಿ ಅಪಘಾತದಲ್ಲಿ: ಅಗ್ನಿಶಾಮಕ ದಳ 101, ರಾಷ್ಟ್ರೀಯ ತುರ್ತು 112, ಪೊಲೀಸ್ 100, ಆಂಬುಲೆನ್ಸ್ 108. ವಿದ್ಯುತ್ ಬೆಂಕಿಯಲ್ಲಿ MESCOM ಸಂಖ್ಯೆ 1912 ಗೆ ಕರೆ ಮಾಡಿ.",
                "pandemic": "ಸಾಂಕ್ರಾಮಿಕದಲ್ಲಿ: ಕೋವಿಡ್ ಹೆಲ್ಪ್‌ಲೈನ್ 104, ರಾಷ್ಟ್ರೀಯ ತುರ್ತು 112, ಆಂಬುಲೆನ್ಸ್ 108, ಸಮೀಪದ ಆರೋಗ್ಯ ಉಪಕೇಂದ್ರವನ್ನು ಸಂಪರ್ಕಿಸಿ. ಆನ್‌ಲೈನ್ ವೈದ್ಯಕೀಯ ಸಲಹೆಗೆ eSanjeevani ಉಪಯೋಗಿಸಿ.",
            }
        }
        
        # Get base answer
        base_answer = answers_db.get(category, {}).get(disaster_type, "")
        
        if base_answer:
            return base_answer
            
        # Generate generic answer if specific not found
        return self._generate_generic_answer(disaster_type, category)
        
    def _generate_generic_answer(self, disaster_type: str, category: str) -> str:
        """Generate generic answer when specific not available"""
        disaster_kn = DISASTER_NAMES_KANNADA.get(disaster_type, disaster_type)
        
        generic_answers = {
            "after_disaster": f"{disaster_kn} ನಂತರ: 1) ಸುರಕ್ಷತೆ ಪರಿಶೀಲಿಸಿ 2) ಸರ್ಕಾರದ ಮಾಹಿತಿ ಅನುಸರಿಸಿ 3) ಆರೋಗ್ಯ ಪರೀಕ್ಷೆ ಮಾಡಿಸಿಕೊಳ್ಳಿ 4) ಹಾನಿಯ ಮೌಲ್ಯಮಾಪನ ಮಾಡಿ 5) ಪುನರ್ವಸತಿ ಸಹಾಯಕ್ಕಾಗಿ ಅರ್ಜಿ ಸಲ್ಲಿಸಿ.",
            "dos_donts": f"{disaster_kn} ವೇಳೆ ಮಾಡಬೇಕಾದವುಗಳು: ಸುದ್ದಿ ಅನುಸರಿಸಿ, ಶಾಂತವಾಗಿರಿ, ಸಹಾಯಕ್ಕಾಗಿ ಕರೆ ಮಾಡಿ. ಮಾಡಬಾರದ್ದು: ಅಫವಾಹಗಳನ್ನು ನಂಬಬೇಡಿ, ಅನಾವಶ್ಯಕವಾಗಿ ಹೊರಗೆ ಹೋಗಬೇಡಿ, ವಿದ್ಯುತ್ ಸಂಪರ್ಕಗಳನ್ನು ಮುಟ್ಟಬೇಡಿ.",
            "emergency_response": f"{disaster_kn} ಸಮಯದಲ್ಲಿ ತುರ್ತು ಸ್ಪಂದನೆ: 1) ತಕ್ಷಣ 112 ಗೆ ಕರೆ ಮಾಡಿ 2) ಸ್ಥಳವನ್ನು ಸುರಕ್ಷಿತವಾಗಿರಿಸಿ 3) ಗಾಯಾಳುಗಳಿಗೆ ಪ್ರಥಮ ಚಿಕಿತ್ಸೆ ನೀಡಿ 4) ಅಧಿಕಾರಿಗಳ ಸೂಚನೆ ಅನುಸರಿಸಿ 5) ನೆರವಿಗಾಗಿ ಸ್ಥಳೀಯರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
            "evacuation": f"{disaster_kn} ವೇಳೆ ನಿರ್ಗಮನ: 1) ಸರ್ಕಾರದ ಎಚ್ಚರಿಕೆ ಅನುಸರಿಸಿ 2) ಅಗತ್ಯ ವಸ್ತುಗಳನ್ನು ತೆಗೆದುಕೊಂಡು ಹೋಗಿ 3) ಪಾಲನಾ ಕೇಂದ್ರದ ಸ್ಥಳ ತಿಳಿದುಕೊಳ್ಳಿ 4) ಪ್ರಾಣಿಗಳಿಗೂ ವ್ಯವಸ್ಥೆ ಮಾಡಿ 5) ಮನೆಯನ್ನು ಲಾಕ್ ಮಾಡಿ.",
            "first_aid": f"{disaster_kn} ವೇಳೆ ಪ್ರಥಮ ಚಿಕಿತ್ಸೆ: 1) ಗಾಯವನ್ನು ಶುದ್ಧ ನೀರಿನಿಂದ ತೊಳೆಯಿರಿ 2) ಆ್ಯಂಟಿಸೆಪ್ಟಿಕ್ ಲೇಪನ ಹಚ್ಚಿ 3) ಬ್ಯಾಂಡೇಜ್ ಹಾಕಿ 4) ರಕ್ತಸ್ರಾವ ಇದ್ದರೆ ಒತ್ತಡ ಹಾಕಿ 5) ತೀವ್ರವಾದರೆ ವೈದ್ಯರನ್ನು ಕರೆಯಿರಿ.",
            "myth_vs_fact": f"{disaster_kn} ಬಗ್ಗೆ ತಪ್ಪು ಕಲ್ಪನೆಗಳಿವೆ. ಸರ್ಕಾರಿ ಮಾರ್ಗದರ್ಶನಗಳನ್ನು ಅನುಸರಿಸಿ, ಅಫವಾಹಗಳನ್ನು ನಂಬಬೇಡಿ. ಸರಿಯಾದ ಮಾಹಿತಿಗಾಗಿ 112 ಅಥವಾ NDMA ವೆಬ್‌ಸೈಟ್ ನೋಡಿ.",
            "short_voice_query": f"{disaster_kn} ಸಮಯದಲ್ಲಿ ಶಾಂತವಾಗಿರಿ. ತಕ್ಷಣ 112 ಗೆ ಕರೆ ಮಾಡಿ. ಸುರಕ್ಷಿತ ಸ್ಥಳಕ್ಕೆ ಹೋಗಿ. ಸುದ್ದಿ ಚಾನೆಲ್‌ಗಳನ್ನು ಅನುಸರಿಸಿ.",
            "government_sop": f"{disaster_kn} ಸಮಯದಲ್ಲಿ ಸರ್ಕಾರದ SOP ಅನುಸರಿಸಿ: ಜಿಲ್ಲಾ ಆಡಳಿತದ ಸೂಚನೆ ಪಾಲಿಸಿ, ಪರಿಹಾರ ಶಿಬಿರಗಳನ್ನು ಬಳಸಿ, ಸಹಾಯಕ್ಕಾಗಿ ತಹಸೀಲ್ದಾರರನ್ನು ಸಂಪರ್ಕಿಸಿ.",
        }
        
        return generic_answers.get(category, f"{disaster_kn} ಬಗ್ಗೆ ಹೆಚ್ಚಿನ ಮಾಹಿತಿಗಾಗಿ KSDMA ವೆಬ್‌ಸೈಟ್ www.ksdma.karnataka.gov.in ನೋಡಿ ಅಥವಾ 112 ಗೆ ಕರೆ ಮಾಡಿ.")
        
    def generate_from_text(self, text: str, disaster_type: str, source_info: Dict) -> List[Dict]:
        """Generate Q&A from actual text content"""
        qa_pairs = []
        
        # Extract key sentences
        key_sentences = self.extract_key_sentences(text)
        
        for sent_data in key_sentences:
            sentence = sent_data["text"]
            categories = sent_data["categories"]
            
            # Generate questions from this sentence
            for category in categories:
                if category in ["before", "during", "after"]:
                    cat_map = {
                        "before": "before_disaster",
                        "during": "during_disaster", 
                        "after": "after_disaster"
                    }
                    mapped_category = cat_map.get(category, category)
                else:
                    mapped_category = category if category in QA_CATEGORIES else "general_awareness"
                    
                # Create question
                question = self._create_question_from_sentence(sentence, mapped_category, disaster_type)
                
                if question:
                    qa_pairs.append({
                        "question": question,
                        "answer": sentence,
                        "disaster_type": disaster_type,
                        "category": mapped_category,
                        "source_name": source_info.get("source_name", "unknown"),
                        "source_url": source_info.get("source_url", ""),
                        "source_type": "extracted_from_text",
                        "confidence": "high"
                    })
                    
        return qa_pairs
        
    def _create_question_from_sentence(self, sentence: str, category: str, disaster_type: str) -> Optional[str]:
        """Create a question from a statement"""
        disaster_kn = DISASTER_NAMES_KANNADA.get(disaster_type, disaster_type)
        
        # Question starters based on category
        starters = {
            "before_disaster": [
                f"{disaster_kn} ಬರುವ ಮುನ್ನ ",
                f"{disaster_kn} ಸಂಭವಿಸುವ ಮುನ್ನ ",
                f"ಮುಂಜಾಗ್ರತೆಯಾಗಿ "
            ],
            "during_disaster": [
                f"{disaster_kn} ಸಮಯದಲ್ಲಿ ",
                f"{disaster_kn} ವೇಳೆ ",
                f"ಅಪಾಯದ ಸಮಯದಲ್ಲಿ "
            ],
            "after_disaster": [
                f"{disaster_kn} ನಂತರ ",
                f"{disaster_kn} ಮುಗಿದ ನಂತರ ",
                f"ಪುನರ್ವಸತಿ ಸಮಯದಲ್ಲಿ "
            ],
            "dos_donts": [
                f"{disaster_kn} ವೇಳೆ ",
                f"{disaster_kn} ಸಮಯದಲ್ಲಿ "
            ],
            "emergency_response": [
                f"{disaster_kn} ಸಮಯದಲ್ಲಿ ತುರ್ತು ಸ್ಥಿತಿಯಲ್ಲಿ ",
                f"{disaster_kn} ವೇಳೆ ರಕ್ಷಣೆಗಾಗಿ ",
                f"ಅಪಾಯದಲ್ಲಿ "
            ],
            "first_aid": [
                f"{disaster_kn} ವೇಳೆ ಗಾಯವಾದರೆ ",
                f"{disaster_kn} ಸಮಯದಲ್ಲಿ ಆರೋಗ್ಯ ಸಮಸ್ಯೆ ಇದ್ದರೆ ",
                f"ಅಪಘಾತದಲ್ಲಿ "
            ]
        }
        
        # Simple heuristic to create question
        starter_list = starters.get(category, [f"{disaster_kn} ಬಗ್ಗೆ "])
        starter = random.choice(starter_list)
        
        # Convert statement to question
        if "ಮಾಡಬೇಕು" in sentence or "should" in sentence.lower():
            question = starter + "ಏನು ಮಾಡಬೇಕು?"
        elif "ಮಾಡಬಾರದು" in sentence or "avoid" in sentence.lower():
            question = starter + "ಏನು ಮಾಡಬಾರದು?"
        elif "ಹೇಗೆ" in sentence:
            question = starter + "ಹೇಗೆ ರಕ್ಷಣೆ ಪಡೆಯಬಹುದು?"
        elif "ಎಲ್ಲಿ" in sentence:
            question = starter + "ಎಲ್ಲಿ ಹೋಗಬೇಕು?"
        elif "ಯಾವಾಗ" in sentence:
            question = starter + "ಯಾವಾಗ ಎಚ್ಚರಿಕೆ ವಹಿಸಬೇಕು?"
        else:
            question = starter + "ಏನು ಮಾಡಬೇಕು?"
            
        return question
        
    def generate_myth_vs_fact(self, disaster_type: str) -> List[Dict]:
        """Generate Myth vs Fact Q&A pairs"""
        qa_pairs = []
        myths = DISASTER_MYTHS.get(disaster_type, [])
        disaster_kn = DISASTER_NAMES_KANNADA.get(disaster_type, disaster_type)
        
        for myth, fact in myths:
            # Myth question
            question_myth = f"{disaster_kn} ಸಮಯದಲ್ಲಿ {myth}?"
            answer_myth = f"ತಪ್ಪು. {disaster_kn} ಸಮಯದಲ್ಲಿ {myth} ಅಪಾಯಕಾರಿ. ಬದಲಾಗಿ {fact}."
            
            qa_pairs.append({
                "question": question_myth,
                "answer": answer_myth,
                "disaster_type": disaster_type,
                "category": "myth_vs_fact",
                "source_type": "fact_checked",
                "confidence": "high"
            })
            
            # Direct fact question
            question_fact = f"{disaster_kn} ವೇಳೆ {myth} ಸರಿಯೇ?"
            answer_fact = f"ಇಲ್ಲ, ಇದು ತಪ್ಪು. {fact}."
            
            qa_pairs.append({
                "question": question_fact,
                "answer": answer_fact,
                "disaster_type": disaster_type,
                "category": "myth_vs_fact",
                "source_type": "fact_checked",
                "confidence": "high"
            })
            
        return qa_pairs
        
    def generate_helpline_qa(self, disaster_type: str) -> List[Dict]:
        """Generate helpline-specific Q&A"""
        qa_pairs = []
        disaster_kn = DISASTER_NAMES_KANNADA.get(disaster_type, disaster_type)
        
        helplines = {
            "ರಾಷ್ಟ್ರೀಯ ತುರ್ತು ಸಂಖ್ಯೆ": "112",
            "ಪೊಲೀಸ್": "100",
            "ಅಗ್ನಿಶಾಮಕ": "101",
            "ಆಂಬುಲೆನ್ಸ್": "108",
            "ವಿಪತ್ತು ನಿರ್ವಹಣೆ": "1070",
            "NDMA": "011-26701728",
            "KSDMA": "080-22256023"
        }
        
        for name, number in helplines.items():
            question = f"{disaster_kn} ಸಮಯದಲ್ಲಿ {name} ಸಂಖ್ಯೆ ಏನು?"
            answer = f"{disaster_kn} ಸಮಯದಲ್ಲಿ {name} {number} ಗೆ ಕರೆ ಮಾಡಬಹುದು. ಈ ಸಂಖ್ಯೆ 24x7 ಲಭ್ಯವಿದೆ."
            
            qa_pairs.append({
                "question": question,
                "answer": answer,
                "disaster_type": disaster_type,
                "category": "helpline",
                "source_type": "official",
                "confidence": "high"
            })
            
        # Combined helpline question
        question_all = f"{disaster_kn} ಸಮಯದಲ್ಲಿ ಯಾವೆಲ್ಲಾ ಹೆಲ್ಪ್‌ಲೈನ್ ಸಂಖ್ಯೆಗಳು ಮುಖ್ಯ?"
        answer_all = f"{disaster_kn} ಸಮಯದಲ್ಲಿ: ತುರ್ತು ಸಹಾಯಕ್ಕೆ 112, ಅಗ್ನಿಶಾಮಕಕ್ಕೆ 101, ಆಂಬುಲೆನ್ಸ್‌ಗೆ 108, ವಿಪತ್ತು ನಿರ್ವಹಣೆಗೆ 1070. ಕರ್ನಾಟಕದಲ್ಲಿ KSDMA 080-22256023."
        
        qa_pairs.append({
            "question": question_all,
            "answer": answer_all,
            "disaster_type": disaster_type,
            "category": "helpline",
            "source_type": "official",
            "confidence": "high"
        })
        
        return qa_pairs
        
    def generate_short_queries(self, disaster_type: str) -> List[Dict]:
        """Generate short voice-style queries"""
        qa_pairs = []
        disaster_kn = DISASTER_NAMES_KANNADA.get(disaster_type, disaster_type)
        
        short_questions = [
            f"{disaster_kn} ಸಹಾಯ",
            f"{disaster_kn} ಏನು ಮಾಡಬೇಕು",
            f"{disaster_kn} ಹೆಲ್ಪ್‌ಲೈನ್",
            f"{disaster_kn} ರಕ್ಷಣೆ",
            f"{disaster_kn} ಸುರಕ್ಷತೆ",
            f"{disaster_kn} ತುರ್ತು",
            f"{disaster_kn} ಎಚ್ಚರಿಕೆ",
            f"{disaster_kn} ಮಾರ್ಗದರ್ಶನ",
            f"{disaster_kn} ಮುನ್ನೆಚ್ಚರಿಕೆ",
            f"{disaster_kn} ಪರಿಹಾರ"
        ]
        
        # Generate comprehensive short answer
        short_answer = f"{disaster_kn} ಸಮಯದಲ್ಲಿ: 1) ಶಾಂತವಾಗಿರಿ 2) 112 ಗೆ ಕರೆ ಮಾಡಿ 3) ಸುರಕ್ಷಿತ ಸ್ಥಳಕ್ಕೆ ಹೋಗಿ 4) ಸುದ್ದಿ ಅನುಸರಿಸಿ. ಹೆಚ್ಚಿನ ಮಾಹಿತಿಗಾಗಿ KSDMA ಸಂಪರ್ಕಿಸಿ."
        
        for question in short_questions:
            qa_pairs.append({
                "question": question,
                "answer": short_answer,
                "disaster_type": disaster_type,
                "category": "short_voice_query",
                "source_type": "synthesized",
                "confidence": "medium"
            })
            
        return qa_pairs
        
    def process_all_data(self):
        """Process all cleaned data and generate Q&A"""
        logger.info("=" * 60)
        logger.info("STARTING Q&A GENERATION")
        logger.info("=" * 60)
        
        # Load cleaned data
        cleaned_file = CLEANED_DATA_DIR / "all_cleaned_data.json"
        if not cleaned_file.exists():
            logger.error("No cleaned data found. Run cleaning pipeline first.")
            return []
            
        all_records = load_json(cleaned_file)
        logger.info(f"Loaded {len(all_records)} cleaned records")
        
        all_qa_pairs = []
        
        # Generate from text content
        for record in all_records:
            disaster_type = record.get("disaster_type", "general")
            text = record.get("cleaned_text", "")
            
            if not text or len(text) < 50:
                continue
                
            source_info = {
                "source_name": record.get("source_name", "unknown"),
                "source_url": record.get("source_url", "")
            }
            
            # Generate from actual text
            text_qa = self.generate_from_text(text, disaster_type, source_info)
            all_qa_pairs.extend(text_qa)
            
        logger.info(f"Generated {len(all_qa_pairs)} Q&A from text extraction")
        
        # Generate template-based Q&A for coverage
        for disaster_type in DISASTER_TYPES:
            logger.info(f"Generating template Q&A for {disaster_type}")
            
            for category in QA_CATEGORIES:
                if category == "myth_vs_fact":
                    qa_pairs = self.generate_myth_vs_fact(disaster_type)
                elif category == "helpline":
                    qa_pairs = self.generate_helpline_qa(disaster_type)
                elif category == "short_voice_query":
                    qa_pairs = self.generate_short_queries(disaster_type)
                else:
                    qa_pairs = self.generate_from_template(disaster_type, category)
                    
                all_qa_pairs.extend(qa_pairs)
                
        logger.info(f"Total Q&A pairs after templates: {len(all_qa_pairs)}")
        
        # Remove duplicates
        unique_qa = self._deduplicate_qa(all_qa_pairs)
        logger.info(f"After deduplication: {len(unique_qa)} unique Q&A pairs")
        
        # Balance categories if needed
        balanced_qa = self._balance_categories(unique_qa)
        
        # Save intermediate
        save_json(balanced_qa, QA_DATA_DIR / "qa_pairs_raw.json")
        
        return balanced_qa
        
    def _deduplicate_qa(self, qa_pairs: List[Dict]) -> List[Dict]:
        """Remove duplicate Q&A pairs"""
        seen_questions = set()
        unique_pairs = []
        
        for qa in qa_pairs:
            # Normalize question for comparison
            q_norm = ' '.join(qa["question"].lower().split())
            
            if q_norm not in seen_questions:
                seen_questions.add(q_norm)
                unique_pairs.append(qa)
                
        return unique_pairs
        
    def _balance_categories(self, qa_pairs: List[Dict]) -> List[Dict]:
        """Ensure reasonable distribution across categories"""
        category_groups = defaultdict(list)
        
        for qa in qa_pairs:
            category_groups[qa["category"]].append(qa)
            
        # Log distribution
        logger.info("Category distribution:")
        for cat, pairs in sorted(category_groups.items()):
            logger.info(f"  {cat}: {len(pairs)}")
            
        # If we have too few, generate more templates
        total = len(qa_pairs)
        if total < TARGET_QA_PAIRS:
            logger.info(f"Need {TARGET_QA_PAIRS - total} more Q&A pairs, generating additional...")
            
            additional = []
            for disaster_type in DISASTER_TYPES:
                for category in ["short_voice_query", "general_awareness"]:
                    if len(additional) >= (TARGET_QA_PAIRS - total):
                        break
                    more_qa = self.generate_from_template(disaster_type, category)
                    additional.extend(more_qa)
                    
            qa_pairs.extend(additional)
            qa_pairs = self._deduplicate_qa(qa_pairs)
            
        return qa_pairs
        
    def finalize_dataset(self, qa_pairs: List[Dict]):
        """Create final dataset in multiple formats"""
        logger.info("=" * 60)
        logger.info("FINALIZING DATASET")
        logger.info("=" * 60)
        
        # Ensure we have required fields
        final_records = []
        for qa in qa_pairs:
            record = {
                "question": qa.get("question", ""),
                "answer": qa.get("answer", ""),
                "disaster_type": qa.get("disaster_type", "general"),
                "category": qa.get("category", "general_awareness"),
                "source_name": qa.get("source_name", "synthesized"),
                "source_url": qa.get("source_url", ""),
                "confidence": qa.get("confidence", "medium"),
                "id": f"qa_{hash(qa['question']) % 10000000:08d}"
            }
            
            # Validate Kannada content
            if len(record["question"]) > 10 and len(record["answer"]) > 10:
                final_records.append(record)
                
        logger.info(f"Final validated records: {len(final_records)}")
        
        # Save as JSON
        json_path = FINAL_DATA_DIR / "kannada_disaster_qa_dataset.json"
        save_json(final_records, json_path)
        
        # Save as CSV
        try:
            import pandas as pd
            df = pd.DataFrame(final_records)
            csv_path = FINAL_DATA_DIR / "kannada_disaster_qa_dataset.csv"
            df.to_csv(csv_path, index=False, encoding='utf-8-sig')
            logger.info(f"Saved CSV with {len(df)} rows")
        except ImportError:
            logger.warning("pandas not available, CSV export skipped")
            
        # Generate statistics
        stats = self._generate_stats(final_records)
        save_json(stats, FINAL_DATA_DIR / "dataset_statistics.json")
        
        return final_records
        
    def _generate_stats(self, records: List[Dict]) -> Dict:
        """Generate dataset statistics"""
        from collections import Counter
        
        stats = {
            "total_records": len(records),
            "by_disaster_type": dict(Counter(r["disaster_type"] for r in records)),
            "by_category": dict(Counter(r["category"] for r in records)),
            "by_source": dict(Counter(r["source_name"] for r in records)),
            "avg_question_length": sum(len(r["question"]) for r in records) / len(records),
            "avg_answer_length": sum(len(r["answer"]) for r in records) / len(records),
        }
        
        logger.info("Dataset Statistics:")
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")
            
        return stats

def run_qa_generation_pipeline():
    """Execute Q&A generation pipeline"""
    generator = KannadaQAGenerator()
    
    # Generate Q&A pairs
    qa_pairs = generator.process_all_data()
    
    # Finalize and export
    final_data = generator.finalize_dataset(qa_pairs)
    
    logger.info("=" * 60)
    logger.info(f"Q&A GENERATION COMPLETE: {len(final_data)} pairs generated")
    logger.info("=" * 60)
    
    return final_data

if __name__ == "__main__":
    run_qa_generation_pipeline()