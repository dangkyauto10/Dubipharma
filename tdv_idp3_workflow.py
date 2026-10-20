"""TDV-IDP 3.0 Preview: in-memory DEMO E-HSMT -> NSX -> leadership pipeline.

This is a conservative extraction/workflow prototype, NOT a tender parser certified
for real E-HSMT. No network, disk writes, API keys, persisted documents or approvals.
"""
from __future__ import annotations

from io import BytesIO
import hashlib
import json
import re
import unicodedata
from typing import Any

from tdv_demo_core import match_fields
from tdv_idp3_rules import analyze_page_layers, review_evidence_link

MAX_BYTES = 25 * 1024 * 1024
MAX_PAGES = 80
MAX_TEXT_PER_PAGE = 25000

LABELS = {
    "lot": "lot_id", "ma thuoc": "lot_id", "ma danh muc": "lot_id",
    "ma hang": "lot_id", "ma phan": "lot_id",
    "ingredient": "hoat_chat", "hoat chat": "hoat_chat", "ten hoat chat": "hoat_chat",
    "strength": "ham_luong", "ham luong": "ham_luong",
    "dosage form": "dang_bao_che", "dang bao che": "dang_bao_che",
    "route": "duong_dung", "duong dung": "duong_dung",
    "quantity": "so_luong", "so luong": "so_luong",
    "product id": "product_id", "ma san pham": "product_id",
    "factory id": "factory_id", "ma nha may": "factory_id",
    "manufacturer id": "manufacturer_id", "ma nha san xuat": "manufacturer_id",
}
LOTS_REQUIRED = ("hoat_chat", "ham_luong", "dang_bao_che", "duong_dung", "so_luong")
PRODUCT_REQUIRED = ("product_id", "factory_id", "manufacturer_id",
                    "hoat_chat", "ham_luong", "dang_bao_che", "duong_dung")
DOC_TYPES = {"GMP_CERT", "GMP_EXPLANATION", "QUOTE", "AUTHORIZATION", "NSX"}


def _fold(text: str) -> str:
    base = unicodedata.normalize("NFKD", text).casefold()
    return re.sub(r"\s+", " ", "".join(c for c in base if not unicodedata.combining(c))).strip()


def _pairs(text: str):
    for line in text.splitlines():
        m = re.fullmatch(r"\s*([^:：]{2,40})\s*[:：]\s*(.{1,500})\s*", line)
        if m:
            key = LABELS.get(_fold(m.group(1)))
            if key:
                yield key, m.group(2).strip(), line.strip()[:240]


def _page_evidence(doc: dict, page: dict, excerpt: str, key: str, value: str) -> dict:
    return {
        "source_id": doc["source_id"], "sha256": doc["sha256"],
        "page": page["page"], "method": page["method"], "excerpt": excerpt,
        "field": key, "value": value, "verified": False
    }


def extract_pdf(data: bytes, *, ocr: bool = False, max_pages: int = MAX_PAGES) -> dict:
    """Read bounded pages; optional local Tesseract OCR. Fail closed if incomplete."""
    if not isinstance(data, bytes) or not data.startswith(b"%PDF-") or len(data) > MAX_BYTES:
        raise ValueError("Chỉ nhận PDF tối đa 25 MB với định dạng hợp lệ")
    if max_pages < 1 or max_pages > MAX_PAGES:
        raise ValueError("Số trang tối đa không hợp lệ")
    import pymupdf

    digest = hashlib.sha256(data).hexdigest()
    pages, warnings = [], []
    try:
        with pymupdf.open(stream=data, filetype="pdf") as pdf:
            if pdf.needs_pass or pdf.page_count == 0:
                raise ValueError("PDF khóa mật khẩu hoặc rỗng; chưa thể đọc")
            total = pdf.page_count
            limit = min(total, max_pages)
            # Explicitly avoid loading the complete PDF into another extractor.
            for i in range(limit):
                page = pdf[i]
                text_a = (page.get_text("text", sort=True) or "")
                text_b = ""
                try:
                    import pdfplumber
                    with pdfplumber.open(BytesIO(data), pages=[i + 1]) as alternate:
                        text_b = alternate.pages[0].extract_text() or ""
                except (ImportError, OSError, RuntimeError, ValueError, IndexError) as exc:
                    warnings.append(f"Trang {i+1}: bộ đọc bảng/lớp chữ thứ hai không khả dụng ({type(exc).__name__})")
                method = "pymupdf"
                text = text_a if text_a.strip() else text_b
                if text and not text_a:
                    method = "pdfplumber"
                ocr_attempted = False
                if len(text.strip()) < 10 and ocr:
                    ocr_attempted = True
                    # Limit huge embedded page sizes; OCR is local, no cloud submission.
                    if page.rect.width <= 2000 and page.rect.height <= 2000:
                        try:
                            tp = page.get_textpage_ocr(language="vie+eng", dpi=160, full=True)
                            extracted = page.get_text("text", textpage=tp)
                            if extracted.strip():
                                text = extracted
                                method = "ocr"
                        except (RuntimeError, ValueError, OSError) as exc:
                            warnings.append(f"Trang {i+1}: OCR cục bộ chưa dùng được ({type(exc).__name__})")
                    else:
                        warnings.append(f"Trang {i+1}: kích thước trang quá lớn để OCR tự động")
                if not text.strip():
                    warnings.append(f"Trang {i+1}: KHÔNG có văn bản; cần OCR/so ảnh gốc")
                comparison = analyze_page_layers(text_a, text_b, text if method == "ocr" else "")
                if comparison["status"] == "SAI_KHAC_SO":
                    warnings.append(f"Trang {i+1}: số liệu hai bộ trích xuất khác nhau")
                truncated = len(text) > MAX_TEXT_PER_PAGE
                if truncated:
                    warnings.append(f"Trang {i+1}: văn bản vượt giới hạn; chưa đủ độ phủ")
                pages.append({"page": i + 1, "text": text[:MAX_TEXT_PER_PAGE],
                              "method": method, "read_status": comparison["status"],
                              "ocr_attempted": ocr_attempted,
                              "needs_ocr": not bool(text.strip()),
                              "truncated": truncated, "verified": False})
    except (RuntimeError, OSError) as exc:
        raise ValueError("Không thể đọc cấu trúc PDF an toàn") from exc
    if total > len(pages):
        warnings.append(f"Chỉ đọc {len(pages)}/{total} trang; KHÔNG báo cáo đầy đủ")
    complete = total == len(pages) and all(not p["needs_ocr"] and not p["truncated"] for p in pages)
    return {"source_id": "PDF-" + digest[:12], "sha256": digest,
            "total_pages": total, "pages_processed": len(pages), "complete": complete,
            "pages": pages, "warnings": warnings, "verified": False}


def read_ehsmt(data: bytes, *, ocr: bool = False) -> dict:
    source = extract_pdf(data, ocr=ocr)
    lots, current = [], None
    warnings = list(source["warnings"])

    def finish() -> None:
        if current is not None:
            missing = [k for k in LOTS_REQUIRED if not current["fields"].get(k)]
            current["missing"] = missing
            current["status"] = "CAN_BO_SUNG" if missing else "CAN_XAC_MINH"
            lots.append(current)

    for p in source["pages"]:
        if not p["text"].strip():
            continue
        for key, value, excerpt in _pairs(p["text"]):
            if key == "lot_id":
                finish()
                current = {"lot_id": value, "fields": {}, "evidence": {},
                           "status": "CAN_XAC_MINH", "missing": []}
            elif current is not None and key in LOTS_REQUIRED:
                if key in current["fields"]:
                    warnings.append(f"Mã {current['lot_id']}: lặp trường {key}; cần đối chiếu thủ công")
                    current["status"] = "CAN_BO_SUNG"
                    continue
                current["fields"][key] = value
                current["evidence"][key] = _page_evidence(source, p, excerpt, key, value)
    finish()
    if not lots:
        warnings.append("Không nhận diện được dòng mã thuốc/LOT trong PDF; cần xử lý bảng hoặc ảnh gốc")
    keys = [v["lot_id"] for v in lots]
    dupes = sorted({k for k in keys if keys.count(k) > 1})
    if dupes:
        warnings.append("Mã danh mục trùng: " + ", ".join(dupes))
        for lot in lots:
            if lot["lot_id"] in dupes:
                lot["status"] = "CAN_BO_SUNG"
    return {"source_id": source["source_id"], "sha256": source["sha256"],
            "pages_processed": source["pages_processed"],
            "total_pages": source["total_pages"], "complete": source["complete"],
            "lot_count": len(lots), "lots": lots, "warnings": warnings,
            "verified": False, "tender_approved": False}


def _read_fields(source: dict) -> tuple[dict, dict]:
    fields, citations = {}, {}
    for p in source["pages"]:
        for key, value, excerpt in _pairs(p["text"]):
            if key == "lot_id":
                continue
            if key in fields:
                # Duplicate key is not silently overwritten.
                continue
            fields[key] = value
            citations[key] = _page_evidence(source, p, excerpt, key, value)
    return fields, citations


def read_nsx_package(product_pdf: bytes, attachments: list[tuple[str, bytes]],
                     *, ocr: bool = False) -> dict:
    product_source = extract_pdf(product_pdf, ocr=ocr)
    product, citations = _read_fields(product_source)
    missing = [key for key in PRODUCT_REQUIRED if not product.get(key)]
    document = {"product": product, "product_source_id": product_source["source_id"],
                "product_sha256": product_source["sha256"],
                "product_evidence": citations, "product_missing": missing,
                "documents": [], "warnings": list(product_source["warnings"]),
                "complete": product_source["complete"], "verified": False}
    if missing:
        document["warnings"].append("Thiếu thông tin sản phẩm/nhà máy/NSX: " + ", ".join(missing))
    for kind, raw in attachments:
        if kind not in DOC_TYPES:
            raise ValueError("Không nhận diện loại tài liệu NSX")
        src = extract_pdf(raw, ocr=ocr)
        fields, evidences = _read_fields(src)
        first = next((p for p in src["pages"] if p["text"].strip()), None)
        if first:
            excerpt = next((line.strip()[:240] for line in first["text"].splitlines() if line.strip()), "")
            evid = _page_evidence(src, first, excerpt, "document", kind)
        else:
            evid = {"source_id": src["source_id"], "sha256": src["sha256"], "page": 0,
                    "method": "", "excerpt": ""}
        evid.update({"document_type": kind, "product_id": fields.get("product_id", ""),
                     "factory_id": fields.get("factory_id", ""),
                     "manufacturer_id": fields.get("manufacturer_id", "")})
        checked = review_evidence_link(evid, product, raw)
        if not src["complete"] and checked["status"] == "CAN_XAC_MINH":
            checked["status"] = "THIEU_CHUNG_CU"
            checked["reasons"].append("Tài liệu không được đọc đầy đủ")
        document["documents"].append({
            "document_type": kind, "source_id": src["source_id"],
            "sha256": src["sha256"], "pages_processed": src["pages_processed"],
            "total_pages": src["total_pages"], "read_complete": src["complete"],
            "fields": fields, "field_evidence": evidences,
            "link_status": checked["status"], "reasons": checked["reasons"],
            "verified": False, "gmp_confirmed": False, "price_approved": False
        })
        document["warnings"].extend(src["warnings"])
        document["complete"] = document["complete"] and src["complete"]
    return document


def leadership_report(tender: dict | None, supplier: dict | None) -> dict:
    """Preliminary comparative dossier with explicit missing/blocked evidence."""
    tender = tender or {}
    supplier = supplier or {}
    product = supplier.get("product") or {}
    documents = supplier.get("documents") or []
    outcomes = []
    for lot in tender.get("lots") or []:
        evaluated = match_fields(lot["fields"], product)
        reasons = list(evaluated["mismatches"]) + list(evaluated["uncertainties"])
        if lot.get("missing"):
            reasons.append("Thiếu trường E-HSMT: " + ", ".join(lot["missing"]))
        if supplier.get("product_missing"):
            reasons.append("Thiếu trường NSX: " + ", ".join(supplier["product_missing"]))
        if lot.get("status") != "CAN_XAC_MINH":
            reasons.append("Bản đọc mã danh mục cần bổ sung")
        if not tender.get("complete") or not supplier.get("complete"):
            reasons.append("Có tài liệu chưa đọc đủ trang/lớp chữ")
        gmp = [d for d in documents if d["document_type"] == "GMP_CERT"]
        quotes = [d for d in documents if d["document_type"] == "QUOTE"]
        auth = [d for d in documents if d["document_type"] == "AUTHORIZATION"]
        for title, group in [("GMP", gmp), ("Báo giá", quotes), ("Ủy quyền", auth)]:
            if not group:
                reasons.append(f"Chưa nạp {title}")
            elif not any(d["link_status"] == "CAN_XAC_MINH" for d in group):
                reasons.append(f"{title}: liên kết chưa hợp lệ")
            else:
                reasons.append(f"{title}: cần kiểm tra pháp lý và phê duyệt")
        if evaluated["status"] == "KHONG_KHOP":
            tech = "KHONG_KHOP"
        elif evaluated["status"] == "KHOP_4_TRUONG" and not lot.get("missing") and not supplier.get("product_missing"):
            tech = "KHOP_SO_BO"
        else:
            tech = "CAN_XAC_MINH"
        outcomes.append({
            "lot_id": lot["lot_id"], "product_id": product.get("product_id", ""),
            "factory_id": product.get("factory_id", ""),
            "technical": tech, "reasons": reasons,
            "tender_field_evidence": lot.get("evidence", {}),
            "product_field_evidence": supplier.get("product_evidence", {}),
            "document_sources": [{"type": d["document_type"], "source_id": d["source_id"],
                                  "sha256": d["sha256"], "status": d["link_status"]}
                                 for d in documents],
            "decision": "CHO_DUYET_THU_CONG", "gmp_confirmed": False,
            "price_approved": False, "bid_eligible": False
        })
    counts = {"lots": len(outcomes), "technical_prelim_match": sum(r["technical"] == "KHOP_SO_BO" for r in outcomes),
              "technical_conflict": sum(r["technical"] == "KHONG_KHOP" for r in outcomes)}
    return {"title": "TDV QC7 - Bao cao lanh dao SO BO / CHUA PHE DUYET",
            "mode": "PREVIEW_DEMO_ONLY", "tender_source_id": tender.get("source_id"),
            "product_source_id": supplier.get("product_source_id"),
            "summary": counts, "items": outcomes,
            "warnings": list(tender.get("warnings", [])) + list(supplier.get("warnings", [])),
            "final_approval": False, "verified": False}


def report_text(report: dict) -> str:
    s = report["summary"]
    lines = ["DUBIPHARMA DUNG BICH - TDV QC7 ONLINE",
             "BAO CAO SO BO - CHUA PHE DUYET - DU LIEU DEMO",
             "", f"So ma E-HSMT doc duoc: {s['lots']}",
             f"So ma khop ky thuat so bo: {s['technical_prelim_match']}",
             f"So ma co xung dot ky thuat: {s['technical_conflict']}", ""]
    for i in report["items"]:
        lines.extend([f"Ma {i['lot_id']} / San pham {i['product_id']}: {i['technical']}",
                      "Nguon chung cu: " + ", ".join(d["source_id"] for d in i["document_sources"]),
                      "Can xu ly: " + "; ".join(i["reasons"]), ""])
    lines.append("Khong ket luan GMP. Khong tu phe duyet gia. Khong xac nhan du dieu kien du thau.")
    return "\n".join(lines)


def _pdf(lines: list[str]) -> bytes:
    import pymupdf
    doc = pymupdf.open()
    page = doc.new_page()
    for idx, line in enumerate(lines):
        page.insert_text((54, 54 + 20 * idx), line, fontsize=12)
    result = doc.tobytes()
    doc.close()
    return result


def make_demo_ehsmt() -> bytes:
    import pymupdf
    result = pymupdf.open()
    for lot, strength in (("LOT-DEMO-01", "1 mg"), ("LOT-DEMO-02", "4 mg")):
        page = result.new_page()
        for idx, line in enumerate([
            "TDV IDP3 DEMO - ARTIFICIAL E-HSMT",
            "Lot: " + lot, "Ingredient: Acenocoumarol", "Strength: " + strength,
            "Dosage Form: Tablet", "Route: Oral", "Quantity: 1000"
        ]):
            page.insert_text((54, 54 + 20 * idx), line, fontsize=12)
    raw = result.tobytes()
    result.close()
    return raw


def make_demo_nsx() -> tuple[bytes, list[tuple[str, bytes]]]:
    p = _pdf(["TDV IDP3 DEMO - ARTIFICIAL PRODUCT DOSSIER",
              "Product ID: PRODUCT-DEMO-01", "Factory ID: FACTORY-DEMO-A",
              "Manufacturer ID: NSX-DEMO-A",
              "Ingredient: Acenocoumarol", "Strength: 1 mg",
              "Dosage Form: Tablet", "Route: Oral"])
    attachments = [
        ("GMP_CERT", _pdf(["TDV FAKE CERT - NEVER REAL GMP", "Factory ID: FACTORY-DEMO-A"])),
        ("QUOTE", _pdf(["TDV FAKE QUOTE - NO REAL PRICES", "Product ID: PRODUCT-DEMO-01",
                        "Factory ID: FACTORY-DEMO-A"])),
        ("AUTHORIZATION", _pdf(["TDV FAKE AUTHORIZATION", "Product ID: PRODUCT-DEMO-01",
                                "Factory ID: FACTORY-DEMO-A", "Manufacturer ID: NSX-DEMO-A"]))
    ]
    return p, attachments
