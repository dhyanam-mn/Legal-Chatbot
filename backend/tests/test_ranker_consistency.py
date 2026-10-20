import pytest
from backend.app.schemas import FlaggedClause, ClientIntakeContext
from backend.app.ranker import rank_flagged_clauses


def test_notice_period_with_forfeiture_gets_no_deposit_boost():
    """
    Assert that a notice_period_garden_leave clause containing the word 'forfeiture'
    does NOT receive the +45.0 dependents deposit boost.
    """
    intake = ClientIntakeContext(
        employment_type="salaried",
        has_dependents=True,
        dependents_count=2,
        income_bracket="medium",
        document_type="employment_contract"
    )
    clause = FlaggedClause(
        clause_id="Clause 5.",
        clause_type="notice_period_garden_leave",
        title="Notice Period / Garden Leave Imbalance",
        original_text="Clause 5. Asymmetric Notice Period and Forfeiture. Employee must serve 6 months notice, failing which salary is forfeited.",
        classification="flag-worthy",
        explanation="Asymmetric notice requirement.",
        risk_reason="Unbalanced forfeiture penalty.",
        priority_score=0.0,
        severity="High"
    )
    ranked = rank_flagged_clauses([clause], intake)
    assert len(ranked) == 1
    # Expected: 50.0 (High base) + 0.0 (NO deposit boost) + 20.0 (salaried) + 20.0 (employment_contract) = 90.0
    assert ranked[0].priority_score == 90.0, (
        f"Expected score 90.0 for notice period clause without deposit boost, got {ranked[0].priority_score}"
    )


def test_rental_deposit_clause_gets_deposit_boost():
    """
    Assert that a rental deposit forfeiture clause (clause_type='penalty')
    still receives the +45.0 dependents deposit boost.
    """
    intake = ClientIntakeContext(
        employment_type="salaried",
        has_dependents=True,
        dependents_count=2,
        income_bracket="medium",
        document_type="rental_agreement"
    )
    clause = FlaggedClause(
        clause_id="Clause 2.",
        clause_type="penalty",
        title="Penalty & Liquidated Damages",
        original_text="Clause 2. Security Deposit and Absolute Forfeiture. Tenant deposits INR 350,000, immediately forfeited upon 48-hour rent delay.",
        classification="flag-worthy",
        explanation="Forfeiture of security deposit.",
        risk_reason="Disproportionate forfeiture without proof of loss.",
        priority_score=0.0,
        severity="High"
    )
    ranked = rank_flagged_clauses([clause], intake)
    assert len(ranked) == 1
    # Expected: 50.0 (High base) + 45.0 (deposit boost) + 20.0 (rental penalty) = 115.0
    assert ranked[0].priority_score == 115.0, (
        f"Expected score 115.0 for rental deposit clause, got {ranked[0].priority_score}"
    )


def test_identical_priority_scores_across_english_and_indic_pairs():
    """
    Assert that identical clauses in English vs Hindi/Tamil produce identical priority scores,
    verifying that keyword evaluation uses the classified English text.
    """
    # 1. Rental Deposit: English vs Hindi
    rental_intake = ClientIntakeContext(
        employment_type="salaried",
        has_dependents=True,
        dependents_count=2,
        income_bracket="medium",
        document_type="rental_agreement"
    )
    en_deposit = FlaggedClause(
        clause_id="Clause 2.",
        clause_type="penalty",
        title="Penalty & Liquidated Damages",
        original_text="Clause 2. Security Deposit and Absolute Forfeiture. Tenant deposits INR 350,000, forfeited upon delay.",
        english_translation=None,
        detected_language="en",
        classification="flag-worthy",
        explanation="Forfeiture of deposit.",
        risk_reason="Disproportionate penalty.",
        priority_score=0.0,
        severity="High"
    )
    hi_deposit = FlaggedClause(
        clause_id="खंड 2.",
        clause_type="penalty",
        title="Penalty & Liquidated Damages",
        original_text="खंड 2. प्रतिभूति जमा और पूर्ण जब्ती। किरायेदार INR 350,000 जमा करेगा, चूक पर जब्ती होगी।",
        english_translation="Section 2. Security deposit and full forfeiture. Tenant deposits INR 350,000, forfeited upon delay.",
        detected_language="hi",
        classification="flag-worthy",
        explanation="Forfeiture of deposit.",
        risk_reason="Disproportionate penalty.",
        priority_score=0.0,
        severity="High"
    )
    ranked_en_dep = rank_flagged_clauses([en_deposit], rental_intake)
    ranked_hi_dep = rank_flagged_clauses([hi_deposit], rental_intake)
    assert ranked_en_dep[0].priority_score == ranked_hi_dep[0].priority_score == 115.0

    # 2. Employment Notice Period: English vs Tamil
    emp_intake = ClientIntakeContext(
        employment_type="salaried",
        has_dependents=True,
        dependents_count=2,
        income_bracket="medium",
        document_type="employment_contract"
    )
    en_notice = FlaggedClause(
        clause_id="Clause 5.",
        clause_type="notice_period_garden_leave",
        title="Notice Period / Garden Leave Imbalance",
        original_text="Clause 5. Asymmetric Notice Period and Forfeiture. Mandatory 6 months notice, failing which salary is forfeited.",
        english_translation=None,
        detected_language="en",
        classification="flag-worthy",
        explanation="Asymmetric notice.",
        risk_reason="Unbalanced forfeiture.",
        priority_score=0.0,
        severity="High"
    )
    ta_notice = FlaggedClause(
        clause_id="பிரிவு 5.",
        clause_type="notice_period_garden_leave",
        title="Notice Period / Garden Leave Imbalance",
        original_text="பிரிவு 5. சமச்சீரற்ற அறிவிப்பு காலம் மற்றும் பறிமுதல். ஊழியர் 6 மாதங்கள் அறிவிப்பு தர வேண்டும்.",
        english_translation="Section 5. Non-uniform notice period and loss of pay. Mandatory 6 months notice, failing which salary is forfeited.",
        detected_language="ta",
        classification="flag-worthy",
        explanation="Asymmetric notice.",
        risk_reason="Unbalanced forfeiture.",
        priority_score=0.0,
        severity="High"
    )
    ranked_en_not = rank_flagged_clauses([en_notice], emp_intake)
    ranked_ta_not = rank_flagged_clauses([ta_notice], emp_intake)
    assert ranked_en_not[0].priority_score == ranked_ta_not[0].priority_score == 90.0
