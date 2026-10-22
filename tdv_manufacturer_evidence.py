"""Read-only manufacturer evidence quality gates for an actual NSX batch.

A document label or source-field match is never proof of authenticity, current
regulatory validity, GMP scope, product registration or tender eligibility.
"""
from __future__ import annotations

import re
import unicodedata
from tdv_nsx_gmp_role_guard import inspect_gmp_role

PROOF_TYPES = frozenset({
    "GMP_CERT", "GMP_EXPLANATION", "REGISTRATION", "AUTHORIZATION", "QUOTE",
})
LABELS = {
    "GMP_CERT": "Giấy GMP (loại gợi ý)",
    "GMP_EXPLANATION": "Giải trình GMP (chứng cứ bổ sung)",
    "REGISTRATION": "Giấy SĐK (loại gợi ý)",
    "AUTHORIZATION": "Giấy ủy quyền (loại gợi ý)",
    "QUOTE": "Báo giá (loại gợi ý)",
}
REQUIRED_REVIEW_FIELDS = {
    "GMP_CERT": ("FACTORY", "GMP_NUMBER", "GMP_SCOPE", "GMP_EXPIRY"),
    "GMP_EXPLANATION": ("FACTORY",),
    "REGISTRATION": ("PRODUCT_NAME", "REGISTRATION_NO"),
    "AUTHORIZATION": ("MANUFACTURER", "AUTH_EXPIRY"),
    "QUOTE": ("QUOTE_UNIT_PRICE", "QUOTE_CURRENCY", "QUOTE_VALID_UNTIL"),
}
COMPARABLE = ("FACTORY", "MANUFACTURER", "REGISTRATION_NO", "PRODUCT_ID")


def _norm(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value or "").strip().casefold())
    return " ".join("".join(c for c in text if not unicodedata.combining(c)).split())


def audit_manufacturer_evidence(report: dict) -> dict:
    """Examine extracted source fields and tentative links; never approve.

    The SHA format and citation agreement checks do not verify source bytes,
    signatures, issuing authority or legal effect. No filesystem/network writes.
    """
    products = {str(p.get("uid")): p for p in (report.get("products") or [])}
    links = report.get("links") or []
    rows = []
    for doc in report.get("sources") or []:
        kind = doc.get("kind")
        if kind not in PROOF_TYPES or doc.get("error"):
            continue
        filename = str(doc.get("filename") or "")
        digest = str(doc.get("sha256") or "").lower()
        fields = doc.get("fields") or {}
        evidence = doc.get("evidence") or {}
        conflicts = doc.get("conflicts") or {}
        warnings = []
        if not doc.get("complete_read"):
            warnings.append("Tệp chưa đọc đầy đủ; phải kiểm tra bản gốc")
        if not re.fullmatch(r"[0-9a-f]{64}", digest):
            warnings.append("Thiếu mã SHA-256 hợp lệ")
        for field in REQUIRED_REVIEW_FIELDS[kind]:
            if not fields.get(field) or field in conflicts:
                warnings.append(f"Thiếu/mâu thuẫn trường {field}")
            else:
                cite = evidence.get(field) or {}
                if (not cite.get("source") or not cite.get("raw")
                        or cite.get("file") != filename
                        or str(cite.get("sha256") or "").lower() != digest):
                    warnings.append(f"Trường {field} chưa có trích dẫn nguồn nhất quán")
        if kind == "GMP_EXPLANATION":
            warnings.append("Công văn giải trình KHÔNG thay thế chứng nhận GMP")
        matched = [l for l in links
                   if l.get("source_evidence") == filename
                   and l.get("source_sha256") == digest
                   and l.get("evidence_kind") == kind]
        for link in matched:
            product = products.get(str(link.get("product_id") or ""))
            if product is None:
                warnings.append("Liên kết trỏ tới mã sản phẩm không tồn tại")
                continue
            pf = product.get("fields") or {}
            cf = product.get("conflicts") or {}
            for field in COMPARABLE:
                pv, dv = pf.get(field), fields.get(field)
                if field in cf or field in conflicts:
                    warnings.append(f"Trường {field} có mâu thuẫn nguồn; không tự đối chiếu")
                elif pv and dv and _norm(pv) != _norm(dv):
                    warnings.append(f"XUNG ĐỘT: {field} khác giữa thuốc và chứng cứ")
        if not matched:
            warnings.append("Chưa có liên kết chứng cứ duy nhất tới thuốc")
        warnings.append("Chưa xác thực giấy gốc, hiệu lực, phạm vi và cơ quan cấp")
        rows.append({
            "Tệp chứng cứ": filename,
            "Loại chứng cứ gợi ý": LABELS[kind],
            "Nhà máy trong giấy": str(fields.get("FACTORY") or ""),
            "SĐK trong giấy": str(fields.get("REGISTRATION_NO") or ""),
            "Số GMP trong giấy": str(fields.get("GMP_NUMBER") or ""),
            "Phạm vi GMP trong giấy": str(fields.get("GMP_SCOPE") or ""),
            "Hết hạn GMP ghi trên giấy": str(fields.get("GMP_EXPIRY") or ""),
            "Ứng viên liên kết": ", ".join(sorted({str(l.get("product_id")) for l in matched})),
            "Số liên kết sơ bộ": len(matched),
            "Vị trí trích xuất": "; ".join(sorted({str(c.get("source"))
                                   for c in evidence.values() if c.get("source")})),
            "SHA256 tệp": digest,
            "Điểm cần kiểm tra": "; ".join(dict.fromkeys(warnings)),
            "Xác minh pháp lý": "CHƯA XÁC MINH",
        })
    return {
        "rows": rows,
        "documents_reviewed": len(rows),
        "provisional_links": sum(r["Số liên kết sơ bộ"] for r in rows),
        "verified": False,
        "gmp_confirmed": False,
        "registration_confirmed": False,
        "quote_approved": False,
        "bid_eligible": False,
    }
