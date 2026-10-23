"""The two verbose SEE PRO status notices should be compact, accessible on click,
and close by native Streamlit popover behavior. Authentication remains mandatory.
"""
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class CompactNoticesQA(unittest.TestCase):
    def test_notices_are_native_popovers_in_source(self):
        code=(ROOT/"app.py").read_text(encoding="utf-8")
        self.assertIn('with st.popover("🔐 Tài khoản & bảo mật"',code)
        self.assertIn('with st.popover("🛡️ TDV QC7 · Trạng thái Preview")',code)
        self.assertIn("TDV QC7 ONLINE — PREVIEW NGHIỆM THU THEO PHÂN HỆ.",code)
        self.assertIn("Chỉ nạp tài liệu được phép và hạn chế ",code)
        self.assertIn("Người dùng: {TDV_EMAIL} · Vai trò: {TDV_ROLE}",code)
        self.assertIn('key="tdv_google_logout"',code)
        self.assertNotIn("st.expander(\"🛡️ TDV QC7",code)

    def test_unauthenticated_user_still_cannot_enter(self):
        at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=45).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertFalse(at.sidebar.radio)
        self.assertTrue(any("ĐÃ KHÓA" in m.value for m in at.error))

    def test_authorized_app_runs_with_both_short_triggers(self):
        with patch("tdv_auth.require_google_access",
                   return_value=("admin","owner@example.com")):
            at=AppTest.from_file(str(ROOT/"app.py"),default_timeout=45).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertTrue(at.sidebar.radio)
        # Native popover triggers may be represented by AppTest as buttons.
        script=(ROOT/"app.py").read_text(encoding="utf-8")
        self.assertEqual(script.count('with st.popover("🔐 Tài khoản & bảo mật"'),1)
        self.assertEqual(script.count('with st.popover("🛡️ TDV QC7 · Trạng thái Preview")'),1)

if __name__=="__main__":unittest.main()
