"""Focused synthetic regression tests: no real tender or manufacturer documents."""
import hashlib
import unittest
from copy import deepcopy
from unittest.mock import patch

import tdv_nsx_gmp_guarded_auto as guard


def batch(name: str, kind: str = "GMP_CERT", sha: str = ""):
    raw = b"artificial-GMP-only"
    sha = sha or hashlib.sha256(raw).hexdigest()
    products = [
        {"uid": f"P{i:04d}", "file": "mock-catalogue.xlsx",
         "fields": {}, "evidence": {},
         "conflicts": {"STRENGTH": ["a", "b"]} if i <= 29 else {}}
        for i in range(1, 48)
    ]
    report = {
        "files": [{"filename": name, "sha256": sha, "kind": kind,
                   "kind_label": "GMP (chưa xác minh)", "reasons": []}],
        "sources": [{"filename": name, "sha256": sha, "kind": kind,
                     "fields": {}, "evidence": {}, "complete_read": True}],
        "products": products,
        "links": [{"source_evidence": name, "source_sha256": sha,
                   "evidence_kind": kind, "product_id": "P0001"}],
        "review_queue": [], "warnings": [],
        "summary": {"linked": 1, "review": 0, "products": 47},
    }
    return report, [(name, raw)]


class GMPTypeBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.hints = patch.object(
            guard, "discover_evidence_candidates",
            side_effect=lambda p, files, sources: {
                "summary": {"registration_hints": 0,
                            "factory_source_groups": sum(
                                f["kind"] == "GMP_CERT" for f in files),
                            "unresolved_evidence": sum(
                                f["kind"] == "OTHER" for f in files)}})
        self.trace = patch.object(
            guard, "build_reverse_dossiers",
            side_effect=lambda r: {"linked": len(r["links"])})
        self.hints.start()
        self.trace.start()
        self.addCleanup(self.hints.stop)
        self.addCleanup(self.trace.stop)

    def test_filename_only_flags_and_unlinks(self):
        report, files = batch("3.1 Công văn giải trình GMP AGP.pdf")
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda name, raw: [])
        self.assertEqual(actual["files"][0]["kind"], "OTHER")
        self.assertEqual(actual["sources"][0]["kind"], "OTHER")
        self.assertEqual(actual["summary"]["linked"], 0)
        self.assertEqual(actual["review_queue"][0]["status"],
                         "CAN_XAC_DINH_LOAI_GMP")
        self.assertEqual(actual["summary"]["factory_source_groups"], 0)
        self.assertEqual(len(actual["products"]), 47)
        self.assertEqual(sum(bool(p["conflicts"]) for p in actual["products"]), 29)

    def test_explicit_letter_is_supplement_and_never_a_gmp_link(self):
        report, files = batch("3.1 Công văn giải trình GMP AGP.pdf")
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda n, raw: [
                {"text": "Công văn giải trình GMP của nhà máy"}])
        self.assertEqual(actual["files"][0]["kind"], "GMP_EXPLANATION")
        self.assertEqual(actual["summary"]["linked"], 0)

    def test_maintenance_note_is_supplement(self):
        report, files = batch("3.3 Giấy xác nhận duy trì GMP - Mỹ Thới.pdf")
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda n, raw: [
                {"text": "Giấy xác nhận duy trì đáp ứng GMP"}])
        self.assertEqual(actual["files"][0]["kind"], "GMP_EXPLANATION")

    def test_conflicting_titles_cannot_become_certificate(self):
        report, files = batch("3.1 Công văn giải trình GMP AGP.pdf")
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda n, raw: [
                {"text": "Công văn giải trình GMP; Giấy chứng nhận GMP"}])
        self.assertEqual(actual["files"][0]["kind"], "OTHER")

    def test_normal_certificate_is_unchanged(self):
        report, files = batch("3 GCN GMP - Agimexpharm (2023).signed.pdf")
        original = deepcopy(report)
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda n, raw: [
                {"text": "Giấy chứng nhận GMP"}])
        self.assertEqual(actual, original)

    def test_mismatched_sha_fails_closed(self):
        report, files = batch("3 GCN GMP - Agimexpharm (2023).signed.pdf",
                              sha="a" * 64)
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda n, raw: [])
        self.assertEqual(actual["files"][0]["kind"], "OTHER")
        self.assertEqual(actual["links"], [])

    def test_registration_unaffected(self):
        report, files = batch("7. AGIMOL 150.pdf", kind="REGISTRATION")
        original = deepcopy(report)
        self.assertEqual(guard.reconcile_gmp_roles(report, files), original)

    def test_unmodified_conflicts_and_51_pair_records(self):
        report, files = batch("3.1 Công văn giải trình GMP AGP.pdf")
        report["source_conflict_pairs"] = [
            {"source_1": "40mg", "source_2": "40mg/4ml"} for _ in range(51)]
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda n, raw: [])
        self.assertEqual(len(actual["source_conflict_pairs"]), 51)
        self.assertEqual(len(actual["products"]), 47)
        self.assertEqual(sum(bool(p["conflicts"]) for p in actual["products"]), 29)


    def test_existing_review_entries_do_not_keep_old_gmp_certificate_label(self):
        report, files = batch("3.1 Công văn giải trình GMP AGP.pdf")
        report["review_queue"] = [{
            "file": files[0][0],
            "kind": "GMP_CERT",
            "status": "CHUA_DU_CHUNG_CU",
            "candidate_products": [],
            "reason": "Không tìm được liên kết duy nhất",
        }]
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda name, raw: []
        )
        self.assertEqual(actual["review_queue"][0]["kind"], "OTHER")
        self.assertIn("bị hủy", actual["review_queue"][0]["reason"])
        self.assertEqual(actual["review_queue"][0]["status"], "CHUA_DU_CHUNG_CU")
        self.assertEqual(actual["review_queue"][1]["status"], "CAN_XAC_DINH_LOAI_GMP")
        self.assertEqual(actual["summary"]["review"], 2)

    def test_review_does_not_change_unrelated_product_label(self):
        report, files = batch("3.3 Giấy xác nhận duy trì GMP - Mỹ Thới.pdf")
        report["review_queue"] = [
            {"file": "Biểu 05 .xlsx", "kind": "PRODUCT", "status": "MAU_THUAN_GIUA_CAC_SHEET",
             "reason": "Nguồn gốc mâu thuẫn", "candidate_products": ["P0001"]},
        ]
        actual = guard.reconcile_gmp_roles(
            report, files, heading_reader=lambda name, raw: []
        )
        self.assertEqual(actual["review_queue"][0]["kind"], "PRODUCT")
        self.assertEqual(actual["review_queue"][0]["status"], "MAU_THUAN_GIUA_CAC_SHEET")


if __name__ == "__main__":
    unittest.main()
