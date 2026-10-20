"""TDV NSX automatic intake: one batch, many documents and many products.

Document roles and evidence links are *proposals*, never GMP/registration/
authorization/price approvals. Preserve original source + SHA256 + row/page.
No external API calls, no Google Drive writes and no model inference.
"""
from __future__ import annotations

from collections import defaultdict
from io import BytesIO
import hashlib
import json
import re
from typing import Any

from see_pro_multiformat import ACCEPTED, extract_file
from tdv_nsx_adaptive import extract_product_rows, _read_grid, FIELD, normalize as norm
from tdv_nsx_intake import KINDS, _read_one
from see_pro_traceability import safe_cell, _format

MAX_FILES = 24
IDENTIFIERS = ("PRODUCT_ID", "REGISTRATION_NO")
ROLES = {"PRODUCT", "GMP_CERT", "GMP_EXPLANATION", "REGISTRATION",
         "AUTHORIZATION", "QUOTE", "OTHER"}
STATUS_MATCH = "LIEN_KET_SO_BO_CAN_XAC_MINH"
STATUS_CONFLICT = "XUNG_DOT_DINH_DANH"
STATUS_UNKNOWN = "CHUA_DU_CHUNG_CU"
STATUS_AMBIGUOUS = "NHIEU_SAN_PHAM_CO_THE_KHOP"


def _source(record: dict, field: str) -> dict:
    return record.get("evidence", {}).get(field, {})


def _usable(record: dict, field: str) -> str:
    # A conflicting field cannot become an automatic exact-match key.
    if field in record.get("conflicts", {}):
        return ""
    return str(record.get("fields", {}).get(field, "")).strip()


def _ref(doc: dict) -> dict:
    return {"file": doc["filename"], "sha256": doc["sha256"],
            "type": doc.get("type", ""), "complete": doc.get("complete_read", False)}


def classify_document(filename: str, raw: bytes, *, enable_ocr: bool = False) -> dict:
    """Use evidence inside the document, never filename-only role labeling.

    A tie or a document that blends multiple primary categories is OTHER and
    explicitly flagged for review. Classification itself makes no claim that
    a certificate, registration or quote is genuine.
    """
    if filename.rsplit(".", 1)[-1].lower() not in ACCEPTED:
        raise ValueError("Định dạng không được hỗ trợ")
    source = extract_file(filename, raw, ocr=enable_ocr)
    text = norm(" ".join(str(line["text"]) for line in source["lines"][:1500]))
    # Use a separate evidence reader to detect labeled field/value pairs.
    parsed = _read_one(
        filename, "OTHER", raw, enable_ocr, source_document=source,
    )
    f = parsed["fields"]
    # Single strong titles take precedence over incidental GMP / product words
    # in a long company document.
    headers = norm(" ".join(str(l["text"]) for l in source["lines"][:55]))
    def has(*phrases: str) -> bool:
        return any(norm(phrase) in text for phrase in phrases)
    def heading(*phrases: str) -> bool:
        return any(norm(phrase) in headers for phrase in phrases)

    scores = {k: 0 for k in ROLES if k != "OTHER"}
    # Explicit document-type phrases, with conservative precedence.
    if heading("giải trình gmp", "gmp explanation", "công văn giải trình gmp"):
        scores["GMP_EXPLANATION"] += 12
    elif heading("giấy chứng nhận gmp", "chứng nhận thực hành tốt sản xuất",
                 "certificate of gmp", "good manufacturing practice certificate",
                 "gmp certificate"):
        scores["GMP_CERT"] += 12
    if heading("giấy ủy quyền", "thư ủy quyền", "letter of authorization",
               "authorization letter", "power of attorney"):
        scores["AUTHORIZATION"] += 12
    if heading("giấy đăng ký lưu hành", "giấy phép lưu hành", "marketing authorization",
               "registration certificate", "giấy chứng nhận đăng ký lưu hành"):
        scores["REGISTRATION"] += 12
    if heading("báo giá", "thư báo giá", "quotation", "price quotation", "commercial offer"):
        scores["QUOTE"] += 12
    if heading("danh mục thuốc", "hồ sơ sản phẩm", "product dossier",
               "drug catalogue", "product catalog"):
        scores["PRODUCT"] += 8

    scores["GMP_CERT"] += 3 * bool(f.get("GMP_NUMBER"))
    scores["GMP_CERT"] += 2 * bool(f.get("GMP_SCOPE"))
    scores["GMP_CERT"] += 2 * bool(f.get("GMP_EXPIRY"))
    scores["AUTHORIZATION"] += 3 * bool(f.get("AUTH_EXPIRY"))
    scores["QUOTE"] += 6 * bool(f.get("QUOTE_UNIT_PRICE"))
    scores["QUOTE"] += 2 * bool(f.get("QUOTE_CURRENCY"))
    scores["QUOTE"] += 2 * bool(f.get("QUOTE_VALID_UNTIL"))
    scores["PRODUCT"] += 2 * bool(f.get("PRODUCT_NAME"))
    scores["PRODUCT"] += 3 * bool(f.get("INGREDIENT"))
    scores["PRODUCT"] += 2 * bool(f.get("STRENGTH"))
    scores["PRODUCT"] += 1 * bool(f.get("DOSAGE_FORM"))
    scores["REGISTRATION"] += 3 * bool(f.get("REGISTRATION_NO"))
    # Do not treat a plain product catalogue with SĐK as registration certificate.
    if scores["PRODUCT"] >= 7 and scores["REGISTRATION"] < 12:
        scores["REGISTRATION"] = 0
    # Real drug catalogues are commonly rectangular tables with no
    # "hồ sơ sản phẩm" title or key:value rows. Inspect semantic column
    # headings to discover the category, not filenames or user selection.
    catalogue_count = 0
    quote_table_present = False
    if source["type"] in ("xlsx", "xls", "csv", "docx"):
        catalogue = extract_product_rows(filename, raw)
        catalogue_count = catalogue["total_candidates"]
        quote_table_present = bool(_table_items(
            filename, raw, source["sha256"], "QUOTE"
        ))
        if catalogue_count:
            scores["PRODUCT"] += 12
        if quote_table_present:
            # Price-per-drug table: QUOTE is the document role, even when the
            # same table includes ingredient/strength/manufacturer columns.
            scores["QUOTE"] += 18
    if scores["GMP_EXPLANATION"] >= 12:
        scores["GMP_CERT"] = 0
    # Quotation tables can contain ingredient/strength; explicit quote wins.
    if scores["QUOTE"] >= 12 and scores["PRODUCT"] < 12:
        scores["PRODUCT"] = 0
    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    winner, best = ranked[0]
    second = ranked[1][1]
    confident = best >= 7 and best - second >= 3
    role = winner if confident else "OTHER"
    candidates = [k for k, v in ranked if v >= 7 and best - v < 3]
    reasons = (
        [] if confident else
        ["Nội dung chưa đủ dấu hiệu để xác định duy nhất loại tài liệu."]
    )
    return {
        "kind": role, "kind_label": KINDS[role],
        "filename": filename, "sha256": source["sha256"],
        "content_type": source["type"],
        "complete_read": bool(source["complete"]),
        "role_confidence": "GỢI_Ý_CẦN_XÁC_MINH" if confident else "CHƯA_PHÂN_LOẠI",
        "role_candidates": candidates,
        "score": best, "reasons": reasons,
        "catalogue_products_found": catalogue_count,
        "quotation_table_found": quote_table_present,
        "_extracted_source": source,
        "verified": False,
    }


def _candidate_from_document(doc: dict) -> list[dict]:
    product_list = doc.get("catalogue_candidates") or []
    if product_list:
        return [
            {
                "fields": dict(row["fields"]),
                "evidence": dict(row["evidence"]),
                "conflicts": {},
                "file": doc["filename"], "sha256": doc["sha256"],
                "origin": f"{row['table']}, dòng {row['row']}",
                "complete_read": doc["complete_read"],
                "verified": False,
            } for row in product_list
        ]
    if "error" in doc:
        return []
    fields = doc.get("fields") or {}
    if not any(fields.get(k) for k in ("PRODUCT_ID", "REGISTRATION_NO", "PRODUCT_NAME")):
        return []
    return [{
        "fields": dict(fields), "evidence": dict(doc.get("evidence") or {}),
        "conflicts": dict(doc.get("conflicts") or {}),
        "file": doc["filename"], "sha256": doc["sha256"],
        "origin": "Trích trường có nhãn từ tài liệu",
        "complete_read": doc["complete_read"], "verified": False,
    }]


def _table_items(filename: str, raw: bytes, sha: str, kind: str) -> list[dict]:
    """Extract exact quote product rows (one table may contain many drugs)."""
    if kind != "QUOTE" or filename.rsplit(".", 1)[-1].lower() not in ("xlsx", "xls", "csv", "docx"):
        return []
    tables, _warnings = _read_grid(filename, raw)
    items = []
    for title, rows in tables:
        heads: dict[str, int] = {}
        for ri, row in enumerate(rows, 1):
            matched = {FIELD[norm(v)]: i for i, v in enumerate(row) if norm(v) in FIELD}
            if "QUOTE_UNIT_PRICE" in matched and any(k in matched for k in IDENTIFIERS):
                heads = matched
                continue
            if not heads:
                continue
            fields = {}; evidence = {}
            for field, pos in heads.items():
                if pos >= len(row) or row[pos] is None or not str(row[pos]).strip():
                    continue
                value = str(row[pos]).strip()[:350]
                fields[field] = value
                evidence[field] = {
                    "file": filename, "sha256": sha,
                    "source": f"{title}, hàng {ri}, cột {pos+1}",
                    "raw": value, "value": value, "verified": False,
                }
            if "QUOTE_UNIT_PRICE" in fields and any(fields.get(k) for k in IDENTIFIERS):
                items.append({
                    "fields": fields, "evidence": evidence, "conflicts": {},
                    "filename": filename, "sha256": sha,
                    "kind": kind, "complete_read": True,
                    "origin": f"{title}, hàng {ri}", "verified": False,
                })
            if len(items) >= 250:
                break
        if len(items) >= 250:
            break
    return items


def _match(product: dict, proof: dict) -> dict:
    """Conservative one-product/one-evidence comparison with source anchors."""
    k = proof["kind"]
    pf, df = product["fields"], proof["fields"]
    anchors = {
        "GMP_CERT": ("FACTORY",), "GMP_EXPLANATION": ("FACTORY",),
        "QUOTE": IDENTIFIERS, "REGISTRATION": ("REGISTRATION_NO",),
        "AUTHORIZATION": (*IDENTIFIERS, "MANUFACTURER"),
    }.get(k, ())
    agreed = []; different = []
    for field in anchors:
        pv, dv = _usable(product, field), _usable(proof, field)
        if pv and dv:
            (agreed if norm(pv) == norm(dv) else different).append(field)
    if k in ("GMP_CERT", "GMP_EXPLANATION"):
        required = "FACTORY" in agreed
    elif k == "REGISTRATION":
        required = "REGISTRATION_NO" in agreed
    elif k == "AUTHORIZATION":
        required = "MANUFACTURER" in agreed and any(x in agreed for x in IDENTIFIERS)
    elif k == "QUOTE":
        required = any(x in agreed for x in IDENTIFIERS)
    else:
        required = False
    if different:
        status = STATUS_CONFLICT
    elif not required:
        status = STATUS_UNKNOWN
    elif not product.get("complete_read") or not proof.get("complete_read"):
        status = "CAN_KIEM_TRA_BAN_GOC"
    else:
        status = STATUS_MATCH
    return {
        "product_id": product["uid"], "product": pf.get("PRODUCT_NAME", ""),
        "source_product": product["file"], "source_evidence": proof["filename"],
        "evidence_kind": k, "evidence_origin": proof.get("origin", ""),
        "match_fields": agreed, "conflict_fields": different,
        "status": status,
        "source_sha256": proof["sha256"],
        "evidence": dict(proof.get("evidence") or {}),
        "reason": ("Trường định danh không khớp: " + ", ".join(different))
                  if different else ("Trùng định danh nguồn, vẫn cần xác minh chứng cứ gốc"
                  if status == STATUS_MATCH else "Thiếu định danh chung xác thực"),
        "verified": False, "gmp_confirmed": False,
        "quote_approved": False, "bid_eligible": False,
    }


def analyze_auto(files: list[tuple[str, bytes]], *, enable_ocr: bool = True) -> dict:
    """One click: detect roles; discover products; link proofs only when unique."""
    if not files or len(files) > MAX_FILES:
        raise ValueError("Chọn từ 1 đến 24 tệp trong một bộ hồ sơ")
    classified = []; detailed = []; original = []
    warnings = []
    for i, (name, raw) in enumerate(files):
        if not isinstance(raw, bytes):
            raise ValueError("Tệp tải lên không có dạng nhị phân hợp lệ")
        try:
            meta = classify_document(name, raw, enable_ocr=enable_ocr)
            kind = meta["kind"]
            # Never require users to pre-label types or choose product rows.
            # Uncertain labels go to the review queue, not arbitrary guesses.
            meta["kind_label"] = KINDS[kind]
            extracted_source = meta.pop("_extracted_source")
            details = _read_one(
                name, kind, raw, enable_ocr,
                source_document=extracted_source,
            )
            meta["complete_read"] = details["complete_read"]
            original.append((name, raw))
            detailed.append(details)
            classified.append(meta)
            warnings.extend(f"{name}: {w}" for w in details["warnings"])
        except Exception as exc:
            sha = hashlib.sha256(raw).hexdigest()
            classified.append({
                "kind": "OTHER", "kind_label": KINDS["OTHER"],
                "filename": name, "sha256": sha, "complete_read": False,
                "role_confidence": "KHÔNG_ĐỌC_ĐƯỢC",
                "role_candidates": [], "reasons": [type(exc).__name__],
                "verified": False,
            })
            detailed.append({"kind": "OTHER", "filename": name, "sha256": sha,
                             "error": type(exc).__name__})
            original.append((name, raw))
            warnings.append(f"{name}: không đọc được ({type(exc).__name__})")
    products = []
    evidence_items = []
    for classification, document, (filename, raw) in zip(classified, detailed, original):
        kind = classification["kind"]
        if "error" in document:
            continue
        if kind == "PRODUCT":
            for p in _candidate_from_document(document):
                p["uid"] = "P" + str(len(products) + 1).zfill(4)
                products.append(p)
        elif kind in ("GMP_CERT", "GMP_EXPLANATION", "REGISTRATION", "QUOTE", "AUTHORIZATION"):
            rows = _table_items(filename, raw, classification["sha256"], kind)
            evidence_items.extend(rows or [{
                **document, "filename": filename, "kind": kind,
                "origin": "Các trường có nhãn trong tệp",
            }])
    links = []
    outstanding = []
    for proof in evidence_items:
        assessments = [_match(p, proof) for p in products]
        candidates = [x for x in assessments if x["status"] == STATUS_MATCH]
        if len(candidates) == 1:
            links.append(candidates[0])
        elif len(candidates) > 1:
            # Never choose an arbitrary one when multiple products share
            # the same factory or identification number.
            outstanding.append({
                "file": proof["filename"], "kind": proof["kind"],
                "origin": proof.get("origin", ""),
                "status": STATUS_AMBIGUOUS,
                "candidate_products": [m["product_id"] for m in candidates],
                "reason": "Nhiều thuốc có cùng định danh trong tài liệu chứng cứ.",
            })
        else:
            # Mismatching identifiers of unrelated products are EXPECTED in
            # a multi-product dossier. They are not automatically data errors.
            # Only surface "conflict" if a common anchor agrees but another
            # identifying anchor contradicts it, or for the sole product.
            conflicting = [
                a for a in assessments if a["status"] == STATUS_CONFLICT
                and (a["match_fields"] or len(products) == 1)
            ]
            outstanding.append({
                "file": proof["filename"], "kind": proof["kind"],
                "origin": proof.get("origin", ""),
                "status": STATUS_CONFLICT if conflicting else STATUS_UNKNOWN,
                "candidate_products": [],
                "reason": "Không tìm được liên kết duy nhất có chứng cứ đủ mạnh.",
            })
    for c in classified:
        if c["role_confidence"] in ("CHƯA_PHÂN_LOẠI", "KHÔNG_ĐỌC_ĐƯỢC"):
            outstanding.append({
                "file": c["filename"], "kind": c["kind"],
                "origin": "", "status": "CAN_PHAN_LOAI_LAI",
                "candidate_products": [], "reason": "; ".join(c["reasons"]),
            })
    if not products:
        warnings.append(
            "Không có danh mục/sản phẩm đủ định danh để liên kết chứng cứ; "
            "không tự tạo thuốc hoặc ghép GMP/báo giá"
        )
        outstanding.append({
            "file": "", "kind": "PRODUCT", "origin": "",
            "status": "CHUA_NHAN_DIEN_DANH_MUC",
            "candidate_products": [],
            "reason": "Chưa có sản phẩm được nhận diện có nguồn kiểm chứng.",
        })
    hashes = defaultdict(list)
    for meta in classified:
        hashes[meta["sha256"]].append(meta["filename"])
    for digest, names in hashes.items():
        if len(names) > 1:
            warnings.append("Tệp có nội dung trùng SHA-256: " + ", ".join(names))
    return {
        "mode": "NSX_AUTO_MULTI_DOCUMENT_READ_ONLY",
        "files": classified, "sources": detailed,
        "products": products, "links": links, "review_queue": outstanding,
        "warnings": warnings,
        "summary": {
            "files": len(files),
            "parsed": sum(x["role_confidence"] != "KHÔNG_ĐỌC_ĐƯỢC" for x in classified),
            "products": len(products),
            "linked": len(links),
            "review": len(outstanding),
        },
        "verified": False, "gmp_confirmed": False,
        "registration_confirmed": False, "quote_approved": False,
        "bid_eligible": False, "cloud_write_enabled": False,
    }


def export_auto_xlsx(report: dict) -> bytes:
    from openpyxl import Workbook
    wb = Workbook()
    overview = wb.active
    overview.title = "TU_DONG_NHAN_DIEN"
    overview.append(["Tệp", "Loại nhận diện", "Độ chắc chắn", "SHA256", "Đọc đủ", "Cần duyệt"])
    for d in report["files"]:
        overview.append([safe_cell(x) for x in (
            d["filename"], d["kind_label"], d["role_confidence"],
            d["sha256"], d["complete_read"],
            "; ".join(d.get("reasons", [])),
        )])
    rows = wb.create_sheet("DANH_MUC_THUOC")
    rows.append(["Mã dòng", "Tên thuốc", "Mã sản phẩm", "SĐK", "Hoạt chất",
                 "Hàm lượng", "NSX", "Nhà máy", "Tệp", "Vị trí", "Xác minh"])
    for p in report["products"]:
        f = p["fields"]
        rows.append([safe_cell(x) for x in (
            p["uid"], f.get("PRODUCT_NAME"), f.get("PRODUCT_ID"),
            f.get("REGISTRATION_NO"), f.get("INGREDIENT"), f.get("STRENGTH"),
            f.get("MANUFACTURER"), f.get("FACTORY"),
            p["file"], p["origin"], "CHƯA",
        )])
    links = wb.create_sheet("LIEN_KET_CHUNG_CU")
    links.append(["Mã dòng", "Thuốc", "Loại chứng cứ", "Nguồn", "Vị trí", "Khớp trường",
                  "Trạng thái", "Giải thích", "Đã xác minh"])
    for item in report["links"]:
        links.append([safe_cell(x) for x in (
            item["product_id"], item["product"], KINDS[item["evidence_kind"]],
            item["source_evidence"], item["evidence_origin"],
            item["match_fields"], item["status"], item["reason"], "CHƯA",
        )])
    inspect = wb.create_sheet("CAN_XAC_MINH")
    inspect.append(["Tệp", "Loại", "Vị trí", "Trạng thái", "Ứng viên", "Lý do"])
    for item in report["review_queue"]:
        inspect.append([safe_cell(x) for x in (
            item["file"], KINDS.get(item["kind"], item["kind"]),
            item["origin"], item["status"], item["candidate_products"], item["reason"],
        )])
    trace = wb.create_sheet("TRUY_XUAT_TUNG_TRUONG")
    trace.append(["Tệp", "Vai trò", "Trường", "Giá trị", "Trang hoặc ô nguồn", "SHA256", "Trích đoạn"])
    for p in report["products"]:
        for field, item in p["evidence"].items():
            trace.append([safe_cell(x) for x in (
                p["file"], "PRODUCT", field, item["value"], item["source"],
                item["sha256"], item["raw"],
            )])
    for d in report["sources"]:
        for field, item in d.get("evidence", {}).items():
            trace.append([safe_cell(x) for x in (
                d["filename"], d["kind"], field, item["value"], item["source"],
                item["sha256"], item["raw"],
            )])
    # Multi-line quotation prices belong to individual drug rows, not to a
    # document-level scalar field. Preserve each exact quote cell as evidence.
    for link in report["links"]:
        for field, item in link.get("evidence", {}).items():
            trace.append([safe_cell(x) for x in (
                link["source_evidence"], link["evidence_kind"], field,
                item["value"], item["source"], item["sha256"], item["raw"],
            )])
    disclaim = wb.create_sheet("GIOI_HAN_KIEM_TOAN")
    disclaim.append(["Giới hạn", "Ý nghĩa"])
    for k, v in (
        ("Phân loại", "Gợi ý tự động, không thay thế xác minh hồ sơ gốc"),
        ("Đối chiếu", "Chỉ liên kết khi định danh nguồn đủ duy nhất"),
        ("GMP", "Chưa xác thực cơ quan cấp, phạm vi hoặc hiệu lực"),
        ("SĐK", "Chưa xác minh trên cơ sở dữ liệu quản lý dược chính thức"),
        ("Giá", "Giá báo không phải giá dự thầu hoặc giá được duyệt"),
        ("Drive", "Chức năng ghi hoàn toàn khóa, chỉ xuất tệp về máy theo yêu cầu"),
    ):
        disclaim.append([k, v])
    for sh in wb:
        sh.freeze_panes = "B2"
        _format(sh, status_field="Trạng thái" if sh.title in
                ("LIEN_KET_CHUNG_CU", "CAN_XAC_MINH") else None)
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
