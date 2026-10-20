"""SEE PRO geometry-based technical table extraction for supported G1 e-GP layout.

No OCR hallucinations, no bid-price creation, no legal decisions.
The CDNT summary is used only to CROSS-CHECK monetary fields, not to
invent missing technical fields. Unsupported page geometry is skipped.
"""
from __future__ import annotations
import re
from decimal import Decimal
from typing import Any

G1 = re.compile(r"G1\.\d{3}$")
# Landscape e-GP G1 Mẫu số 00: bounded x column intervals in PDF points.
REGIONS = {
    "MA_PHAN_LO_BANG_KY_THUAT": (78, 147),
    "HOAT_CHAT_BANG_KY_THUAT": (215, 283),
    "NONG_DO_HAM_LUONG": (283, 340),
    "DUONG_DUNG": (340, 391),
    "DANG_BAO_CHE": (391, 446),
    "DON_VI_TINH": (446, 499),
    "SO_LUONG_CHINH": (499, 550),
    "DON_GIA_KE_HOACH": (550, 624),
    "NHOM_THUOC": (624, 658),
}


def _codes(words: list[tuple]) -> list[tuple]:
    return sorted((w for w in words if G1.fullmatch(w[4]) and 142 <= w[0] <= 160),
                  key=lambda w: w[1])


def _geometry_ok(page) -> bool:
    return 831 < page.rect.width < 852 and 587 < page.rect.height < 604


def _numeric(tokens: list[str]) -> int | None:
    raw = "".join(tokens)
    if not re.fullmatch(r"\d+(?:\.\d+)*", raw):
        return None
    try:
        return int(raw.replace(".", ""))
    except ValueError:
        return None


def extract_g1_technical(pdf_data: bytes, summary: dict, *, max_pages: int = 1200) -> dict:
    """Extract every G1 row as candidates and validate with CDNT financial totals.

    This does NOT certify field correctness. Evidence includes page, token text
    and column x bounds. Never fill unsupported fields from inferred defaults.
    """
    import pymupdf
    source_lots = {r["MA_THUOC"]: r for r in summary.get("lots", [])}
    extracted, findings = {}, []
    if not pdf_data.startswith(b"%PDF-"):
        raise ValueError("Yêu cầu PDF hợp lệ")
    with pymupdf.open(stream=pdf_data, filetype="pdf") as pdf:
        if pdf.needs_pass or pdf.page_count > max_pages:
            raise ValueError("PDF khóa mật khẩu hoặc quá giới hạn")
        for pi in range(pdf.page_count):
            page = pdf[pi]
            if not _geometry_ok(page):
                continue
            words = page.get_text("words", sort=True)
            codes = _codes(words)
            if not codes:
                continue
            for index, code_word in enumerate(codes):
                code = code_word[4]
                if code not in source_lots:
                    continue
                start = code_word[1] - 2
                end = min(codes[index + 1][1] - 2 if index + 1 < len(codes) else 545,
                          start + 150)
                cells = [w for w in words if start <= w[1] < end and w[0] < 660 and w[1] < 544]
                evidence_pages = [pi + 1]
                # A row printed at the bottom of a page can continue above
                # the first new row of the following page (under its header).
                if index == len(codes) - 1 and start > 450 and pi + 1 < pdf.page_count:
                    following = pdf[pi + 1]
                    if _geometry_ok(following):
                        nxt = following.get_text("words", sort=True)
                        nxt_codes = _codes(nxt)
                        if nxt_codes:
                            limit_y = nxt_codes[0][1] - 5
                            continued = [w for w in nxt if 175 <= w[1] < limit_y
                                         and 50 < w[0] < 660]
                            if continued:
                                cells.extend(continued)  # KEEP page order, not y sort.
                                evidence_pages.append(pi + 2)
                fields = {}
                citations = {}
                for field, (left, right) in REGIONS.items():
                    tokens = [w[4] for w in cells if left <= w[0] < right]
                    if tokens:
                        fields[field] = tokens
                        citations[field] = {
                            "pages": evidence_pages,
                            "x_range": [left, right],
                            "raw_tokens": tokens,
                            "verified": False,
                        }
                qty = _numeric(fields.get("SO_LUONG_CHINH", []))
                unit_price = _numeric(fields.get("DON_GIA_KE_HOACH", []))
                source = source_lots[code]
                source_amount = source.get("GIA_TRI_UOC_TINH")
                math_ok = (
                    isinstance(source_amount, int) and qty is not None and
                    unit_price is not None and qty * unit_price == source_amount
                )
                pp_from_tech = "".join(fields.get("MA_PHAN_LO_BANG_KY_THUAT", []))
                pp_ok = pp_from_tech == source.get("MA_PHAN_LO")
                row = {
                    "MA_THUOC": code,
                    "MA_PHAN_LO": source.get("MA_PHAN_LO", ""),
                    "TRANG_KY_THUAT": pi + 1,
                    "TRANG_CHUNG_CU": evidence_pages,
                    "NONG_DO_HAM_LUONG": " ".join(fields.get("NONG_DO_HAM_LUONG", [])),
                    "DUONG_DUNG": " ".join(fields.get("DUONG_DUNG", [])),
                    "DANG_BAO_CHE": " ".join(fields.get("DANG_BAO_CHE", [])),
                    "DON_VI_TINH": " ".join(fields.get("DON_VI_TINH", [])),
                    "NHOM_THUOC": "".join(fields.get("NHOM_THUOC", [])),
                    "HOAT_CHAT_BANG_KY_THUAT": " ".join(fields.get("HOAT_CHAT_BANG_KY_THUAT", [])),
                    "SO_LUONG_CHINH": qty,
                    "DON_GIA_KE_HOACH": unit_price,
                    "GIA_TRI_UOC_TINH": source_amount,
                    "KHOP_TONG_GIA_TRI": math_ok,
                    "KHOP_MA_PHAN_LO": pp_ok,
                    "EVIDENCE": citations,
                    "verified": False,
                    "TRANG_THAI": "DOI_CHIEU_SO_HOC_KHOP_CHUA_XAC_MINH" if math_ok and pp_ok
                                  else "CAN_XEM_LAI_BANG_KY_THUAT",
                }
                if code in extracted:
                    findings.append({"type": "DUPLICATE_TECHNICAL_CODE", "code": code,
                                     "page": pi + 1})
                extracted[code] = row
                if not math_ok:
                    findings.append({"type": "MATH_OR_EXTRACTION_MISMATCH", "code": code,
                                     "page": pi + 1, "source_amount": source_amount,
                                     "quantity": qty, "unit_price": unit_price})
                if not pp_ok:
                    findings.append({"type": "PART_CODE_SOURCE_CONFLICT", "code": code,
                                     "page": pi + 1, "source": source.get("MA_PHAN_LO"),
                                     "technical": pp_from_tech})
    missing = sorted(set(source_lots) - set(extracted))
    if missing:
        findings.append({"type": "MISSING_TECHNICAL_ROWS", "count": len(missing),
                         "codes": missing[:100]})
    return {
        "rows": sorted(extracted.values(), key=lambda r: int(r["MA_THUOC"].split(".")[1])),
        "found_rows": len(extracted),
        "financial_crosschecked": sum(r["KHOP_TONG_GIA_TRI"] for r in extracted.values()),
        "part_crosschecked": sum(r["KHOP_MA_PHAN_LO"] for r in extracted.values()),
        "expected": len(source_lots), "findings": findings,
        "verified": False,
        "note": "Financial arithmetic and spatial evidence only; no technical or legal approval.",
    }
