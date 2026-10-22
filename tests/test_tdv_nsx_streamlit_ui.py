"""Smoke test the real NSX route in Streamlit without touching Drive or users' data."""
from __future__ import annotations
from pathlib import Path
import unittest
from unittest.mock import patch
from streamlit.testing.v1 import AppTest


class NSXPreviewNavigationTest(unittest.TestCase):
    def test_app_can_open_nsx_and_blocks_upload_until_consent(self):
        entry = Path(__file__).resolve().parents[1] / "app.py"
        # Default: no Secrets means ALL business routes are locked.
        unconfigured = AppTest.from_file(str(entry), default_timeout=45).run()
        self.assertEqual(len(unconfigured.exception), 0, str(unconfigured.exception))
        self.assertFalse(unconfigured.sidebar.radio)
        self.assertTrue(any("ĐÃ KHÓA" in x.value for x in unconfigured.error))
        # Navigation smoke only: inject an approved identity at the module
        # boundary, never insert fake login credentials or real secrets.
        with patch("tdv_auth.require_google_access",
                   return_value=("admin", "owner@example.com")):
            at = AppTest.from_file(str(entry), default_timeout=45).run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        nav = at.sidebar.radio[0]
        nav.set_value("💊 Báo giá & hồ sơ NSX")
        with patch("tdv_auth.require_google_access",
                   return_value=("admin", "owner@example.com")):
            at.run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        consent = [c for c in at.checkbox
                   if c.key == "tdv_nsx_real_allowed_preview"]
        self.assertEqual(len(consent), 1)
        self.assertFalse(consent[0].value)
        # Streamlit's AppTest info elements expose a Markdown value, not
        # a .message attribute. The gate should be informative but must not
        # depend on private proto internals.
        self.assertTrue(len(at.info) >= 1)
        # A non-confidential test can opt in, but uploads do not occur by default.
        consent[0].set_value(True)
        with patch("tdv_auth.require_google_access",
                   return_value=("admin", "owner@example.com")):
            at.run()
        self.assertEqual(len(at.exception), 0, str(at.exception))


if __name__ == "__main__":
    unittest.main()
