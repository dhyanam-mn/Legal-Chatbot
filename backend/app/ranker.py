from typing import List
from .schemas import FlaggedClause, ClientIntakeContext

def rank_flagged_clauses(
    flagged_clauses: List[FlaggedClause],
    intake: ClientIntakeContext
) -> List[FlaggedClause]:
    """
    Sorts and ranks flagged clauses based on severity and client intake context.
    """
    if not flagged_clauses:
        return []

    severity_base = {
        "High": 50.0,
        "Medium": 30.0,
        "Low": 10.0
    }

    ranked = []
    for clause in flagged_clauses:
        score = severity_base.get(clause.severity, 20.0)
        c_type = clause.clause_type

        if intake.has_dependents or intake.dependents_count > 0:
            # Substantial boost for direct financial liabilities threatening household stability
            is_sec_deposit_or_maintenance = any(
                term in (clause.title or "").lower() or term in (clause.original_text or "").lower()
                for term in ["security deposit", "maintenance", "forfeiture"]
            )
            if c_type in ["indemnity"]:
                score += 45.0
            elif c_type in ["penalty"] or is_sec_deposit_or_maintenance:
                score += 45.0
            elif c_type in ["termination"]:
                score += 15.0

        if intake.employment_type in ["salaried", "self_employed"]:
            if c_type in ["non_compete"]:
                score += 25.0
            elif c_type in ["termination"]:
                score += 20.0

        if intake.document_type == "rental_agreement":
            if c_type in ["termination"]:
                score += 25.0
            elif c_type in ["penalty"]:
                score += 20.0
        elif intake.document_type == "employment_contract":
            if c_type in ["non_compete"]:
                score += 25.0
            elif c_type in ["indemnity"]:
                score += 20.0
        elif intake.document_type == "loan_agreement":
            if c_type in ["penalty"]:
                score += 30.0

        if intake.income_bracket == "low":
            if c_type in ["penalty", "indemnity"]:
                score += 20.0

        clause.priority_score = score
        ranked.append(clause)

    ranked.sort(key=lambda x: x.priority_score, reverse=True)
    return ranked
