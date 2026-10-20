"""Smoke test the real NSX route in Streamlit without touching Drive or users' data."""
from __future__ import annotations
from pathlib import Path
import unittest
from streamlit.testing.v1 import AppTest


class NSXPreviewNavigationTest(unittest.TestCase):
    def test_app_can_open_nsx_and_blocks_upload_until_consent(self):
        entry = Path(__file__).resolve().parents[1] / "app.py"
        at = AppTest.from_file(str(entry), default_timeout=45).run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        nav = at.sidebar.radio[0]
        nav.set_value("💊 Báo giá & hồ sơ NSX")
        at.run()
        self.assertEqual(len(at.exception), 0, str(at.exception))
        consent = [c for c in at.checkbox
                   if c.key == "tdv_nsx_real_allowed_preview"]
        self.assertEqual(len(consent), 1)
        self.assertFalse(consent[0].value)
        self.assertTrue(any("tài liệu công khai" in item.message
                            or "xác nhận phạm vi dữ liệu" in item.message
                            for item in at.info))
        # A non-confidential test can opt in, but uploads do not occur by default.
        consent[0].set_value(True)
        at.run()
        self.assertEqual(len(at.exception), 0, str(at.exception))


if __name__ == "__main__":
    unittest.main()
