# Legal Document Chatbot

A multilingual AI-assisted legal document analysis system that inspects contracts, identifies one-sided or high-risk clauses, retrieves verified statutory provisions from Indian law, translates explanations and risk rationales into Hindi and Tamil using a local IndicTrans2 model, and provides grounded chat assistance.

---

## Architecture Overview

1. **Document Parsing & Clause Segmentation**:
   - PDF parsing via `pdfplumber` (with OCR fallback capability).
   - Strict structural clause boundary segmentation preserving sentence grammar (e.g. `WHEREAS` handling).
2. **Grounding & Retrieval-Augmented Generation (RAG)**:
   - Vector store powered by ChromaDB with `BAAI/bge-small-en-v1.5` embeddings.
   - Separate ChromaDB collection `legal_statutes` storing verified statutory provisions (1 provision = 1 chunk).
   - Deterministic clause-to-statute mapping to bias retrieval for high-risk clause types.
3. **Statutory Citations**:
   - Pinned strictly to the strongest configured Gemini model (`gemini-3.8-flash`).
   - Generates single-sentence descriptive reasons and attaches verbatim statutory provision text in English.
   - Falls back safely to `"Legal basis unavailable right now"` if the strongest model is unavailable (rotation to lite models is prohibited).
   - Closed-world citation validation: drops and logs any hallucination attempts (no case law or outside sections).
4. **Multilingual Translation Layer**:
   - Local `ai4bharat/indictrans2-en-indic-dist-200M` model runs completely on CPU/CUDA with **zero Gemini API calls**.
   - Language-aware legal glossary enforcement (`hi` and `ta`) preserving statutory identifiers, Section numbers, and Act names in English.
5. **Interactive UI**:
   - React + Tailwind CSS interface with trilingual toggle (**English | हिंदी | தமிழ்**), collapsible "Legal basis" (with verbatim statutory text) and "Typical phrasing" panels, and client intake context personalization.

---

## Known Limitations

1. **Statute Ingestion & Provenance Verification**:
   - Only statutory texts matching official government sources (`indiacode.nic.in` / `legislative.gov.in`) with 100% exact provenance are admitted into `data/statutes/`.
   - Automated fetching from `indiacode.nic.in` is susceptible to `HTTP 504 Gateway Timeout` due to government server rate-limiting/firewalls. In such cases, official PDFs must be manually downloaded and placed in `data/statutes_raw/` (`arbitration_and_conciliation_act_1996.pdf` and `consumer_protection_act_2019.pdf`) for local verification.
2. **Citation Model Pinning & API Free-Tier Quota**:
   - Citation generation requires deep statutory reasoning and is strictly pinned to the strongest Gemini model (`gemini-3.8-flash`). Under Google's free-tier rate limits (20 requests per day per model), if the strongest model's daily quota is exhausted, citation generation safely returns `"Legal basis unavailable right now"` rather than guessing with lightweight models.
3. **Local IndicTrans2 CPU Inference Latency**:
   - IndicTrans2 200M beam search on CPU averages ~5–8 seconds per clause. While translation is fully private and free from LLM API fees, running on CPU introduces noticeable latency compared to GPU acceleration.
4. **Jurisdictional Scope**:
   - Current statutory knowledge base covers federal Indian statutes (Constitution of India, Indian Contract Act 1872). State-specific amendments and foreign legal jurisdictions are outside the current corpus scope.

---

## Quick Start & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API Key

### Backend Setup
```bash
# 1. Clone repository and navigate to root
cd Legal-Chatbot

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and supply GEMINI_API_KEY (and optional HF_TOKEN)

# 5. Start FastAPI backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.
