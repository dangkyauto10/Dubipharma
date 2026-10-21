"""TDV QC7 leadership: real E-HSMT↔NSX comparison and evidence report.

Only compares data extracted within the SAME Streamlit session.
No demo fallback, external API, disk/cloud writes or bid/compliance approvals.
An ingredient match is NOT a technical match; incomplete fields are reported.
"""
from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from io import BytesIO
import re
import unicodedata

LOT = re.compile(r"^G\d+[.．]\d{2,4}$", re.I)
VN = timezone(timedelta(hours=7))


def norm(value) -> str:
    txt = unicodedata.normalize("NFKD", str(value or "").replace("Đ", "D").replace("đ", "d"))
    txt = "".join(c for c in txt if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", txt.casefold())).strip()


def compare_sources(ehsmt: dict | None, nsx: dict | None) -> dict:
    """Conservative, source-based comparison with no arbitrary row selection."""
    ehsmt = ehsmt or {}
    nsx = nsx or {}
    entries = {}
    warnings = []
    for record in ehsmt.get("rows", []):
        code = str(record.get("MA_THUOC") or "").strip().upper()
        if not LOT.fullmatch(code):
            continue
        if code in entries:
            warnings.append(f"Mã {code} có nhiều bản ghi E-HSMT; KHÔNG tự chọn bản đúng.")
            entries[code]["duplicated"] = True
            continue
        entries[code] = dict(record)
    products = nsx.get("traceability", {}).get("products")
    if products is None:
        products = []
    raw_products = {p.get("uid"): p for p in nsx.get("products", [])}
    group = defaultdict(list)
    for p in products:
        if p.get("ingredient"):
            group[norm(p["ingredient"])].append(p)
    rows = []
    counted = defaultdict(int)
    for code, lot in sorted(entries.items()):
        ingredient = str(lot.get("HOAT_CHAT_HSMT") or lot.get("HOAT_CHAT_CHUAN") or "").strip()
        strength = str(lot.get("NONG_DO_HAM_LUONG") or "").strip()
        candidates = group.get(norm(ingredient), []) if ingredient else []
        full = [p for p in candidates if strength and p.get("strength") and
                norm(strength) == norm(p.get("strength"))]
        if lot.get("duplicated"):
            state = "E_HSMT_TRUNG_MA_CAN_DOI_CHIEU"
            chosen = []
        elif len(full) == 1:
            state = "UNG_VIEN_KHOP_HOAT_CHAT_HAM_LUONG_CHUA_XAC_MINH"
            chosen = full
        elif len(full) > 1:
            state = "NHIEU_THUOC_CUNG_THONG_SO_KHONG_TU_CHON"
            chosen = full
        elif not ingredient:
            state = "E_HSMT_CHUA_TRICH_DUOC_HOAT_CHAT"
            chosen = []
        elif not candidates:
            state = ("NSX_CHUA_CO_DANH_MUC" if not products
                     else "NSX_KHONG_TIM_THAY_HOAT_CHAT")
            chosen = []
        elif len(candidates) == 1:
            state = "CUNG_HOAT_CHAT_THIEU_HAM_LUONG_DOI_CHIEU"
            chosen = candidates
        else:
            state = "NHIEU_UNG_VIEN_CUNG_HOAT_CHAT_CHUA_DU_TRUONG"
            chosen = candidates
        counted[state] += 1
        specific = chosen[0] if len(chosen) == 1 else None
        parties = specific.get("parties", {}) if specific else {}
        src = raw_products.get(specific["product_id"], {}) if specific else {}
        ev = src.get("evidence", {})
        rows.append({
            "MA_THUOC_EHSMT": code,
            "HOAT_CHAT_EHSMT": ingredient,
            "HAM_LUONG_EHSMT": strength,
            "MA_PHAN_LO": str(lot.get("MA_PHAN_LO") or ""),
            "NGUON_EHSMT": str(lot.get("FILE_NGUON") or ""),
            "VI_TRI_EHSMT": str(lot.get("TRANG_VI_TRI") or ""),
            "TRICH_DAN_EHSMT": str(lot.get("TRICH_DAN") or "")[:1000],
            "TRANG_THAI_DOI_CHIEU": state,
            "SO_UNG_VIEN_NSX": len(chosen),
            "MA_THUOC_NSX": specific["product_id"] if specific else "",
            "TEN_THUOC_NSX": specific["product_name"] if specific else "",
            "SO_DANG_KY": specific["registration_no"] if specific else "",
            "HOAT_CHAT_NSX": specific["ingredient"] if specific else "",
            "HAM_LUONG_NSX": specific["strength"] if specific else "",
            "DON_VI_CUNG_CAP": parties.get("SUPPLIER", {}).get("value", ""),
            "NHA_THAU": parties.get("BIDDER", {}).get("value", ""),
            "DON_VI_DANG_KY": parties.get("REGISTRATION_HOLDER", {}).get("value", ""),
            "NHA_SAN_XUAT": parties.get("MANUFACTURER", {}).get("value", ""),
            "NHA_MAY": parties.get("FACTORY", {}).get("value", ""),
            "NGUON_THUOC_NSX": specific.get("origin_file", "") if specific else "",
            "VI_TRI_NSX": specific.get("origin", "") if specific else "",
            "SHA256_NSX": specific.get("source_sha256", "") if specific else "",
            "NGUON_HAM_LUONG_NSX": ev.get("STRENGTH", {}).get("source", ""),
            "DA_XAC_MINH": "CHUA",
            "DAP_UNG_THAU": "CHUA_DU_CO_SO_KET_LUAN",
        })
    if not ehsmt.get("rows"):
        warnings.append("Chưa có kết quả E-HSMT THẬT trong phiên; không thực hiện đối chiếu.")
    elif not entries:
        warnings.append("Kết quả E-HSMT chưa có mã Gx.xxx; không được tự lập mã.")
    if not products:
        warnings.append("Chưa có sản phẩm NSX được nhận diện có nguồn; không kết luận không có sản phẩm.")
    if not nsx.get("files"):
        warnings.append("Chưa có kết quả bộ tài liệu NSX THẬT trong phiên.")
    if ehsmt.get("warnings"):
        warnings.append(f'E-HSMT có {len(ehsmt["warnings"])} cảnh báo nguồn; tra bảng gốc.')
    if nsx.get("warnings"):
        warnings.append(f'NSX có {len(nsx["warnings"])} cảnh báo nguồn; tra bảng gốc.')
    return {
        "created_at_vn": datetime.now(VN).strftime("%d/%m/%Y %H:%M:%S +07:00"),
        "mode": "REAL_SOURCES_ONLY_NO_DEMO",
        "summary": {
            "ehsmt_lots": len(entries), "nsx_products": len(products),
            "nsx_files": len(nsx.get("files") or []),
            "nsx_review": len(nsx.get("review_queue") or []),
            "matching_fields_unverified": counted["UNG_VIEN_KHOP_HOAT_CHAT_HAM_LUONG_CHUA_XAC_MINH"],
            "other_cases": len(entries) - counted["UNG_VIEN_KHOP_HOAT_CHAT_HAM_LUONG_CHUA_XAC_MINH"],
            "fully_verified": 0,
        },
        "comparison": rows,
        "traceability": nsx.get("traceability") or {},
        "ehsmt_documents": ehsmt.get("documents") or [],
        "tender_documents": ehsmt.get("tender_documents") or [],
        "nsx_documents": nsx.get("files") or [],
        "warnings": warnings,
        "verified": False, "gmp_approved": False,
        "bid_eligible": False, "requirements_checked": False,
        "note": ("Các cột khớp chỉ là gợi ý cùng dữ kiện chữ và hàm lượng, "
                 "KHÔNG chứng minh đáp ứng kỹ thuật, GMP/SĐK, giá, thầu hay pháp lý."),
    }


def _safe(value):
    from see_pro_traceability import safe_cell
    return safe_cell(value)


def export_leadership_xlsx(report: dict) -> bytes:
    from openpyxl import Workbook
    from see_pro_traceability import _format
    wb = Workbook()
    title = wb.active
    title.title = "TONG_QUAN_LANH_DAO"
    title.append(["Thông tin", "Giá trị / ghi chú"])
    title.append(["Ngày báo cáo (VN)", report["created_at_vn"]])
    title.append(["Loại báo cáo", "Nguồn thật trong phiên; không DEMO"])
    for key, value in report["summary"].items():
        title.append([key, value])
    title.append(["Trạng thái pháp lý", "CHUA XAC MINH — KHONG KET LUAN DU DIEU KIEN"])
    compare = wb.create_sheet("DOI_CHIEU_EHSMT_NSX")
    rows = report["comparison"]
    cols = list(rows[0]) if rows else [
        "MA_THUOC_EHSMT", "TRANG_THAI_DOI_CHIEU", "DAP_UNG_THAU"
    ]
    compare.append(cols)
    for row in rows:
        compare.append([_safe(row.get(k)) for k in cols])
    trace = report.get("traceability") or {}
    party = wb.create_sheet("TRUY_XUAT_DOANH_NGHIEP")
    party.append(["Mã thuốc NSX", "Tên thuốc", "SĐK", "Vai trò", "Đơn vị",
                  "Trạng thái", "Tệp", "Vị trí nguồn", "SHA256"])
    for p in trace.get("products") or []:
        for detail in p.get("parties", {}).values():
            party.append([_safe(z) for z in (
                p["product_id"], p["product_name"], p["registration_no"],
                detail["label"], detail["value"], detail["status"],
                detail["file"], detail["source"], detail["sha256"],
            )])
    proof = wb.create_sheet("CHUNG_CU_THEO_SAN_PHAM")
    proof.append(["Mã NSX", "Tên thuốc", "Giấy tờ cần rà soát",
                  "Có nguồn trực tiếp?", "Yêu cầu theo E-HSMT",
                  "Tệp", "Vị trí nguồn", "SHA256", "Trích dẫn"])
    for x in trace.get("checklist", []) or []:
        proof.append([_safe(z) for z in (
            x["product_id"], x["product_name"], x["label"], x["status"],
            x["requirement_status"], x["file"], x["location"], x["sha256"],
            x["excerpt"],
        )])
    sources = wb.create_sheet("DANH_MUC_TAI_LIEU")
    sources.append(["Hệ", "Tệp", "Loại", "SHA256", "Đọc đủ", "Xác minh"])
    for doc in report.get("ehsmt_documents", []):
        sources.append([_safe(z) for z in ("E-HSMT", doc.get("Tệp"),
                        doc.get("Loại nghiệp vụ"), doc.get("SHA256"),
                        doc.get("Đọc toàn bộ"), "CHUA")])
    for doc in report.get("nsx_documents", []):
        sources.append([_safe(z) for z in ("NSX", doc.get("filename"),
                        doc.get("kind"), doc.get("sha256"),
                        doc.get("complete_read"), "CHUA")])
    alerts = wb.create_sheet("CANH_BAO_KHUYEN_NGHI")
    alerts.append(["STT", "Nội dung", "Xử lý / giới hạn"])
    for i, warn in enumerate(report.get("warnings", []), 1):
        alerts.append([i, _safe(warn), "Tra hồ sơ gốc trước khi kết luận"])
    alerts.append([len(report.get("warnings", []))+1,
                   "Không có kết luận thuốc đủ điều kiện dự thầu.",
                   "Đối chiếu E-HSMT hiện hành và xác minh với người có thẩm quyền."])
    for sheet in wb.worksheets:
        _format(sheet, status_field="TRANG_THAI_DOI_CHIEU"
                if sheet.title == "DOI_CHIEU_EHSMT_NSX" else None)
    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def export_leadership_docx(report: dict) -> bytes:
    from docx import Document
    from docx.shared import Pt
    doc = Document()
    doc.add_heading("BÁO CÁO LÃNH ĐẠO — TDV QC7 ONLINE", 0)
    doc.add_paragraph("Đối chiếu E-HSMT – NSX và truy xuất chứng cứ theo hồ sơ thật")
    doc.add_paragraph("Lập lúc: " + report["created_at_vn"])
    doc.add_heading("1. Tổng quan dữ liệu", level=1)
    labels = {
        "ehsmt_lots": "Mã E-HSMT nhận diện",
        "nsx_products": "Thuốc NSX có định danh nguồn",
        "nsx_files": "Tài liệu NSX đã nạp",
        "nsx_review": "Mục NSX cần kiểm tra",
        "matching_fields_unverified": "Ứng viên trùng hoạt chất và hàm lượng (CHƯA XÁC MINH)",
        "other_cases": "Mã E-HSMT chưa có ứng viên đủ trường",
        "fully_verified": "Mã được xác minh đáp ứng hoàn toàn",
    }
    for key, label in labels.items():
        doc.add_paragraph(f'{label}: {report["summary"].get(key,0)}',style="List Bullet")
    doc.add_heading("2. Kết quả đối chiếu và vấn đề tồn tại",level=1)
    doc.add_paragraph(report["note"])
    for row in report["comparison"][:40]:
        doc.add_paragraph(
            f'{row["MA_THUOC_EHSMT"]} — {row["HOAT_CHAT_EHSMT"]}: '
            f'{row["TRANG_THAI_DOI_CHIEU"]}',
            style="List Bullet",
        )
    if len(report["comparison"])>40:
        doc.add_paragraph("Các mã còn lại và chứng cứ đầy đủ nằm trong file Excel kèm theo.")
    for message in report["warnings"]:
        doc.add_paragraph(message, style="List Bullet")
    doc.add_heading("3. Kiến nghị cho Lãnh đạo",level=1)
    for message in (
        "Không phê duyệt đáp ứng E-HSMT chỉ dựa trên phép so trùng hoạt chất/hàm lượng.",
        "Đọc đầy đủ E-HSMT, phiên bản sửa đổi/làm rõ và yêu cầu hồ sơ của đúng gói.",
        "Đối chiếu gốc SĐK, GMP, nhà sản xuất, nhà máy, ủy quyền và báo giá theo từng thuốc.",
        "Tiếp tục hoàn thiện những trường chưa có nguồn, rồi xuất lại báo cáo đã kiểm chứng.",
    ):
        doc.add_paragraph(message, style="List Number")
    doc.add_paragraph("TRẠNG THÁI: BÁO CÁO SƠ BỘ — CHƯA XÁC MINH, KHÔNG LÀ KẾT LUẬN THẦU.")
    for p in doc.paragraphs:
        p.style.font.size = Pt(10)
    output=BytesIO()
    doc.save(output)
    return output.getvalue()
