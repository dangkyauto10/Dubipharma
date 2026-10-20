"""TDV-IDP 3.0: in-memory, demonstration-only PDF reading and strict field audit.

No uploaded user documents, no network, no Google Sheets/Drive writes, no eligibility
conclusions. Fixtures here are illustrative; never evidence for an actual tender.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from io import BytesIO
import re
import unicodedata


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKC", str(value or "")).casefold()
    return re.sub(r"\s+", " ", value).strip()


UNITS = {"mg": Decimal("1"), "g": Decimal("1000"),
         "mcg": Decimal("0.001"), "µg": Decimal("0.001"), "μg": Decimal("0.001")}
STRENGTH = re.compile(r"\s*(\d+(?:[.,]\d+)?)\s*(mg|mcg|[µμ]g|g)\s*", re.I)


def exact_strength_mg(value: str) -> Decimal | None:
    text = str(value or "").strip()
    m = STRENGTH.fullmatch(text)
    if not m:
        return None
    number = m.group(1)
    if re.fullmatch(r"[1-9]\d{0,2}[.,]\d{3}", number):
        return None  # Locale/thousands ambiguity: request source review.
    try:
        result = Decimal(number.replace(",", ".")) * UNITS[m.group(2).lower()]
        return result if result > 0 else None
    except (InvalidOperation, KeyError):
        return None


def match_fields(lot: dict, nsx: dict) -> dict:
    mismatches, uncertain, same = [], [], []
    for key, title in (
        ("hoat_chat", "Hoạt chất"), ("ham_luong", "Hàm lượng"),
        ("dang_bao_che", "Dạng bào chế"), ("duong_dung", "Đường dùng")
    ):
        a, b = str(lot.get(key) or "").strip(), str(nsx.get(key) or "").strip()
        if not a or not b:
            uncertain.append(f"Thiếu {title.lower()}"); continue
        if key == "ham_luong":
            left, right = exact_strength_mg(a), exact_strength_mg(b)
            if left is None or right is None:
                uncertain.append(f"{title} phức tạp hoặc mơ hồ: cần đọc nguồn gốc")
                continue
            eq = left == right
        else:
            eq = normalize_name(a) == normalize_name(b)
        (same if eq else mismatches).append(title if eq else f"{title}: {a} ≠ {b}")
    status = ("KHONG_KHOP" if mismatches else
              "CAN_XAC_MINH" if uncertain else "KHOP_4_TRUONG")
    return {"status": status, "mismatches": mismatches,
            "uncertainties": uncertain, "same": same,
            "verified": False, "bid_eligible": False}


def legal_evidence(doc_type: str, factory: str, product_factory: str) -> dict:
    if not factory or not product_factory:
        return {"status": "CAN_XAC_MINH", "note": "Chưa có định danh nhà máy"}
    if normalize_name(factory) != normalize_name(product_factory):
        return {"status": "CHAN_LIEN_KET", "note": "Không được gắn GMP khác nhà máy"}
    kind = normalize_name(doc_type)
    if any(t in kind for t in ("cong van", "công văn", "quyet dinh", "quyết định", "giai trinh", "giải trình")):
        return {"status": "CHUNG_CU_BO_SUNG",
                "note": "Không coi công văn/quyết định là chứng nhận GMP gia hạn"}
    return {"status": "CAN_XAC_MINH", "note": "Cần đọc nội dung, phạm vi và thời hạn chứng nhận"}


def make_synthetic_pdf() -> bytes:
    """Generate an in-memory two-page DEMO with artificial layout, no source data."""
    import pymupdf
    doc = pymupdf.open()
    for label, active, strength in (
        ("G1.003", "Acenocoumarol", "1 mg"),
        ("G1.004", "Acenocoumarol", "4 mg"),
    ):
        page = doc.new_page()
        page.insert_text((66, 80), "TDV IDP 3.0 - DEMO - NOT REAL TENDER", fontsize=14)
        page.insert_text((66, 125), f"Lot: {label}", fontsize=12)
        page.insert_text((66, 155), f"Ingredient: {active}", fontsize=12)
        page.insert_text((66, 185), f"Strength: {strength}", fontsize=12)
    result = doc.tobytes()
    doc.close()
    return result


def read_pdf_pages(pdf: bytes, *, first: int = 1, maximum: int = 4) -> dict:
    """Extract bounded pages with two methods when available; never certify accuracy."""
    import pymupdf
    if not pdf.startswith(b"%PDF-") or len(pdf) > 30 * 1024 * 1024:
        raise ValueError("PDF không hợp lệ hoặc vượt 30 MB")
    if not 1 <= maximum <= 8:
        raise ValueError("Giới hạn 1–8 trang/lượt")
    rows, warnings = [], []
    with pymupdf.open(stream=pdf, filetype="pdf") as doc:
        if first < 1 or first > doc.page_count:
            raise ValueError("Trang bắt đầu nằm ngoài tài liệu")
        for idx in range(first - 1, min(first - 1 + maximum, doc.page_count)):
            text_a = doc[idx].get_text("text", sort=True) or ""
            text_b = ""
            try:
                import pdfplumber
                with pdfplumber.open(BytesIO(pdf), pages=[idx + 1]) as copy:
                    text_b = copy.pages[0].extract_text() or ""
            except (ImportError, OSError, ValueError, RuntimeError, IndexError):
                warnings.append(f"Trang {idx+1}: bộ đọc thứ hai chưa khả dụng")
            if not text_a.strip():
                warnings.append(f"Trang {idx+1}: lớp chữ trống, cần OCR hoặc xem ảnh gốc")
            if text_a and text_b:
                num_a = re.findall(r"\d+(?:[.,]\d+)?", text_a)
                num_b = re.findall(r"\d+(?:[.,]\d+)?", text_b)
                if sorted(num_a) != sorted(num_b):
                    warnings.append(f"Trang {idx+1}: hai cách đọc khác token số")
            rows.append({"trang": idx+1, "PyMuPDF": text_a[:900],
                         "pdfplumber": text_b[:900],
                         "cần_OCR": not bool(text_a.strip()),
                         "kết_luận": "CHƯA XÁC MINH"})
        if len(rows) < doc.page_count:
            warnings.append(f"Đã xử lý {len(rows)}/{doc.page_count} trang — chưa đọc toàn bộ")
        return {"total_pages": doc.page_count, "pages_read": len(rows),
                "pages": rows, "warnings": warnings, "verified": False}


def demo_audit() -> dict:
    lot_1 = {"hoat_chat": "Acenocoumarol", "ham_luong": "1 mg",
             "dang_bao_che": "Viên nén", "duong_dung": "Uống"}
    lot_4 = dict(lot_1, ham_luong="4 mg")
    product = dict(lot_1)
    return {"same_strength": match_fields(lot_1, product),
            "different_strength": match_fields(lot_4, product),
            "wrong_gmp_factory": legal_evidence("Chứng nhận GMP", "Mỹ Thới", "Bình Hòa"),
            "gmp_explanation": legal_evidence("Công văn giải trình", "Mỹ Thới", "Mỹ Thới")}
