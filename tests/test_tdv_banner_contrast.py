"""Regression tests for SEE PRO banner readability and safe visual polish."""
import re
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

SOURCE = Path(__file__).resolve().parents[1] / "app.py"


class BannerContrastQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.code=SOURCE.read_text(encoding="utf-8")
        cls.style=cls.code.split('STYLE = """',1)[1].split('"""',1)[0]

    def test_glossy_background_and_3d_logo_preserve_image(self):
        self.assertIn('linear-gradient(113deg,#edfaff', self.style)
        self.assertIn('inset 0 2px 2px rgba(255,255,255,.95)',self.style)
        self.assertIn('perspective(650px) rotateY(-3deg)',self.style)
        self.assertIn('drop-shadow(0 14px 11px',self.style)
        self.assertIn('tdv_logo.webp.b64',self.code)
        self.assertIn('tdv_art.webp.b64',self.code)
        self.assertIn('logo + art_small', self.code)

    def test_two_small_text_regions_have_opaque_contrasting_background(self):
        pill=self.style.rsplit('.tdv-main-hero .tdv-pill{',1)[1].split('}',1)[0]
        chip=self.style.rsplit('.tdv-main-hero .tdv-tags span{',1)[1].split('}',1)[0]
        self.assertIn('color:#08412f!important',pill)
        self.assertIn('background:rgba(243,255,247,.96)!important',pill)
        self.assertIn('font-weight:850!important',pill)
        self.assertIn('color:#113f69!important',chip)
        self.assertIn('background:rgba(255,255,255,.96)!important',chip)
        self.assertIn('font-weight:800!important',chip)
        self.assertIn('border:1px',pill)
        self.assertIn('border:1px',chip)

    def test_banner_on_small_screens_remains_flat_and_legible(self):
        self.assertIn('max-width:899px',self.style)
        self.assertIn('max-height:569px',self.style)
        self.assertIn('tdv-main-logo img{transform:none',self.style)

    def test_app_still_auth_locked_without_secrets(self):
        at=AppTest.from_file(str(SOURCE),default_timeout=45).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertFalse(at.sidebar.radio)

    def test_authenticated_homepage_renders(self):
        with patch("tdv_auth.require_google_access",return_value=("admin","owner@example.com")):
            at=AppTest.from_file(str(SOURCE),default_timeout=45).run()
        self.assertFalse(at.exception,str(list(at.exception)))
        self.assertTrue(at.sidebar.radio)


if __name__ == "__main__":
    unittest.main()
