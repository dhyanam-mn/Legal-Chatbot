import os
import json
import logging
import re
import time
import hashlib
from pathlib import Path
from typing import Optional, Tuple, List, Dict

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor

from .config import DATA_DIR, HF_TOKEN, INDICTRANS2_MODEL_NAME

logger = logging.getLogger(__name__)

# Path to legal glossary JSON
GLOSSARY_PATH = DATA_DIR / "legal_glossary.json"

def load_legal_glossary() -> Dict[str, Dict[str, str]]:
    if GLOSSARY_PATH.exists():
        try:
            with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "hi" in data and "ta" in data:
                    return data
        except Exception as e:
            logger.error(f"Error loading legal_glossary.json: {e}")
    return {
        "hi": {
            "indemnity": "क्षतिपूर्ति",
            "indemnification": "क्षतिपूर्ति",
            "indemnify": "क्षतिपूर्ति करना",
            "arbitration": "मध्यस्थता",
            "jurisdiction": "क्षेत्राधिकार",
            "forum selection": "क्षेत्राधिकार चयन",
            "unilateral forum selection": "एकपक्षीय क्षेत्राधिकार चयन",
            "maintenance": "रखरखाव",
            "termination": "समाप्ति",
            "unilateral termination": "एकपक्षीय समाप्ति",
            "penalty": "शास्ति",
            "liquidated damages": "परिनिर्धारित क्षतिपूर्ति",
            "non-compete": "गैर-प्रतिस्पर्धा",
            "restraint of trade": "व्यापार पर प्रतिबंध",
            "terms": "शर्तें",
            "clause": "खंड"
        },
        "ta": {
            "indemnity": "இழப்பீட்டுப் பொறுப்பு",
            "indemnification": "இழப்பீட்டுப் பொறுப்பு",
            "indemnify": "இழப்பீடு வழங்குதல்",
            "arbitration": "இசைவுத்தீர்ப்பு",
            "jurisdiction": "அதிகார வரம்பு",
            "forum selection": "நீதிமன்றத் தேர்வு",
            "unilateral forum selection": "ஒருதலைப்பட்ச நீதிமன்றத் தேர்வு",
            "maintenance": "பராமரிப்பு",
            "termination": "ஒப்பந்த முடிவு",
            "unilateral termination": "ஒருதலைப்பட்ச ஒப்பந்த முடிவு",
            "penalty": "அபராதம்",
            "liquidated damages": "முன்நிர்ணயிக்கப்பட்ட இழப்பீடு",
            "non-compete": "போட்டித் தடை",
            "restraint of trade": "வணிகத் தடை",
            "terms": "விதிமுறைகள்",
            "clause": "பிரிவு"
        }
    }

LEGAL_GLOSSARY = load_legal_glossary()

# Language-aware variation replacements handling inflected forms, loose synonyms,
# and restoring Act names, Section/Article numbers, and Statute IDs to English
VARIATION_REPLACEMENTS_HI = {
    # Keep Act names untranslated in English
    r"भारतीय\s+(?:संविदा|अनुबंध|ठेका)\s+अधिनियम\s*,\s*1872|भारतीय\s+(?:संविदा|अनुबंध|ठेका)\s+अधिनियम\s+1872": "Indian Contract Act, 1872",
    r"भारतीय\s+(?:संविदा|अनुबंध|ठेका)\s+अधिनियम": "Indian Contract Act",
    r"भारत\s+के\s+संविधान|भारत\s+का\s+संविधान|भारतीय\s+संविधान": "Constitution of India",
    r"(?:माध्यस्थम्|मध्यस्थता|पंचनिर्णय)\s+(?:और|एवं|तथा)\s+सुलह\s+अधिनियम\s*,\s*1996|(?:माध्यस्थम्|मध्यस्थता|पंचनिर्णय)\s+(?:और|एवं|तथा)\s+सुलह\s+अधिनियम\s+1996": "Arbitration and Conciliation Act, 1996",
    r"(?:माध्यस्थम्|मध्यस्थता|पंचनिर्णय)\s+(?:और|एवं|तथा)\s+सुलह\s+अधिनियम": "Arbitration and Conciliation Act",
    r"उपभोक्ता\s+संरक्षण\s+अधिनियम\s*,\s*2019|उपभोक्ता\s+संरक्षण\s+अधिनियम\s+2019": "Consumer Protection Act, 2019",
    r"उपभोक्ता\s+संरक्षण\s+अधिनियम": "Consumer Protection Act",
    # Keep Statute IDs untranslated in English (including spaced Devanagari transliterations)
    r"(?:आई\.?\s*सी\.?\s*ए\.?|ica|ICA)\s*-\s*1872\s*-\s*(?:एस\.?|धारा|s|S)\s*-?\s*(\d+[A-Za-z]?)": r"ICA-1872-s\1",
    r"(?:सी\.?\s*ओ\.?\s*आई\.?|coi|COI)\s*-\s*(?:आर्ट\.?|अनुच्छेद|कला|ए\.?\s*आर\.?\s*टी\.?|art|ART)\s*-?\s*(\d+[A-Za-z]?)": r"COI-art\1",
    r"(?:ए\.?\s*सी\.?\s*ए\.?|aca|ACA)\s*-\s*1996\s*-\s*(?:एस\.?|धारा|s|S)\s*-?\s*(\d+[A-Za-z]?)": r"ACA-1996-s\1",
    r"(?:सी\.?\s*पी\.?\s*ए\.?|cpa|CPA)\s*-\s*2019\s*-\s*(?:एस\.?|धारा|s|S)\s*-?\s*(\d+[A-Za-z]?)": r"CPA-2019-s\1",
    # Keep Section and Article numbers untranslated in English (must run BEFORE धारा -> खंड)
    r"धाराओं\s+(\d+[A-Za-z0-9\(\)\-]*)": r"Sections \1",
    r"धारा\s+(\d+[A-Za-z0-9\(\)\-]*)": r"Section \1",
    r"अनुच्छेदों\s+(\d+[A-Za-z0-9\(\)\-]*)": r"Articles \1",
    # Keep Exception wording untranslated in English
    r"अपवाद\s+(\d+)": r"Exception \1",
    r"अपवादों\s+(\d+)": r"Exceptions \1",
    r"अपवाद": "Exception",
    # Never allow बचत / बचतें in statutory context
    r"अनुबंध\s+की\s+बचत|ठेके\s+की\s+बचत|संविदा\s+की\s+बचत": "समझौतों का संरक्षण",
    r"\bबचत\b": "संरक्षण",
    # Legal glossary terms
    r"हर्जाने|हर्जाना": "क्षतिपूर्ति",
    r"नुकसान\s+की\s+भरपाई|नुकसान\s+भरपाई|प्रतिपूर्ति": "क्षतिपूर्ति",
    r"मुआवजे|मुआवजा": "क्षतिपूर्ति",
    r"पंच\s+निर्णय|पंचनिर्णय|निजी\s+मध्यस्थ(?=\s+के\s+माध्यम)": "मध्यस्थता",
    r"न्यायाधिकार\s+क्षेत्र|न्यायाधिकार": "क्षेत्राधिकार",
    r"अदालती\s+क्षेत्र|मंच(?=\s+और\s+निर्णय)": "क्षेत्राधिकार",
    r"परिसमापन\s+किए\s+गए\s+नुकसान|परिसमापन\s+नुकसान": "परिनिर्धारित क्षतिपूर्ति",
    r"दण्डित|दंडित": "शास्ति के अधीन",
    r"दण्डात्मक|दंडात्मक": "शास्ति संबंधी",
    r"दण्डों|दंडों|दण्ड|दंड\b": "शास्ति",
    r"जुर्माने|जुर्माना": "शास्ति",
    r"अनुबंध\s+की\s+समाप्ति": "समाप्ति",
    r"करार\s+रद्द\s+करना|रद्दीकरण": "समाप्ति",
    r"प्रतिस्पर्धा-विरोधी|गैर-प्रतिस्पर्धी|गैर\s+प्रतिस्पर्धी": "गैर-प्रतिस्पर्धा",
    r"व्यापार\s+का\s+एक\s+चरम,\s+एकतरफा\s+संयम": "एक चरम, एकतरफा व्यापार पर प्रतिबंध (गैर-प्रतिस्पर्धा)",
    r"व्यापार\s+का\s+संयम|व्यापार\s+रोक": "व्यापार पर प्रतिबंध",
    r"अमान्य|बातिल": "शून्य",
    r"क्लॉज|धारा(?!\s*\d)": "खंड",
    r"खंड\s+(\d+[A-Za-z0-9\(\)\-]*)": r"Section \1",
    r"नियमों|शब्दों(?=\s+से\s+मिलता)": "शर्तों",
}

VARIATION_REPLACEMENTS_TA = {
    # Keep Act names untranslated in English
    r"இந்திய\s+ஒப்பந்தச்?\s+சட்டம்\s*,\s*1872|இந்திய\s+ஒப்பந்தச்?\s+சட்டம்\s+1872": "Indian Contract Act, 1872",
    r"இந்திய\s+ஒப்பந்தச்?\s+சட்டம்": "Indian Contract Act",
    r"இந்திய\s+அரசியலமைப்பு(?:ச்?\s*சட்டம்|ின்|ற்கு|க்கு|இல்)?|இந்தியாவின்\s+அரசியலமைப்பு(?:ச்?\s*சட்டம்|ின்|ற்கு|க்கு|இல்)?": "Constitution of India",
    r"(?:இசைவுத்தீர்ப்பு|மத்தியஸ்தம்|நடுவர்)\s+மற்றும்\s+சமரசச்?\s+சட்டம்\s*,\s*1996|(?:இசைவுத்தீர்ப்பு|மத்தியஸ்தம்|நடுவர்)\s+மற்றும்\s+சமரசச்?\s+சட்டம்\s+1996": "Arbitration and Conciliation Act, 1996",
    r"(?:இசைவுத்தீர்ப்பு|மத்தியஸ்தம்|நடுவர்)\s+மற்றும்\s+சமரசச்?\s+சட்டம்": "Arbitration and Conciliation Act",
    r"நுகர்வோர்\s+பாதுகாப்புச்?\s+சட்டம்\s*,\s*2019|நுகர்வோர்\s+பாதுகாப்புச்?\s+சட்டம்\s+2019": "Consumer Protection Act, 2019",
    r"நுகர்வோர்\s+பாதுகாப்புச்?\s+சட்டம்": "Consumer Protection Act",
    # Keep Statute IDs untranslated in English (including Tamil transliterations)
    r"(?:ஐ\.?\s*சி\.?\s*ஏ\.?|ica|ICA)\s*-\s*1872\s*-\s*(?:எஸ்\.?|பிரிவு|s|S)\s*-?\s*(\d+[A-Za-z]?)": r"ICA-1872-s\1",
    r"(?:சி\.?\s*ஓ\.?\s*ஐ\.?|coi|COI)\s*-\s*(?:ஆர்ட்\.?|கலை|சரத்து|பிரிவு|art|ART)\s*-?\s*(\d+[A-Za-z]?)": r"COI-art\1",
    r"(?:ஏ\.?\s*சி\.?\s*ஏ\.?|aca|ACA)\s*-\s*1996\s*-\s*(?:எஸ்\.?|பிரிவு|s|S)\s*-?\s*(\d+[A-Za-z]?)": r"ACA-1996-s\1",
    r"(?:சி\.?\s*பி\.?\s*ஏ\.?|cpa|CPA)\s*-\s*2019\s*-\s*(?:எஸ்\.?|பிரிவு|s|S)\s*-?\s*(\d+[A-Za-z]?)": r"CPA-2019-s\1",

    # Keep Section and Article numbers untranslated in English
    r"(?:சரத்து|உறுப்பு)\s+(\d+[A-Za-z0-9\(\)\-]*)": r"Article \1",
    r"(\d+[A-Za-z0-9\(\)\-]*)\s*[-]?\s*வது\s*(?:சரத்து|உறுப்பு)": r"Article \1",
    r"(?:பிரிவு|ஷரத்து)\s+(\d+[A-Za-z0-9\(\)\-]*)": r"Section \1",
    r"(\d+[A-Za-z0-9\(\)\-]*)\s*[-]?\s*வது\s*(?:பிரிவு|ஷரத்து)": r"Section \1",
    # Keep Exception wording untranslated in English
    r"(?:விதிவிலக்கு|விதிவிலக்காக|விலக்கு)\s+(\d+)": r"Exception \1",
    r"(\d+)\s*[-]?\s*வது\s*(?:விதிவிலக்கு|விதிவிலக்காக|விலக்கு)": r"Exception \1",
    r"விதிவிலக்குகள்\s+(\d+)": r"Exceptions \1",
    r"விதிவிலக்கு|விதிவிலக்காக|விலக்கு": "Exception",
    # Never allow சேமிப்பு in statutory context
    r"ஒப்பந்தத்தின்\s+சேமிப்பு|ஒப்பந்தச்?\s+சேமிப்பு": "ஒப்பந்தப் பாதுகாப்பு",
    r"\bசேமிப்பு\b": "பாதுகாப்பு",
    # Liquidated damages MUST run before termination/damages rules
    r"முடிவு\s+செய்யப்பட்ட\s+சேதங்கள்|ஒப்பந்த\s+முடிவு\s+செய்யப்பட்ட\s+சேதங்கள்|கலைக்கப்பட்ட\s+சேதங்கள்|நிர்ணயிக்கப்பட்ட\s+நஷ்டஈடு|கணக்கிடப்பட்ட\s+இழப்பீடு": "முன்நிர்ணயிக்கப்பட்ட இழப்பீடு",
    # Indemnity & inflected forms (including reimburse / financial liability in indemnity context)
    r"நஷ்டஈடு|நட்டஈடு": "இழப்பீட்டுப் பொறுப்பு",
    r"திருப்பிச்\s+செலுத்த\s+வேண்டும்": "இழப்பீடு வழங்க வேண்டும் (இழப்பீட்டுப் பொறுப்பு)",
    r"பிரிவினை\s+இழப்பீடும்|பிரிவினை\s+இழப்பீடு": "பிரிவு இழப்பீட்டுத் தொகையும்",
    r"இழப்பீடு(?=\s+பிரிவு|\s+வாசகம்)": "இழப்பீட்டுப் பொறுப்பு",
    r"இழப்பீட்டு(?=\s+பிரிவு|\s+வாசகம்)": "இழப்பீட்டுப் பொறுப்பு",
    # Arbitration & inflected forms (including arbitrator -> இசைவுத்தீர்ப்பு நடுவர்)
    r"மத்தியஸ்தம்|மத்தியஸ்த|நடுவர்\s+தீர்ப்பு": "இசைவுத்தீர்ப்பு",
    r"தனியார்\s+நடுவர்": "தனியார் இசைவுத்தீர்ப்பு நடுவர்",
    # Jurisdiction / Forum selection & inflected forms
    r"ஆள்வரை|அதிகார\s+எல்லை|நீதிவரம்பு": "அதிகார வரம்பு",
    r"(?<!நீதி)மன்றத்தையும்": "அதிகார வரம்பு கொண்ட நீதிமன்றத்தையும்",
    r"(?<!நீதி)மன்றத்தை(?!யும்)": "அதிகார வரம்பு கொண்ட நீதிமன்றத்தை",
    # Maintenance & inflected forms
    r"பழுதுபார்ப்பு\s+செலவு": "பராமரிப்பு",
    # Termination & inflected forms
    r"பணிநீக்கம்|பணிநீக்க\b": "ஒப்பந்த முடிவு",
    r"வேலையை\s+உடனடியாக\s+நிறுத்த": "வேலையை உடனடியாக ஒப்பந்த முடிவு செய்ய",
    r"குத்தகைக்கு\s+முடிவடையவும்": "குத்தகையை ஒப்பந்த முடிவு செய்யவும்",
    r"முடிவுக்கு\s+பிந்தைய": "ஒப்பந்த முடிவுக்குப் பிந்தைய",
    r"முடிவுத்துடன்": "ஒப்பந்த முடிவுடன்",
    r"ரத்து\s+செய்தல்|முடிவுறுத்தல்|முடிவுக்குக்\s+கொண்டுவருதல்": "ஒப்பந்த முடிவு",
    r"(?<!ஒப்பந்த\s)முடிவு(?=\s+பிரிவு|\s+செய்ய)": "ஒப்பந்த முடிவு",
    # Penalty & inflected forms (avoiding mid-word replacement inside தண்டனைக்குரிய)
    r"தண்டனைக்குரிய\s+நிதி\s+அபராதத்தை": "அபராதத்தை",
    r"தண்டனைக்குரிய": "அபராத",
    r"தண்டிக்கப்படலாம்|தண்டிக்க\b": "அபராதம் விதிக்க",
    r"தண்டனையாக": "அபராதமாக",
    r"தண்டனை\b": "அபராதம்",
    r"அபராதத்தையும்": "அபராதம் தொகையையும்",
    r"அபராதத்தை\b": "அபராதம் தொகையை",
    r"அபராதத்\s+தொகை": "அபராதம்",
    # Non-compete & inflected forms
    r"போட்டியிடாமை|போட்டி\s+போடாத|போட்டியிடக்\s+கூடாது\s+என்ற|போட்டி\s+அல்லாத": "போட்டித் தடை",
    r"வர்த்தகத்தின்\s+தீவிரமான,\s+ஒருதலைப்பட்ச\s+கட்டுப்பாட்டை": "தீவிரமான, ஒருதலைப்பட்ச வணிகத் தடையை (போட்டித் தடை)",
    r"தொழில்நுட்ப\s+வணிகத்தையும்\s+தொடங்குவதையோ": "தொழில்நுட்ப வணிகத்திலும் போட்டித் தடை மீறி ஈடுபடுவதையோ",
    r"வெற்றிட(?=\s+ஒப்பந்த)": "செல்லாத",
    # Terms & Clause inflected forms
    r"இந்த\s+விதியின்\s+படி": "இந்தப் பிரிவின் படி",
    r"இந்த\s+விதி\b": "இந்தப் பிரிவு",
    r"உட்பிரிவில்": "பிரிவில்",
    r"வாசகம்|ஷரத்து(?!\s*\d)|உட்பிரிவு": "பிரிவு",
    r"பிரிவு\s+(\d+[A-Za-z0-9\(\)\-]*)": r"Section \1",
    r"விதிகளை": "விதிமுறைகளை",
    r"விதிகள்": "விதிமுறைகள்",
    r"சொற்களை|வார்த்தைகளை|நிபந்தனைகளை": "விதிமுறைகளை",
    r"சொற்கள்|வார்த்தைகள்|நிபந்தனைகள்": "விதிமுறைகள்",
}



def _preserve_english_statutes(orig_text: str, translated_text: str) -> str:
    """
    Ensures that any statute IDs (e.g., ICA-1872-s27, COI-art19), Section/Article numbers,
    and Act names present in orig_text remain untranslated in English in translated_text.
    """
    if not orig_text or not translated_text:
        return translated_text

    res = translated_text

    # If original had 'Article <num>', ensure variations in Tamil/Hindi are restored to 'Article <num>'
    for art_match in re.finditer(r"\b(Articles?\s+\d+[A-Za-z0-9\(\)\-]*)", orig_text):
        art_str = art_match.group(1)
        num_part = re.sub(r"^Articles?\s+", "", art_str)
        res = re.sub(rf"\bSections?\s+{re.escape(num_part)}\b", art_str, res)
        res = re.sub(rf"{re.escape(num_part)}\s*[-]?\s*வது\s*(?:பிரிவு|சரத்து|உறுப்பு|ஷரத்து)", art_str, res)
        res = re.sub(rf"(?:சரத்து|உறுப்பு|பிரிவு|ஷரத்து)\s+{re.escape(num_part)}", art_str, res)
        res = re.sub(rf"अनुच्छेद\s+{re.escape(num_part)}", art_str, res)

    for sec_match in re.finditer(r"\b(Sections?\s+\d+[A-Za-z0-9\(\)\-]*)", orig_text):
        sec_str = sec_match.group(1)
        num_part = re.sub(r"^Sections?\s+", "", sec_str)
        res = re.sub(rf"{re.escape(num_part)}\s*[-]?\s*வது\s*(?:பிரிவு|சரத்து|உறுப்பு|ஷரத்து)", sec_str, res)
        res = re.sub(rf"(?:பிரிவு|ஷரத்து)\s+{re.escape(num_part)}", sec_str, res)
        res = re.sub(rf"धारा\s+{re.escape(num_part)}", sec_str, res)

    for exc_match in re.finditer(r"\b(Exceptions?\s+\d+[A-Za-z0-9\(\)\-]*)", orig_text):
        exc_str = exc_match.group(1)
        num_part = re.sub(r"^Exceptions?\s+", "", exc_str)
        res = re.sub(rf"{re.escape(num_part)}\s*[-]?\s*வது\s*(?:விதிவிலக்கு|விதிவிலக்காக|விலக்கு|अपवाद)", exc_str, res)
        res = re.sub(rf"(?:விதிவிலக்கு|விதிவிலக்காக|விலக்கு|अपवाद)\s+{re.escape(num_part)}", exc_str, res)

    if re.search(r"\bExceptions?\b", orig_text) and not re.search(r"\bExceptions?\b", res):
        res = re.sub(r"\b(?:விதிவிலக்கு|விதிவிலக்காக|விலக்கு|अपवाद)\b", "Exception", res)

    # Ensure Act names with years match original if year was present in original
    act_years = [
        ("Indian Contract Act, 1872", r"Indian Contract Act(?!\s*,\s*1872|\s+1872)"),
        ("Arbitration and Conciliation Act, 1996", r"Arbitration and Conciliation Act(?!\s*,\s*1996|\s+1996)"),
        ("Consumer Protection Act, 2019", r"Consumer Protection Act(?!\s*,\s*2019|\s+2019)"),
    ]
    for full_act, bare_pattern in act_years:
        if full_act in orig_text or full_act.replace(",", "") in orig_text:
            res = re.sub(bare_pattern, full_act, res)

    if "Constitution of India" in orig_text and "Constitution of India" not in res:
        res = re.sub(r"இந்திய\s+அரசியலமைப்பு[^\s,\.]*|இந்தியாவின்\s+அரசியலமைப்பு[^\s,\.]*", "Constitution of India", res)
        res = re.sub(r"भारत\s+(?:के|का|की)\s+संविधान|भारतीय\s+संविधान", "Constitution of India", res)
        if "Constitution of India" not in res:
            res = f"Constitution of India, {res}"

    # Ensure every statute ID present in orig_text appears verbatim in English in res
    statute_ids = re.findall(
        r"\b(?:ICA-\d{4}-s\d+[A-Za-z]?|COI-art\d+[A-Za-z]?|ACA-\d{4}-s\d+[A-Za-z]?|CPA-\d{4}-s\d+[A-Za-z]?)\b",
        orig_text
    )
    for sid in statute_ids:
        if sid not in res:
            res = f"[{sid}] {res}"

    return res


def enforce_glossary(text: str, lang: str = "hi", orig_text: Optional[str] = None) -> str:
    """
    Language-aware post-processor ('hi' or 'ta') that replaces loose/colloquial
    or inflected term translations with the exact standard legal glossary terms,
    and preserves statute IDs, section numbers, and Act names in English.
    """
    if not text:
        return text

    result = text
    replacements = VARIATION_REPLACEMENTS_TA if lang in ("ta", "tam_Taml") else VARIATION_REPLACEMENTS_HI
    for variation_pattern, fixed_term in replacements.items():
        result = re.sub(variation_pattern, fixed_term, result)

    if orig_text:
        result = _preserve_english_statutes(orig_text, result)

    return result



# In-memory translation cache keyed by (sha256_text_hash, tgt_lang)
_TRANSLATION_CACHE: Dict[Tuple[str, str], str] = {}

def _get_text_hash(text: str) -> str:
    return hashlib.sha256(text.strip().encode("utf-8")).hexdigest()


class IndicTrans2Engine:
    """
    Singleton wrapper for local IndicTrans2 (ai4bharat/indictrans2-en-indic-dist-200M)
    loaded once at startup on CPU (or CUDA if available).
    Supports both Hindi ('hin_Deva') and Tamil ('tam_Taml') with batching, num_beams=2,
    and caching keyed by (text_hash, language). Makes ZERO Gemini API calls.
    """
    def __init__(self, model_name: str = INDICTRANS2_MODEL_NAME):
        self.model_name = model_name
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        masked_token = "hf_****" if HF_TOKEN else "None"
        logger.info(f"Loading IndicTrans2 model '{self.model_name}' on device '{self.device}' (token={masked_token})...")
        t0 = time.time()
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            token=HF_TOKEN if HF_TOKEN else None
        )
        self.model = AutoModelForSeq2SeqLM.from_pretrained(
            self.model_name,
            trust_remote_code=True,
            token=HF_TOKEN if HF_TOKEN else None
        ).to(self.device)
        self.model.eval()
        self.processor = IndicProcessor(inference=True)
        self.load_time_sec = time.time() - t0
        logger.info(
            f"IndicTrans2 model '{self.model_name}' loaded successfully on device='{self.device}' in {self.load_time_sec:.2f}s."
        )

    def translate_batch(
        self,
        texts: List[str],
        src_lang: str = "eng_Latn",
        tgt_lang: str = "hin_Deva",
        num_beams: int = 2
    ) -> List[str]:
        if not texts:
            return []

        short_lang = "ta" if tgt_lang == "tam_Taml" else "hi"
        results = ["" for _ in texts]
        uncached_indices: List[int] = []
        uncached_texts: List[str] = []

        for i, t in enumerate(texts):
            if not t or not t.strip():
                continue
            cleaned = t.strip()
            cache_key = (_get_text_hash(cleaned), tgt_lang)
            if cache_key in _TRANSLATION_CACHE:
                results[i] = _TRANSLATION_CACHE[cache_key]
            else:
                uncached_indices.append(i)
                uncached_texts.append(cleaned)

        if uncached_texts:
            batch = self.processor.preprocess_batch(uncached_texts, src_lang=src_lang, tgt_lang=tgt_lang)
            inputs = self.tokenizer(
                batch,
                truncation=True,
                padding="longest",
                return_tensors="pt",
                return_attention_mask=True
            ).to(self.device)

            with torch.no_grad():
                generated_tokens = self.model.generate(
                    **inputs,
                    use_cache=True,
                    min_length=0,
                    max_length=256,
                    num_beams=num_beams,
                    num_return_sequences=1
                )

            decoded = self.tokenizer.batch_decode(
                generated_tokens,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=True
            )
            postprocessed = self.processor.postprocess_batch(decoded, lang=tgt_lang)

            for idx, orig_text, trans in zip(uncached_indices, uncached_texts, postprocessed):
                final_trans = enforce_glossary(trans, lang=short_lang, orig_text=orig_text)
                cache_key = (_get_text_hash(orig_text), tgt_lang)
                _TRANSLATION_CACHE[cache_key] = final_trans
                results[idx] = final_trans

        return results


# Load once at startup when module is imported
_translator_engine: Optional[IndicTrans2Engine] = None

def get_translator_engine() -> IndicTrans2Engine:
    global _translator_engine
    if _translator_engine is None:
        _translator_engine = IndicTrans2Engine()
    return _translator_engine

# Eagerly initialize at startup
_translator_engine = get_translator_engine()


def translate_clause_analysis_multilingual(explanation: str, risk_reason: str) -> Tuple[str, str, str, str]:
    """
    Translates English explanation and risk_reason into BOTH Hindi ('hin_Deva') and Tamil ('tam_Taml')
    using the single loaded IndicTrans2 model with batching, num_beams=2, caching, and enforce_glossary().
    Returns: (explanation_hi, risk_reason_hi, explanation_ta, risk_reason_ta)
    Makes ZERO Gemini API calls.
    """
    if not explanation and not risk_reason:
        return "", "", "", ""

    engine = get_translator_engine()
    batch_inputs = [explanation or "", risk_reason or ""]

    t0 = time.time()
    hi_out = engine.translate_batch(batch_inputs, src_lang="eng_Latn", tgt_lang="hin_Deva", num_beams=2)
    ta_out = engine.translate_batch(batch_inputs, src_lang="eng_Latn", tgt_lang="tam_Taml", num_beams=2)
    elapsed = time.time() - t0
    logger.info(f"IndicTrans2 translated clause into HI & TA on {engine.device} in {elapsed:.2f}s (num_beams=2).")
    return hi_out[0], hi_out[1], ta_out[0], ta_out[1]


def translate_texts_multilingual(texts: List[str]) -> Tuple[List[str], List[str]]:
    """
    Translates a batch of English strings (e.g., statutory citation reasons) into BOTH Hindi and Tamil
    via local IndicTrans2 while keeping statute IDs, section numbers, and Act names untranslated in English.
    """
    if not texts:
        return [], []
    engine = get_translator_engine()
    hi_out = engine.translate_batch(texts, src_lang="eng_Latn", tgt_lang="hin_Deva", num_beams=2)
    ta_out = engine.translate_batch(texts, src_lang="eng_Latn", tgt_lang="tam_Taml", num_beams=2)
    return hi_out, ta_out


def translate_clause_analysis_to_hindi(explanation: str, risk_reason: str) -> Tuple[str, str]:
    """Translates English explanation and risk reason into Hindi using local IndicTrans2."""
    if not explanation and not risk_reason:
        return "", ""
    engine = get_translator_engine()
    hi_out = engine.translate_batch([explanation or "", risk_reason or ""], src_lang="eng_Latn", tgt_lang="hin_Deva", num_beams=2)
    return hi_out[0], hi_out[1]


def translate_clause_analysis_to_tamil(explanation: str, risk_reason: str) -> Tuple[str, str]:
    """Translates English explanation and risk reason into Tamil using local IndicTrans2."""
    if not explanation and not risk_reason:
        return "", ""
    engine = get_translator_engine()
    ta_out = engine.translate_batch([explanation or "", risk_reason or ""], src_lang="eng_Latn", tgt_lang="tam_Taml", num_beams=2)
    return ta_out[0], ta_out[1]


def translate_text_to_hindi(text: str) -> str:
    """Translates a single English text string to Hindi using local IndicTrans2 + enforce_glossary."""
    if not text or not text.strip():
        return ""
    engine = get_translator_engine()
    translated = engine.translate_batch([text], src_lang="eng_Latn", tgt_lang="hin_Deva", num_beams=2)
    return translated[0]


def translate_text_to_tamil(text: str) -> str:
    """Translates a single English text string to Tamil using local IndicTrans2 + enforce_glossary."""
    if not text or not text.strip():
        return ""
    engine = get_translator_engine()
    translated = engine.translate_batch([text], src_lang="eng_Latn", tgt_lang="tam_Taml", num_beams=2)
    return translated[0]

