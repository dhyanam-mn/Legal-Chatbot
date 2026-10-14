import unittest
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from audit_statutes_provenance import (
    clean_pdf_page_text,
    normalize_provision_text,
    extract_pdf_body_text,
)


class TestProvenanceAudit(unittest.TestCase):
    """
    Tests for statutory provenance audit, normalization pipeline,
    and negative control assertions.
    """

    @classmethod
    def setUpClass(cls):
        cls.raw_dir = Path(__file__).resolve().parent.parent.parent / "data" / "statutes_raw"
        cls.ica_pdf = cls.raw_dir / "A187209.pdf"
        assert cls.ica_pdf.exists(), f"Missing {cls.ica_pdf}"
        cls.ica_body = extract_pdf_body_text(cls.ica_pdf, start_page=11)

    def test_normalization_rules(self):
        """Verify normalizations applied by audit script."""
        # 1. Unicode quotes and dashes
        raw = '“Smart” ‘quotes’ and — em-dash – en-dash'
        norm = normalize_provision_text(raw)
        self.assertEqual(norm, '"Smart" \'quotes\' and — em-dash - en-dash')

        # 2. Footnote and amendment brackets
        raw_brackets = '2[Every agreement,]'
        norm_brackets = normalize_provision_text(raw_brackets)
        self.assertEqual(norm_brackets, 'Every agreement,')

        # 3. Whitespace collapsing
        raw_spaces = "   Text    with   \n   extra   spaces.  "
        norm_spaces = normalize_provision_text(raw_spaces)
        self.assertEqual(norm_spaces, "Text with extra spaces.")

    def test_ica_section_27_positive_match(self):
        """Assert unedited ICA Section 27 matches 100% in official PDF."""
        sec27_text = (
            "27. Agreement in restraint of trade, void.—Every agreement by which any one is restrained "
            "from exercising a lawful profession, trade or business of any kind, is to that extent void. "
            "Exception 1.—Saving of agreement not to carry on business of which good-will is sold.—One who "
            "sells the good-will of a business may agree with the buyer to refrain from carrying on a similar "
            "business, within specified local limits, so long as the buyer, or any person deriving title to "
            "the good-will from him, carries on a like business therein, provided that such limits appear to "
            "the Court reasonable, regard being had to the nature of the business."
        )
        norm_sec27 = normalize_provision_text(sec27_text)
        self.assertIn(
            norm_sec27,
            self.ica_body,
            "Expected verbatim Section 27 to match official PDF body text."
        )

    def test_negative_control_fails_on_single_word_change(self):
        """
        Negative-control test: Copy a verified statutory provision, change exactly ONE word,
        and assert that the provenance audit fails (exact match is False and diff is detected).
        """
        # Verified provision: ICA Section 27
        original_text = (
            "27. Agreement in restraint of trade, void.—Every agreement by which any one is restrained "
            "from exercising a lawful profession, trade or business of any kind, is to that extent void. "
            "Exception 1.—Saving of agreement not to carry on business of which good-will is sold.—One who "
            "sells the good-will of a business may agree with the buyer to refrain from carrying on a similar "
            "business, within specified local limits, so long as the buyer, or any person deriving title to "
            "the good-will from him, carries on a like business therein, provided that such limits appear to "
            "the Court reasonable, regard being had to the nature of the business."
        )
        # Change exactly ONE word: 'void' -> 'enforceable'
        tampered_text = original_text.replace("is to that extent void.", "is to that extent enforceable.")
        self.assertNotEqual(original_text, tampered_text)

        norm_tampered = normalize_provision_text(tampered_text)

        # 1. Assert exact containment in official PDF text fails
        is_exact_match = norm_tampered in self.ica_body
        self.assertFalse(
            is_exact_match,
            "Negative control failed: tampered provision unexpectedly matched official PDF text!"
        )

        # 2. Check that changing another single word ('restrained' -> 'compelled') also fails
        tampered_text_2 = original_text.replace("any one is restrained", "any one is compelled")
        norm_tampered_2 = normalize_provision_text(tampered_text_2)
        self.assertFalse(
            norm_tampered_2 in self.ica_body,
            "Negative control failed: tampered provision with substituted verb unexpectedly matched!"
        )


if __name__ == "__main__":
    unittest.main()
