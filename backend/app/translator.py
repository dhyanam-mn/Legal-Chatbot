import os
import json
import logging
import re
import time
from pathlib import Path
from typing import Optional, Tuple, List

import torch
from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
from IndicTransToolkit.processor import IndicProcessor

from .config import DATA_DIR, HF_TOKEN, INDICTRANS2_MODEL_NAME

logger = logging.getLogger(__name__)

# Path to legal glossary JSON
GLOSSARY_PATH = DATA_DIR / "legal_glossary.json"

def load_legal_glossary() -> dict:
    if GLOSSARY_PATH.exists():
        try:
            with open(GLOSSARY_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading legal_glossary.json: {e}")
    return {
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
        "restraint of trade": "व्यापार पर प्रतिबंध"
    }

LEGAL_GLOSSARY = load_legal_glossary()

# Mapping of potential loose/varied Hindi translations to forced exact glossary terms
VARIATION_REPLACEMENTS = {
    r"हर्जाना": "क्षतिपूर्ति",
    r"नुकसान भरपाई": "क्षतिपूर्ति",
    r"मुआवजा": "क्षतिपूर्ति",
    r"पंच निर्णय": "मध्यस्थता",
    r"न्यायाधिकार": "क्षेत्राधिकार",
    r"अदालती क्षेत्र": "क्षेत्राधिकार",
    r"दण्ड": "शास्ति",
    r"दंडित": "शास्ति के अधीन",
    r"दंड": "शास्ति",
    r"जुर्माना": "शास्ति",
    r"अनुबंध की समाप्ति": "समाप्ति",
    r"करार रद्द करना": "समाप्ति",
    r"प्रतिस्पर्धा-विरोधी": "गैर-प्रतिस्पर्धा",
    r"गैर-प्रतिस्पर्धी": "गैर-प्रतिस्पर्धा",
    r"व्यापार रोक": "गैर-प्रतिस्पर्धा",
}

def enforce_glossary(hindi_text: str) -> str:
    """
    Post-processes translated Hindi text to replace inconsistent term translations
    with the exact legal glossary terms.
    """
    if not hindi_text:
        return hindi_text

    result = hindi_text
    for variation_pattern, fixed_term in VARIATION_REPLACEMENTS.items():
        result = re.sub(variation_pattern, fixed_term, result)

    return result


class IndicTrans2Engine:
    """
    Singleton wrapper for local IndicTrans2 (ai4bharat/indictrans2-en-indic-dist-200M)
    loaded once at startup on CPU (or CUDA if available).
    Makes ZERO Gemini API calls.
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

    def translate_batch(self, texts: List[str], src_lang: str = "eng_Latn", tgt_lang: str = "hin_Deva") -> List[str]:
        if not texts:
            return []
        non_empty_indices = [i for i, t in enumerate(texts) if t and t.strip()]
        if not non_empty_indices:
            return ["" for _ in texts]

        valid_texts = [texts[i].strip() for i in non_empty_indices]
        batch = self.processor.preprocess_batch(valid_texts, src_lang=src_lang, tgt_lang=tgt_lang)
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
                num_beams=5,
                num_return_sequences=1
            )

        decoded = self.tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True
        )
        postprocessed = self.processor.postprocess_batch(decoded, lang=tgt_lang)

        results = ["" for _ in texts]
        for idx, trans in zip(non_empty_indices, postprocessed):
            results[idx] = enforce_glossary(trans)
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


def translate_clause_analysis_to_hindi(explanation: str, risk_reason: str) -> Tuple[str, str]:
    """
    Translates English explanation and risk reason into Hindi using local IndicTrans2
    inference in a single batch, then enforces fixed legal glossary terms.
    Zero Gemini API calls are made here.
    """
    if not explanation and not risk_reason:
        return "", ""

    engine = get_translator_engine()
    t0 = time.time()
    translated = engine.translate_batch([explanation or "", risk_reason or ""], src_lang="eng_Latn", tgt_lang="hin_Deva")
    elapsed = time.time() - t0
    logger.info(f"IndicTrans2 translated clause (explanation + risk_reason) on {engine.device} in {elapsed:.2f}s.")
    return translated[0], translated[1]


def translate_text_to_hindi(text: str) -> str:
    """Translates a single English text string to Hindi using local IndicTrans2 + enforce_glossary."""
    if not text or not text.strip():
        return ""
    engine = get_translator_engine()
    t0 = time.time()
    translated = engine.translate_batch([text], src_lang="eng_Latn", tgt_lang="hin_Deva")
    elapsed = time.time() - t0
    logger.info(f"IndicTrans2 translated single text on {engine.device} in {elapsed:.2f}s.")
    return translated[0]
