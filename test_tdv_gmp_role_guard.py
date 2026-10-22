"""Regression tests for conservative classification of GMP supplementary letters."""
import hashlib
import unittest

from tdv_nsx_gmp_role_guard import inspect_gmp_role
from tdv_manufacturer_evidence import audit_manufacturer_evidence


def case(filename, text):
    return inspect_gmp_role(filename, [{"text": text}] if text else [])


class TestGmpRoleSafety(unittest.TestCase):
    def test_filename_only_cannot_certify_explanation(self):
        self.assertEqual(
            case("3.1 Công văn giải trình GMP AGP.pdf", "")["status"], "NEEDS_REVIEW"
        )

    def test_explicit_explanation_content_is_supplementary(self):
        result = case("3.1 Công văn giải trình GMP AGP.pdf",
                      "CÔNG VĂN giải trình về việc tuân thủ GMP")
        self.assertEqual(result["kind"], "GMP_EXPLANATION")

    def test_maintenance_document_not_certificate(self):
        self.assertEqual(
            case("3.3 Giấy xác nhận duy trì GMP - Mỹ Thới.pdf", "")["status"],
            "NEEDS_REVIEW",
        )

    def test_maintenance_title_is_supplementary(self):
        self.assertEqual(
            case("3.3 Giấy xác nhận duy trì GMP - Mỹ Thới.pdf",
                 "Giấy xác nhận duy trì đáp ứng GMP")["kind"],
            "GMP_EXPLANATION",
        )

    def test_real_certificate_does_not_trigger_guard(self):
        self.assertEqual(
            case("3 GCN GMP - Agimexpharm (2023).signed.pdf",
                 "Giấy chứng nhận GMP")["status"],
            "NO_SIGNAL",
        )

    def test_conflicting_titles_must_be_reviewed(self):
        self.assertEqual(
            case("3.1 Công văn giải trình GMP AGP.pdf",
                 "Công văn giải trình GMP; Giấy chứng nhận GMP")["status"],
            "NEEDS_REVIEW",
        )

    def test_3b_downgrades_misleading_gmp_certificate_label(self):
        fname = "3.1 Công văn giải trình GMP AGP.pdf"
        digest = hashlib.sha256(b"synthetic-only").hexdigest()
        report = {"sources": [{
            "kind": "GMP_CERT", "filename": fname, "sha256": digest,
            "fields": {"FACTORY": "Nhà máy A"}, "evidence": {},
            "conflicts": {}, "complete_read": True,
        }]}
        audit = audit_manufacturer_evidence(report)
        row = audit["rows"][0]
        self.assertIn("CẦN XÁC ĐỊNH", row["Loại chứng cứ gợi ý"])
        self.assertIn("CẢNH BÁO PHÂN LOẠI", row["Điểm cần kiểm tra"])
        self.assertFalse(audit["gmp_confirmed"])

    def test_missing_registration_is_extraction_gap_not_document_verdict(self):
        report = {"sources": [{
            "kind": "REGISTRATION", "filename": "AGICARVIR.pdf",
            "sha256": hashlib.sha256(b"fixture").hexdigest(),
            "fields": {"PRODUCT_NAME": "AGICARVIR"},
            "evidence": {}, "conflicts": {}, "complete_read": True,
        }]}
        row = audit_manufacturer_evidence(report)["rows"][0]
        self.assertIn("Chưa trích được trường REGISTRATION_NO", row["Điểm cần kiểm tra"])
        self.assertEqual(row["Xác minh pháp lý"], "CHƯA XÁC MINH")


if __name__ == "__main__":
    unittest.main()
