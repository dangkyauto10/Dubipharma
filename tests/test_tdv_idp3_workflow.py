import json
import unittest

from tdv_idp3_workflow import (extract_pdf, read_ehsmt, read_nsx_package,
    leadership_report, report_text, make_demo_ehsmt, make_demo_nsx, MAX_PAGES)


class EhsmtNsxLeadershipPipelineTests(unittest.TestCase):
    def setUp(self):
        self.ehsmt = make_demo_ehsmt()
        product, docs = make_demo_nsx()
        self.product_pdf = product
        self.attachments = docs

    def test_read_two_lots_every_page(self):
        report = read_ehsmt(self.ehsmt)
        self.assertTrue(report["complete"])
        self.assertEqual(report["lot_count"], 2)
        self.assertEqual([r["fields"]["ham_luong"] for r in report["lots"]], ["1 mg", "4 mg"])

    def test_field_evidence_hash_and_page(self):
        report = read_ehsmt(self.ehsmt)
        e = report["lots"][1]["evidence"]["ham_luong"]
        self.assertEqual(e["page"], 2)
        self.assertEqual(e["sha256"], report["sha256"])
        self.assertIn("Strength: 4 mg", e["excerpt"])
        self.assertFalse(e["verified"])

    def test_nsx_all_attachments_are_scanned(self):
        report = read_nsx_package(self.product_pdf, self.attachments)
        self.assertEqual(len(report["documents"]), 3)
        self.assertTrue(report["complete"])
        self.assertFalse(report["verified"])
        self.assertTrue(all(d["link_status"] == "CAN_XAC_MINH" for d in report["documents"]))

    def test_report_one_prelim_match_one_mismatch(self):
        a = read_ehsmt(self.ehsmt)
        b = read_nsx_package(self.product_pdf, self.attachments)
        report = leadership_report(a, b)
        self.assertEqual(report["summary"]["lots"], 2)
        self.assertEqual(report["summary"]["technical_prelim_match"], 1)
        self.assertEqual(report["summary"]["technical_conflict"], 1)
        self.assertFalse(report["final_approval"])
        self.assertTrue(all(not i["bid_eligible"] for i in report["items"]))
        self.assertTrue(all(not i["gmp_confirmed"] and not i["price_approved"] for i in report["items"]))

    def test_report_without_nsx_marks_uncertainty(self):
        r = leadership_report(read_ehsmt(self.ehsmt), None)
        self.assertTrue(all(i["technical"] == "CAN_XAC_MINH" for i in r["items"]))

    def test_missing_gmp_quote_authorization_warns(self):
        r = leadership_report(read_ehsmt(self.ehsmt), read_nsx_package(self.product_pdf, []))
        self.assertIn("Chưa nạp GMP", r["items"][0]["reasons"])
        self.assertIn("Chưa nạp Báo giá", r["items"][0]["reasons"])
        self.assertIn("Chưa nạp Ủy quyền", r["items"][0]["reasons"])

    def test_wrong_factory_gmp_blocked(self):
        from tdv_idp3_workflow import _pdf
        bad = _pdf(["FAKE GMP", "Factory ID: FACTORY-DEMO-B"])
        s = read_nsx_package(self.product_pdf, [("GMP_CERT", bad)])
        self.assertEqual(s["documents"][0]["link_status"], "CHAN_LIEN_KET")

    def test_wrong_quote_product_blocked(self):
        from tdv_idp3_workflow import _pdf
        bad = _pdf(["FAKE QUOTE", "Product ID: WRONG", "Factory ID: FACTORY-DEMO-A"])
        s = read_nsx_package(self.product_pdf, [("QUOTE", bad)])
        self.assertEqual(s["documents"][0]["link_status"], "CHAN_LIEN_KET")

    def test_ocr_does_not_claim_verified(self):
        r = extract_pdf(self.ehsmt, ocr=True)
        self.assertFalse(r["verified"])
        self.assertEqual(r["pages_processed"], 2)

    def test_limit_causes_incomplete_status(self):
        r = extract_pdf(self.ehsmt, max_pages=1)
        self.assertFalse(r["complete"])
        self.assertIn("1/2", " ".join(r["warnings"]))

    def test_bad_pdf_rejected(self):
        with self.assertRaises(ValueError):
            extract_pdf(b"not a PDF")
        with self.assertRaises(ValueError):
            extract_pdf(self.ehsmt, max_pages=MAX_PAGES + 1)

    def test_source_is_not_persisted_in_return(self):
        a = read_ehsmt(self.ehsmt)
        b = read_nsx_package(self.product_pdf, self.attachments)
        dump = json.dumps(leadership_report(a, b), ensure_ascii=False)
        self.assertNotIn("%PDF-", dump)
        self.assertNotIn("raw_bytes", dump)

    def test_report_text_is_safe_preliminary(self):
        r = leadership_report(read_ehsmt(self.ehsmt), read_nsx_package(self.product_pdf, self.attachments))
        txt = report_text(r)
        self.assertIn("CHUA PHE DUYET", txt)
        self.assertIn("LOT-DEMO-02", txt)

    def test_gmp_explanation_not_certificate(self):
        from tdv_idp3_workflow import _pdf
        fake = _pdf(["DEMO LETTER", "Factory ID: FACTORY-DEMO-A"])
        s = read_nsx_package(self.product_pdf, [("GMP_EXPLANATION", fake)])
        self.assertEqual(s["documents"][0]["link_status"], "CHUNG_CU_BO_SUNG")


if __name__ == "__main__":
    unittest.main()
