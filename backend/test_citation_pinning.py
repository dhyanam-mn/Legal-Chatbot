import unittest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from app.config import GEMINI_MODELS
from app.schemas import StatutoryProvision, ClauseItem, GroundingExample
from app.classifier import (
    generate_statutory_citations,
    classify_and_explain_clause,
    LEGAL_BASIS_UNAVAILABLE_MESSAGE,
    LEGAL_BASIS_UNAVAILABLE_MESSAGE_HI,
    LEGAL_BASIS_UNAVAILABLE_MESSAGE_TA,
)


class TestCitationModelPinning(unittest.TestCase):
    """
    Verifies that citation generation is strictly pinned to GEMINI_MODELS[0].
    On failure or quota exhaustion of GEMINI_MODELS[0], citation generation MUST NOT
    fall back to lite or alternate models; it must immediately return
    'Legal basis unavailable right now' and record _model_used=None.
    """

    def setUp(self):
        self.sample_provision = StatutoryProvision(
            id="ACA-1996-s11",
            act="Arbitration and Conciliation Act, 1996",
            section="Section 11",
            title="Appointment of arbitrators",
            text="11. Appointment of arbitrators.—(1) A person of any nationality may be an arbitrator...",
            source_url="https://www.indiacode.nic.in/handle/123456789/1978"
        )
        self.clause_text = (
            "Any claim by Tenant against Landlord must be submitted to private arbitration "
            "selected exclusively by Landlord, while Landlord retains the right to sue Tenant in court."
        )

    @patch("app.classifier.call_gemini_json")
    def test_quota_exhaustion_on_strongest_model_returns_unavailable_and_no_lite_fallback(self, mock_call):
        """When GEMINI_MODELS[0] fails with 429 quota exhaustion, assert no lite model is called."""
        strongest = GEMINI_MODELS[0]
        # Simulate 429 quota exhaustion on GEMINI_MODELS[0]
        mock_call.side_effect = RuntimeError(f"429 RESOURCE_EXHAUSTED on {strongest}")

        citations, msg, hallucinations, model_used = generate_statutory_citations(
            clause_id="sec_4",
            clause_text=self.clause_text,
            retrieved_provisions=[self.sample_provision],
            translate=False
        )

        # 1. Assert exactly 1 attempt was made, specifically for GEMINI_MODELS[0] with allow_rotation=False
        self.assertEqual(mock_call.call_count, 1)
        args, kwargs = mock_call.call_args
        self.assertEqual(kwargs.get("model_name"), strongest)
        self.assertFalse(kwargs.get("allow_rotation"))

        # 2. Assert no lite model was ever invoked
        called_models = [call.kwargs.get("model_name") for call in mock_call.call_args_list]
        self.assertNotIn("gemini-3.1-flash-lite", called_models)
        self.assertNotIn("gemini-3.5-flash-lite", called_models)

        # 3. Assert return contract
        self.assertEqual(citations, [])
        self.assertEqual(msg, LEGAL_BASIS_UNAVAILABLE_MESSAGE)
        self.assertIsNone(model_used, "Expected _model_used=None when strongest model fails")

    @patch("app.classifier.call_gemini_json")
    def test_classify_and_explain_clause_sets_model_used_none_on_citation_failure(self, mock_call):
        """End-to-end clause classifier must record citation_model_used=None when citation model fails."""
        strongest = GEMINI_MODELS[0]

        def call_side_effect(prompt, model_name=None, allow_rotation=True):
            if allow_rotation:
                # This is the initial clause classification call
                return {
                    "clause_type": "dispute_resolution",
                    "classification": "flag-worthy",
                    "explanation": "This clause mandates arbitration selected exclusively by one party.",
                    "risk_reason": "It deprives the tenant of mutual arbitrator appointment rights.",
                    "severity": "High",
                    "_model_used": "gemini-3.7-flash"
                }
            else:
                # This is the citation call pinned to strongest_model with allow_rotation=False
                raise RuntimeError(f"429 Quota Exceeded on {strongest}")

        mock_call.side_effect = call_side_effect

        clause = ClauseItem(
            clause_id="sec_4",
            text=self.clause_text,
            heading="Section 4. Unilateral Forum Selection"
        )
        grounding = [
            GroundingExample(category="one_sided", clause_type="dispute_resolution", text=self.clause_text, distance=0.1)
        ]

        flagged = classify_and_explain_clause(clause, grounding_examples=grounding)
        self.assertIsNotNone(flagged)
        self.assertEqual(flagged.classification, "flag-worthy")
        self.assertEqual(flagged.legal_basis_message, LEGAL_BASIS_UNAVAILABLE_MESSAGE)
        self.assertEqual(flagged.legal_basis_message_hi, LEGAL_BASIS_UNAVAILABLE_MESSAGE_HI)
        self.assertEqual(flagged.legal_basis_message_ta, LEGAL_BASIS_UNAVAILABLE_MESSAGE_TA)
        self.assertIsNone(flagged.citation_model_used, "Expected flagged.citation_model_used to be None")
        self.assertEqual(flagged.statutory_citations, [])

    @patch("app.classifier.call_gemini_json")
    def test_citation_generation_success_records_strongest_model(self, mock_call):
        """When GEMINI_MODELS[0] succeeds, it is recorded as citation_model_used."""
        strongest = GEMINI_MODELS[0]
        mock_call.return_value = {
            "citations": [
                {
                    "provision_id": "ACA-1996-s11",
                    "reason": "Under ACA-1996-s11, Section 11 of the Arbitration and Conciliation Act, 1996 governs appointment of arbitrators."
                }
            ],
            "_model_used": strongest
        }

        citations, msg, _, model_used = generate_statutory_citations(
            clause_id="sec_4",
            clause_text=self.clause_text,
            retrieved_provisions=[self.sample_provision],
            translate=False
        )

        self.assertEqual(len(citations), 1)
        self.assertEqual(citations[0].provision_id, "ACA-1996-s11")
        self.assertEqual(model_used, strongest)
        self.assertEqual(citations[0].model_used, strongest)
        self.assertEqual(msg, "")


if __name__ == "__main__":
    unittest.main()
