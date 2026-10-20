import hashlib
import unittest
from tdv_idp3_rules import analyze_page_layers, review_evidence_link, synthetic_evidence_cases


class TDVIDP3RuleTests(unittest.TestCase):
    def setUp(self):
        self.raw = b"TDV synthetic document"
        self.product = {"product_id": "P1", "factory_id": "F1", "manufacturer_id": "M1"}
        self.doc = {"source_id": "D1", "sha256": hashlib.sha256(self.raw).hexdigest(),
                    "page": 1, "method": "pymupdf", "excerpt": "DEMO ONLY",
                    "factory_id": "F1", "product_id": "P1", "document_type": "GMP_CERT"}

    def review(self, **overrides):
        return review_evidence_link({**self.doc, **overrides}, self.product, self.raw)

    def test_scanned_page_needs_ocr(self):
        self.assertEqual(analyze_page_layers("", "")["status"], "CAN_OCR")

    def test_ocr_only_cannot_verify(self):
        self.assertEqual(analyze_page_layers("", "", "4mg")["status"], "OCR_CHUA_KIEM_CHUNG")

    def test_numeric_disagreement(self):
        self.assertEqual(analyze_page_layers("4 mg", "1 mg")["status"], "SAI_KHAC_SO")

    def test_text_disagreement(self):
        self.assertEqual(analyze_page_layers("alpha", "beta")["status"], "CAN_DOI_CHIEU")

    def test_matching_extractors_still_not_verified(self):
        r = analyze_page_layers("4 mg", "4 mg")
        self.assertEqual(r["status"], "TRICH_XUAT_CHUA_XAC_MINH")
        self.assertFalse(r["verified"])

    def test_wrong_factory_blocked(self):
        self.assertEqual(self.review(factory_id="F2")["status"], "CHAN_LIEN_KET")

    def test_missing_factory_blocked(self):
        self.assertEqual(self.review(factory_id="")["status"], "THIEU_DINH_DANH")

    def test_incomplete_provenance_blocked(self):
        self.assertEqual(self.review(page=0)["status"], "THIEU_CHUNG_CU")
        self.assertEqual(self.review(excerpt="")["status"], "THIEU_CHUNG_CU")

    def test_hash_mismatch_blocked(self):
        self.assertEqual(self.review(sha256="0"*64)["status"], "CHAN_LIEN_KET")

    def test_gmp_never_autovalidated(self):
        r = self.review()
        self.assertEqual(r["status"], "CAN_XAC_MINH")
        self.assertFalse(r["gmp_confirmed"])
        self.assertFalse(r["bid_eligible"])

    def test_explanation_not_certificate(self):
        self.assertEqual(self.review(document_type="GMP_EXPLANATION")["status"], "CHUNG_CU_BO_SUNG")

    def test_quote_wrong_product_blocked(self):
        self.assertEqual(self.review(document_type="QUOTE", product_id="P2")["status"], "CHAN_LIEN_KET")

    def test_quote_no_price_approval(self):
        r = self.review(document_type="QUOTE")
        self.assertEqual(r["status"], "CAN_XAC_MINH")
        self.assertFalse(r["price_approved"])

    def test_authorization_wrong_manufacturer(self):
        self.assertEqual(self.review(document_type="AUTHORIZATION", manufacturer_id="M2")["status"], "CHAN_LIEN_KET")

    def test_authorization_missing_manufacturer(self):
        self.assertEqual(self.review(document_type="AUTHORIZATION")["status"], "THIEU_DINH_DANH")

    def test_missing_original_prevents_hash_verification_claim(self):
        r = review_evidence_link(self.doc, self.product)
        self.assertFalse(r["verified"])
        self.assertTrue(any("SHA-256" in x for x in r["reasons"]))

    def test_unknown_document_type_needs_review(self):
        self.assertEqual(self.review(document_type="LETTER")["status"], "CAN_XAC_MINH")

    def test_demo_cases_have_expected_outcomes(self):
        cases = synthetic_evidence_cases()
        self.assertEqual(len(cases), 7)
        self.assertEqual([v["kết_quả"] for v in cases], [
            "CAN_XAC_MINH", "CHAN_LIEN_KET", "CHUNG_CU_BO_SUNG", "CHAN_LIEN_KET",
            "CAN_XAC_MINH", "CHAN_LIEN_KET", "CAN_XAC_MINH"])
        self.assertTrue(all(v["cần_duyệt"] == "CÓ" for v in cases))


if __name__ == "__main__":
    unittest.main()
