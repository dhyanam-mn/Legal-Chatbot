import unittest
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.vector_store import retrieve_statutes_for_clause, ReferenceVectorStore
from app.classifier import generate_statutory_citations, NO_STATUTE_MESSAGE


class TestUnmappedProvisions(unittest.TestCase):
    """
    Verifies that clause types with no verified statutory provisions mapped
    reliably retrieve 0 statutory provisions and display 'No statutory provision retrieved'.
    """

    @classmethod
    def setUpClass(cls):
        cls.store = ReferenceVectorStore()

    def test_unmapped_clause_types_return_no_statute_message(self):
        unmapped_types = [
            "acceleration",
            "guarantor_liability",
            "set_off_lien",
            "ip_assignment",
            "unilateral_interest_change",
        ]
        for clause_type in unmapped_types:
            provisions = retrieve_statutes_for_clause("Sample contract clause text", clause_type=clause_type)
            citations, msg, hallucinations, model_used = generate_statutory_citations(
                f"test_{clause_type}",
                "Sample contract clause text",
                provisions,
            )
            self.assertEqual(len(provisions), 0, f"Expected 0 provisions for {clause_type}, got {len(provisions)}")
            self.assertEqual(len(citations), 0, f"Expected 0 citations for {clause_type}, got {len(citations)}")
            self.assertEqual(
                msg,
                NO_STATUTE_MESSAGE,
                f"Expected '{NO_STATUTE_MESSAGE}' for {clause_type}, got '{msg}'"
            )


if __name__ == "__main__":
    unittest.main()
