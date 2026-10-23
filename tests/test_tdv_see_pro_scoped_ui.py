"""Streamlit scoped leadership page smoke test (synthetic only)."""
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from tdv_see_pro_scope import bind_report

S={"project_id":"DA-TQ-01","package_id":"BP2600899572","ehsmt_revision_id":"R01"}

def toy():
    left={
      "MA_THUOC":"G1.001","MA_GOI_THAU":S["package_id"],
      "MA_PHAN_LO":"PP2600428380","HOAT_CHAT_HSMT":"Acarbose",
      "NONG_DO_HAM_LUONG":"50mg","DANG_BAO_CHE":"Viên","DUONG_DUNG":"Uống",
      "FILE_NGUON":"E-HSMT.xlsx","TRANG_VI_TRI":"Sheet Danh mục, dòng 2",
      "EVIDENCE":{
         "HOAT_CHAT_HSMT":{"source":"E-HSMT.xlsx","sheet":"Danh mục","row":2,
                            "column":"C","raw":"Acarbose"},
         "NONG_DO_HAM_LUONG":{"source":"E-HSMT.xlsx","sheet":"Danh mục","row":2,
                             "column":"D","raw":"50mg"},
         "DANG_BAO_CHE":{"source":"E-HSMT.xlsx","sheet":"Danh mục","row":2,
                         "column":"E","raw":"Viên"},
         "DUONG_DUNG":{"source":"E-HSMT.xlsx","sheet":"Danh mục","row":2,
                        "column":"F","raw":"Uống"}}}
    p={
      "uid":"P0001","file":"NSX.xlsx","sha256":"b"*64,
      "fields":{"PRODUCT_NAME":"Acabo","INGREDIENT":"Acarbose","STRENGTH":"50mg",
                "DOSAGE_FORM":"Viên","ROUTE":"Uống"},
      "conflicts":{},
      "evidence":{k:{"file":"NSX.xlsx","source":"Sheet Bang Thuoc, B2",
                      "raw":v,"sha256":"b"*64}
                  for k,v in {"PRODUCT_NAME":"Acabo","INGREDIENT":"Acarbose",
                              "STRENGTH":"50mg","DOSAGE_FORM":"Viên","ROUTE":"Uống"}.items()}}
    e=bind_report({"rows":[left],"documents":[],"warnings":[]},S,[("E-HSMT.xlsx",b"tender")])
    n=bind_report({"products":[p],"files":[],"warnings":[],"review_queue":[]},S,
                  [("NSX.xlsx",b"supplier")])
    return e,n

class LeadershipUiScopeSmoke(unittest.TestCase):
    def test_full_report_render_with_real_layout_synthetic_data(self):
        app=Path(__file__).resolve().parents[1]/"app.py"
        with patch("tdv_auth.require_google_access",return_value=("admin","owner@example.com")):
            at=AppTest.from_file(str(app),default_timeout=60).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        e,n=toy()
        at.session_state["tdv_see_pro_active_scope"]=S
        at.session_state["tdv_see_pro_analysis"]=e
        at.session_state["tdv_nsx_auto_report"]=n
        at.sidebar.radio[0].set_value("📊 Báo cáo lãnh đạo")
        with patch("tdv_auth.require_google_access",return_value=("admin","owner@example.com")):
            at.run()
        self.assertFalse(at.exception,str(list(at.exception)))
        metrics=[x.label for x in at.metric]
        self.assertIn("Mã E-HSMT",metrics)
        self.assertIn("Đạt đã xác minh",metrics)
        self.assertIn("Chưa đạt / cần xác minh",metrics)
        self.assertIn("Chờ ghép NSX",metrics)
