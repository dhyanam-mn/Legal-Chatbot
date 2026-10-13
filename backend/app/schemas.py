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
    severity: str  # High, Medium, Low
    priority_score: float
    grounding_examples: List[GroundingExample] = []

class AnalysisResponse(BaseModel):
    document_summary: str
    document_summary_hi: Optional[str] = None
    parsed_method: str  # pdfplumber or ocr
    total_clauses: int
    flagged_clauses: List[FlaggedClause]
    all_clauses: List[ClauseItem]
    intake_context: ClientIntakeContext
    disclaimer: str
    disclaimer_hi: Optional[str] = None

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
    disclaimer: str
    disclaimer_hi: Optional[str] = None

