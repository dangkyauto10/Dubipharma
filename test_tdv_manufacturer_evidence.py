import hashlib
import unittest
from tdv_manufacturer_evidence import audit_manufacturer_evidence


def doc(kind, fields, complete=True):
    fn = "proof.pdf"
    sha = hashlib.sha256(b"fixture-only").hexdigest()
    return {
        "kind": kind, "filename": fn, "sha256": sha,
        "complete_read": complete, "fields": fields,
        "evidence": {k: {"source": "trang 1", "raw": f"{k}: {v}",
                         "file": fn, "sha256": sha} for k, v in fields.items()},
    }


class EvidenceTests(unittest.TestCase):
    def test_real_source_is_reviewed_not_approved(self):
        source = doc("GMP_CERT", {"FACTORY": "Mỹ Thới", "GMP_NUMBER": "A12",
                                  "GMP_SCOPE": "Dây chuyền viên", "GMP_EXPIRY": "2027-10-01"})
        result = audit_manufacturer_evidence({"sources": [source]})
        self.assertEqual(result["documents_reviewed"], 1)
        self.assertFalse(result["gmp_confirmed"])
        self.assertEqual(result["rows"][0]["Xác minh pháp lý"], "CHƯA XÁC MINH")
        self.assertIn("Chưa có liên kết", result["rows"][0]["Điểm cần kiểm tra"])

    def test_factory_mismatch_even_with_reported_link(self):
        source = doc("GMP_CERT", {"FACTORY": "Bình Hòa", "GMP_NUMBER": "A12",
                                  "GMP_SCOPE": "Viên", "GMP_EXPIRY": "2027"})
        result = audit_manufacturer_evidence({
            "sources": [source],
            "products": [{"uid": "P1", "fields": {"FACTORY": "Mỹ Thới"}}],
            "links": [{"source_evidence": source["filename"], "source_sha256": source["sha256"],
                       "evidence_kind": "GMP_CERT", "product_id": "P1"}],
        })
        self.assertIn("XUNG ĐỘT: FACTORY", result["rows"][0]["Điểm cần kiểm tra"])
        self.assertFalse(result["verified"])

    def test_explanation_does_not_replace_gmp(self):
        result = audit_manufacturer_evidence({"sources": [doc("GMP_EXPLANATION", {"FACTORY": "Mỹ Thới"})]})
        self.assertIn("KHÔNG tự thay thế", result["rows"][0]["Điểm cần kiểm tra"])

    def test_ambiguous_registration_never_approves(self):
        result = audit_manufacturer_evidence({"sources": [doc("REGISTRATION", {"PRODUCT_NAME": "Thuốc A"})]})
        self.assertIn("REGISTRATION_NO", result["rows"][0]["Điểm cần kiểm tra"])
        self.assertFalse(result["registration_confirmed"])

    def test_broken_source_citation_is_flagged(self):
        source = doc("GMP_CERT", {"FACTORY": "Mỹ Thới"})
        source["evidence"]["FACTORY"]["sha256"] = "0" * 64
        result = audit_manufacturer_evidence({"sources": [source]})
        self.assertIn("chưa có trích dẫn", result["rows"][0]["Điểm cần kiểm tra"])

    def test_other_files_are_not_relabelled(self):
        result = audit_manufacturer_evidence({"sources": [doc("OTHER", {"FACTORY": "X"})]})
        self.assertEqual(result["documents_reviewed"], 0)


if __name__ == "__main__":
    unittest.main()
