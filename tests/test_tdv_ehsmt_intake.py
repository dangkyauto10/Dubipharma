import io
import unittest
import pymupdf
from tdv_ehsmt_intake import inspect_ehsmt_pdf, export_ehsmt_csv

class IntakeTests(unittest.TestCase):
    def test_two_page_pdf_and_dedup(self):
        pdf = pymupdf.open()
        for value in ("PP2600428380 G1.001 Acarbose", "G1.001 Acarbose; G1.002 Aceclofenac"):
            page = pdf.new_page()
            page.insert_text((72, 72), value)
        result = inspect_ehsmt_pdf(pdf.tobytes())
        self.assertEqual(result["total_pages"], 2)
        self.assertEqual(result["lot_count"], 2)
        self.assertEqual(result["lots"][0]["TRANG_NGUON"], [1, 2])
        self.assertEqual(result["lots"][0]["MA_PHAN_LO"], "PP2600428380")
        self.assertFalse(result["verified"])
        self.assertEqual(result["summary_rows"], 0)
        self.assertEqual(len(result["missing_summary"]), 2)
        self.assertIn(b"G1.001", export_ehsmt_csv(result))
    def test_summary_row_extraction(self):
        pdf = pymupdf.open()
        page = pdf.new_page()
        page.insert_text((72, 72), "3    PP2600428382  G1.003    Acenocoumarol     32.040.000    480.600")
        result = inspect_ehsmt_pdf(pdf.tobytes())
        self.assertEqual(result["summary_rows"], 1)
        lot = result["lots"][0]
        self.assertEqual(lot["HOAT_CHAT_CHUAN"], "Acenocoumarol")
        self.assertEqual(lot["GIA_TRI_UOC_TINH"], 32040000)
        self.assertEqual(lot["BAO_DAM_DU_THAU"], 480600)
        self.assertEqual(lot["TRANG_BANG_TONG_HOP"], 1)
    def test_invalid_pdf_rejected(self):
        with self.assertRaises(ValueError):
            inspect_ehsmt_pdf(b"not a pdf")
if __name__ == "__main__":
    unittest.main()
