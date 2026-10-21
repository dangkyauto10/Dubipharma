"""Regression of NSX source extraction diagnostics and non-misleading N/A ratio.

Synthetic only: neither uploaded customer records nor manufacturer credentials.
"""
import unittest
from tdv_nsx_workbench import diagnose_extracted_documents
from tdv_leadership_report import compare_sources


class NSXDiagnosticQA(unittest.TestCase):
    def test_empty_nsx_has_no_percentage_not_zero(self):
        tender = {"rows": [{
            "MA_THUOC":"G1.001", "HOAT_CHAT_HSMT":"Acarbose",
            "NONG_DO_HAM_LUONG":"50mg",
            "DUONG_DUNG":"Uống", "DANG_BAO_CHE":"Viên",
            "FILE_NGUON":"public_ehsmt.xlsx"
        }]}
        report = compare_sources(tender, {
            "products": [], "files": [{"filename":"proof.pdf"}],
            "sources": [], "traceability": {"products":[]},
            "warnings":[], "review_queue":[]
        })
        self.assertIsNone(report["summary"]["matching_percent_preliminary"])
        self.assertIsNone(report["comparison"][0]["TY_LE_KHOP_SO_BO"])
        self.assertEqual(report["summary"]["green_criteria_preliminary"],0)
        self.assertEqual(report["summary"]["yellow_criteria"],4)
        self.assertEqual(report["summary"]["red_mismatch_preliminary"],0)
        self.assertFalse(report["verified"])

    def test_no_raw_sensitive_values_in_diagnostic_table(self):
        report={
            "files":[
                {"filename":"registration_1.pdf","kind":"REGISTRATION",
                 "kind_label":"Giấy đăng ký lưu hành",
                 "role_confidence":"GỢI_Ý_CẦN_XÁC_MINH"},
                {"filename":"registration_2.pdf","kind":"REGISTRATION",
                 "kind_label":"Giấy đăng ký lưu hành",
                 "role_confidence":"GỢI_Ý_CẦN_XÁC_MINH"}],
            "sources":[
                {"complete_read":True, "fields":{"PRODUCT_NAME":"SECRET PRODUCT",
                 "REGISTRATION_NO":"SECRET-CODE", "INGREDIENT":"Secret Compound"},
                 "conflicts":{}},
                {"complete_read":True,"fields":{"REGISTRATION_NO":"SECRET-2"},
                 "conflicts":{}}
            ],
        }
        result=diagnose_extracted_documents(report)
        self.assertEqual(result[0]["Tên thuốc trong nội dung"],"CÓ")
        self.assertEqual(result[1]["Tên thuốc trong nội dung"],"CHƯA TRÍCH")
        self.assertIn("THIẾU",result[1]["Nguyên nhân / bước tiếp"])
        self.assertNotIn("SECRET",str(result))
        self.assertEqual(len(result),2)

    def test_incomplete_pdf_remains_a_warning(self):
        diag=diagnose_extracted_documents({
            "files":[{"filename":"scan.pdf","kind":"REGISTRATION",
                "role_confidence":"GỢI_Ý_CẦN_XÁC_MINH"}],
            "sources":[{"complete_read":False,"fields":{},"conflicts":{}}]
        })
        self.assertIn("OCR",diag[0]["Nguyên nhân / bước tiếp"])


if __name__=="__main__":
    unittest.main()
