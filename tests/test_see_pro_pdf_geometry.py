"""Geometry parser tests: synthetic layout fixtures, never auto-approve fields."""
import unittest
import pymupdf
from see_pro_pdf_geometry import extract_g1_technical


class GeometryTests(unittest.TestCase):
    def test_one_technical_lot_matches_summary_arithmetic(self):
        pdf = pymupdf.open()
        p = pdf.new_page(width=841.89, height=595.28)
        for x, y, s in [
            (83, 265, "PP260042"), (83, 284, "8741"),
            (150, 265, "G1.362"), (230, 265, "Hydroxypropyl"),
            (287, 265, "45mg/15ml"), (345, 265, "Nho"),
            (401, 265, "Thuoc"), (455, 265, "Lo"),
            (503, 265, "17.250"), (558, 265, "32.800"), (628, 265, "4"),
        ]:
            p.insert_text((x, y), s, fontsize=11)
        source = {"lots": [{
            "MA_THUOC": "G1.362", "MA_PHAN_LO": "PP2600428741",
            "GIA_TRI_UOC_TINH": 565800000,
        }]}
        result = extract_g1_technical(pdf.tobytes(), source)
        pdf.close()
        self.assertEqual(result["found_rows"], 1)
        self.assertEqual(result["financial_crosschecked"], 1)
        self.assertEqual(result["part_crosschecked"], 1)
        row = result["rows"][0]
        self.assertFalse(row["verified"])
        self.assertEqual(row["SO_LUONG_CHINH"], 17250)
        self.assertEqual(row["DON_GIA_KE_HOACH"], 32800)
        self.assertEqual(row["EVIDENCE"]["SO_LUONG_CHINH"]["pages"], [1])

    def test_crosspage_numeric_continuation(self):
        pdf = pymupdf.open()
        a = pdf.new_page(width=841.89, height=595.28)
        for x, y, t in [(83, 534, "PP260042"), (150, 534, "G1.002"),
                        (503, 534, "121.00"), (561, 534, "4.450")]:
            a.insert_text((x, y), t, fontsize=11)
        b = pdf.new_page(width=841.89, height=595.28)
        for x, y, t in [(83, 200, "8381"), (519, 200, "0"),
                        (150, 337, "G1.003")]:
            b.insert_text((x, y), t, fontsize=11)
        source = {"lots": [{
            "MA_THUOC": "G1.002", "MA_PHAN_LO": "PP2600428381",
            "GIA_TRI_UOC_TINH": 538450000,
        }]}
        result = extract_g1_technical(pdf.tobytes(), source)
        pdf.close()
        self.assertEqual(result["financial_crosschecked"], 1)
        self.assertEqual(result["part_crosschecked"], 1)
        self.assertEqual(result["rows"][0]["TRANG_CHUNG_CU"], [1, 2])

    def test_wrong_amount_requires_review_not_inference(self):
        pdf = pymupdf.open()
        p = pdf.new_page(width=841.89, height=595.28)
        for x, y, t in [(83, 250, "PP260042"), (83, 270, "8741"),
                        (150, 250, "G1.362"), (503, 250, "17.250"),
                        (561, 250, "32.800")]:
            p.insert_text((x, y), t, fontsize=11)
        source = {"lots": [{
            "MA_THUOC": "G1.362", "MA_PHAN_LO": "PP2600428741",
            "GIA_TRI_UOC_TINH": 123456789,
        }]}
        result = extract_g1_technical(pdf.tobytes(), source)
        pdf.close()
        self.assertEqual(result["financial_crosschecked"], 0)
        self.assertFalse(result["verified"])
        self.assertTrue(any(item["type"] == "MATH_OR_EXTRACTION_MISMATCH"
                            for item in result["findings"]))


if __name__ == "__main__":
    unittest.main()
