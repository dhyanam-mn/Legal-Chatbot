from typing import List, Optional
from pydantic import BaseModel, Field

class ClientIntakeContext(BaseModel):
    employment_type: str = Field(default="salaried", description="salaried, self_employed, business_owner, unemployed, retired")
    has_dependents: bool = Field(default=False, description="Whether client has dependents")
    dependents_count: int = Field(default=0, description="Number of dependents")
    income_bracket: str = Field(default="medium", description="low, medium, high")
    document_type: str = Field(default="employment_contract", description="employment_contract, rental_agreement, loan_agreement, service_agreement, other")

class ClauseItem(BaseModel):
    clause_id: str
    text: str

class GroundingExample(BaseModel):
    category: str  # standard or one_sided
    clause_type: str
    text: str
    distance: float

class StatutoryProvision(BaseModel):
    id: str
    act: str
    section: str
    title: str
    text: str
    source_url: str
    distance: Optional[float] = None
    retrieval_source: str = "semantic"  # semantic, mapped, or mapped+semantic

class StatutoryCitation(BaseModel):
    provision_id: str
    act: str
    section: str
    title: str
    source_url: str = ""
    statutory_text: str = ""
    reason: str
    reason_hi: Optional[str] = None
    reason_ta: Optional[str] = None
    model_used: Optional[str] = None

class FlaggedClause(BaseModel):
    clause_id: str
    clause_type: str
    title: str
    original_text: str
    classification: str  # standard or flag-worthy
    explanation: str
    risk_reason: str
    explanation_hi: Optional[str] = None
    risk_reason_hi: Optional[str] = None
    explanation_ta: Optional[str] = None
    risk_reason_ta: Optional[str] = None
    severity: str  # High, Medium, Low
    priority_score: float
    model_used: Optional[str] = None
    citation_model_used: Optional[str] = None
    grounding_examples: List[GroundingExample] = []
    statutory_provisions: List[StatutoryProvision] = []
    statutory_citations: List[StatutoryCitation] = []
    legal_basis_message: str = "No statutory provision retrieved"
    legal_basis_message_hi: Optional[str] = None
    legal_basis_message_ta: Optional[str] = None
    typical_phrasing_header: str = "How this is typically written"
    typical_phrasing_disclaimer: str = ""
    typical_phrasing_disclaimer_hi: Optional[str] = None
    typical_phrasing_disclaimer_ta: Optional[str] = None
    standard_alternatives: List[str] = []




class AnalysisResponse(BaseModel):
    document_summary: str
    document_summary_hi: Optional[str] = None
    document_summary_ta: Optional[str] = None
    parsed_method: str  # pdfplumber or ocr
    total_clauses: int
    flagged_clauses: List[FlaggedClause]
    all_clauses: List[ClauseItem]
    intake_context: ClientIntakeContext
    disclaimer: str
    disclaimer_hi: Optional[str] = None
    disclaimer_ta: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # user or assistant
    content: str

class ChatRequest(BaseModel):
    message: str
    document_text: str
    intake_context: Optional[ClientIntakeContext] = None
    chat_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    reply: str
    reply_hi: Optional[str] = None
    reply_ta: Optional[str] = None
    disclaimer: str
    disclaimer_hi: Optional[str] = None
    disclaimer_ta: Optional[str] = None


