"""TDV QC7: mandatory reverse traceability view for a product in a tender dossier.

Read-only and evidence-first. A product is NOT a verified medicine, a matching
certificate is NOT an approved GMP, and a candidate proof is NOT sufficient
to claim that the tender's project-specific submission list has been satisfied.
All source metadata comes from the uploaded batch, never from a filename guess.
"""
from __future__ import annotations

REVIEW_CATEGORIES = (
    ("REGISTRATION", "Giấy đăng ký lưu hành / SĐK"),
    ("GMP_CERT", "Chứng cứ GMP của nhà máy / phạm vi sản xuất"),
    ("AUTHORIZATION", "Ủy quyền và chuỗi ủy quyền (nếu E-HSMT yêu cầu)"),
    ("QUOTE", "Báo giá / chứng cứ thương mại (theo yêu cầu gói thầu)"),
)
PARTY_FIELDS = (
    ("SUPPLIER", "Đơn vị cung cấp / phân phối"),
    ("BIDDER", "Nhà thầu"),
    ("REGISTRATION_HOLDER", "Đơn vị đứng tên đăng ký"),
    ("MANUFACTURER", "Nhà sản xuất"),
    ("FACTORY", "Cơ sở / nhà máy sản xuất"),
)


def build_reverse_dossiers(report: dict) -> dict:
    """Return full trace for every identified product, without unverified links.

    The required set of submission documents can only be decided once
    project E-HSMT terms and legal requirements have been extracted/approved.
    These categories form an audit *review checklist*, not a legal ruling.
    """
    documents = {x.get("sha256"): x for x in report.get("files", [])
                 if x.get("sha256")}
    products = []
    checklist = []
    provenance = []
    for p in report.get("products", []):
        uid = p["uid"]
        fields = p.get("fields") or {}
        evidence = p.get("evidence") or {}
        sha = p.get("sha256", "")
        matches = [l for l in report.get("links", [])
                   if l.get("product_id") == uid]
        unresolved = [
            q for q in report.get("review_queue", [])
            if uid in (q.get("candidate_products") or [])
        ]
        parties = {}
        for field, label in PARTY_FIELDS:
            ev = evidence.get(field) or {}
            value = fields.get(field) or ""
            parties[field] = {
                "label": label, "value": value,
                "status": "CO_TRICH_DAN_CHUA_XAC_MINH" if value and ev else
                          "CHUA_CO_CHUNG_CU_DINH_DANH",
                "file": ev.get("file", p["file"]) if value and ev else "",
                "source": ev.get("source", "") if value and ev else "",
                "sha256": ev.get("sha256", sha) if value and ev else "",
            }
        dossier = {
            "product_id": uid,
            "product_name": fields.get("PRODUCT_NAME", ""),
            "registration_no": fields.get("REGISTRATION_NO", ""),
            "product_code": fields.get("PRODUCT_ID", ""),
            "ingredient": fields.get("INGREDIENT", ""),
            "strength": fields.get("STRENGTH", ""),
            "origin_file": p["file"], "origin": p.get("origin", ""),
            "source_sha256": sha,
            "parties": parties,
            "proofs": [],
            "unresolved": unresolved,
            "verified": False, "bid_eligible": False,
        }
        for field, field_ev in evidence.items():
            provenance.append({
                "product_id": uid, "product_name": dossier["product_name"],
                "field": field, "value": fields.get(field, ""),
                "file": field_ev.get("file", p["file"]),
                "source": field_ev.get("source", p.get("origin", "")),
                "sha256": field_ev.get("sha256", sha),
                "raw": field_ev.get("raw", ""),
                "status": "CHUA_XAC_MINH",
            })
        for kind, label in REVIEW_CATEGORIES:
            related = [l for l in matches if l.get("evidence_kind") == kind]
            self_registration = (
                kind == "REGISTRATION"
                and p.get("registration_document_source")
                and bool(fields.get("REGISTRATION_NO"))
                and bool(evidence.get("REGISTRATION_NO"))
            )
            if related:
                status = "CO_LIEN_KET_SO_BO_CHUA_XAC_MINH"
            elif self_registration:
                status = "CO_TAI_LIEU_GOC_CHUA_XAC_MINH"
            else:
                status = "CHUA_CO_LIEN_KET_CHUNG_CU"
            entries = []
            if self_registration:
                origin = evidence["REGISTRATION_NO"]
                entries.append({
                    "file": p["file"], "sha256": sha,
                    "location": origin.get("source", p.get("origin", "")),
                    "excerpt": origin.get("raw", ""),
                    "status": "CHUA_XAC_MINH",
                })
            for match in related:
                meta = documents.get(match.get("source_sha256"), {})
                ev = match.get("evidence") or {}
                excerpt = " | ".join(str(x.get("raw", ""))[:300]
                                     for x in ev.values() if isinstance(x, dict))
                entries.append({
                    "file": match.get("source_evidence", ""),
                    "sha256": match.get("source_sha256", ""),
                    "location": match.get("evidence_origin", ""),
                    "excerpt": excerpt,
                    "status": match.get("status", "CHUA_XAC_MINH"),
                    "document_class": meta.get("public_document_class", ""),
                })
            proof = {
                "kind": kind, "label": label, "status": status,
                "requirement_status": "CHUA_DOI_CHIEU_EHSMT_CUA_GOI_THAU",
                "sources": entries, "business_verified": False,
            }
            dossier["proofs"].append(proof)
            if not entries:
                dossier["unresolved"].append({
                    "file": "", "kind": kind, "origin": "",
                    "status": "CHUA_CO_LIEN_KET_CHUNG_CU",
                    "candidate_products": [uid],
                    "reason": "Chưa có chứng cứ gắn đích danh sản phẩm; kiểm tra điều kiện E-HSMT",
                })
            for entry in entries or [{}]:
                checklist.append({
                    "product_id": uid, "product_name": dossier["product_name"],
                    "registration_no": dossier["registration_no"],
                    "manufacturer": parties["MANUFACTURER"]["value"],
                    "supplier": parties["SUPPLIER"]["value"],
                    "registration_holder": parties["REGISTRATION_HOLDER"]["value"],
                    "factory": parties["FACTORY"]["value"],
                    "kind": kind, "label": label,
                    "status": status,
                    "requirement_status": proof["requirement_status"],
                    "file": entry.get("file", ""),
                    "location": entry.get("location", ""),
                    "sha256": entry.get("sha256", ""),
                    "excerpt": entry.get("excerpt", ""),
                    "verified": False,
                })
        products.append(dossier)
    return {
        "products": products, "checklist": checklist, "provenance": provenance,
        "unassigned_files": [
            {"file": f.get("filename", ""), "sha256": f.get("sha256", ""),
             "role": f.get("kind", ""), "status": f.get("role_confidence", ""),
             "reason": "; ".join(f.get("reasons") or [])}
            for f in report.get("files", [])
            if f.get("kind") == "OTHER"
        ],
        "complete": False, "business_verified": False,
        "requirement_source": "CHUA_TRICH_DUOC_DIEU_KIEN_EHSMT_CUA_DU_AN",
        "note": ("Danh mục này dùng để truy xuất ngược sản phẩm và chứng cứ gốc. "
                 "Chưa có cơ sở đánh dấu đầy đủ giấy tờ pháp lý bắt buộc theo E-HSMT "
                 "của gói thầu, chưa duyệt thuốc/nhà sản xuất/GMP/SĐK/ủy quyền/báo giá."),
    }
