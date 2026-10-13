import os
import logging
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

logger = logging.getLogger(__name__)

# Search for .env dynamically in current working dir or project parent dirs
dotenv_file = find_dotenv(usecwd=True)
if dotenv_file:
    load_dotenv(dotenv_path=dotenv_file)
    logger.info(f"Loaded environment variables from: {dotenv_file}")
else:
    load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CHROMA_PERSIST_DIR = BASE_DIR / "chroma_db"

GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
HF_TOKEN = (os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN") or "").strip()
EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5")
INDICTRANS2_MODEL_NAME = os.getenv("INDICTRANS2_MODEL_NAME", "ai4bharat/indictrans2-en-indic-dist-200M")
ALLOW_HEURISTIC_FALLBACK = os.getenv("ALLOW_HEURISTIC_FALLBACK", "false").lower() in ("true", "1", "yes")

# Ordered list of Gemini models for quota rotation (never falls back to heuristic classifier)
GEMINI_MODELS = [
    m.strip()
    for m in os.getenv(
        "GEMINI_MODELS",
        "gemini-3.8-flash,gemini-3.7-flash,gemini-3.5-flash,gemini-3.6-flash,gemini-3.5-flash-lite,gemini-3.1-flash-lite",
    ).split(",")
    if m.strip()
]


# Mandatory legal disclaimer strings required by specification (English, Hindi, and Tamil)
MANDATORY_DISCLAIMER = "This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this."
MANDATORY_DISCLAIMER_HI = "यह क्लॉज के अर्थ की व्याख्या करता है। यह कानूनी सलाह नहीं है। इस पर कार्रवाई करने से पहले वकील से परामर्श लें।"
MANDATORY_DISCLAIMER_TA = "இது இந்தப் பிரிவின் பொருளை விளக்குகிறது. இது சட்ட ஆலோசனை அல்ல. இதன் அடிப்படையில் செயல்படுவதற்கு முன் ஒரு வழக்கறிஞரைக் கலந்தாலோசிக்கவும்."


# Fail-loud check at startup unless explicitly opted into heuristic dev mode
if not GEMINI_API_KEY and not ALLOW_HEURISTIC_FALLBACK:
    raise RuntimeError(
        "CRITICAL ERROR: GEMINI_API_KEY is not set in environment or .env file! "
        "The application cannot start without a valid Gemini API key. "
        "To enable offline development heuristic fallback, set ALLOW_HEURISTIC_FALLBACK=true in .env."
    )
elif GEMINI_API_KEY:
    logger.info("GEMINI_API_KEY successfully configured.")
else:
    logger.warning("ALLOW_HEURISTIC_FALLBACK=true is active. Running in offline dev heuristic mode.")
