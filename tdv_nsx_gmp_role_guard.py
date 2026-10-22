"""Conservative role guard for GMP explanations and maintenance letters.

Text headings can support a provisional supplemental-document role. A filename
alone can only block a potentially unsafe CERT label, never establish validity.
"""
from __future__ import annotations

import re
import unicodedata


def _norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", str(value or "").replace("Đ", "D").replace("đ", "d"))
    value = "".join(c for c in value if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", value)).strip()


def inspect_gmp_role(filename: str, lines: list[dict]) -> dict:
    """Return a cautious document-role suggestion without changing source facts."""
    name = _norm(filename.rsplit(".", 1)[0])
    header = _norm(" ".join(str(row.get("text") or "") for row in lines[:80]))
    excerpt = _norm(" ".join(str(row.get("text") or "") for row in lines[:180]))
    gmp_word = ("gmp" in excerpt or "thuc hanh tot san xuat" in excerpt)
    is_explanation = "giai trinh" in header and gmp_word
    is_maintenance = (
        ("xac nhan duy tri" in header or "duy tri dap ung" in header)
        and gmp_word
    )
    # Exact certificate expressions, NOT a generic mention of GMP.
    certificate_title = any(phrase in header for phrase in (
        "giay chung nhan gmp", "gmp certificate",
        "certificate of good manufacturing practice",
        "giay chung nhan dat tieu chuan thuc hanh tot",
        "chung nhan thuc hanh tot san xuat",
    ))
    name_support = (
        ("gmp" in name or "thuc hanh tot san xuat" in name)
        and any(term in name for term in (
            "giai trinh", "xac nhan duy tri", "duy tri dap ung",
            "cong van giai trinh",
        ))
    )
    content_support = is_explanation or is_maintenance
    if content_support and not certificate_title:
        return {
            "status": "SUPPLEMENT",
            "kind": "GMP_EXPLANATION",
            "filename_hint": name_support,
            "reason": ("Tiêu đề/nội dung trích xuất gợi ý văn bản giải trình "
                       "hoặc xác nhận duy trì GMP; KHÔNG phải chứng nhận GMP."),
        }
    if name_support or (content_support and certificate_title):
        return {
            "status": "NEEDS_REVIEW",
            "kind": "OTHER",
            "filename_hint": name_support,
            "reason": ("Tên tệp hoặc nội dung gợi ý văn bản bổ sung GMP, "
                       "nhưng văn bản trích xuất chưa đủ nhất quán để xác định loại; "
                       "không được tự phân loại thành giấy chứng nhận GMP."),
        }
    return {"status": "NO_SIGNAL", "kind": "", "filename_hint": False, "reason": ""}
