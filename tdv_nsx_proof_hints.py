"""Source-anchored extraction *hints* for PDF SĐK/GMP audit.

Only detects explicitly labeled values on the same page. Hints never populate
product fields, create proof links, certify validity or approve a medicine.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

ALIASES = {
    "PRODUCT_NAME": (
        "ten thuoc", "ten thuoc dang ky", "ten biet duoc",
        "ten thuong mai", "ten san pham", "ten thuoc duoc cap phep",
        "product name", "trade name",
    ),
    "REGISTRATION_NO": (
        "so dang ky", "so dang ky luu hanh", "so dang ky luu hanh thuoc",
        "so giay dang ky luu hanh", "registration number", "registration no",
        "marketing authorization number", "ma so dang ky",
        "so dk", "so dklh", "sdk", "registration no.",
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
    "REGISTRATION": ("PRODUCT_NAME", "REGISTRATION_NO"),
    "GMP_CERT": ("GMP_NUMBER", "GMP_SCOPE", "GMP_EXPIRY"),
    "GMP_EXPLANATION": ("GMP_NUMBER", "GMP_SCOPE", "GMP_EXPIRY"),
}
_LABEL_VALUE = re.compile(r"^(.{3,95}?)(?:\s*[:：]\s*|\s+[-–]\s+)(.{2,250})$")
_DATE = re.compile(r"(?<!\d)(?:[0-3]?\d[/.-][01]?\d[/.-](?:19|20)\d{2}|(?:19|20)\d{2}[/.-][01]?\d[/.-][0-3]?\d)(?!\d)")
# Strict source-context candidates, NOT legal SĐK verification.
_REGISTRATION_CONTEXT = ("dang ky", "dangky", "giay phep luu hanh",
                         "registration", "so dk", "s8k", "sdk", "dklh")
_REGISTRATION_CODE = re.compile(
    r"(?<![A-Za-z0-9])(?:VD|VN)\s*[.\-]\s*\d{3,6}\s*[.\-]\s*\d{2}(?![A-Za-z0-9])",
    re.IGNORECASE,
)


def _norm(value: str) -> str:
    s = unicodedata.normalize("NFKD", str(value or "").replace("Đ", "D").replace("đ", "d"))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    # Trim punctuation first so labels like "Tên thuốc (biệt dược):"
    # still drop the trailing explanatory qualifier.
    s = s.strip().rstrip(". :：;,-–").strip()
    s = re.sub(r"\s*\([^)]{1,24}\)\s*$", "", s).strip()
    return " ".join(s.split()).rstrip(". :：;,-–").strip()


def _supported_value(field: str, value: str) -> bool:
    if not 2 <= len(value) <= 250:
        return False
    if field == "PRODUCT_NAME":
        # Multi-column OCR headings are NOT drug names.
        if "|" in value:
            return False
        name = _norm(value)
        return (
            2 <= len(name) <= 100
            and len(re.findall(r"[a-z]", name)) >= 2
            and name not in {a for group in ALIASES.values() for a in group}
            and not name.startswith(("giay dang ky", "giay chung nhan", "so dang ky"))
        )
    if field in ("REGISTRATION_NO", "GMP_NUMBER"):
        token = re.sub(r"\s*([./-])\s*", r"\1", value.strip().upper())
        # A date is not an unambiguous SĐK/GMP certificate number.
        if _DATE.fullmatch(token):
            return False
        return (len(token) <= 65 and
                bool(re.fullmatch(r"[A-Z0-9]+(?:[./-][A-Z0-9]+)*", token)) and
                sum(ch.isdigit() for ch in token) >= 2)
    if field == "GMP_EXPIRY":
        return bool(_DATE.search(value))
    if field == "GMP_SCOPE":
        if "|" in value:
            return False
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
    # Weak, explicitly unverified fallback: an SĐK-shaped token may sit on
    # the same line as a registration label or immediately after it on the
    # SAME page. Do not read unrelated annex/table rows or unlabeled numbers.
    if kind == "REGISTRATION" and "REGISTRATION_NO" in missing and len(candidates) < limit:
        for index, line in enumerate(lines):
            place = str(line.get("source") or "")
            raw = str(line.get("text") or "").strip()
            if not place or "|" in raw:
                continue
            this_context = _norm(raw)
            previous_context = ""
            if index and str(lines[index - 1].get("source") or "") == place:
                previous_context = _norm(str(lines[index - 1].get("text") or ""))
            if not any(key in this_context or key in previous_context
                       for key in _REGISTRATION_CONTEXT):
                continue
            for match in _REGISTRATION_CODE.finditer(raw):
                value = match.group(0).strip()
                identity = ("REGISTRATION_NO", place, _norm(value))
                if identity in seen:
                    continue
                seen.add(identity)
                candidates.append({
                    "field": "REGISTRATION_NO",
                    "value": value,
                    "source": place,
                    "raw": raw[:450],
                    "sha256": str(source.get("sha256") or ""),
                    "reading_method": "OCR (chưa đối chiếu)" if "OCR" in place.upper()
                                      else "Lớp chữ PDF (chưa đối chiếu)",
                    "status": "GOI_Y_MA_DANG_KY_CAN_SO_BAN_GOC",
                    "verified": False,
                })
                if len(candidates) >= limit:
                    break
            if len(candidates) >= limit:
                break
    # Different punctuation across OCR/native pages should not be reported
    # as conflicting numbers when the underlying registration token agrees.
    by_field: dict[str, set[str]] = {}
    for row in candidates:
        value = str(row["value"])
        normalized_value = (re.sub(r"[^A-Z0-9]", "", value.upper())
                            if row["field"] == "REGISTRATION_NO"
                            else _norm(value))
        by_field.setdefault(row["field"], set()).add(normalized_value)
    for row in candidates:
        if len(by_field[row["field"]]) > 1:
            row["status"] = "NHIEU_GIA_TRI_GOI_Y_CAN_DOI_CHIEU"
    return candidates


def diagnose_proof_source(kind: str, source: dict, fields: dict,
                          hints: list[dict]) -> dict | None:
    """Read-only coverage diagnostics, not a verdict that the PDF lacks a field."""
    relevant = FIELDS_BY_KIND.get(kind)
    if source.get("type") != "pdf" or not relevant:
        return None
    lines = source.get("lines") or []
    absent = [field for field in relevant if not (fields or {}).get(field)]
    hinted = {item.get("field") for item in hints or []}
    missing_hints = [field for field in absent if field not in hinted]
    ocr_lines = sum("OCR" in str(row.get("source") or "").upper() for row in lines)
    message = (
        "CHUA_CO_GOI_Y_THEO_NHAN; CAN_SO_PDF_GOC" if missing_hints
        else "CO_GOI_Y_CHUA_XAC_MINH" if hints
        else "CAC_TRUONG_THEO_NHAN_DA_TRICH; CHUA_XAC_MINH"
    )
    return {
        "kind": kind,
        "pages": int(source.get("pages") or 0),
        "source_lines": len(lines),
        "ocr_lines": ocr_lines,
        "fields_without_extracted_value": ", ".join(absent),
        "fields_without_hint": ", ".join(missing_hints),
        "hint_count": len(hints or []),
        "status": message,
        "verified": False,
    }


# Conservative OCR/text context for human source inspection. These are NOT
# extracted SĐK/GMP fields. Adjacent text can help diagnose broken OCR labels.
_CONTEXT_TERMS = {
    "REGISTRATION": (
        "dang ky", "dangky", "sodangky", "sdk", "s d k", "so dk", "dklh",
        "registration", "luu hanh", "giay phep",
    ),
    "GMP_CERT": (
        "gmp", "thuc hanh tot", "pham vi", "chung nhan",
        "hieu luc", "het han", "giay chung nhan",
    ),
    "GMP_EXPLANATION": (
        "gmp", "thuc hanh tot", "pham vi", "chung nhan",
        "hieu luc", "het han",
    ),
}


def collect_proof_contexts(kind: str, source: dict, *, limit: int = 24) -> list[dict]:
    """Sample matching source/OCR lines with SAME-page neighbours for review.

    A hit is only a string-search result. This function neither infers a
    registration number nor changes evidence or legal status. Limits are
    documented in the exported data.
    """
    if source.get("type") != "pdf" or kind not in _CONTEXT_TERMS or limit < 1:
        return []
    lines = (source.get("lines") or [])[:10000]
    keywords = _CONTEXT_TERMS[kind]
    found: list[dict] = []
    by_page: dict[str, int] = {}
    for idx, line in enumerate(lines):
        location = str(line.get("source") or "")
        text = str(line.get("text") or "").strip()
        if not location or not text:
            continue
        lowered = _norm(text)
        matched = [term for term in keywords if term in lowered]
        if not matched or by_page.get(location, 0) >= 5:
            continue
        before = str(lines[idx - 1].get("text") or "").strip() if idx and str(
            lines[idx - 1].get("source") or "") == location else ""
        after = str(lines[idx + 1].get("text") or "").strip() if idx + 1 < len(lines) and str(
            lines[idx + 1].get("source") or "") == location else ""
        found.append({
            "source": location,
            "keywords": ", ".join(matched),
            "line": text[:230],
            "previous_line": before[:160],
            "next_line": after[:160],
            "reading_method": "OCR chưa đối chiếu" if "OCR" in location.upper()
                              else "Lớp chữ PDF chưa đối chiếu",
            "status": "DOAN_VAN_CAN_SO_BAN_GOC",
            "verified": False,
        })
        by_page[location] = by_page.get(location, 0) + 1
        if len(found) >= limit:
            break
    return found
