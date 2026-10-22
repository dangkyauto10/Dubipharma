"""Google OIDC sign-in and least-privilege business access for TDV QC7.

DENY by default. No password storage, bypass for developers, fallback access,
cookie-query authentication, or secret material committed to GitHub.
This controls app entry, NOT enterprise storage/retention/approval authorization.
"""
from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from urllib.parse import urlparse

GOOGLE_ISSUERS = frozenset(("https://accounts.google.com", "accounts.google.com"))
ROLES = frozenset(("admin", "analyst", "viewer"))
GOOGLE_DISCOVERY = "https://accounts.google.com/.well-known/openid-configuration"
BUSINESS_SENSITIVE = frozenset((
    "📄 E-HSMT", "💊 Báo giá & hồ sơ NSX",
    "🔬 TDV-IDP 3.0 · Đọc đa tầng", "🛡️ Chứng cứ nhà sản xuất",
    "🔗 Google Sheets",
))


def valid_configuration(auth: Mapping | None, access: Mapping | None) -> bool:
    """Both native OIDC and an explicit allowlist are mandatory."""
    if not isinstance(auth, Mapping) or not isinstance(access, Mapping):
        return False
    required = ("client_id", "client_secret", "cookie_secret", "redirect_uri",
                "server_metadata_url")
    if not all(isinstance(auth.get(k), str) and auth[k].strip() for k in required):
        return False
    if len(auth["cookie_secret"].strip()) < 32:
        return False
    if auth["server_metadata_url"] != GOOGLE_DISCOVERY:
        return False
    url = urlparse(auth["redirect_uri"])
    if (url.scheme != "https" or not url.hostname
            or not url.path.endswith("/oauth2callback")
            or url.username or url.password or url.query or url.fragment):
        return False
    users = access.get("roles")
    if not isinstance(users, Mapping) or not users:
        return False
    normalized = []
    for email, role in users.items():
        if not isinstance(email, str) or not isinstance(role, str):
            return False
        if email.strip() != email or email != email.lower() or "@" not in email:
            return False
        if role not in ROLES:
            return False
        normalized.append(email)
    if len(set(normalized)) != len(normalized):
        return False
    return any(role == "admin" for role in users.values())


def role_from_claims(claims: Mapping, auth: Mapping, access: Mapping) -> str | None:
    """Enforce Google's verified email, signed-client audience, live token age."""
    if not isinstance(claims, Mapping) or not claims.get("is_logged_in"):
        return None
    if claims.get("iss") not in GOOGLE_ISSUERS:
        return None
    if claims.get("aud") != auth.get("client_id"):
        return None
    verified = claims.get("email_verified")
    if verified is not True and verified != "true":
        return None
    email = claims.get("email")
    if not isinstance(email, str) or not email.strip():
        return None
    if not isinstance(claims.get("sub"), str) or not claims["sub"].strip():
        return None
    issued = claims.get("iat")
    expiry = claims.get("exp")
    try:
        now = int(datetime.now(timezone.utc).timestamp())
        # Fail closed when claims do not provide a verifiable token lifetime.
        if not isinstance(issued, (int, float)) or not isinstance(expiry, (int, float)):
            return None
        if issued > now + 120 or expiry <= now or expiry <= issued:
            return None
    except (TypeError, ValueError, OverflowError):
        return None
    role = access["roles"].get(email.strip().lower())
    return role if role in ROLES else None


def may_open_section(role: str, page: str) -> bool:
    """Viewer is read-only: no file intake or technical input pages."""
    return role in ("admin", "analyst") or (role == "viewer" and
            page not in BUSINESS_SENSITIVE)


def require_google_access(st) -> tuple[str, str]:
    """Block ALL business execution until OIDC and allowlist are configured.

    st.stop() is intentional and must be called before any sensitive widgets.
    """
    try:
        auth = st.secrets.get("auth")
        access = st.secrets.get("tdv_access")
    except Exception:
        auth, access = None, None  # No secrets present: NEVER fall back to open.

    if not valid_configuration(auth, access):
        st.error("🔒 TDV QC7 ĐÃ KHÓA — chưa cấu hình đăng nhập Google an toàn.")
        st.caption(
            "Quản trị viên phải cấu hình Google OAuth và danh sách email được phép "
            "trong Streamlit Community Cloud → Settings → Secrets. "
            "Không nhập mật khẩu hoặc mã bí mật vào chat hoặc GitHub."
        )
        st.stop()

    user = st.user
    if not user.is_logged_in:
        st.info("🔒 TDV QC7 chỉ dành cho tài khoản Google đã được cấp quyền.")
        if st.button("Đăng nhập với Google", type="primary", key="tdv_oidc_login"):
            st.login()
        st.stop()

    role = role_from_claims(user, auth, access)
    if role is None:
        st.error(
            "⛔ Tài khoản Google chưa được phép, email chưa xác minh, "
            "hoặc phiên đăng nhập đã hết hạn."
        )
        if st.button("Đăng xuất / đăng nhập lại", key="tdv_oidc_logout_denied"):
            st.logout()
        st.stop()

    email = user.get("email", "").strip().lower()
    return role, email
