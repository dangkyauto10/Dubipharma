"""Multi-round NSX acceptance tests. Does not upload private documents."""
import unittest
from hashlib import sha256
from tdv_see_pro_nsx_batches import (
    stage_append, manifest_for_report, payload_for_analysis, verify_ledger)

class TestNsxIncrementalIntake(unittest.TestCase):
    def test_first_batch(self):
        p=stage_append([], [("registration.pdf",b"registration")])
        self.assertEqual(p["status"],"READY")
        self.assertEqual(len(p["records"]),1)
        self.assertTrue(verify_ledger(p["records"]))
    def test_second_batch_preserves_first(self):
        first=stage_append([], [("registration.pdf",b"reg")])["records"]
        later=stage_append(first,[("GMP.pdf",b"gmp")])
        self.assertEqual(later["status"],"READY")
        self.assertEqual(len(later["records"]),2)
        self.assertEqual(payload_for_analysis(later["records"])[0],("registration.pdf",b"reg"))
        self.assertEqual(later["records"][0]["batch_no"],1)
        self.assertEqual(later["records"][1]["batch_no"],2)
    def test_duplicate_sha_skipped(self):
        first=stage_append([], [("product.pdf",b"x")])["records"]
        repeated=stage_append(first,[("copy-product.pdf",b"x")])
        self.assertEqual(repeated["status"],"REPEAT_ONLY")
        self.assertEqual(len(repeated["records"]),1)
        self.assertEqual(len(repeated["repeated"]),1)
    def test_multiple_batches_same_product_are_not_double_counted(self):
        first=stage_append([], [("products.xlsx",b"products-v1")])["records"]
        p=stage_append(first,[("authorization.pdf",b"auth")])
        self.assertEqual([x["filename"] for x in p["records"]],
                         ["products.xlsx","authorization.pdf"])
        self.assertEqual(len({x["sha256"] for x in p["records"]}),2)
    def test_same_filename_changed_contents_blocks_auto_replace(self):
        old=stage_append([], [("GMP.pdf",b"old-gmp")])["records"]
        result=stage_append(old,[("GMP.pdf",b"new-gmp")])
        self.assertEqual(result["status"],"CONFLICT")
        self.assertEqual(result["records"],old)
        self.assertEqual(len(result["added"]),0)
    def test_identical_same_filename_repeated_is_safe(self):
        old=stage_append([], [("GMP.pdf",b"old")])["records"]
        result=stage_append(old,[("GMP.pdf",b"old")])
        self.assertEqual(result["status"],"REPEAT_ONLY")
        self.assertEqual(len(result["records"]),1)
    def test_same_name_two_different_new_files_blocks(self):
        result=stage_append([], [("SĐK.pdf",b"a"),("SĐK.pdf",b"b")])
        self.assertEqual(result["status"],"CONFLICT")
        self.assertFalse(result["added"])
    def test_over_cap_does_not_discard_prior(self):
        old=stage_append([], [("A.pdf",b"a")],combined_cap=2)["records"]
        result=stage_append(old,[("B.pdf",b"b"),("C.pdf",b"c")],combined_cap=2)
        self.assertEqual(result["status"],"LIMIT")
        self.assertEqual(result["records"],old)
    def test_per_batch_limit_is_enforced(self):
        with self.assertRaises(ValueError):
            stage_append([], [("A.pdf",b"a"),("B.pdf",b"b")],batch_cap=1)
    def test_no_raw_bytes_in_report_manifest(self):
        rows=stage_append([], [("A.pdf",b"confidential")])["records"]
        m=manifest_for_report(rows)
        self.assertNotIn("content",m[0])
        self.assertEqual(m[0]["sha256"],sha256(b"confidential").hexdigest())
    def test_corrupted_ram_bytes_prevent_reuse(self):
        rows=stage_append([], [("A.pdf",b"a")])["records"]
        rows[0]["content"]=b"tampered"
        self.assertFalse(verify_ledger(rows))
    def test_immutable_old_list_on_new_batch(self):
        old=stage_append([], [("A.pdf",b"a")])["records"]
        snapshot=list(old)
        ready=stage_append(old,[("B.pdf",b"b")])
        self.assertEqual(old,snapshot)
        self.assertEqual(len(old),1)
        self.assertEqual(len(ready["records"]),2)

if __name__=="__main__": unittest.main()
