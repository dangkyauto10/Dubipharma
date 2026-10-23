"""Guide UX regression: the handbook opens in a separate authenticated route.

Synthetic OIDC mock only at app boundary, no real login or confidential files.
"""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import unittest
import re
from streamlit.testing.v1 import AppTest
from tdv_guide import handbook_bytes, guide_requested, GUIDE_FILENAME


class TestGuideAssets(unittest.TestCase):
    def test_same_download_document_has_all_roles(self):
        data=handbook_bytes()
        self.assertGreater(len(data),20000)
        html=data.decode("utf-8")
        ids=set(re.findall(r'<button[^>]*data-target="([^"]+)"',html))
        self.assertEqual(len(ids),12)
        self.assertTrue({"leader","tender","pricing","approver","admin","nsx",
                         "exceptions","acceptance"}.issubset(ids))
        self.assertIn('id="searchBox"',html)
        self.assertIn("<script>",html)
        self.assertTrue(GUIDE_FILENAME.endswith(".html"))

    def test_query_flag_requires_explicit_one(self):
        class Context:
            def __init__(self,v):self.query_params=v
        self.assertTrue(guide_requested(Context({"see_pro_guide":"1"})))
        for v in ({},{"see_pro_guide":"0"},{"see_pro_guide":"yes"}):
            self.assertFalse(guide_requested(Context(v)))

    def test_sidebar_new_tab_anchor_and_download_identical(self):
        from tdv_guide import render_handbook_sidebar
        class Fake:
            def __init__(self):self.markdowns=[];self.downloads=[];self.captions=[]
            def markdown(self,v,**kw):self.markdowns.append(v)
            def download_button(self,label,**kw):self.downloads.append((label,kw))
            def caption(self,v):self.captions.append(v)
            def error(self,v):raise AssertionError(v)
        fake=Fake()
        render_handbook_sidebar(fake)
        self.assertEqual(len(fake.downloads),1)
        self.assertEqual(fake.downloads[0][1]["data"],handbook_bytes())
        self.assertEqual(fake.downloads[0][1]["file_name"],GUIDE_FILENAME)
        self.assertTrue(any('target="_blank"' in x and
                            'href="?see_pro_guide=1"' in x for x in fake.markdowns))


class TestGuideAuthenticatedUi(unittest.TestCase):
    def test_sidebar_button_visible_on_authorized_account(self):
        app=Path(__file__).resolve().parents[1]/"app.py"
        with patch("tdv_auth.require_google_access",
                   return_value=("admin","owner@example.com")):
            at=AppTest.from_file(str(app),default_timeout=45).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertTrue(any('href="?see_pro_guide=1"' in x.value
                            for x in at.sidebar.markdown))
        # Separate guide entry isn't a business page that viewers can edit.

    def test_guide_route_requires_google_access(self):
        app=Path(__file__).resolve().parents[1]/"app.py"
        at=AppTest.from_file(str(app),default_timeout=45)
        at.query_params["see_pro_guide"]="1"
        at.run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertTrue(any("ĐÃ KHÓA" in x.value for x in at.error))

    def test_open_guide_with_approved_identity_no_app_crash(self):
        app=Path(__file__).resolve().parents[1]/"app.py"
        at=AppTest.from_file(str(app),default_timeout=45)
        at.query_params["see_pro_guide"]="1"
        with patch("tdv_auth.require_google_access",
                   return_value=("viewer","leader@example.com")):
            at.run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertTrue(any("Cẩm nang sử dụng" in x.value for x in at.markdown))

if __name__=="__main__":unittest.main()
