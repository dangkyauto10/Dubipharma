"""Focused synthetic regression tests for source-only SĐK/GMP recovery hints."""
import hashlib
import unittest
from tdv_nsx_proof_hints import extract_labeled_hints, diagnose_proof_source, collect_proof_contexts


SHA = hashlib.sha256(b"synthetic-pdf-no-private-document").hexdigest()


def doc(*items):
    return {"type": "pdf", "sha256": SHA,
            "lines": [{"source": where, "text": text} for where, text in items]}


class TestLabeledProofHints(unittest.TestCase):
    def test_registration_inline_parenthetical_label(self):
        x = extract_labeled_hints(
            "REGISTRATION",
            doc(("Trang 4", "Số đăng ký lưu hành (SĐK): VD-12345-22")), {}
        )
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["field"], "REGISTRATION_NO")
        self.assertEqual(x[0]["value"], "VD-12345-22")
        self.assertEqual(x[0]["source"], "Trang 4")
        self.assertEqual(x[0]["sha256"], SHA)
        self.assertFalse(x[0]["verified"])

    def test_product_name_labeled_in_registration_pdf_is_only_hint(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(("Trang 4", "Tên thương mại: AGIMOL 150")), {}
        )
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["field"], "PRODUCT_NAME")
        self.assertEqual(x[0]["value"], "AGIMOL 150")
        self.assertFalse(x[0]["verified"])

    def test_unlabeled_brand_is_never_guessed(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(("Trang 4", "AGIMOL 150")), {}
        )
        self.assertEqual(x, [])

    def test_adjacent_ocr_value_same_page(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(
                ("Trang 12 (OCR)", "Số đăng ký lưu hành"),
                ("Trang 12 (OCR)", "893110123456"),
            ), {}
        )
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["value"], "893110123456")
        self.assertIn("OCR", x[0]["reading_method"])

    def test_adjacent_different_page_rejected(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(
                ("Trang 3", "Số đăng ký"),
                ("Trang 4", "VD-12345-22"),
            ), {}
        )
        self.assertEqual(x, [])

    def test_unlabeled_number_rejected(self):
        x = extract_labeled_hints(
            "REGISTRATION",
            doc(("Trang 4", "VD-12345-22"), ("Trang 4", "AGICARVIR")), {}
        )
        self.assertEqual(x, [])

    def test_non_numeric_registration_caption_rejected(self):
        x = extract_labeled_hints(
            "REGISTRATION",
            doc(("Trang 1", "Số đăng ký: theo thông báo kèm theo")), {}
        )
        self.assertEqual(x, [])

    def test_gmp_fields_are_only_hints(self):
        x = extract_labeled_hints(
            "GMP_CERT", doc(
                ("Trang 1", "Số giấy chứng nhận GMP: GMP-2023-123"),
                ("Trang 1", "Phạm vi GMP: Dây chuyền thuốc viên"),
                ("Trang 2", "Ngày hết hạn GMP: 20/11/2027"),
            ), {}
        )
        self.assertEqual({row["field"] for row in x},
                         {"GMP_NUMBER", "GMP_SCOPE", "GMP_EXPIRY"})
        self.assertTrue(all(row["status"] == "GOI_Y_CAN_SO_BAN_GOC" for row in x))
        self.assertTrue(all(row["verified"] is False for row in x))

    def test_missing_date_not_inferred(self):
        x = extract_labeled_hints(
            "GMP_CERT", doc(("Trang 3", "Ngày hết hạn GMP: chờ xác minh")), {}
        )
        self.assertEqual(x, [])

    def test_existing_source_field_cannot_be_overwritten(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(("Trang 3", "Số đăng ký: VD-12345-22")),
            {"REGISTRATION_NO": "VN-00001-20"},
        )
        self.assertEqual(x, [])

    def test_multiple_values_preserved_and_flagged(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(
                ("Trang 1", "Số đăng ký: VD-12345-22"),
                ("Trang 2", "Số đăng ký: VN-67890-20"),
            ), {}
        )
        self.assertEqual(len(x), 2)
        self.assertEqual({row["value"] for row in x},
                         {"VD-12345-22", "VN-67890-20"})
        self.assertTrue(all("NHIEU_GIA_TRI" in row["status"] for row in x))

    def test_duplicate_on_same_page_deduplicated(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(
                ("Trang 1", "Số đăng ký: VD-12345-22"),
                ("Trang 1", "Số đăng ký: VD-12345-22"),
            ), {}
        )
        self.assertEqual(len(x), 1)

    def test_non_pdf_no_scan(self):
        x = extract_labeled_hints(
            "REGISTRATION",
            {"type": "docx", "sha256": SHA,
             "lines": [{"source": "Bảng 1", "text": "Số đăng ký: VD-12345-22"}]},
            {},
        )
        self.assertEqual(x, [])

    def test_non_primary_kind_no_auto_promote(self):
        x = extract_labeled_hints(
            "OTHER", doc(("Trang 1", "Số đăng ký: VD-12345-22")), {}
        )
        self.assertEqual(x, [])


    def test_split_colon_registration_label(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(
                ("Trang 4", "Số đăng ký lưu hành:"),
                ("Trang 4", "VD-12345-22"),
            ), {},
        )
        self.assertEqual(len(x), 1)
        self.assertEqual(x[0]["value"], "VD-12345-22")
        self.assertFalse(x[0]["verified"])

    def test_split_parenthetical_product_name_label(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(
                ("Trang 4", "Tên thuốc (biệt dược):"),
                ("Trang 4", "AGIMOL 150"),
            ), {},
        )
        self.assertEqual(x[0]["value"], "AGIMOL 150")

    def test_split_ocr_registration_abbreviation(self):
        x = extract_labeled_hints(
            "REGISTRATION", doc(
                ("Trang 12 (OCR)", "Số ĐK:"),
                ("Trang 12 (OCR)", "893110123456"),
            ), {},
        )
        self.assertEqual(x[0]["field"], "REGISTRATION_NO")
        self.assertIn("OCR", x[0]["reading_method"])

    def test_date_not_registration_number(self):
        self.assertEqual(extract_labeled_hints(
            "REGISTRATION", doc(("Trang 1", "Số đăng ký: 20/10/2026")), {}
        ), [])

    def test_diagnostic_does_not_claim_missing_document(self):
        source = doc(("Trang 4", "Văn bản chưa tách được nhãn SĐK"))
        source["pages"] = 8
        diagnosis = diagnose_proof_source("REGISTRATION", source, {}, [])
        self.assertEqual(diagnosis["hint_count"], 0)
        self.assertEqual(diagnosis["pages"], 8)
        self.assertIn("CAN_SO_PDF_GOC", diagnosis["status"])
        self.assertFalse(diagnosis["verified"])

    def test_multi_value_spacing_preserves_raw_value(self):
        x = extract_labeled_hints(
            "REGISTRATION",
            doc(("Trang 2", "Số đăng ký: VD - 12345 - 22")), {},
        )
        self.assertEqual(x[0]["value"], "VD - 12345 - 22")


    def test_ocr_context_keeps_source_not_suggested_sdk(self):
        source = doc(
            ("Trang 4 (OCR)", "Số đăng ký bị OCR cắt"),
            ("Trang 4 (OCR)", "893110123456"),
        )
        got = collect_proof_contexts("REGISTRATION", source)
        self.assertEqual(got[0]["source"], "Trang 4 (OCR)")
        self.assertEqual(got[0]["next_line"], "893110123456")
        self.assertEqual(got[0]["status"], "DOAN_VAN_CAN_SO_BAN_GOC")
        self.assertFalse(got[0]["verified"])
        self.assertNotIn("value", got[0])

    def test_no_cross_page_context(self):
        got = collect_proof_contexts(
            "REGISTRATION", doc(
                ("Trang 4", "Số đăng ký"),
                ("Trang 5", "VD-12345-22"),
            )
        )
        self.assertEqual(got[0]["next_line"], "")

    def test_limit_and_per_page_cap(self):
        source = doc(*[("Trang 2", "Thông tin đăng ký sản phẩm") for _ in range(10)])
        got = collect_proof_contexts("REGISTRATION", source)
        self.assertEqual(len(got), 5)
        self.assertTrue(all(not row["verified"] for row in got))

    def test_context_only_for_known_pdf_roles(self):
        source = doc(("Trang 1", "GMP certificate number 123"))
        self.assertEqual(collect_proof_contexts("OTHER", source), [])
        self.assertEqual(collect_proof_contexts("REGISTRATION", source), [])


if __name__ == "__main__":
    unittest.main()
