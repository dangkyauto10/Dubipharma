"""Safety tests for anonymous synthetic SEE PRO preview."""
from __future__ import annotations
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from tdv_public_preview import demo_sources, is_public_visitor
from tdv_leadership_report import compare_sources

ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"

class FakeUser:
    def __init__(self, logged_in=False): self.is_logged_in=logged_in
class Fake:
    def __init__(self, logged_in=False): self.user=FakeUser(logged_in)

class PublicDemoQA(unittest.TestCase):
    def test_only_anonymous_visitors_get_demo(self):
        self.assertTrue(is_public_visitor(Fake()))
        self.assertFalse(is_public_visitor(Fake(True)))

    def test_synthetic_source_uses_original_comparison_engine(self):
        t,n=demo_sources()
        self.assertEqual(len(t["rows"]),3)
        self.assertEqual(len(n["products"]),2)
        report=compare_sources(t,n)
        s=report["summary"]
        self.assertEqual(s["green_criteria_preliminary"],7)
        self.assertEqual(s["yellow_criteria"],4)
        self.assertEqual(s["red_mismatch_preliminary"],1)
        self.assertFalse(report["bid_eligible"])

    def test_guest_route_never_reads_user_files_or_calls_external_writes(self):
        code=(ROOT/"tdv_public_preview.py").read_text(encoding="utf-8")
        for forbidden in ("file_uploader(", "save_batch(", "drive_service(",
                          "render_ehsmt_workbench(", "GEMINI_API_KEY",
                          'st.session_state.get("tdv_'):
            self.assertNotIn(forbidden,code)
        app=APP.read_text(encoding="utf-8")
        self.assertLess(app.index("render_public_preview(st)"),
                        app.index("require_google_access(st)"))

    def test_root_opens_synthetic_demo_without_google(self):
        at=AppTest.from_file(str(APP),default_timeout=60).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertTrue(any("DỮ LIỆU MẪU GIẢ LẬP" in x.value
                            for x in at.warning))
        self.assertTrue(any("DÙNG THỬ" in x.value for x in at.sidebar.markdown))
        self.assertFalse(at.error)

if __name__=="__main__": unittest.main()
