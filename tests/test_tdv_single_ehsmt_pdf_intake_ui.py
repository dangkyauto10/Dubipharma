"""Keep a single visible E-HSMT intake while retaining the proven PDF reader.

The legacy PDF parser remains imported by the unified SEE PRO workbench.
Only the duplicate Streamlit expander/upload controls are retired.
"""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


class SingleVisibleEhsmtIntake(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=(ROOT/"app.py").read_text(encoding="utf-8")
        cls.workbench=(ROOT/"see_pro_workbench.py").read_text(encoding="utf-8")

    def test_unified_workbench_is_still_active(self):
        self.assertIn("from see_pro_workbench import render_ehsmt_workbench",self.app)
        self.assertIn("render_ehsmt_workbench()",self.app)
        self.assertIn("Đọc và kiểm toán bộ hồ sơ",self.workbench)

    def test_legacy_pdf_parser_is_kept_in_unified_workbench(self):
        self.assertIn("from tdv_ehsmt_intake import inspect_ehsmt_pdf",self.workbench)
        self.assertIn("report = inspect_ehsmt_pdf(data)",self.workbench)
        self.assertTrue((ROOT/"tdv_ehsmt_intake.py").is_file())

    def test_duplicate_pdf_expander_is_not_on_screen(self):
        self.assertNotIn("Bộ đọc PDF trước nâng cấp – đối chiếu dự phòng",self.app)
        self.assertNotIn("tdv_real_ehsmt_pdf",self.app)
        self.assertNotIn("tdv_real_ehsmt_run",self.app)
        self.assertNotIn("tdv_real_ehsmt_export",self.app)


if __name__=="__main__":
    unittest.main()
