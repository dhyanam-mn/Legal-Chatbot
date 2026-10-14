import unittest
from unittest.mock import patch, MagicMock
import re
import os
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.schemas import StatutoryProvision, FlaggedClause
from app.vector_store import ReferenceVectorStore, CLAUSE_TYPE_STATUTE_MAP
from app.classifier import (
    generate_statutory_citations,
    validate_statutory_citations,
    LEGAL_BASIS_UNAVAILABLE_MESSAGE,
    NO_STATUTE_MESSAGE,
)
from app.config import GEMINI_MODELS

class TestStatuteQuarantineAndCitations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = ReferenceVectorStore()

    def test_arbitration_retrieval_returns_verified_aca(self):
        """
        Confirm that retrieval for an arbitration clause returns verified ACA-1996 provisions.
        """
        arbitration_clause_text = (
            "Any dispute, controversy or claim arising out of or relating to this Agreement "
            "shall be referred to and finally resolved by arbitration administered in Singapore."
        )
        retrieved = self.store.retrieve_statutes_for_clause(
            arbitration_clause_text,
            clause_type="arbitration",
            top_k=5,
        )
        retrieved_ids = [p.id for p in retrieved]

        # Assert verified ACA provisions are retrieved
        aca_ids = [pid for pid in retrieved_ids if pid.startswith("ACA-")]
        self.assertTrue(len(aca_ids) > 0, "Expected verified ACA provisions to be retrieved!")
        self.assertIn("ICA-1872-s28", retrieved_ids)
        self.assertIn("ACA-1996-s7", retrieved_ids)

    def test_strongest_model_pinning_and_unavailable_fallback(self):
        """
        Test that citation generation is pinned to GEMINI_MODELS[0].
        If GEMINI_MODELS[0] fails (e.g. 429/error), it returns 'Legal basis unavailable right now'
        without falling back to lite models, and logs _model_used = None.
        """
        provision = StatutoryProvision(
            id="ICA-1872-s27",
            act="Indian Contract Act, 1872",
            section="Section 27",
            title="Agreement in restraint of trade, void",
            text="Every agreement by which any one is restrained from exercising a lawful profession, trade or business of any kind, is to that extent void. Exception 1.—Saving of agreement not to carry on business of which good-will is sold.",
            source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        )

        # Mock call_gemini_json to simulate GEMINI_MODELS[0] failure
        with patch("app.classifier.call_gemini_json", side_effect=RuntimeError("Quota exceeded on strongest model")):
            citations, msg, _, model_used = generate_statutory_citations(
                clause_id="clause_test_1",
                clause_text="Employee agrees not to work for any competitor for 3 years.",
                retrieved_provisions=[provision],
                translate=False,
            )

            self.assertEqual(len(citations), 0)
            self.assertEqual(msg, LEGAL_BASIS_UNAVAILABLE_MESSAGE)
            self.assertIsNone(model_used)

    def test_citation_verbatim_text_and_concept_cross_check(self):
        """
        Test that:
        (a) StatutoryCitation includes statutory_text verbatim matching prov.text.
        (b) The description concepts are a subset of the retrieved provision's concepts
            (no words absent from the retrieved text and standard legal descriptor tokens).
        """
        provision = StatutoryProvision(
            id="ICA-1872-s27",
            act="Indian Contract Act, 1872",
            section="Section 27",
            title="Agreement in restraint of trade, void",
            text="Every agreement by which any one is restrained from exercising a lawful profession, trade or business of any kind, is to that extent void. Exception 1.—Saving of agreement not to carry on business of which good-will is sold.",
            source_url="https://www.indiacode.nic.in/handle/123456789/2187",
        )

        mock_gemini_response = {
            "_model_used": GEMINI_MODELS[0],
            "citations": [
                {
                    "provision_id": "ICA-1872-s27",
                    "reason": "Section 27 of the Indian Contract Act, 1872 provides that agreements restraining a lawful profession, trade, or business are void to that extent, with an exception for good-will sale.",
                }
            ],
        }

        with patch("app.classifier.call_gemini_json", return_value=mock_gemini_response):
            citations, msg, hallucinations, model_used = generate_statutory_citations(
                clause_id="clause_non_compete",
                clause_text="The employee covenants not to engage in any competing trade.",
                retrieved_provisions=[provision],
                translate=False,
            )

            self.assertEqual(len(citations), 1)
            cit = citations[0]

            # 1. Check verbatim statutory_text presence
            self.assertEqual(cit.statutory_text, provision.text)
            self.assertEqual(cit.provision_id, "ICA-1872-s27")
            self.assertEqual(cit.model_used, GEMINI_MODELS[0])

            # 2. Concept cross-check:
            prov_corpus = (
                f"{provision.id} {provision.act} {provision.section} {provision.title} {provision.text}"
            ).lower()
            prov_words = set(re.findall(r"\b[a-z]{3,}\b", prov_corpus))

            allowed_grammar = {
                "under", "the", "and", "that", "this", "with", "for", "from", "are", "covers",
                "provides", "rule", "regarding", "terms", "such", "its", "any", "which", "one",
                "extent", "exception", "saving", "section", "act", "indian", "contract", "trade",
                "profession", "business", "good-will", "will", "sale", "sold", "void", "law",
                "statutory", "provisions", "restraining", "restrained", "lawful", "agreements"
            }
            allowed_concepts = prov_words.union(allowed_grammar)

            reason_words = set(re.findall(r"\b[a-z]{3,}\b", cit.reason.lower()))
            unmatched = reason_words - allowed_concepts

            self.assertEqual(
                len(unmatched), 0,
                f"Generated description contained concepts/words absent from retrieved provision: {unmatched}"
            )

if __name__ == "__main__":
    unittest.main()
