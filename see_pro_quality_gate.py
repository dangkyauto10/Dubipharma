"""SEE PRO deterministic quality gate. Coverage is NOT measured accuracy.

99.9999% is an aspirational accuracy target requiring a blinded, expert-labelled
validation corpus. No legal decisions, paid APIs or external writes here.
"""
from collections import Counter

TECH = ("HOAT_CHAT_HSMT", "NONG_DO_HAM_LUONG", "DANG_BAO_CHE", "DUONG_DUNG")
NSX = ("PRODUCT_NAME", "INGREDIENT", "STRENGTH", "DOSAGE_FORM", "ROUTE",
       "REGISTRATION_NO", "MANUFACTURER", "FACTORY")


def _result(scope, files, entries, field_coverage, issues):
    return {
        "scope": scope, "files": files, "entries": entries,
        "coverage": field_coverage, "issues": issues,
        "issue_count": len(issues),
        "status": "CAN_KIEM_TRA" if issues else "TRICH_XUAT_SO_BO",
        "legal_verified": False, "accuracy_validated": False,
        "accuracy_rate": None, "target_accuracy": 0.999999,
        "note": "Độ phủ có nguồn không phải tỷ lệ chính xác hoặc chứng nhận pháp lý.",
    }


def audit_ehsmt(data):
    data = data or {}
    docs, rows = data.get("documents") or [], data.get("rows") or []
    uploaded = data.get("input_files") or []
    issues = []
    recorded = Counter(x.get("SHA256") for x in docs)
    for f in uploaded:
        sha = f.get("sha256")
        if recorded[sha]:
            recorded[sha] -= 1
        else:
            issues.append({"type":"TEP_CHUA_DUOC_GHI_NHAN","file":f.get("name",""),
                           "reason":"Nguồn đã tải lên chưa có kết quả đọc.","priority":1})
    for d in docs:
        if not d.get("Đọc toàn bộ"):
            issues.append({"type":"DOC_CHUA_DAY_DU","file":d.get("Tệp",""),
                           "reason":"OCR hoặc trích xuất chưa hoàn tất.","priority":1})
    for d in data.get("failed_inputs") or []:
        issues.append({"type":"LOI_DOC","file":d.get("name",""),
                       "reason":d.get("error","Không xử lý được"),"priority":1})
    coverage = {}
    for field in TECH:
        found = sum(bool(str(r.get(field) or "").strip()) for r in rows)
        anchors = 0
        for row in rows:
            if not row.get(field):
                continue
            direct = (row.get("EVIDENCE") or {}).get(field) or {}
            technical = (row.get("EVIDENCE_KY_THUAT") or {}).get(field) or {}
            if (direct.get("source") and (direct.get("row") or direct.get("raw"))
                or technical.get("pages") and technical.get("raw_tokens")):
                anchors += 1
        coverage[field] = {"values":found,"field_cited":anchors}
        missing = found - anchors
        if missing:
            issues.append({
                "type":"TRUONG_EHSMT_THIEU_CHUNG_CU_RIENG",
                "file":"", "field":field, "count":missing,
                "reason":f"{field}: {missing} giá trị đã đọc nhưng không có "
                         "nguồn riêng đủ kiểm tra; không tự kết luận đúng.",
                "priority":2,
            })
    # A source row from the SUMMARY can be cited, while the separately read
    # TECHNICAL ingredient must still be checked independently; provenance
    # alone is not equality or chemical equivalence.
    crosscheck = Counter(str(r.get("DOI_CHIEU_HOAT_CHAT_HAI_BANG") or "")
                         for r in rows)
    for status in ("KHAC_CHUOI_CAN_SO_GOC", "THIEU_HOAT_CHAT_KY_THUAT"):
        if crosscheck[status]:
            issues.append({
                "type":"HOAT_CHAT_TONG_HOP_KY_THUAT_" + status,
                "file":"", "field":"HOAT_CHAT_HSMT",
                "count":crosscheck[status], "priority":2,
                "reason":f"{crosscheck[status]} mã có tình trạng {status}. "
                         "Giữ nguyên hai nguồn; chưa xác minh tương đương.",
            })
    # The upstream 'warnings' list includes classification/BP status and
    # must not disappear from the global Quality Gate summary.
    for warning in data.get("warnings") or []:
        issues.append({
            "type":"CANH_BAO_NGHIEP_VU_CHUA_GIAI_QUYET", "file":"",
            "reason":str(warning)[:350], "priority":2,
        })
    codes = Counter(str(r.get("MA_THUOC") or "") for r in rows)
    for code, n in codes.items():
        if code and n>1:
            issues.append({"type":"TRUNG_MA_LO","file":"","reason":f"{code}: {n} dòng",
                           "priority":1})
    if not rows:
        issues.append({"type":"KHONG_CO_DANH_MUC","file":"",
                       "reason":"Chưa có mã E-HSMT để so sánh.","priority":1})
    return _result("E-HSMT",len(uploaded) or len(docs),len(rows),coverage,issues)


def audit_nsx(data):
    data = data or {}
    docs, products = data.get("files") or [], data.get("products") or []
    issues = []
    for d in docs:
        if not d.get("complete_read"):
            issues.append({"type":"NSX_CHUA_DOC_DU","file":d.get("filename",""),
                           "reason":"Không đọc đủ nguồn gốc.","priority":1})
    coverage = {}
    for field in NSX:
        found = cited = 0
        for p in products:
            if (p.get("fields") or {}).get(field):
                found += 1
                ref = (p.get("evidence") or {}).get(field) or {}
                if (ref.get("file") and ref.get("source")
                    and field not in (p.get("conflicts") or {})):
                    cited += 1
        coverage[field] = {"values":found,"field_cited":cited}
    for p in products:
        if p.get("conflicts"):
            issues.append({"type":"NSX_MAU_THUAN","file":p.get("file",""),
                           "reason":", ".join(sorted(p["conflicts"])),"priority":1})
    if not products:
        issues.append({"type":"NSX_CHUA_CO_SAN_PHAM","file":"",
                       "reason":"Không suy ra không đạt từ danh mục trống.","priority":1})
    return _result("NSX",len(docs),len(products),coverage,issues)


def audit_comparison(data):
    data=data or {}
    issues=[]
    for lot in data.get("comparison") or []:
        for field in lot.get("criteria") or []:
            if field.get("status") != "DAT_SO_BO":
                continue
            a,b=field.get("ehsmt_evidence") or {}, field.get("nsx_evidence") or {}
            if not (a.get("file") and (a.get("location") or a.get("raw"))
                    and b.get("file") and b.get("location") and b.get("sha256")):
                issues.append({"type":"XANH_THIEU_DAU_VET",
                               "file":b.get("file",""),
                               "reason":str(lot.get("MA_THUOC_EHSMT",""))+
                                        " / "+str(field.get("label","")),
                               "priority":1})
    return _result("SO_SÁNH",0,len(data.get("comparison") or []),{},issues)
