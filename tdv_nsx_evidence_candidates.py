"""Non-authoritative, citation-first NSX evidence discovery.

A marketing authorization document does not by itself prove registration
validity. A GMP certificate is a factory-level source, not automatic approval
of all products. This module makes no changes to linked/approved verdicts.
No network, Drive writes, OCR calls, filenames-as-identity or paid APIs.
"""
from __future__ import annotations
from collections import defaultdict
from datetime import date, datetime
import re
from tdv_nsx_adaptive import normalize as norm

REG_FIELDS = ("REGISTRATION_NO", "STRENGTH", "INGREDIENT",
              "MANUFACTURER", "FACTORY")
GMP_FIELDS = ("GMP_NUMBER", "GMP_SCOPE", "GMP_EXPIRY")


def _sourced(item: dict, field: str) -> str:
    """A disputed or uncited statement may not form an identity key."""
    if field in (item.get("conflicts") or {}):
        return ""
    value = str((item.get("fields") or {}).get(field) or "").strip()
    ev = (item.get("evidence") or {}).get(field) or {}
    if not value or not ev.get("source") or not ev.get("file"):
        return ""
    return value


def _cite(item: dict, field: str) -> dict:
    v = (item.get("evidence") or {}).get(field) or {}
    return {
        "file": str(v.get("file") or item.get("filename") or item.get("file") or ""),
        "location": str(v.get("source") or ""),
        "sha256": str(v.get("sha256") or item.get("sha256") or ""),
        "raw": str(v.get("raw") or "")[:350],
    }


def _expiry_flag(value: str, reference_date: date) -> str:
    """Calendar observation only, never regulator GMP-validity determination."""
    value = (value or "").strip()
    if not value:
        return "CHUA_TRICH_NGAY_HET_HAN"
    parsed = None
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            parsed = datetime.strptime(value, fmt).date()
            break
        except ValueError:
            pass
    if parsed is None:
        return "NGAY_GHI_TREN_GIAY_CAN_DOC_BAN_GOC"
    if parsed < reference_date:
        return "QUA_NGAY_GHI_TREN_GIAY_CAN_XAC_MINH_GIA_HAN"
    if parsed == reference_date:
        return "DEN_NGAY_GHI_TREN_GIAY_CAN_XAC_MINH"
    return "CHUA_DEN_NGAY_GHI_TREN_GIAY_KHONG_PHAI_DA_XAC_NHAN_GMP"


def discover_evidence_candidates(
    products: list[dict], classified: list[dict], sources: list[dict],
    *, reference_date: date | None = None,
) -> dict:
    """Suggestions only, preserving original product identity and page/row.

    Registration: exact original drug name plus independent, noncontradicting
    cited strength/ingredient/registration/manufacturer/site evidence to make
    a candidate; name-only remains a weaker lookup hint. An exact name in more
    than one product always remains ambiguous.

    GMP: records factory-level references, possibly covering >1 product,
    WITHOUT creating per-product proof links or validating GMP status.
    """
    reference_date = reference_date or date.today()
    registrations, factories, unresolved = [], [], []
    for meta, source in zip(classified, sources):
        kind = meta.get("kind")
        if kind not in ("REGISTRATION", "GMP_CERT"):
            continue
        if "error" in source or not meta.get("complete_read"):
            unresolved.append({
                "type": kind, "file": meta.get("filename", ""),
                "sha256": meta.get("sha256", ""), "status": "CAN_KIEM_TRA_BAN_GOC",
                "reason": "Nguồn chưa đọc đủ hoặc lỗi; không liên kết tự động.",
            })
            continue
        if meta.get("public_document_class"):
            unresolved.append({
                "type": kind, "file": meta.get("filename", ""),
                "sha256": meta.get("sha256", ""), "status": "THAM_KHAO_KHONG_PHAI_CHUNG_CU_GOC",
                "reason": "Tài liệu công khai không tự thay thế chứng cứ nhà sản xuất.",
            })
            continue
        if kind == "REGISTRATION":
            title = _sourced(source, "PRODUCT_NAME")
            if not title:
                unresolved.append({
                    "type": kind, "file": meta.get("filename", ""),
                    "sha256": meta.get("sha256", ""),
                    "status": "THIEU_TEN_THUOC_CO_NGUON",
                    "reason": "Chưa trích được TÊN THUỐC có trang/dòng từ giấy đăng ký.",
                })
                continue
            matches = [p for p in products
                       if not (p.get("registration_document_source") and
                               p.get("sha256") == meta.get("sha256"))
                       and _sourced(p, "PRODUCT_NAME") and
                       norm(_sourced(p, "PRODUCT_NAME")) == norm(title)]
            if not matches:
                unresolved.append({
                    "type": kind, "file": meta.get("filename", ""),
                    "sha256": meta.get("sha256", ""),
                    "status": "CHUA_TIM_THAY_TEN_TRUNG_CHINH_XAC",
                    "reason": "Tên có trích dẫn trong giấy đăng ký chưa khớp chính xác danh mục.",
                })
                continue
            for p in matches:
                agreed, different = [], []
                for field in REG_FIELDS:
                    a, b = _sourced(p, field), _sourced(source, field)
                    if a and b:
                        (agreed if norm(a) == norm(b) else different).append(field)
                status = ("MAU_THUAN_DINH_DANH" if different else
                          "TRUNG_TEN_NHIEU_UNG_VIEN" if len(matches) != 1 else
                          "GOI_Y_CO_DINH_DANH_PHU_CHUA_XAC_MINH" if agreed else
                          "GOI_Y_CHI_TRUNG_TEN_CHUA_XAC_MINH")
                registrations.append({
                    "product_id": p.get("uid", ""), "product_name": title,
                    "registration_no_in_proof": _sourced(source, "REGISTRATION_NO"),
                    "product_source": _cite(p, "PRODUCT_NAME"),
                    "document_source": _cite(source, "PRODUCT_NAME"),
                    "registration_source": _cite(source, "REGISTRATION_NO"),
                    "document_file": meta.get("filename", ""),
                    "document_sha256": meta.get("sha256", ""),
                    "supporting_fields": agreed, "conflict_fields": different,
                    "status": status,
                    "verified": False, "registration_confirmed": False,
                    "bid_eligible": False,
                })
        elif kind == "GMP_CERT":
            factory = _sourced(source, "FACTORY")
            if not factory:
                unresolved.append({
                    "type": kind, "file": meta.get("filename", ""),
                    "sha256": meta.get("sha256", ""),
                    "status": "THIEU_NHA_MAY_CO_TRICH_DAN",
                    "reason": "GMP không trích được tên nhà máy có nguồn; không suy từ NSX.",
                })
                continue
            matched = [p for p in products if
                       _sourced(p, "FACTORY") and
                       norm(_sourced(p, "FACTORY")) == norm(factory)]
            if not matched:
                unresolved.append({
                    "type": kind, "file": meta.get("filename", ""),
                    "sha256": meta.get("sha256", ""),
                    "status": "CHUA_GHEP_DUOC_NHA_MAY",
                    "reason": "Tên nhà máy có trích dẫn chưa trùng chính xác danh mục; không tự gắn GMP cho thuốc.",
                })
                continue
            expiry = _sourced(source, "GMP_EXPIRY")
            factories.append({
                "factory": factory, "factory_source": _cite(source, "FACTORY"),
                "document_file": meta.get("filename", ""),
                "document_sha256": meta.get("sha256", ""),
                "gmp_number_in_proof": _sourced(source, "GMP_NUMBER"),
                "gmp_scope_in_proof": _sourced(source, "GMP_SCOPE"),
                "expiry_in_proof": expiry,
                "expiry_observation": _expiry_flag(expiry, reference_date),
                "related_product_ids": [p.get("uid", "") for p in matched],
                "related_product_count": len(matched),
                "status": "CUNG_NHA_MAY_THEO_NGUON_KHONG_PHAI_GMP_CHO_MOI_THUOC",
                "verified": False, "gmp_confirmed": False,
                "bid_eligible": False,
            })
    return {
        "registrations": registrations, "factories": factories,
        "unresolved": unresolved,
        "summary": {
            "registration_hints": len(registrations),
            "factory_source_groups": len(factories),
            "unresolved_evidence": len(unresolved),
        },
        "verified": False, "legal_approval": False,
        "independent_proof_links_created": 0,
    }
