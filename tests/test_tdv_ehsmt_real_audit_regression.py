"""Synthetic E-HSMT business QA. Actual G1-SYT.pdf remains user-held.

Checks per-field citation, page in Word/Excel, document-category conflict,
and conservative two-source ingredient comparison. Never verifies a drug.
"""
import unittest
from io import BytesIO
from openpyxl import load_workbook
import pymupdf

from see_pro_workbench import analyze_uploads, _compare_two_ingredient_strings
from see_pro_quality_gate import audit_ehsmt
from see_pro_traceability import build_audit_workbook
from tdv_leadership_report import compare_sources


def synthetic_g1_pdf(*, ambiguous_heading=False):
    doc=pymupdf.open()
    p=doc.new_page(width=842,height=595)
    if ambiguous_heading:
        p.insert_text((35,40),"Ket qua lua chon nha thau")
    p.insert_text((35,100),"1 PP2600428380 G1.001 Acarbose 69.300.000 1.039.500")
    data=doc.tobytes()
    doc.close()
    return data


class RealBusinessAuditRegression(unittest.TestCase):
    def test_summary_ingredient_has_specific_pdf_page_and_hash(self):
        data=analyze_uploads([("synthetic_G1.pdf",synthetic_g1_pdf())])
        self.assertEqual(len(data["input_files"]),1)
        self.assertEqual(len(data["rows"]),1)
        drug=data["rows"][0]
        self.assertEqual(drug["MA_THUOC"],"G1.001")
        self.assertEqual(drug["HOAT_CHAT_HSMT"],"Acarbose")
        self.assertEqual(drug["EVIDENCE"]["HOAT_CHAT_HSMT"]["page"],1)
        self.assertEqual(drug["EVIDENCE"]["HOAT_CHAT_HSMT"]["source"],"synthetic_G1.pdf")
        self.assertIn("Acarbose",drug["EVIDENCE"]["HOAT_CHAT_HSMT"]["raw"])
        self.assertEqual(drug["EVIDENCE"]["HOAT_CHAT_HSMT"]["sha256"],drug["SHA256"])
        self.assertFalse(drug["EVIDENCE"]["HOAT_CHAT_HSMT"]["verified"])
        self.assertEqual(data["quality_gate"]["coverage"]["HOAT_CHAT_HSMT"]["values"],1)
        self.assertEqual(data["quality_gate"]["coverage"]["HOAT_CHAT_HSMT"]["field_cited"],1)
        self.assertFalse(data["quality_gate"]["accuracy_validated"])

    def test_excel_and_leadership_keep_actual_summary_page(self):
        analysis=analyze_uploads([("synthetic_G1.pdf",synthetic_g1_pdf())])
        wb=load_workbook(BytesIO(build_audit_workbook(analysis)),read_only=True)
        try:
            trace=list(wb["TRUY_XUAT_CHUNG_CU"].values)
            match=[r for r in trace if "HOAT_CHAT_HSMT" in r]
            self.assertEqual(len(match),1)
            self.assertIn(1,match[0])
        finally:
            wb.close()
        report=compare_sources(analysis,{"products":[],"files":[]})
        c=report["comparison"][0]["criteria"][0]
        self.assertIn("Trang 1",c["ehsmt_evidence"]["location"])
        self.assertTrue(c["ehsmt_evidence"]["sha256"])

    def test_missing_field_proof_is_explicit_issue_not_zero(self):
        row={"FILE_NGUON":"some.pdf","MA_THUOC":"G1.001",
             "HOAT_CHAT_HSMT":"Acarbose"}
        quality=audit_ehsmt({"rows":[row], "documents":[
            {"Tệp":"some.pdf","Đọc toàn bộ":True},
        ]})
        self.assertEqual(quality["coverage"]["HOAT_CHAT_HSMT"]["field_cited"],0)
        self.assertIn("TRUONG_EHSMT_THIEU_CHUNG_CU_RIENG",
                      {r["type"] for r in quality["issues"]})
        self.assertTrue(quality["issue_count"])

    def test_previous_unresolved_warning_must_not_vanish(self):
        quality=audit_ehsmt({"documents":[{"Tệp":"some.pdf","Đọc toàn bộ":True}],
                             "rows":[{"MA_THUOC":"G1.001"}],
                             "warnings":["Mã BP chưa xác minh"]})
        self.assertIn("CANH_BAO_NGHIEP_VU_CHUA_GIAI_QUYET",
                      {r["type"] for r in quality["issues"]})

    def test_technical_disagreement_never_rewrites_summary(self):
        self.assertEqual(
            _compare_two_ingredient_strings("Acetyl leucin","Acetylleucin"),
            "CUNG_CHUOI_CHUA_XAC_MINH")
        self.assertEqual(
            _compare_two_ingredient_strings("Acarbose","Acyclovir"),
            "KHAC_CHUOI_CAN_SO_GOC")
        self.assertEqual(
            _compare_two_ingredient_strings("Acarbose",""),
            "THIEU_HOAT_CHAT_KY_THUAT")
        quality=audit_ehsmt({"rows":[{"MA_THUOC":"G1.001",
            "HOAT_CHAT_HSMT":"Acarbose", "DOI_CHIEU_HOAT_CHAT_HAI_BANG":
            "KHAC_CHUOI_CAN_SO_GOC"}]})
        self.assertIn("HOAT_CHAT_TONG_HOP_KY_THUAT_KHAC_CHUOI_CAN_SO_GOC",
                      {x["type"] for x in quality["issues"]})

    def test_ambiguous_classification_not_silently_selection_result(self):
        data=analyze_uploads([("synthetic.pdf",synthetic_g1_pdf(
            ambiguous_heading=True))])
        self.assertEqual(len(data["rows"]),1)
        self.assertTrue(data["tender_documents"])
        category=data["tender_documents"][0]
        self.assertEqual(category["kind"],"CAN_XAC_MINH_LOAI")
        self.assertIn("KET_QUA_LCNT",category["classification_conflict"])
        self.assertTrue(any("mâu thuẫn loại tài liệu" in x
                            for x in data["warnings"]))
        self.assertTrue(any(x["type"]=="CANH_BAO_NGHIEP_VU_CHUA_GIAI_QUYET"
                            for x in data["quality_gate"]["issues"]))

    def test_770_source_rows_are_not_770_proven_accuracies(self):
        source=analyze_uploads([("g1.pdf",synthetic_g1_pdf())])["rows"][0]
        rows=[]
        for i in range(770):
            row=dict(source)
            row["MA_THUOC"]=f"G1.{i+1:03d}"
            rows.append(row)
        audit=audit_ehsmt({"rows":rows, "documents":[{
            "Tệp":"g1.pdf", "Đọc toàn bộ":True}]})
        self.assertEqual(audit["coverage"]["HOAT_CHAT_HSMT"]["values"],770)
        self.assertEqual(audit["coverage"]["HOAT_CHAT_HSMT"]["field_cited"],770)
        self.assertIsNone(audit["accuracy_rate"])
        self.assertFalse(audit["legal_verified"])

if __name__=="__main__":
    unittest.main()
