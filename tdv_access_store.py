"""SEE PRO private credential store: PostgreSQL only, never Streamlit RAM/disk.

The service never creates Admin from public input. Only an already verified
Google Admin can initialize the store and set the first Admin password.
"""
from __future__ import annotations

import hashlib
import re
import secrets
from datetime import datetime, timedelta, timezone
from urllib.parse import parse_qs, urlparse

from argon2 import PasswordHasher, Type
from argon2.exceptions import InvalidHashError, VerificationError
import psycopg
from psycopg.rows import dict_row

ADMIN = "admin"
MEMBER = "member"
ALLOWED_GRANTS = frozenset((
    "📄 E-HSMT", "💊 Báo giá & hồ sơ NSX",
    "🔬 TDV-IDP 3.0 · Đọc đa tầng", "⚖️ So sánh kỹ thuật",
    "📊 Báo cáo lãnh đạo", "☁️ Tình trạng Online",
))
HASHER = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1,
                        hash_len=32, salt_len=16, type=Type.ID)
SESSION_HOURS = 8
MAX_ATTEMPTS = 5
LOCK_MINUTES = 15
USERNAME = re.compile(r"[a-z][a-z0-9_.-]{2,39}$")


class SecurityNotConfigured(RuntimeError):
    pass


def database_url(st) -> str:
    try:
        config = st.secrets.get("seepro_admin_db") or {}
        dsn = str(config.get("url") or "").strip()
    except Exception as exc:
        raise SecurityNotConfigured("Chưa cấu hình kho bảo mật") from exc
    try:
        parsed = urlparse(dsn)
        params = parse_qs(parsed.query)
        sslmode = params.get("sslmode", [""])[0]
        if parsed.scheme not in ("postgres", "postgresql") or not parsed.hostname:
            raise ValueError("not postgres")
        if sslmode not in ("require", "verify-ca", "verify-full"):
            raise ValueError("TLS required")
        if not parsed.username or not parsed.password:
            raise ValueError("incomplete credentials")
    except ValueError as exc:
        raise SecurityNotConfigured("Kho bảo mật phải dùng PostgreSQL qua TLS") from exc
    return dsn


def _conn(dsn):
    return psycopg.connect(dsn, connect_timeout=6, row_factory=dict_row)


def valid_password(value):
    return isinstance(value, str) and 12 <= len(value) <= 128 and not value.isspace()


def hash_password(value):
    if not valid_password(value):
        raise ValueError("Mật khẩu cần dài 12–128 ký tự")
    return HASHER.hash(value)


def check_password(password, encoded):
    try:
        return isinstance(password, str) and HASHER.verify(encoded, password)
    except (InvalidHashError, VerificationError, TypeError, ValueError):
        return False


def _token_digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def initialize(dsn):
    """Schema install is callable only from the authenticated Admin UI."""
    with _conn(dsn) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS seepro_users (
          username TEXT PRIMARY KEY,
          password_hash TEXT NOT NULL,
          role TEXT NOT NULL CHECK (role IN ('admin','member')),
          active BOOLEAN NOT NULL DEFAULT TRUE,
          must_change BOOLEAN NOT NULL DEFAULT FALSE,
          version INTEGER NOT NULL DEFAULT 1,
          failed INTEGER NOT NULL DEFAULT 0,
          locked_until TIMESTAMPTZ,
          created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS seepro_grants (
          username TEXT NOT NULL REFERENCES seepro_users(username) ON DELETE CASCADE,
          page TEXT NOT NULL,
          PRIMARY KEY(username,page)
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS seepro_sessions (
          token_hash TEXT PRIMARY KEY,
          username TEXT NOT NULL REFERENCES seepro_users(username) ON DELETE CASCADE,
          version INTEGER NOT NULL,
          expires_at TIMESTAMPTZ NOT NULL
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS seepro_audit (
          id BIGSERIAL PRIMARY KEY,
          actor TEXT NOT NULL, action TEXT NOT NULL,
          target TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        )""")


def has_admin(dsn):
    with _conn(dsn) as conn:
        row = conn.execute("SELECT 1 FROM seepro_users WHERE role='admin' LIMIT 1").fetchone()
        return bool(row)


def bootstrap_admin(dsn, password, *, google_admin_verified=False):
    if not google_admin_verified:
        raise PermissionError("Chỉ Admin Google đã xác thực mới tạo mật khẩu ban đầu")
    encoded = hash_password(password)
    with _conn(dsn) as conn:
        conn.execute("SELECT pg_advisory_xact_lock(85142026)")
        if conn.execute("SELECT 1 FROM seepro_users WHERE role='admin' LIMIT 1").fetchone():
            raise PermissionError("Admin đã được thiết lập")
        conn.execute("""INSERT INTO seepro_users
            (username,password_hash,role) VALUES ('admin',%s,'admin')""",
                     (encoded,))
        conn.execute("""INSERT INTO seepro_audit(actor,action,target)
            VALUES (%s,'BOOTSTRAP_ADMIN','admin')""", ("google-admin",))


def sign_in(dsn, username, password):
    username = str(username or "").lower().strip()
    if not USERNAME.fullmatch(username) or not isinstance(password, str):
        return None
    with _conn(dsn) as conn:
        user = conn.execute("SELECT * FROM seepro_users WHERE username=%s FOR UPDATE",
                            (username,)).fetchone()
        now = datetime.now(timezone.utc)
        if not user or not user["active"] or (
                user["locked_until"] and user["locked_until"] > now):
            return None
        if not check_password(password,user["password_hash"]):
            failed = user["failed"] + 1
            until = now+timedelta(minutes=LOCK_MINUTES) if failed>=MAX_ATTEMPTS else None
            conn.execute("""UPDATE seepro_users SET failed=%s, locked_until=%s
                WHERE username=%s""",(failed,until,username))
            return None
        conn.execute("""UPDATE seepro_users SET failed=0, locked_until=NULL
                        WHERE username=%s""",(username,))
        token=secrets.token_urlsafe(36)
        conn.execute("""INSERT INTO seepro_sessions
            (token_hash,username,version,expires_at)
            VALUES (%s,%s,%s,%s)""",
            (_token_digest(token),username,user["version"],now+timedelta(hours=SESSION_HOURS)))
        return token


def check_session(dsn, token):
    if not isinstance(token,str) or len(token)>250 or len(token)<30:
        return None
    with _conn(dsn) as conn:
        row=conn.execute("""SELECT u.username,u.role,u.active,u.must_change,
            u.version,s.expires_at FROM seepro_sessions s
            JOIN seepro_users u ON u.username=s.username
            WHERE s.token_hash=%s""",(_token_digest(token),)).fetchone()
        if (not row or not row["active"] or
                row["expires_at"] <= datetime.now(timezone.utc)):
            return None
        if row["version"] != conn.execute(
                "SELECT version FROM seepro_sessions WHERE token_hash=%s",
                (_token_digest(token),)).fetchone()["version"]:
            return None
        grants={r["page"] for r in conn.execute(
            "SELECT page FROM seepro_grants WHERE username=%s",(row["username"],)).fetchall()}
        return {"username":row["username"],"role":row["role"],
                "must_change":row["must_change"],"grants":grants}


def logout(dsn, token):
    with _conn(dsn) as conn:
        conn.execute("DELETE FROM seepro_sessions WHERE token_hash=%s",
                     (_token_digest(token),))


def change_password(dsn, username, old, new):
    encoded=hash_password(new)
    with _conn(dsn) as conn:
        user=conn.execute("SELECT password_hash FROM seepro_users WHERE username=%s FOR UPDATE",
                          (username,)).fetchone()
        if not user or not check_password(old,user["password_hash"]):
            return False
        conn.execute("""UPDATE seepro_users SET password_hash=%s,
            must_change=FALSE,version=version+1,failed=0,locked_until=NULL
            WHERE username=%s""",(encoded,username))
        conn.execute("DELETE FROM seepro_sessions WHERE username=%s",(username,))
        conn.execute("""INSERT INTO seepro_audit(actor,action,target)
            VALUES (%s,'CHANGE_PASSWORD',%s)""",(username,username))
        return True


def users(dsn):
    with _conn(dsn) as conn:
        records=conn.execute("""SELECT username,role,active,must_change,
            created_at FROM seepro_users ORDER BY username""").fetchall()
        result=[]
        for rec in records:
            grants=[x["page"] for x in conn.execute(
                "SELECT page FROM seepro_grants WHERE username=%s",
                (rec["username"],)).fetchall()]
            result.append({**rec,"grants":grants})
        return result


def create_member(dsn, username, temporary_password, pages, *, actor):
    username=str(username or "").lower().strip()
    if username==ADMIN or not USERNAME.fullmatch(username):
        raise ValueError("Tên thành viên cần 3–40 ký tự a–z, số, dấu chấm/gạch")
    pages=set(pages or [])
    if not pages.issubset(ALLOWED_GRANTS):
        raise ValueError("Quyền không nằm trong danh sách được phép")
    encoded=hash_password(temporary_password)
    with _conn(dsn) as conn:
        conn.execute("""INSERT INTO seepro_users
            (username,password_hash,role,must_change)
            VALUES (%s,%s,'member',TRUE)""",(username,encoded))
        for page in sorted(pages):
            conn.execute("INSERT INTO seepro_grants(username,page) VALUES (%s,%s)",
                         (username,page))
        conn.execute("""INSERT INTO seepro_audit(actor,action,target)
            VALUES (%s,'CREATE_MEMBER',%s)""",(actor,username))


def update_member(dsn, username, pages, active, *, actor):
    pages=set(pages or [])
    if username==ADMIN or not pages.issubset(ALLOWED_GRANTS):
        raise PermissionError("Không thể thay đổi quyền Admin qua phân quyền thành viên")
    with _conn(dsn) as conn:
        changed=conn.execute("""UPDATE seepro_users SET
            active=%s,version=version+1 WHERE username=%s AND role='member'
            RETURNING username""",(bool(active),username)).fetchone()
        if not changed:
            raise ValueError("Không tìm thấy thành viên")
        conn.execute("DELETE FROM seepro_grants WHERE username=%s",(username,))
        for page in sorted(pages):
            conn.execute("INSERT INTO seepro_grants(username,page) VALUES (%s,%s)",
                         (username,page))
        conn.execute("DELETE FROM seepro_sessions WHERE username=%s",(username,))
        conn.execute("""INSERT INTO seepro_audit(actor,action,target)
            VALUES (%s,'UPDATE_GRANTS',%s)""",(actor,username))


def reset_member_password(dsn, username, temporary_password, *, actor):
    if username==ADMIN:
        raise PermissionError("Không thể đặt lại mật khẩu Admin qua tài khoản thành viên")
    encoded=hash_password(temporary_password)
    with _conn(dsn) as conn:
        changed=conn.execute("""UPDATE seepro_users SET password_hash=%s,
          must_change=TRUE, version=version+1,failed=0,locked_until=NULL
          WHERE username=%s AND role='member' RETURNING username""",
          (encoded,username)).fetchone()
        if not changed: raise ValueError("Không tìm thấy thành viên")
        conn.execute("DELETE FROM seepro_sessions WHERE username=%s",(username,))
        conn.execute("""INSERT INTO seepro_audit(actor,action,target)
            VALUES (%s,'RESET_MEMBER_PASSWORD',%s)""",(actor,username))
