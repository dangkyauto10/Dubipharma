import unittest

from tdv_demo_core import (
    demo_audit, exact_strength_mg, legal_evidence,
    make_synthetic_pdf, match_fields, read_pdf_pages,
)


class TDVReadOnlyIDPTests(unittest.TestCase):
    def setUp(self):
        self.lot = {"hoat_chat": "Acenocoumarol", "ham_luong": "4 mg",
                    "dang_bao_che": "Viên nén", "duong_dung": "Uống"}

    def test_strength_incompatible_1_and_4(self):
        self.assertEqual(
            match_fields(self.lot, dict(self.lot, ham_luong="1 mg"))["status"],
            "KHONG_KHOP")

    def test_strength_incompatible_4_and_40(self):
        self.assertEqual(
            match_fields(self.lot, dict(self.lot, ham_luong="40 mg"))["status"],
            "KHONG_KHOP")

    def test_strength_units_exact_conversion(self):
        self.assertEqual(exact_strength_mg("1 g"), exact_strength_mg("1000 mg"))

    def test_ambiguous_numeric_text_is_not_accepted(self):
        self.assertIsNone(exact_strength_mg("1,000 mg"))

    def test_complex_dose_does_not_silently_match(self):
        self.assertEqual(
            match_fields(self.lot, dict(self.lot, ham_luong="4 mg/ml"))["status"],
            "CAN_XAC_MINH")

    def test_missing_drug_active_is_uncertain(self):
        self.assertEqual(
            match_fields(self.lot, dict(self.lot, hoat_chat=""))["status"],
            "CAN_XAC_MINH")

    def test_match_is_not_legal_approval(self):
        result = match_fields(self.lot, dict(self.lot))
        self.assertEqual(result["status"], "KHOP_4_TRUONG")
        self.assertFalse(result["verified"])
        self.assertFalse(result["bid_eligible"])

    def test_gmp_from_wrong_factory_is_blocked(self):
        self.assertEqual(
            legal_evidence("Giấy chứng nhận GMP", "Mỹ Thới", "Bình Hòa")["status"],
            "CHAN_LIEN_KET")

    def test_letter_is_not_gmp_extension(self):
        self.assertEqual(
            legal_evidence("Công văn giải trình", "Mỹ Thới", "Mỹ Thới")["status"],
            "CHUNG_CU_BO_SUNG")

    def test_demo_report_has_expected_safety_blocks(self):
        r = demo_audit()
        self.assertEqual(r["different_strength"]["status"], "KHONG_KHOP")
        self.assertEqual(r["wrong_gmp_factory"]["status"], "CHAN_LIEN_KET")

    def test_real_two_reader_pdf_extraction_on_synthetic_data(self):
        output = read_pdf_pages(make_synthetic_pdf(), maximum=4)
        self.assertEqual(output["total_pages"], 2)
        self.assertEqual(output["pages_read"], 2)
        self.assertIn("G1.003", output["pages"][0]["PyMuPDF"])
        self.assertIn("1 mg", output["pages"][0]["PyMuPDF"])
        self.assertIn("G1.004", output["pages"][1]["PyMuPDF"])
        self.assertFalse(output["verified"])

    def test_pdf_page_limits_do_not_claim_full_read(self):
        output = read_pdf_pages(make_synthetic_pdf(), first=1, maximum=1)
        self.assertEqual(output["pages_read"], 1)
        self.assertTrue(any("chưa đọc toàn bộ" in w for w in output["warnings"]))

    def test_pdf_invalid_page_and_limits_fail(self):
        data = make_synthetic_pdf()
        with self.assertRaises(ValueError):
            read_pdf_pages(data, first=0)
        with self.assertRaises(ValueError):
            read_pdf_pages(data, maximum=99)


if __name__ == "__main__":
    unittest.main()
