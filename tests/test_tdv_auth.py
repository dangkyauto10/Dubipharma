"""Security regressions for Google identity; all accounts are fictitious fixtures."""
import time
import unittest
from tdv_auth import (
    GOOGLE_DISCOVERY, AUTH_SESSION_MAX_AGE_SECONDS,
    valid_configuration, role_from_claims,
    may_open_section, require_google_access,
)

AUTH = {
    "client_id": "test-client-id-123456.apps.googleusercontent.com",
    "client_secret": "test-client-secret-123456",
    "redirect_uri": ("https://tdv-qc7.streamlit.app/oauth2callback"),
    "cookie_secret": "ab" * 32,
    "server_metadata_url": GOOGLE_DISCOVERY,
}
ACCESS = {"roles": {
    "owner@example.com":"admin",
    "analyst@example.com":"analyst",
    "viewer@example.com":"viewer",
}}


def claims(email="owner@example.com", **changes):
    now=int(time.time())
    v={"is_logged_in":True, "iss":"https://accounts.google.com",
       "aud":AUTH["client_id"],"email_verified":True,"sub":"google-sub-id",
       "email":email, "iat":now-30,"exp":now+3500}
    v.update(changes)
    return v


class Halt(Exception):
    pass


class FakeSecrets(dict):
    pass


class FakeUser(dict):
    @property
    def is_logged_in(self):
        return bool(self.get("is_logged_in"))


class FakeStreamlit:
    def __init__(self, auth=None, access=None, user=None):
        self.secrets = FakeSecrets()
        if auth is not None:
            self.secrets["auth"] = auth
        if access is not None:
            self.secrets["tdv_access"] = access
        self.user = FakeUser(user or {})
        self.messages=[]
        self.buttons=[]
    def error(self,message):self.messages.append(("error",message))
    def caption(self,message):self.messages.append(("caption",message))
    def info(self,message):self.messages.append(("info",message))
    def button(self,label,**kwargs):
        self.buttons.append(label)
        return False
    def stop(self):raise Halt("blocked")


class AuthSecurityQA(unittest.TestCase):
    def test_required_admin_and_google_keys(self):
        self.assertTrue(valid_configuration(AUTH,ACCESS))
        self.assertFalse(valid_configuration({},ACCESS))
        self.assertFalse(valid_configuration(AUTH,{"roles":{"viewer@example.com":"viewer"}}))
        self.assertFalse(valid_configuration({**AUTH,"cookie_secret":"short"},ACCESS))
        self.assertFalse(valid_configuration({**AUTH,"server_metadata_url":"https://evil.test"},ACCESS))
        self.assertFalse(valid_configuration({**AUTH,"redirect_uri":"http://insecure.test/oauth2callback"},ACCESS))

    def test_verified_admin_analyst_viewer(self):
        for name,role in (("owner","admin"),("analyst","analyst"),("viewer","viewer")):
            self.assertEqual(role_from_claims(claims(name+"@example.com"),AUTH,ACCESS),role)
        self.assertIsNone(role_from_claims(claims("stranger@example.com"),AUTH,ACCESS))

    def test_untrusted_claims_never_grant_business_access(self):
        bad=[
            {"is_logged_in":False},
            {"iss":"https://attacker.invalid"},
            {"aud":"another-google-oauth-client"},
            {"email_verified":False},
            {"email_verified":"false"},
            {"sub":""},
            {"iat":int(time.time())+3600},
            {"exp":int(time.time())-100, "iat":int(time.time())-50},
            {"iat":int(time.time())-AUTH_SESSION_MAX_AGE_SECONDS-5,
             "exp":int(time.time())-AUTH_SESSION_MAX_AGE_SECONDS+3595},
        ]
        for changes in bad:
            with self.subTest(changes=changes):
                self.assertIsNone(role_from_claims(claims(**changes),AUTH,ACCESS))

    def test_short_lived_id_token_does_not_end_valid_streamlit_session(self):
        now=int(time.time())
        # Google's exp may be over, but Streamlit's signed identity cookie is live.
        identity=claims(iat=now-3*3600, exp=now-2*3600)
        self.assertEqual(role_from_claims(identity,AUTH,ACCESS),"admin")
        self.assertEqual(
            require_google_access(FakeStreamlit(AUTH,ACCESS,identity)),
            ("admin","owner@example.com"),
        )
        # Never accept the same old identity without the Streamlit login cookie.
        self.assertIsNone(role_from_claims(
            {**identity,"is_logged_in":False},AUTH,ACCESS))

    def test_signed_session_has_24h_cap_and_fails_closed(self):
        now=int(time.time())
        old=claims(iat=now-AUTH_SESSION_MAX_AGE_SECONDS-2,
                   exp=now-AUTH_SESSION_MAX_AGE_SECONDS+3598)
        self.assertIsNone(role_from_claims(old,AUTH,ACCESS))
        with self.assertRaises(Halt):
            require_google_access(FakeStreamlit(AUTH,ACCESS,old))
        # New Google authentication restores a bounded working session.
        new=claims(iat=now-15, exp=now+3585)
        self.assertEqual(role_from_claims(new,AUTH,ACCESS),"admin")
        for malformed in (
            {"iat":True},
            {"exp":False},
            {"iat":"not-a-timestamp"},
            {"exp":None},
        ):
            self.assertIsNone(role_from_claims(claims(**malformed),AUTH,ACCESS))

    def test_missing_verified_email_and_expiry_fail_closed(self):
        for missing in ("email","email_verified","iat","exp","sub"):
            with self.subTest(missing=missing):
                payload=claims()
                payload.pop(missing)
                self.assertIsNone(role_from_claims(payload,AUTH,ACCESS))

    def test_role_menu_viewer_cannot_upload(self):
        self.assertTrue(may_open_section("admin","📄 E-HSMT"))
        self.assertTrue(may_open_section("analyst","💊 Báo giá & hồ sơ NSX"))
        self.assertFalse(may_open_section("viewer","📄 E-HSMT"))
        self.assertFalse(may_open_section("viewer","💊 Báo giá & hồ sơ NSX"))
        self.assertFalse(may_open_section("viewer","🔗 Google Sheets"))
        self.assertTrue(may_open_section("viewer","📊 Báo cáo lãnh đạo"))
        self.assertTrue(may_open_section("viewer","⚖️ So sánh kỹ thuật"))
        self.assertFalse(may_open_section("unknown","📄 E-HSMT"))

    def test_no_secrets_blocks_before_any_login_or_business_page(self):
        st=FakeStreamlit()
        with self.assertRaises(Halt):
            require_google_access(st)
        self.assertFalse(st.buttons)
        self.assertTrue(any("ĐÃ KHÓA" in message for _,message in st.messages))

    def test_no_login_only_shows_google_signin(self):
        st=FakeStreamlit(AUTH,ACCESS,{"is_logged_in":False})
        with self.assertRaises(Halt):
            require_google_access(st)
        self.assertEqual(st.buttons,["Đăng nhập với Google"])

    def test_unauthorized_account_cannot_view_page(self):
        st=FakeStreamlit(AUTH,ACCESS,claims("attacker@example.com"))
        with self.assertRaises(Halt):
            require_google_access(st)
        self.assertTrue(any("Tài khoản Google chưa được phép" in message
                            for _,message in st.messages))

    def test_authorized_user_yields_current_identity_and_role(self):
        st=FakeStreamlit(AUTH,ACCESS,claims("analyst@example.com"))
        self.assertEqual(require_google_access(st),("analyst","analyst@example.com"))
        self.assertEqual(st.buttons,[])

if __name__ == "__main__":
    unittest.main()
