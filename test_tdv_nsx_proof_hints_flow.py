"""Integration checks: source hints must never become core product identifiers."""
import hashlib
import unittest

from tdv_nsx_intake import _read_one


class TestProofHintBoundary(unittest.TestCase):
    def source(self, *lines):
        raw = b"synthetic-input"
        return raw, {
            "name": "fake.pdf",
            "type": "pdf",
            "sha256": hashlib.sha256(raw).hexdigest(),
            "complete": True,
            "pages": 4,
            "warnings": [],
            "lines": [{"source": p, "text": s} for p, s in lines],
        }

    def test_parenthesized_sdk_label_is_only_hint(self):
        raw, source = self.source(
            ("Trang 4", "Số đăng ký lưu hành (SĐK): VD-12345-22"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("REGISTRATION_NO", result["fields"])
        self.assertNotIn("REGISTRATION_NO", result["evidence"])
        self.assertEqual(result["proof_hints"][0]["value"], "VD-12345-22")
        self.assertFalse(result["registration_confirmed"])
        self.assertFalse(result["verified"])

    def test_strict_parsed_sdk_not_duplicated_as_hint(self):
        raw, source = self.source(
            ("Trang 1", "Số đăng ký: VD-12345-22"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertEqual(result["fields"]["REGISTRATION_NO"], "VD-12345-22")
        self.assertEqual(result["proof_hints"], [])
        self.assertFalse(result["registration_confirmed"])

    def test_gmp_number_from_unknown_label_remains_hint(self):
        raw, source = self.source(
            ("Trang 1", "Số GCN GMP: GMP-2023-123"),
        )
        result = _read_one(
            "fake.pdf", "GMP_CERT", raw, False, source_document=source,
        )
        self.assertNotIn("GMP_NUMBER", result["fields"])
        self.assertEqual(result["proof_hints"][0]["field"], "GMP_NUMBER")
        self.assertFalse(result["gmp_confirmed"])


if __name__ == "__main__":
    unittest.main()
