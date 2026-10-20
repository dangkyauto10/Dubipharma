"""Read-only TDV-IDP 3.0 review gates. Never produces regulatory/bid approvals.

This layer evaluates *links* between documentary evidence and product/factory IDs.
It does not validate a GMP certificate, authorisation, bid price, or authenticity.
Document bytes must remain in memory in Preview; no network/database operations.
"""
from __future__ import annotations

from collections import Counter
import hashlib
import re
from typing import Any

_HASH = re.compile(r"[0-9a-f]{64}\Z")
_NUMBER = re.compile(r"(?<![\w])\d+(?:[.,]\d+)*")
_DOCS = {"E_HSMT", "NSX", "GMP_CERT", "GMP_EXPLANATION", "QUOTE", "AUTHORIZATION"}
_METHODS = {"pymupdf", "pdfplumber", "ocr"}


def analyze_page_layers(pdf_text: str, table_text: str, ocr_text: str = "") -> dict[str, Any]:
    """Flag missing text or discordant numeric tokens, not 'two-reader validation'."""
    a, b, c = (str(x or "").strip() for x in (pdf_text, table_text, ocr_text))
    if not a and not b and not c:
        return {"status": "CAN_OCR", "warnings": ["Không có lớp chữ; cần OCR và xem ảnh gốc"], "verified": False}
    if c and not (a or b):
        return {"status": "OCR_CHUA_KIEM_CHUNG", "warnings": ["OCR phải đối chiếu ảnh trang và người kiểm tra"], "verified": False}
    if a and b and Counter(_NUMBER.findall(a)) != Counter(_NUMBER.findall(b)):
        return {"status": "SAI_KHAC_SO", "warnings": ["Các bộ trích xuất không thống nhất token số"], "verified": False}
    if a and b and a != b:
        return {"status": "CAN_DOI_CHIEU", "warnings": ["Hai bộ đọc khác chuỗi; so trang nguồn"], "verified": False}
    return {"status": "TRICH_XUAT_CHUA_XAC_MINH", "warnings": ["Trích xuất không thay thế đối chiếu chứng cứ"], "verified": False}


def review_evidence_link(evidence: dict[str, Any], product: dict[str, Any],
                         source_bytes: bytes | None = None) -> dict[str, Any]:
    """Fail closed for missing/mismatched source, factory, product or document type.

    source_bytes, when provided, establishes that claimed digest matches these
    *bytes only*. It never establishes issuance, validity, or regulatory status.
    """
    result = {"status": "CAN_XAC_MINH", "reasons": [], "verified": False,
              "gmp_confirmed": False, "price_approved": False, "bid_eligible": False}

    def stop(status: str, reason: str) -> dict[str, Any]:
        result["status"] = status
        result["reasons"].append(reason)
        return result

    source_id = str(evidence.get("source_id") or "").strip()
    digest = str(evidence.get("sha256") or "").lower().strip()
    page = evidence.get("page")
    method = str(evidence.get("method") or "").lower().strip()
    excerpt = str(evidence.get("excerpt") or "").strip()
    if not source_id or not _HASH.fullmatch(digest) or type(page) is not int or page < 1 or method not in _METHODS or not excerpt:
        return stop("THIEU_CHUNG_CU", "Thiếu mã tệp, SHA-256, trang, cách đọc hoặc trích dẫn nguồn")
    if source_bytes is not None:
        if not isinstance(source_bytes, bytes) or hashlib.sha256(source_bytes).hexdigest() != digest:
            return stop("CHAN_LIEN_KET", "SHA-256 không khớp nội dung tệp cung cấp")
    else:
        result["reasons"].append("Chưa kiểm chứng SHA-256 với tệp gốc")

    kind = str(evidence.get("document_type") or "").strip().upper()
    if kind not in _DOCS:
        return stop("CAN_XAC_MINH", "Loại tài liệu chưa được phân loại chắc chắn")

    product_id = str(product.get("product_id") or "").strip()
    factory_id = str(product.get("factory_id") or "").strip()
    doc_factory_id = str(evidence.get("factory_id") or "").strip()
    if not product_id or not factory_id or not doc_factory_id:
        return stop("THIEU_DINH_DANH", "Thiếu định danh sản phẩm hoặc nhà máy")
    if factory_id != doc_factory_id:
        return stop("CHAN_LIEN_KET", "Nhà máy trên chứng cứ không phải nhà máy của sản phẩm")

    if kind in {"QUOTE", "NSX", "AUTHORIZATION"}:
        linked_id = str(evidence.get("product_id") or "").strip()
        if not linked_id:
            return stop("THIEU_DINH_DANH", "Không có định danh sản phẩm ghi trong chứng cứ")
        if linked_id != product_id:
            return stop("CHAN_LIEN_KET", "Chứng cứ gắn với sản phẩm khác")

    if kind == "AUTHORIZATION":
        principal_id = str(product.get("manufacturer_id") or "").strip()
        doc_principal = str(evidence.get("manufacturer_id") or "").strip()
        if not principal_id or not doc_principal:
            return stop("THIEU_DINH_DANH", "Thiếu định danh đơn vị ủy quyền/nhà sản xuất")
        if principal_id != doc_principal:
            return stop("CHAN_LIEN_KET", "Chủ thể ủy quyền khác nhà sản xuất đã liên kết")

    if kind == "GMP_EXPLANATION":
        return stop("CHUNG_CU_BO_SUNG", "Công văn/giải trình không tự trở thành chứng nhận GMP")
    if kind == "GMP_CERT":
        result["reasons"].append("Chưa xác minh hiệu lực, phạm vi GMP, cơ quan cấp và cơ sở sản xuất")
    elif kind == "QUOTE":
        result["reasons"].append("Báo giá chưa được phê duyệt; cần kiểm tra đơn vị, tiền tệ, điều kiện và thời hạn")
    elif kind == "AUTHORIZATION":
        result["reasons"].append("Giấy ủy quyền cần xác minh phạm vi, thời hạn, chữ ký và chuỗi ủy quyền")
    else:
        result["reasons"].append("Cần đối chiếu bản gốc, phiên bản tài liệu và phạm vi áp dụng")
    return result


def synthetic_evidence_cases() -> list[dict[str, str]]:
    """In-memory invented evidence for QA only; does not reference real tenders."""
    original = b"TDV-IDP3 SYNTHETIC ONLY; NO REAL GMP OR QUOTE"
    base = {"source_id": "DEMO-001", "sha256": hashlib.sha256(original).hexdigest(),
            "page": 1, "method": "pymupdf", "excerpt": "Synthetic document for testing",
            "factory_id": "FACTORY-A", "product_id": "DRUG-1"}
    product = {"product_id": "DRUG-1", "factory_id": "FACTORY-A", "manufacturer_id": "NSX-A"}
    cases = [
        ("GMP đúng nhà máy nhưng chưa xác minh", {**base, "document_type": "GMP_CERT"}, product),
        ("GMP sai nhà máy bị chặn", {**base, "document_type": "GMP_CERT", "factory_id": "FACTORY-B"}, product),
        ("Công văn không là gia hạn GMP", {**base, "document_type": "GMP_EXPLANATION"}, product),
        ("Báo giá sai sản phẩm bị chặn", {**base, "document_type": "QUOTE", "product_id": "DRUG-2"}, product),
        ("Báo giá đúng mã nhưng chưa duyệt", {**base, "document_type": "QUOTE"}, product),
        ("Ủy quyền sai NSX bị chặn", {**base, "document_type": "AUTHORIZATION", "manufacturer_id": "NSX-B"}, product),
        ("Ủy quyền đúng mã nhưng chưa xác minh", {**base, "document_type": "AUTHORIZATION", "manufacturer_id": "NSX-A"}, product),
    ]
    return [{"tình_huống": label, "kết_quả": review_evidence_link(e, p, original)["status"],
             "chứng_cứ": e["source_id"] + ":trang " + str(e["page"]),
             "cần_duyệt": "CÓ"} for label, e, p in cases]
