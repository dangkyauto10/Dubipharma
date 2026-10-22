"""Source-anchored extraction *hints* for PDF SĐK/GMP audit.

Only detects explicitly labeled values on the same page. Hints never populate
product fields, create proof links, certify validity or approve a medicine.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

ALIASES = {
    "REGISTRATION_NO": (
        "so dang ky", "so dang ky luu hanh", "so dang ky luu hanh thuoc",
        "so giay dang ky luu hanh", "registration number", "registration no",
        "marketing authorization number", "ma so dang ky",
    ),
    "GMP_NUMBER": (
        "so gmp", "so giay chung nhan gmp", "so chung nhan gmp",
        "so gcn gmp", "gmp number", "gmp certificate number",
        "certificate number gmp",
    ),
    "GMP_SCOPE": (
        "pham vi gmp", "pham vi chung nhan gmp",
        "gmp scope", "pham vi chung nhan thuc hanh tot san xuat",
    ),
    "GMP_EXPIRY": (
        "ngay het han gmp", "hieu luc gmp den ngay",
        "gmp expiry", "gmp expiration date",
    ),
}
FIELDS_BY_KIND = {
    "REGISTRATION": ("REGISTRATION_NO",),
    "GMP_CERT": ("GMP_NUMBER", "GMP_SCOPE", "GMP_EXPIRY"),
    "GMP_EXPLANATION": ("GMP_NUMBER", "GMP_SCOPE", "GMP_EXPIRY"),
}
_LABEL_VALUE = re.compile(r"^(.{3,95}?)(?:\s*[:：]\s*|\s+[-–]\s+)(.{2,250})$")
_DATE = re.compile(r"(?<!\d)(?:[0-3]?\d[/.-][01]?\d[/.-](?:19|20)\d{2}|(?:19|20)\d{2}[/.-][01]?\d[/.-][0-3]?\d)(?!\d)")


def _norm(value: str) -> str:
    s = unicodedata.normalize("NFKD", str(value or "").replace("Đ", "D").replace("đ", "d"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"\s*\([^)]{1,24}\)\s*$", "", s).strip()
    return " ".join(s.split()).rstrip(".")


def _supported_value(field: str, value: str) -> bool:
    if not 2 <= len(value) <= 250:
        return False
    if field in ("REGISTRATION_NO", "GMP_NUMBER"):
        token = value.strip().upper()
        return (len(token) <= 65 and
                bool(re.fullmatch(r"[A-Z0-9]+(?:[./-][A-Z0-9]+)*", token)) and
                sum(ch.isdigit() for ch in token) >= 2)
    if field == "GMP_EXPIRY":
        return bool(_DATE.search(value))
    if field == "GMP_SCOPE":
        return 5 <= len(value) <= 250 and not any(
            _norm(value) in aliases for aliases in ALIASES.values()
        )
    return False


def extract_labeled_hints(
    kind: str, source: dict, extracted_fields: dict,
    *, limit: int = 18,
) -> list[dict]:
    """Preserve candidate text, precise page source, and OCR uncertainty."""
    relevant = FIELDS_BY_KIND.get(kind, ())
    if source.get("type") != "pdf" or not relevant:
        return []
    missing = [key for key in relevant if not extracted_fields.get(key)]
    if not missing:
        return []
    aliases = {field: {_norm(a) for a in ALIASES[field]} for field in missing}
    lines = (source.get("lines") or [])[:10000]
    candidates: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    for i, line in enumerate(lines):
        place = str(line.get("source") or "")
        raw_label = str(line.get("text") or "").strip()
        if not place or not raw_label:
            continue
        pair = _LABEL_VALUE.fullmatch(raw_label)
        for field in missing:
            value = ""
            original = ""
            if pair and _norm(pair.group(1)) in aliases[field]:
                value = pair.group(2).strip()
                original = raw_label
            elif _norm(raw_label) in aliases[field] and i + 1 < len(lines):
                nxt = lines[i + 1]
                if str(nxt.get("source") or "") != place:
                    continue
                value = str(nxt.get("text") or "").strip()
                original = raw_label + " | " + value
            if not value or not _supported_value(field, value):
                continue
            identity = (field, place, _norm(value))
            if identity in seen:
                continue
            seen.add(identity)
            candidates.append({
                "field": field,
                "value": value,
                "source": place,
                "raw": original[:450],
                "sha256": str(source.get("sha256") or ""),
                "reading_method": "OCR (chưa đối chiếu)" if "OCR" in place.upper()
                                  else "Lớp chữ PDF (chưa đối chiếu)",
                "status": "GOI_Y_CAN_SO_BAN_GOC",
                "verified": False,
            })
            if len(candidates) >= limit:
                break
        if len(candidates) >= limit:
            break
    counts = Counter(row["field"] for row in candidates)
    for row in candidates:
        if counts[row["field"]] > 1:
            row["status"] = "NHIEU_GIA_TRI_GOI_Y_CAN_DOI_CHIEU"
    return candidates
