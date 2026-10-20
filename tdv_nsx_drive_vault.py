"""TDV NSX append-only Google Drive vault.

Storage is DISABLED until an approved destination and credentials are supplied.
No connected ChatGPT Drive account token is reused by Streamlit.
"""
from __future__ import annotations
from datetime import datetime, timezone
from io import BytesIO
import hashlib
import json
import re
import uuid
from typing import Any

MAX_FILES = 24
MAX_BYTES = 30 * 1024 * 1024
SCOPE = "https://www.googleapis.com/auth/drive"
FOLDER_MIME = "application/vnd.google-apps.folder"
ROLES = {"viewer", "editor", "admin"}


class VaultNotReady(RuntimeError):
    pass


def authorize_user(user: dict, roles: dict, *, now: int | None = None,
                   expected_aud: str = "") -> dict:
    if not user.get("is_logged_in"):
        return {"allowed": False, "reason": "CHUA_DANG_NHAP"}
    email = str(user.get("email") or "").casefold().strip()
    if not re.fullmatch(r"[a-z0-9._%+\-]+@[a-z0-9.\-]+\.[a-z]{2,}", email):
        return {"allowed": False, "reason": "EMAIL_KHONG_HOP_LE"}
    if user.get("email_verified") not in (True, "true", "True", 1):
        return {"allowed": False, "reason": "EMAIL_CHUA_XAC_THUC"}
    if user.get("iss") not in ("https://accounts.google.com", "accounts.google.com"):
        return {"allowed": False, "reason": "SAI_NHA_CUNG_CAP_DANH_TINH"}
    if expected_aud and user.get("aud") != expected_aud:
        return {"allowed": False, "reason": "OIDC_AUD_KHONG_KHOP"}
    if now is None:
        now = int(datetime.now(timezone.utc).timestamp())
    try:
        expires = int(user.get("exp") or 0)
    except (TypeError, ValueError):
        expires = 0
    if expires <= now:
        return {"allowed": False, "reason": "PHIEN_HET_HAN"}
    role = roles.get(email, "")
    if role not in ROLES:
        return {"allowed": False, "reason": "CHUA_CAP_QUYEN"}
    return {"allowed": True, "email": email, "role": role,
            "can_upload": role in ("admin", "editor")}


def validate_config(cfg: dict) -> dict:
    if not cfg.get("enabled"):
        raise VaultNotReady("Lưu Drive chưa được kích hoạt")
    mode = cfg.get("mode")
    if mode not in ("company_shared_drive", "approved_my_drive"):
        raise VaultNotReady("Chưa chọn Shared Drive hoặc My Drive được phê duyệt")
    fid = str(cfg.get("folder_id") or "")
    if not re.fullmatch(r"[A-Za-z0-9_\-]{12,128}", fid):
        raise VaultNotReady("Thiếu ID thư mục lưu trữ")
    roles = cfg.get("roles")
    if not isinstance(roles, dict) or not roles:
        raise VaultNotReady("Thiếu danh sách vai trò")
    norm = {str(k).casefold().strip(): str(v).lower().strip()
            for k, v in roles.items()}
    if any(role not in ROLES for role in norm.values()):
        raise VaultNotReady("Vai trò không hợp lệ")
    if mode == "company_shared_drive" and not isinstance(cfg.get("service_account"), dict):
        raise VaultNotReady("Thiếu tài khoản dịch vụ")
    if mode == "approved_my_drive" and not isinstance(cfg.get("authorized_user"), dict):
        raise VaultNotReady("Thiếu quyền OAuth người sở hữu My Drive")
    return {**cfg, "roles": norm}


def drive_service(cfg: dict):
    cfg = validate_config(cfg)
    from googleapiclient.discovery import build
    if cfg["mode"] == "company_shared_drive":
        from google.oauth2 import service_account
        credentials = service_account.Credentials.from_service_account_info(
            cfg["service_account"], scopes=[SCOPE])
    else:
        from google.oauth2.credentials import Credentials
        credentials = Credentials.from_authorized_user_info(
            cfg["authorized_user"], scopes=[SCOPE])
    return build("drive", "v3", credentials=credentials, cache_discovery=False)


def verify_folder(service: Any, cfg: dict) -> dict:
    cfg = validate_config(cfg)
    f = service.files().get(
        fileId=cfg["folder_id"], fields="id,mimeType,trashed,driveId,capabilities(canAddChildren)",
        supportsAllDrives=True).execute()
    if f.get("id") != cfg["folder_id"] or f.get("mimeType") != FOLDER_MIME:
        raise VaultNotReady("Sai thư mục lưu trữ")
    if f.get("trashed") or f.get("capabilities", {}).get("canAddChildren") is not True:
        raise VaultNotReady("Thư mục không còn hợp lệ hoặc thiếu quyền ghi")
    if cfg["mode"] == "company_shared_drive" and not f.get("driveId"):
        raise VaultNotReady("Tài khoản dịch vụ yêu cầu Shared Drive thật")
    if cfg["mode"] == "approved_my_drive" and f.get("driveId"):
        raise VaultNotReady("Thư mục My Drive không hợp lệ")
    if cfg.get("expected_drive_id") and f.get("driveId") != cfg["expected_drive_id"]:
        raise VaultNotReady("Sai ID Shared Drive được cấp")
    return f


def _name(name: str) -> str:
    name = str(name).replace("\\", "/").split("/")[-1]
    name = re.sub(r"[\x00-\x1f\x7f]", "_", name).strip(" .")
    if not name or len(name) > 180:
        raise ValueError("Tên tệp không hợp lệ")
    return name


def prepare_batch(files: list[tuple[str, str, bytes]], report: dict,
                  user: dict, *, batch_id: str | None = None) -> dict:
    if not user.get("allowed") or not user.get("can_upload"):
        raise PermissionError("Tài khoản không được lưu hồ sơ")
    if not 1 <= len(files) <= MAX_FILES:
        raise ValueError("Số tệp không hợp lệ")
    batch_id = batch_id or uuid.uuid4().hex
    if not re.fullmatch(r"[a-fA-F0-9]{32}", batch_id):
        raise ValueError("Mã lưu trữ không hợp lệ")
    original_files = []
    for index, (kind, filename, data) in enumerate(files, 1):
        if not isinstance(data, bytes) or not 0 < len(data) <= MAX_BYTES:
            raise ValueError("Tệp rỗng hoặc quá lớn")
        sha = hashlib.sha256(data).hexdigest()
        original_files.append({
            "seq": index, "kind": kind, "name": _name(filename),
            "archive_name": f"{index:02d}_{sha[:12]}_{_name(filename)}",
            "bytes": len(data), "sha256": sha,
        })
    observed = [report.get("product") or {}, *(report.get("documents") or [])]
    if len(observed) != len(original_files) or any(
        f["sha256"] != record.get("sha256")
        for f, record in zip(original_files, observed)
    ):
        raise ValueError("Bộ nguồn không còn khớp phân tích; phải đọc lại trước khi lưu")
    return {
        "schema": "TDV_NSX_VAULT_V1", "batch_id": batch_id,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "operator": user["email"], "role": user["role"],
        "source_files": original_files, "report": report,
        "business_verified": False, "gmp_approved": False,
        "quote_approved": False,
    }


def save_batch(service: Any, cfg: dict, files: list[tuple[str, str, bytes]],
               report: dict, user: dict, *, confirmed_by_user: bool = False) -> dict:
    """Each save creates a new batch folder and files. No overwrite or deletion."""
    if not confirmed_by_user:
        raise PermissionError("Chưa xác nhận lệnh lưu Google Drive")
    cfg = validate_config(cfg)
    folder = verify_folder(service, cfg)
    manifest = prepare_batch(files, report, user)
    from googleapiclient.http import MediaIoBaseUpload
    created_folder = service.files().create(
        body={"name": "NSX_" + manifest["batch_id"][:16],
              "mimeType": FOLDER_MIME, "parents": [cfg["folder_id"]],
              "appProperties": {"tdv_type": "nsx_batch",
                                "batch_id": manifest["batch_id"]}},
        fields="id,webViewLink,driveId", supportsAllDrives=True).execute()
    folder_id = created_folder.get("id")
    if not folder_id:
        raise RuntimeError("Drive chưa xác nhận thư mục lưu")
    saved = []
    for original, (kind, filename, data) in zip(manifest["source_files"], files):
        if hashlib.sha256(data).hexdigest() != original["sha256"] or kind != original["kind"]:
            raise RuntimeError("Nội dung tệp đã thay đổi trong lúc lưu")
        result = service.files().create(
            body={"name": original["archive_name"], "parents": [folder_id],
                  "mimeType": "application/octet-stream",
                  "appProperties": {"tdv_type": "nsx_source",
                                    "batch_id": manifest["batch_id"],
                                    "sha256": original["sha256"]}},
            media_body=MediaIoBaseUpload(BytesIO(data),
                mimetype="application/octet-stream", resumable=False),
            fields="id,md5Checksum", supportsAllDrives=True).execute()
        if not result.get("id"):
            raise RuntimeError("Drive chưa xác nhận tệp nguồn")
        if result.get("md5Checksum") and (
            result["md5Checksum"] != hashlib.md5(data).hexdigest()
        ):
            raise RuntimeError("MD5 của tệp lưu khác với bản gốc")
        saved.append({**original, "drive_file_id": result["id"]})
    manifest.update({
        "stored_files": saved, "batch_folder_id": folder_id,
        "parent_folder_id": cfg["folder_id"],
        "shared_drive_id": folder.get("driveId"),
    })
    raw = json.dumps(manifest, ensure_ascii=False, default=str,
                     sort_keys=True).encode("utf-8")
    receipt = service.files().create(
        body={"name": "MANIFEST.json", "parents": [folder_id],
              "mimeType": "application/json"},
        media_body=MediaIoBaseUpload(BytesIO(raw),
                 mimetype="application/json", resumable=False),
        fields="id", supportsAllDrives=True).execute()
    if not receipt.get("id"):
        raise RuntimeError("Tệp nguồn đã lưu nhưng thiếu manifest; cần kiểm tra thủ công")
    return {"ok": True, "batch_id": manifest["batch_id"],
            "folder_id": folder_id, "manifest_id": receipt["id"],
            "saved_count": len(saved),
            "url": f"https://drive.google.com/drive/folders/{folder_id}",
            "manifest_sha256": hashlib.sha256(raw).hexdigest()}
