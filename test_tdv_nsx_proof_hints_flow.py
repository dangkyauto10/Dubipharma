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

    def test_labeled_product_name_hint_remains_outside_core(self):
        raw, source = self.source(
            ("Trang 4", "Tên thuốc (biệt dược):"),
            ("Trang 4", "AGIMOL 150"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("PRODUCT_NAME", result["fields"])
        self.assertIn("AGIMOL 150", [x["value"] for x in result["proof_hints"]])
        self.assertFalse(result["registration_confirmed"])
        self.assertEqual(result["proof_diagnostic"]["hint_count"], 1)

    def test_diagnostic_reports_unread_field_not_missing_legal_document(self):
        raw, source = self.source(("Trang 1", "Mã hồ sơ không có nhãn"))
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        d = result["proof_diagnostic"]
        self.assertEqual(d["hint_count"], 0)
        self.assertIn("REGISTRATION_NO", d["fields_without_hint"])
        self.assertFalse(d["verified"])
        self.assertFalse(result["registration_confirmed"])


    def test_ocr_table_headers_are_not_product_name_or_strength(self):
        raw, source = self.source(
            ("Trang 4 (OCR)", "Tên thuốc"),
            ("Trang 4 (OCR)", "Hoạt chất chính- | Dạng bào chế | Quy cách đóng gói | Tiêu | Tuổi | Sốđăngký | Số"),
            ("Trang 4 (OCR)", "Hàm lượng"),
            ("Trang 4 (OCR)", "chuẩn | thọ"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("PRODUCT_NAME", result["fields"])
        self.assertNotIn("STRENGTH", result["fields"])
        self.assertFalse(result["registration_confirmed"])

    def test_single_pdf_heading_fragment_is_not_product_name(self):
        raw, source = self.source(("Trang 4 (OCR)", "Tên thuốc | Hoạt chất chính-"))
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("PRODUCT_NAME", result["fields"])

    def test_true_adjacent_pdf_name_remains_source_cited(self):
        raw, source = self.source(
            ("Trang 1", "Tên thuốc"),
            ("Trang 1", "THUỐC MẪU 500"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertEqual(result["fields"]["PRODUCT_NAME"], "THUỐC MẪU 500")
        self.assertEqual(result["evidence"]["PRODUCT_NAME"]["source"], "Trang 1 (hai dòng liền kề)")
        self.assertFalse(result["registration_confirmed"])


    def test_split_ocr_strength_label_does_not_accept_word_fragment(self):
        raw, source = self.source(
            ("Trang 4 (OCR)", "Hàm lượng"),
            ("Trang 4 (OCR)", "chế"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("STRENGTH", result["fields"])
        self.assertFalse(result["registration_confirmed"])

    def test_inline_strength_label_does_not_accept_word_fragment(self):
        raw, source = self.source(
            ("Trang 4 (OCR)", "Hàm lượng: chế"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("STRENGTH", result["fields"])

    def test_credible_strength_remains_unverified_but_cited(self):
        raw, source = self.source(
            ("Trang 4", "Hàm lượng"),
            ("Trang 4", "150mg"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertEqual(result["fields"].get("STRENGTH"), "150mg")
        self.assertFalse(result["verified"])

    def test_new_registration_hint_does_not_promote_to_fields_or_link(self):
        raw, source = self.source(
            ("Trang 8", "đối với thuốc có s6 dang kY: VD-99999-22."),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("REGISTRATION_NO", result["fields"])
        self.assertTrue(any(
            r["field"] == "REGISTRATION_NO" and r["value"] == "VD-99999-22"
            for r in result["proof_hints"]
        ))
        self.assertFalse(result["registration_confirmed"])


    def test_ocr_composition_sentence_not_scalar_ingredient(self):
        raw, source = self.source(
            ("Trang 12 (OCR)", "Thành phần hoạt chất:"),
            ("Trang 12 (OCR)", "M6i vien AGICARVIR chira 0,5 mg Entecavir "
             "(dum dang Entecavir monohydrate)."),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertNotIn("INGREDIENT", result["fields"])
        rejected = result["rejected_scalar_candidates"]
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["field"], "INGREDIENT")
        self.assertIn("AGICARVIR", rejected[0]["raw"])
        self.assertEqual(rejected[0]["source"], "Trang 12 (OCR) (hai dòng liền kề)")
        self.assertFalse(rejected[0]["verified"])

    def test_legitimate_labeled_ingredient_remains_source_cited(self):
        raw, source = self.source(
            ("Trang 1", "Thành phần hoạt chất: Entecavir"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertEqual(result["fields"]["INGREDIENT"], "Entecavir")
        self.assertEqual(result["rejected_scalar_candidates"], [])
        self.assertFalse(result["verified"])

    def test_sentence_guard_does_not_change_product_table(self):
        raw, source = self.source(
            ("Trang 1", "Tên thuốc: THUỐC MẪU"),
            ("Trang 1", "Số đăng ký: VD-12345-22"),
        )
        result = _read_one(
            "fake.pdf", "REGISTRATION", raw, False, source_document=source,
        )
        self.assertEqual(result["fields"]["PRODUCT_NAME"], "THUỐC MẪU")
        self.assertEqual(result["fields"]["REGISTRATION_NO"], "VD-12345-22")
        self.assertFalse(result["registration_confirmed"])


if __name__ == "__main__":
    unittest.main()
