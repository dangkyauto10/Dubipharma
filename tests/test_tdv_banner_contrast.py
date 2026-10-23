"""Guardrail: SEE PRO banner must look authentic, without synthetic 3D marketing effects."""
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest

SOURCE=Path(__file__).resolve().parents[1]/"app.py"

class BannerContrastQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=SOURCE.read_text(encoding="utf-8")
        style=cls.code.split('STYLE = """',1)[1].split('"""',1)[0]
        cls.style=style
        cls.final=style.split("/* 23/10 corrective review",1)[1]

    def test_calm_banner_without_synthetic_3d(self):
        self.assertIn("linear-gradient(108deg,#f7fbff",self.final)
        self.assertIn("box-shadow:0 2px 7px rgba(20,65,106,.07)!important",self.final)
        self.assertNotIn("perspective(",self.final)
        self.assertNotIn("rotateY(",self.final)
        self.assertNotIn("drop-shadow(",self.final)
        self.assertIn("tdv_logo.webp.b64",self.code)
        self.assertIn("tdv_art.webp.b64",self.code)
        self.assertIn("""'<section class="tdv-main-hero">' + art + art_small""",self.code)

    def test_logo_flat_and_source_unchanged(self):
        logo=self.final.split(".tdv-main-hero .tdv-main-logo img{",1)[1].split("}",1)[0]
        self.assertIn("transform:none!important",logo)
        self.assertIn("filter:none!important",logo)
        self.assertIn("box-shadow:none!important",logo)
        self.assertIn("background:transparent!important",logo)

    def test_artwork_calm_not_glowing(self):
        art=self.final.split(".tdv-main-hero .tdv-main-art{",1)[1].split("}",1)[0]
        vignette=self.final.split(".tdv-main-hero .tdv-left-photo{",1)[1].split("}",1)[0]
        self.assertIn("opacity:.42!important",art)
        self.assertIn("saturate(.60)",art)
        self.assertIn("opacity:.28!important",vignette)

    def test_small_text_has_contrast_but_no_fake_depth(self):
        for sel,color,bg in [
            (".tdv-main-hero .tdv-pill{","color:#185c43!important","background:#edf7f1!important"),
            (".tdv-main-hero .tdv-tags span{","color:#315674!important","background:#f9fbfd!important")
        ]:
            rule=self.final.split(sel,1)[1].split("}",1)[0]
            self.assertIn(color,rule)
            self.assertIn(bg,rule)
            self.assertIn("box-shadow:none!important",rule)
            self.assertIn("text-shadow:none!important",rule)
            self.assertIn("border:1px",rule)

    def test_mobile_flat_and_legible(self):
        self.assertIn("@media(max-width:899px),(max-height:569px)",self.final)
        self.assertIn("tdv-main-logo img{transform:none!important;filter:none!important;}",self.final)

    def test_unauthorized_app_locked(self):
        at=AppTest.from_file(str(SOURCE),default_timeout=45).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertFalse(at.sidebar.radio)

    def test_authorized_homepage_renders(self):
        with patch("tdv_auth.require_google_access",return_value=("admin","owner@example.com")):
            at=AppTest.from_file(str(SOURCE),default_timeout=45).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertTrue(at.sidebar.radio)

if __name__=="__main__":
    unittest.main()
