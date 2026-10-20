"""NSX Drive vault security regression tests; all Drive calls are mocked."""
from __future__ import annotations

import hashlib
from io import BytesIO
from unittest import TestCase
from unittest.mock import MagicMock, patch

from tdv_nsx_drive_vault import (
    VaultNotReady, authorize_user, prepare_batch,
    validate_config, verify_folder, save_batch,
)

NOW = 1792560000


def logged_in(email="staff@example.com", expire=1792563600):
    return {"is_logged_in": True, "email": email, "email_verified": True,
            "iss": "https://accounts.google.com", "aud": "gclient-123",
            "exp": expire}


def config(mode="company_shared_drive"):
    c = {"enabled": True, "mode": mode, "folder_id": "test_company_vault_1234",
         "roles": {"staff@example.com": "editor", "viewer@example.com": "viewer"}}
    if mode == "company_shared_drive":
        c["service_account"] = {"type": "service_account"}
    else:
        c["authorized_user"] = {"type": "authorized_user"}
    return c


def docs():
    src = b"fake_product_attachment"
    row = {"kind": "PRODUCT", "sha256": hashlib.sha256(src).hexdigest()}
    return [("PRODUCT", "product.docx", src)], {"product": row, "documents": []}


class VaultTests(TestCase):
    def test_unconfigured_storage_fails_closed(self):
        with self.assertRaises(VaultNotReady):
            validate_config({})
        with self.assertRaises(VaultNotReady):
            validate_config({"enabled": True, "mode": "approved_my_drive"})
        with self.assertRaises(VaultNotReady):
            validate_config({**config(), "roles": {"person@example.com": "everyone"}})

    def test_login_role_and_expiry(self):
        roles = {"staff@example.com": "editor", "viewer@example.com": "viewer"}
        self.assertFalse(authorize_user({}, roles, now=NOW)["allowed"])
        self.assertFalse(authorize_user(logged_in(expire=NOW - 1), roles, now=NOW)["allowed"])
        self.assertFalse(authorize_user(logged_in("other@example.com"), roles, now=NOW)["allowed"])
        good = authorize_user(logged_in(), roles, now=NOW, expected_aud="gclient-123")
        self.assertTrue(good["allowed"])
        self.assertTrue(good["can_upload"])
        readonly = authorize_user(logged_in("viewer@example.com"), roles, now=NOW)
        self.assertTrue(readonly["allowed"])
        self.assertFalse(readonly["can_upload"])
        forged = logged_in()
        forged["email_verified"] = False
        self.assertFalse(authorize_user(forged, roles, now=NOW)["allowed"])
        forged = logged_in()
        forged["iss"] = "https://attacker.example"
        self.assertFalse(authorize_user(forged, roles, now=NOW)["allowed"])
        self.assertFalse(authorize_user(logged_in(), roles, now=NOW,
                                        expected_aud="another-client")["allowed"])

    def test_shared_drive_mode_requires_actual_shared_drive(self):
        service = MagicMock()
        service.files().get().execute.return_value = {
            "id": config()["folder_id"], "mimeType": "application/vnd.google-apps.folder",
            "capabilities": {"canAddChildren": True}, "trashed": False,
        }
        with self.assertRaises(VaultNotReady):
            verify_folder(service, config())
        service.files().get().execute.return_value["driveId"] = "approved-shared-drive"
        self.assertEqual(verify_folder(service, config())["driveId"],
                         "approved-shared-drive")

    def test_my_drive_mode_rejects_shared_folder(self):
        service = MagicMock()
        service.files().get().execute.return_value = {
            "id": config("approved_my_drive")["folder_id"],
            "mimeType": "application/vnd.google-apps.folder",
            "driveId": "some_shared_drive", "capabilities": {"canAddChildren": True},
        }
        with self.assertRaises(VaultNotReady):
            verify_folder(service, config("approved_my_drive"))

    def test_report_sha_mismatch_blocks_upload(self):
        files, report = docs()
        report["product"]["sha256"] = "0" * 64
        actor = authorize_user(logged_in(), config()["roles"], now=NOW)
        with self.assertRaises(ValueError):
            prepare_batch(files, report, actor)
        report["product"]["sha256"] = hashlib.sha256(files[0][2]).hexdigest()
        plan = prepare_batch(files, report, actor, batch_id="a" * 32)
        self.assertEqual(plan["source_files"][0]["sha256"], report["product"]["sha256"])
        self.assertEqual(plan["source_files"][0]["archive_name"][:15],
                         "01_" + plan["source_files"][0]["sha256"][:12])
        self.assertFalse(plan["business_verified"])

    def test_no_implicit_drive_save(self):
        files, report = docs()
        service = MagicMock()
        actor = authorize_user(logged_in(), config()["roles"], now=NOW)
        with self.assertRaises(PermissionError):
            save_batch(service, config(), files, report, actor)
        self.assertEqual(service.files.call_count, 0)

    def test_viewer_cannot_upload_even_if_button_called(self):
        files, report = docs()
        service = MagicMock()
        actor = authorize_user(logged_in("viewer@example.com"), config()["roles"], now=NOW)
        service.files().get().execute.return_value = {
            "id": config()["folder_id"], "mimeType": "application/vnd.google-apps.folder",
            "driveId": "shared", "capabilities": {"canAddChildren": True},
        }
        with self.assertRaises(PermissionError):
            save_batch(service, config(), files, report, actor, confirmed_by_user=True)
        self.assertFalse(service.files().create.called)

    def test_append_only_batch_and_manifest(self):
        files, report = docs()
        service = MagicMock()
        actor = authorize_user(logged_in(), config()["roles"], now=NOW)
        files_resource = service.files.return_value
        files_resource.get.return_value.execute.return_value = {
            "id": config()["folder_id"], "mimeType": "application/vnd.google-apps.folder",
            "driveId": "shared", "capabilities": {"canAddChildren": True},
        }
        files_resource.create.return_value.execute.side_effect = [
            {"id": "batch-folder-123"},
            {"id": "original-file-1", "md5Checksum": hashlib.md5(files[0][2]).hexdigest()},
            {"id": "manifest-1"},
        ]
        result = save_batch(service, config(), files, report, actor,
                            confirmed_by_user=True)
        self.assertTrue(result["ok"])
        self.assertEqual(result["saved_count"], 1)
        self.assertEqual(result["manifest_id"], "manifest-1")
        self.assertEqual(files_resource.create.call_count, 3)
        self.assertFalse(files_resource.update.called)
        self.assertFalse(files_resource.delete.called)

    def test_md5_mismatch_fails_without_claimed_success(self):
        files, report = docs()
        service = MagicMock()
        actor = authorize_user(logged_in(), config()["roles"], now=NOW)
        service.files().get().execute.return_value = {
            "id": config()["folder_id"], "mimeType": "application/vnd.google-apps.folder",
            "driveId": "shared", "capabilities": {"canAddChildren": True},
        }
        service.files().create().execute.side_effect = [
            {"id": "folder"}, {"id": "doc", "md5Checksum": "bad"},
        ]
        with self.assertRaises(RuntimeError):
            save_batch(service, config(), files, report, actor, confirmed_by_user=True)


if __name__ == "__main__":
    import unittest
    unittest.main()
