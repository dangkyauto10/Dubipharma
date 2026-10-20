"""SEE PRO AI gateway: regression with no external calls or real customer data."""
from __future__ import annotations

import hashlib
import json
import unittest
from unittest.mock import patch
from io import BytesIO

from openpyxl import Workbook

from see_pro_ai_review import (
    prepare_context, verify_model_output, review_with_gemini, AIReviewSchema,
    SUPPORTED_MODELS,
)


def response_dict(source_req="S0001", source_offer="S0002",
                  req_quote="G1.362 yêu cầu 4 mg", offer_quote="G1.362 cung cấp 4 mg",
                  code="G1.362", result="CO_THE_KHOP"):
    return {"document_note": "Cần chuyên viên rà soát", "comparisons": [{
        "lot_id": code, "field_name": "Hàm lượng",
        "required_spec": "4 mg", "offered_spec": "4 mg",
        "suggested_relation": result,
        "explanation": "Trích đoạn có nội dung tương ứng",
        "requirement_quote": {"source_id": source_req, "quote": req_quote},
        "offered_quote": {"source_id": source_offer, "quote": offer_quote},
    }]}


def context():
    docs = [
        {"file_id": "F001", "filename": "ehsmt.pdf", "sha256": "abc", "verified": False},
        {"file_id": "F002", "filename": "hdst.pdf", "sha256": "def", "verified": False},
    ]
    return {"lot_code": "G1.362", "context_sha256": "testhash", "documents": docs,
            "matching_lines": 2, "warnings": [], "context_truncated": False,
            "excerpts": [
                {"source_id": "S0001", "filename": "ehsmt.pdf", "sha256": "abc",
                 "locator": "Trang 25", "text": "G1.362 yêu cầu 4 mg"},
                {"source_id": "S0002", "filename": "hdst.pdf", "sha256": "def",
                 "locator": "Trang 18", "text": "G1.362 cung cấp 4 mg"},
            ]}


class DummyModels:
    def __init__(self, parsed):
        self.calls = []
        self.parsed = parsed
    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return type("Response", (), {"parsed": self.parsed, "text": None})()


class DummyClient:
    def __init__(self, parsed):
        self.models = DummyModels(parsed)
        self.files = object()  # If the engine attempted an upload, it would fail.


class EvidenceAITests(unittest.TestCase):
    def test_two_real_quotes_are_linked_but_not_approved(self):
        result = verify_model_output(context(), response_dict())
        finding = result["findings"][0]
        self.assertTrue(finding["TRICH_DAN_KHOP_NGUON"])
        self.assertFalse(finding["DA_XAC_MINH_KY_THUAT"])
        self.assertFalse(finding["DUOC_TU_DONG_KET_LUAN"])
        self.assertEqual(finding["CHUNG_CU_YEU_CAU"]["locator"], "Trang 25")
        self.assertEqual(finding["CHUNG_CU_DE_XUAT"]["file"], "hdst.pdf")

    def test_fake_quote_cannot_pass_local_audit(self):
        f = verify_model_output(context(), response_dict(req_quote="không hề có nguồn"))
        self.assertFalse(f["findings"][0]["TRICH_DAN_KHOP_NGUON"])
        self.assertEqual(f["findings"][0]["CHUNG_CU_YEU_CAU"]["reason"],
                         "TRICH_DAN_KHONG_CO_TRONG_NGUON")

    def test_unknown_source_id_and_wrong_lot_are_rejected(self):
        a = verify_model_output(context(), response_dict(source_req="S9999"))
        b = verify_model_output(context(), response_dict(code="G1.363"))
        self.assertFalse(a["findings"][0]["TRICH_DAN_KHOP_NGUON"])
        self.assertFalse(b["findings"][0]["TRICH_DAN_KHOP_NGUON"])

    def test_same_excerpt_both_sides_insufficient(self):
        f = verify_model_output(context(), response_dict(
            source_offer="S0001", offer_quote="G1.362 yêu cầu 4 mg"))
        self.assertFalse(f["findings"][0]["TRICH_DAN_KHOP_NGUON"])

    def test_missing_evidence_is_not_boolean_false_positive(self):
        response = response_dict()
        response["comparisons"][0]["offered_quote"] = None
        response["comparisons"][0]["suggested_relation"] = "CHUA_DU_CHUNG_CU"
        f = verify_model_output(context(), response)
        self.assertEqual(f["findings"][0]["TRANG_THAI"],
                         "CHUA_DU_CHUNG_CU_KHONG_DUOC_KET_LUAN")

    def test_explicit_approval_required_for_api_call(self):
        client = DummyClient(response_dict())
        with self.assertRaises(PermissionError):
            review_with_gemini(context(), api_key="test-placeholder",
                               client=client, explicitly_authorized=False)
        self.assertEqual(client.models.calls, [])

    def test_api_receives_snippets_only_and_parsed_checked(self):
        client = DummyClient(AIReviewSchema.model_validate(response_dict()))
        report = review_with_gemini(context(), api_key="test-placeholder",
                                    explicitly_authorized=True, client=client)
        self.assertEqual(len(client.models.calls), 1)
        self.assertIn("S0001", client.models.calls[0]["contents"])
        self.assertEqual(client.models.calls[0]["model"], "gemini-3.8-flash")
        self.assertEqual(report["provider"], "Google Gemini Developer API")
        self.assertTrue(report["external_text_sent"])
        self.assertNotIn("DA_XAC_MINH", report["findings"][0]["TRANG_THAI"])

    def test_model_allowlist_and_api_key_required(self):
        with self.assertRaises(ValueError):
            review_with_gemini(context(), api_key="", explicitly_authorized=True,
                               client=DummyClient(response_dict()))
        with self.assertRaises(ValueError):
            review_with_gemini(context(), api_key="placeholder", model="fake-model",
                               explicitly_authorized=True,
                               client=DummyClient(response_dict()))

    def test_prepare_context_lot_specific_and_trace_sha(self):
        wb = Workbook()
        s = wb.active
        s["A1"] = "G1.362 yêu cầu 4 mg"
        s["A2"] = "G1.999 yêu cầu 8 mg"
        f = BytesIO()
        wb.save(f)
        raw = f.getvalue()
        c = prepare_context([("evidence.xlsx", raw)], lot_code="G1.362")
        self.assertEqual(c["matching_lines"], 1)
        self.assertEqual(c["documents"][0]["sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(c["excerpts"][0]["source_id"], "S0001")
        self.assertTrue(c["context_sha256"])
        self.assertFalse(c["verified"])

    def test_empty_code_and_overlimit_documents_fail(self):
        with self.assertRaises(ValueError):
            prepare_context([("x.pdf", b"%PDF-")], lot_code="")
        with self.assertRaises(ValueError):
            prepare_context([("x.pdf", b"%PDF-")] * 9, lot_code="G1.362")

    def test_truncated_context_cannot_claim_full_document_review(self):
        c = context()
        c["context_truncated"] = True
        report = verify_model_output(c, {"document_note": "x", "comparisons": []})
        self.assertTrue(any("một phần trích đoạn" in w for w in report["warnings"]))
        self.assertFalse(report["is_full_document_review"])
        self.assertFalse(report["verified"])

    def test_schema_refuses_made_up_status_and_extra_fields(self):
        invalid = response_dict()
        invalid["comparisons"][0]["suggested_relation"] = "DA_XAC_NHAN_DAT"
        with self.assertRaises(Exception):
            AIReviewSchema.model_validate(invalid)
        invalid2 = response_dict()
        invalid2["secret_action"] = "delete spreadsheet"
        with self.assertRaises(Exception):
            AIReviewSchema.model_validate(invalid2)


if __name__ == "__main__":
    unittest.main()
