import json
import logging
from typing import Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware

from .config import (
    MANDATORY_DISCLAIMER,
    MANDATORY_DISCLAIMER_HI,
    MANDATORY_DISCLAIMER_TA,
    GEMINI_API_KEY,
    ALLOW_HEURISTIC_FALLBACK
)
from .schemas import (
    ClientIntakeContext, AnalysisResponse, ChatRequest, ChatResponse
)
from .parser import parse_pdf
from .segmenter import segment_text_into_clauses
from .vector_store import get_vector_store
from .classifier import (
    classify_and_explain_clause, generate_document_summary, call_gemini_json, genai_client
)
from .ranker import rank_flagged_clauses
from .translator import translate_text_to_hindi, translate_text_to_tamil, get_translator_engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("legal-chatbot")

app = FastAPI(
    title="Legal Document Chatbot Backend",
    description="Multilingual Legal Document Chatbot API with clause segmentation, vector grounding, and local IndicTrans2 (Hindi & Tamil) translation.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers: Attach mandatory disclaimer (EN, HI, TA) to all error responses (400, 422, 500)
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "disclaimer": MANDATORY_DISCLAIMER,
            "disclaimer_hi": MANDATORY_DISCLAIMER_HI,
            "disclaimer_ta": MANDATORY_DISCLAIMER_TA
        }
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "disclaimer": MANDATORY_DISCLAIMER,
            "disclaimer_hi": MANDATORY_DISCLAIMER_HI,
            "disclaimer_ta": MANDATORY_DISCLAIMER_TA
        }
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error occurred.",
            "disclaimer": MANDATORY_DISCLAIMER,
            "disclaimer_hi": MANDATORY_DISCLAIMER_HI,
            "disclaimer_ta": MANDATORY_DISCLAIMER_TA
        }
    )

@app.on_event("startup")
def startup_event():
    logger.info("Initializing Legal Chatbot Backend...")
    
    # Loud fail check if API key is missing and heuristic dev fallback is disabled
    if not GEMINI_API_KEY and not ALLOW_HEURISTIC_FALLBACK:
        raise RuntimeError(
            "CRITICAL: GEMINI_API_KEY is missing! The server cannot start without a valid Gemini API key. "
            "Set GEMINI_API_KEY in .env or set ALLOW_HEURISTIC_FALLBACK=true for offline development mode."
        )
        
    try:
        get_vector_store()
        logger.info("Vector store initialized successfully.")
    except Exception as e:
        logger.error(f"Vector store initialization error: {e}")

    try:
        engine = get_translator_engine()
        logger.info(f"IndicTrans2 ready: model='{engine.model_name}', device='{engine.device}'")
    except Exception as e:
        logger.error(f"IndicTrans2 initialization error: {e}")

@app.get("/api/health")
def health_check():
    engine = get_translator_engine()
    return {
        "status": "healthy",
        "gemini_configured": bool(GEMINI_API_KEY),
        "heuristic_fallback_allowed": ALLOW_HEURISTIC_FALLBACK,
        "translation_model": engine.model_name,
        "translation_device": engine.device,
        "disclaimer": MANDATORY_DISCLAIMER,
        "disclaimer_hi": MANDATORY_DISCLAIMER_HI,
        "disclaimer_ta": MANDATORY_DISCLAIMER_TA
    }

@app.post("/api/upload", response_model=AnalysisResponse)
async def upload_document(
    file: UploadFile = File(...),
    employment_type: str = Form("salaried"),
    has_dependents: bool = Form(False),
    dependents_count: int = Form(0),
    income_bracket: str = Form("medium"),
    document_type: str = Form("employment_contract")
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    try:
        content = await file.read()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    text, parse_method = parse_pdf(content)
    if not text or not text.strip():
        raise HTTPException(status_code=422, detail="Could not extract readable text from PDF.")

    clauses = segment_text_into_clauses(text)
    if not clauses:
        raise HTTPException(status_code=422, detail="No valid clauses detected in document.")

    vector_store = get_vector_store()
    flagged_clauses = []

    for clause in clauses:
        grounding_examples = vector_store.query_nearest_references(clause.text, top_k=4)
        flagged = classify_and_explain_clause(clause, grounding_examples)
        if flagged:
            flagged_clauses.append(flagged)

    intake_context = ClientIntakeContext(
        employment_type=employment_type,
        has_dependents=has_dependents,
        dependents_count=dependents_count,
        income_bracket=income_bracket,
        document_type=document_type
    )
    
    ranked_flags = rank_flagged_clauses(flagged_clauses, intake_context)
    summary_en, summary_hi, summary_ta = generate_document_summary(text, len(clauses), len(ranked_flags))

    return AnalysisResponse(
        document_summary=summary_en,
        document_summary_hi=summary_hi,
        document_summary_ta=summary_ta,
        parsed_method=parse_method,
        total_clauses=len(clauses),
        flagged_clauses=ranked_flags,
        all_clauses=clauses,
        intake_context=intake_context,
        disclaimer=MANDATORY_DISCLAIMER,
        disclaimer_hi=MANDATORY_DISCLAIMER_HI,
        disclaimer_ta=MANDATORY_DISCLAIMER_TA
    )

@app.post("/api/chat", response_model=ChatResponse)
async def chat_document(request: ChatRequest):
    user_msg = request.message
    doc_text = request.document_text[:4000]
    intake = request.intake_context or ClientIntakeContext()

    prompt = f"""You are an assistant explaining a legal document to a user.
USER PROFILE:
- Employment: {intake.employment_type}
- Dependents: {'Yes (' + str(intake.dependents_count) + ')' if intake.has_dependents else 'No'}
- Income Bracket: {intake.income_bracket}
- Document Type: {intake.document_type}

DOCUMENT EXCERPT:
"{doc_text}"

USER QUESTION:
"{user_msg}"

Provide a helpful, plain-English answer explaining the document in simple terms relevant to their profile.
Be concise (2-3 paragraphs max).
"""

    reply = ""
    if genai_client:
        models_to_try = ["gemini-3.6-flash"]
        for mod in models_to_try:
            try:
                if hasattr(genai_client, 'models'):
                    res = genai_client.models.generate_content(model=mod, contents=prompt)
                    reply = res.text.strip()
                    break
                else:
                    model = genai_client.GenerativeModel(mod)
                    res = model.generate_content(prompt)
                    reply = res.text.strip()
                    break
            except Exception as e:
                logger.warning(f"Gemini chat with '{mod}' failed: {e}")

    if not reply:
        if not ALLOW_HEURISTIC_FALLBACK:
            raise HTTPException(status_code=500, detail="Gemini API is required for chat responses but is unavailable.")
        reply = (
            f"Regarding your document ({intake.document_type}): The clause terms outline specific rights and responsibilities. "
            f"Based on your profile ({intake.employment_type}), ensure you carefully inspect any clauses restricting post-termination activities or imposing financial penalties."
        )

    reply_hi = translate_text_to_hindi(reply)
    reply_ta = translate_text_to_tamil(reply)

    return ChatResponse(
        reply=reply,
        reply_hi=reply_hi,
        reply_ta=reply_ta,
        disclaimer=MANDATORY_DISCLAIMER,
        disclaimer_hi=MANDATORY_DISCLAIMER_HI,
        disclaimer_ta=MANDATORY_DISCLAIMER_TA
    )

