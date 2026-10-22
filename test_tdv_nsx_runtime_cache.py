"""Synthetic regression: NSX reports cannot outlive their analysis revision."""
import hashlib
import unittest
from unittest.mock import patch

import tdv_nsx_workbench as workbench
import tdv_nsx_intake
import tdv_nsx_proof_hints
import tdv_nsx_auto


class NSXRuntimeCacheSafetyTests(unittest.TestCase):
    def setUp(self):
        self.files = [("mock registration.pdf", b"synthetic-content")]

    def test_uploaded_bytes_alone_cannot_reuse_old_report(self):
        old = hashlib.sha256()
        for name, raw in self.files:
            old.update(name.encode("utf-8"))
            old.update(len(raw).to_bytes(8, "big"))
            old.update(hashlib.sha256(raw).digest())
        self.assertNotEqual(workbench._signature(self.files), old.hexdigest())

    def test_report_requires_matching_version_and_fingerprint(self):
        digest = workbench._signature(self.files)
        correct = {"analysis_version": workbench.NSX_EXPECTED_PIPELINE_VERSION,
                   "analysis_fingerprint": digest}
        self.assertTrue(workbench._report_from_current_pipeline(correct, digest))
        for stale in (
            {"analysis_version": "2026-10-22H", "analysis_fingerprint": digest},
            {"analysis_version": workbench.NSX_EXPECTED_PIPELINE_VERSION,
             "analysis_fingerprint": "0" * 64},
            {"analysis_fingerprint": digest},
            {},
        ):
            self.assertFalse(workbench._report_from_current_pipeline(stale, digest))
        self.assertFalse(workbench._report_from_current_pipeline(None, digest))

    def test_modules_have_consistent_release_markers(self):
        code = workbench.NSX_EXPECTED_PIPELINE_VERSION
        self.assertEqual(tdv_nsx_intake.NSX_INTAKE_RUNTIME_REV, code)
        self.assertEqual(tdv_nsx_proof_hints.NSX_HINTS_RUNTIME_REV, code)
        self.assertEqual(tdv_nsx_auto.NSX_AUTO_RUNTIME_REV, code)
        self.assertTrue(workbench._runtime_is_consistent())

    def test_stale_imported_module_blocks_processing(self):
        with patch.object(workbench._runtime_hints, "NSX_HINTS_RUNTIME_REV",
                          "2026-10-22H"):
            self.assertFalse(workbench._runtime_is_consistent())

    def test_version_change_changes_input_signature(self):
        first = workbench._signature(self.files)
        with patch.object(workbench, "NSX_EXPECTED_PIPELINE_VERSION",
                          "2026-10-22K"):
            second = workbench._signature(self.files)
        self.assertNotEqual(first, second)


if __name__ == "__main__":
    unittest.main()
