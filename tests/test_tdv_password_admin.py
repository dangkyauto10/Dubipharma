"""Secure SEE PRO password management: no plaintext, no open bootstrap."""
import unittest
from unittest.mock import patch
from tdv_access_store import (
    database_url, SecurityNotConfigured, valid_password,
    hash_password, check_password, bootstrap_admin, ALLOWED_GRANTS,
)
from tdv_admin_ui import local_identity

class FakeSt:
    def __init__(self,secret=None,token=None):
        self.secrets={} if secret is None else secret
        self.session_state={} if token is None else {"seepro_local_token":token}

class AdminPasswordQA(unittest.TestCase):
    def test_password_hashing_uses_salted_argon2id(self):
        a=hash_password("MauKhauBaoMat-2026!")
        b=hash_password("MauKhauBaoMat-2026!")
        self.assertNotEqual(a,b)
        self.assertTrue(a.startswith("$argon2id$"))
        self.assertTrue(check_password("MauKhauBaoMat-2026!",a))
        self.assertFalse(check_password("Sai-Mat-Khau-2026",a))
        self.assertNotIn("MauKhauBaoMat-2026!",a)

    def test_password_policy(self):
        self.assertFalse(valid_password("short"))
        self.assertFalse(valid_password(" " * 14))
        self.assertTrue(valid_password("This-is-a-long-passphrase"))
        self.assertFalse(valid_password("x" * 129))
        with self.assertRaises(ValueError):
            hash_password("too-short")

    def test_database_requires_credentials_and_tls(self):
        for url in ("", "sqlite:///tmp/seepro.db",
                    "postgresql://u:p@localhost/db",
                    "postgresql://u:p@host/db?sslmode=disable",
                    "postgresql://u@host/db?sslmode=require"):
            with self.subTest(url=url):
                with self.assertRaises(SecurityNotConfigured):
                    database_url(FakeSt({"seepro_admin_db":{"url":url}}))
        good="postgresql://u:p@host/db?sslmode=require"
        self.assertEqual(database_url(FakeSt({"seepro_admin_db":{"url":good}})),good)

    def test_public_cannot_initialize_admin(self):
        with self.assertRaises(PermissionError):
            bootstrap_admin("postgresql://irrelevant","SomePassphrase-2026",
                            google_admin_verified=False)

    def test_no_database_never_authenticates_local_user(self):
        s=FakeSt(token="opaque-session-token")
        self.assertIsNone(local_identity(s))
        self.assertNotIn("seepro_local_token",s.session_state)

    def test_stored_session_must_be_revalidated(self):
        s=FakeSt({"seepro_admin_db":{
            "url":"postgresql://u:p@host/db?sslmode=require"}},token="opaque")
        with patch("tdv_admin_ui.check_session",return_value=None) as check:
            self.assertIsNone(local_identity(s))
            check.assert_called_once()
        self.assertNotIn("seepro_local_token",s.session_state)

    def test_grant_list_has_no_storage_or_price_access(self):
        self.assertIn("📄 E-HSMT",ALLOWED_GRANTS)
        self.assertIn("📊 Báo cáo lãnh đạo",ALLOWED_GRANTS)
        self.assertNotIn("💰 Cân đối & phê duyệt giá chào",ALLOWED_GRANTS)
        self.assertNotIn("🔗 Google Sheets",ALLOWED_GRANTS)

if __name__=="__main__":
    unittest.main()
