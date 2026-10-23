"""Unified E-HSMT / SEE PRO workbench inside TDV QC7 ONLINE.

One multi-file intake. Old E-HSMT PDF semantics preserved; other formats
are preliminary evidence inventory, not automatically mapped specifications.
"""
from __future__ import annotations

import hashlib
import io
import json
import pandas as pd
import streamlit as st
from tdv_ehsmt_intake import inspect_ehsmt_pdf, export_ehsmt_csv
from see_pro_multiformat import ACCEPTED, extract_file, identify_codes
from see_pro_structured import identify_document
from see_pro_adapters import parse_tabular_document
from see_pro_pdf_geometry import extract_g1_technical
from see_pro_structured import normalize as normalize_field
from see_pro_traceability import build_audit_workbook
from see_pro_pdf_viewer import render_original_pdf_viewer
from tdv_readable_tables import render_readable_table

from tdv_ehsmt_xlsx import inspect_ehsmt_xlsx
from tdv_see_pro_scope import bind_report, validate_scope
from see_pro_quality_gate import audit_ehsmt
from tdv_tender_context import (
    detect_procurement_document, index_tender_documents, PUBLIC_REFERENCES,
)


def _append_xlsx_ehsmt_summary(result: dict, filename: str, package_id: str,
                               scanned: dict) -> None:
    """Source-anchored fallback for authentic summary-style E-HSMT workbooks.

    Only used when the existing structured technical-table reader finds no rows.
    Keep incomplete or contradictory codes visible rather than silently dropping
    them; never automatically verify legal or technical compliance.
    """
    complete = scanned["complete_read"] and not scanned["missing_summary"]
    result["structured_tables"].append({
        "Tệp": filename, "Mã gói BP": package_id,
        "Số lô": scanned["lot_count"], "Nhận diện cấu trúc": complete,
        "Số cảnh báo": len(scanned["warnings"]),
        "Các Sheet": f'{scanned["sheets"]} sheet',
        "Dòng bảng tổng hợp rõ": scanned["summary_rows"],
        "Loại bảng": "Bảng tổng hợp E-HSMT (tự nhận diện)",
    })
    result["warnings"].extend(f"{filename}: {warning}" for warning in scanned["warnings"])
    for lot in scanned["lots"]:
        evidence = lot.get("EVIDENCE") or {}
        refs = lot.get("VI_TRI_THAM_CHIEU") or []
        place = ({"sheet": evidence["sheet"], "row": evidence["row"]}
                 if evidence else refs[0] if refs else {})
        original = " | ".join(str(c["raw"]) for c in evidence.get("cells", []))
        location = (f'{place["sheet"]} – dòng {place["row"]}' if place else "")
        field_evidence = ({
            "DONG_BANG_TONG_HOP": {
                "source": filename, "sheet": evidence["sheet"], "row": evidence["row"],
                "column": "", "raw": original, "verified": False,
            }
        } if evidence else {})
        result["rows"].append({
            "FILE_NGUON": filename, "MA_GOI_THAU": package_id,
            "MA_THUOC": lot["MA_THUOC"], "MA_PHAN_LO": lot.get("MA_PHAN_LO", ""),
            "HOAT_CHAT_HSMT": lot.get("HOAT_CHAT_CHUAN"),
            "GIA_UOC_TINH_PHAN": lot.get("GIA_TRI_UOC_TINH"),
            "TIEN_BAO_DAM_DU_THAU": lot.get("BAO_DAM_DU_THAU"),
            "SHEET": place.get("sheet", ""), "DONG_NGUON": place.get("row", ""),
            "TRANG_VI_TRI": location, "TRICH_DAN": original[:600],
            "TRANG_THAI": lot["TRANG_THAI"],
            "EVIDENCE": field_evidence, "verified": False,
        })



def _compare_two_ingredient_strings(summary: str, technical: str) -> str:
    """Compare only literal extracted strings, not chemical equivalents."""
    if not summary:
        return "THIEU_HOAT_CHAT_TONG_HOP"
    if not technical:
        return "THIEU_HOAT_CHAT_KY_THUAT"
    left = "".join(normalize_field(summary).split())
    right = "".join(normalize_field(technical).split())
    return "CUNG_CHUOI_CHUA_XAC_MINH" if left and left == right else "KHAC_CHUOI_CAN_SO_GOC"


def analyze_uploads(uploaded: list[tuple[str, bytes]], *, enable_ocr: bool = False,
                    deep_technical: bool = False) -> dict:
    """Classify before reading. Do not force every PDF to use G1.xxx."""
    result = {"documents": [], "rows": [], "warnings": [],
              "pdf_reports": [], "notices": [], "structured_tables": [],
              "tender_documents": [], "tender_index": {},
              "input_files": [{"name":name,"sha256":hashlib.sha256(raw).hexdigest(),
                               "bytes":len(raw)} for name,raw in uploaded],
              "failed_inputs": []}
    for filename, data in uploaded:
        try:
            classification = identify_document(filename, data)
            role = classification["type"]
            source = extract_file(filename, data, ocr=enable_ocr)
            tender_meta = detect_procurement_document(source["lines"])
            if (tender_meta and role == "BANG_EHSMT_PDF" and
                    tender_meta["kind"] == "KET_QUA_LCNT"):
                # The header keyword is in conflict with independently detected
                # E-HSMT G1/PP structure. Do not label a tender document as a
                # winning-bid decision based on an incidental phrase.
                tender_meta = {
                    **tender_meta,
                    "kind": "CAN_XAC_MINH_LOAI",
                    "classification_conflict": ["BANG_EHSMT_PDF", "KET_QUA_LCNT"],
                    "suggested_action": (
                        "Tài liệu có cấu trúc bảng E-HSMT G1/PP nhưng vùng "
                        "đầu chứa cụm 'kết quả lựa chọn nhà thầu'. "
                        "Kiểm tra trang bìa/văn bản gốc trước khi phân loại."
                    ),
                }
                result["warnings"].append(
                    f"{filename}: mâu thuẫn loại tài liệu E-HSMT / "
                    "KET_QUA_LCNT, cần kiểm tra trang đầu.")
            if tender_meta:
                result["tender_documents"].append({
                    "filename": filename, "sha256": source["sha256"],
                    "complete_read": source["complete"], **tender_meta,
                })
            document_info = {
                "Tệp": filename, "Loại": source["type"].upper(),
                "Loại nghiệp vụ": role,
                "Mã gói BP": classification["package_id"],
                "Đoạn/dòng đọc": len(source["lines"]),
                "Số trang": source["pages"], "Đọc toàn bộ": source["complete"],
                "SHA256": source["sha256"], "Xác minh": "CHƯA",
            }
            result["documents"].append(document_info)
            result["warnings"].extend(f"{filename}: {w}" for w in source["warnings"])

            if role == "THONG_BAO_MOI_THAU":
                result["notices"].append({"file": filename, **classification})
                # Absence of G1.xxx in a notice is NORMAL; never raise a lot warning.
                continue

            if filename.lower().endswith((".xlsx", ".xls", ".csv", ".docx")):
                parsed = parse_tabular_document(filename, data)
                if filename.lower().endswith(".xlsx") and not parsed["rows"]:
                    summary = inspect_ehsmt_xlsx(data)
                    if summary["lot_count"]:
                        _append_xlsx_ehsmt_summary(
                            result, filename, classification["package_id"], summary)
                        continue
                result["structured_tables"].append({
                    "Tệp": filename, "Mã gói BP": parsed["package_id"],
                    "Số lô": parsed["total_lots"], "Nhận diện cấu trúc": parsed["complete"],
                    "Số cảnh báo": len(parsed["issues"]),
                    "Các Sheet": ", ".join(x["sheet"] for x in parsed["sheets"]),
                })
                if not parsed["complete"]:
                    result["warnings"].append(
                        f"{filename}: không nhận diện đầy đủ bảng nghiệp vụ; cần đối chiếu tên cột")
                for note in parsed.get("warnings", []):
                    result["warnings"].append(f"{filename}: {note}")
                for issue in parsed["issues"]:
                    result["warnings"].append(f"{filename}: {issue['type']}: {issue}")
                for row in parsed["rows"]:
                    result["rows"].append({
                        **row,
                        "TRANG_VI_TRI": f"{row['SHEET']} – dòng {row['DONG_NGUON']}",
                        "TRICH_DAN": str(row.get("HOAT_CHAT_HSMT") or "")[:350],
                    })
                if parsed["rows"]:
                    continue

            if role == "BANG_EHSMT_PDF":
                report = inspect_ehsmt_pdf(data)
                deep_report = extract_g1_technical(data, report) if deep_technical else None
                deep_by_code = ({r["MA_THUOC"]: r for r in deep_report["rows"]}
                                if deep_report else {})
                if deep_report:
                    result["warnings"].extend(
                        f"{filename}: kỹ thuật {finding}" for finding in deep_report["findings"])
                result["pdf_reports"].append({
                    "Tệp": filename, "Số trang": report["total_pages"],
                    "Trang đã đọc": report["pages_processed"],
                    "Mã G1 nhận diện": report["lot_count"],
                    "Dòng tổng hợp": report["summary_rows"],
                    "Chưa tách được": len(report["missing_summary"]),
                    "Mã chưa tách": ", ".join(report["missing_summary"][:20]),
                    "SHA256": report["sha256"],
                    "Dòng kỹ thuật": deep_report["found_rows"] if deep_report else None,
                    "Khớp tiền": deep_report["financial_crosschecked"] if deep_report else None,
                    "Khớp mã phần": deep_report["part_crosschecked"] if deep_report else None,
                })
                result["warnings"].extend(f"{filename}: {w}" for w in report["warnings"])
                for lot in report["lots"]:
                    tech = deep_by_code.get(lot["MA_THUOC"])
                    summary_ingredient = lot.get("HOAT_CHAT_CHUAN") or ""
                    summary_raw = lot.get("CHUNG_CU_BANG_TONG_HOP") or ""
                    summary_page = lot.get("TRANG_BANG_TONG_HOP")
                    # Field-level proof comes from original SUMMARY page, not
                    # from a guessed technical-column value or product name.
                    summary_evidence = ({
                        "HOAT_CHAT_HSMT": {
                            "source": filename, "file": filename,
                            "page": summary_page, "row": lot.get("STT"),
                            "raw": summary_raw, "value": summary_ingredient,
                            "sha256": report["sha256"],
                            "basis": "BANG_TONG_HOP_PDF",
                            "verified": False,
                        },
                    } if summary_ingredient and summary_page and
                    normalize_field(summary_ingredient) in normalize_field(summary_raw)
                    else {})
                    tech_ingredient = (
                        tech.get("HOAT_CHAT_BANG_KY_THUAT", "") if tech else "")
                    result["rows"].append({
                        "FILE_NGUON": filename, "MA_GOI_THAU": "",
                        "SHA256": report["sha256"],
                        "MA_THUOC": lot["MA_THUOC"],
                        "MA_PHAN_LO": lot.get("MA_PHAN_LO", ""),
                        "HOAT_CHAT_HSMT": lot.get("HOAT_CHAT_CHUAN"),
                        "HOAT_CHAT_KY_THUAT_NGUON": tech_ingredient,
                        "DOI_CHIEU_HOAT_CHAT_HAI_BANG": (
                            _compare_two_ingredient_strings(summary_ingredient, tech_ingredient)
                            if deep_report else "CHUA_DOI_CHIEU_BANG_KY_THUAT"),
                        "EVIDENCE": summary_evidence,
                        "GIA_UOC_TINH_PHAN": lot.get("GIA_TRI_UOC_TINH"),
                        "TIEN_BAO_DAM_DU_THAU": lot.get("BAO_DAM_DU_THAU"),
                        "TRANG_VI_TRI": lot.get("TRANG_BANG_TONG_HOP"),
                        "TRICH_DAN": lot.get("CHUNG_CU_BANG_TONG_HOP")
                                       or lot.get("TRICH_DOAN", ""),
                        "TRANG_THAI": lot.get("TRANG_THAI", "CAN_XAC_MINH"),
                        **({
                            "NONG_DO_HAM_LUONG": tech["NONG_DO_HAM_LUONG"],
                            "DUONG_DUNG": tech["DUONG_DUNG"],
                            "DANG_BAO_CHE": tech["DANG_BAO_CHE"],
                            "DON_VI_TINH": tech["DON_VI_TINH"],
                            "NHOM_THUOC": tech["NHOM_THUOC"],
                            "SO_LUONG_CHINH": tech["SO_LUONG_CHINH"],
                            "DON_GIA_KE_HOACH": tech["DON_GIA_KE_HOACH"],
                            "TRANG_BANG_KY_THUAT": tech["TRANG_KY_THUAT"],
                            "KHOP_SO_HOC": tech["KHOP_TONG_GIA_TRI"],
                            "KHOP_MA_PHAN_LO": tech["KHOP_MA_PHAN_LO"],
                            "EVIDENCE_KY_THUAT": tech["EVIDENCE"],
                        } if tech else {}),
                    })
            else:
                # Keep original generic evidence intake for Word, CSV, images, non-lot PDFs.
                for item in identify_codes(source):
                    result["rows"].append({
                        "FILE_NGUON": filename, "MA_GOI_THAU": classification["package_id"],
                        "MA_THUOC": item["Mã lô"], "MA_PHAN_LO": "",
                        "HOAT_CHAT_HSMT": None, "GIA_UOC_TINH_PHAN": None,
                        "TIEN_BAO_DAM_DU_THAU": None,
                        "TRANG_VI_TRI": item["Nguồn"], "TRICH_DAN": item["Trích dẫn"],
                        "TRANG_THAI": "CAN_XAC_MINH_TRUONG_DU_LIEU",
                    })
        except (ValueError, RuntimeError, OSError, ImportError) as exc:
            result["failed_inputs"].append({"name":filename,"error":type(exc).__name__})
            result["warnings"].append(
                f"{filename}: không thể đọc ({type(exc).__name__})")
    for notice in result["notices"]:
        bp = notice.get("package_id")
        # Only link tables with the same identified BP; never combine unrelated packages.
        related = [t for t in result["structured_tables"] if t["Mã gói BP"] == bp]
        expected = (notice.get("evidence", {}).get("SO_PHAN_LO") or {}).get("value")
        if not related:
            # A tender notice is a legitimate standalone document. No lot sheet
            # was supplied for this BP: status, not an extraction failure.
            notice["lot_list_status"] = "Chưa có bảng danh mục đúng mã gói"
            continue
        actual = sum(t["Số lô"] for t in related)
        notice["lot_list_status"] = f"Đã đọc {actual} lô của gói {bp}"
        if expected and expected.isdigit() and int(expected) != actual:
            notice["lot_list_status"] = "CẦN KIỂM TRA: số lô không khớp"
            result["warnings"].append(
                f"{notice['file']}: số lô thông báo {expected}, bảng khớp {actual}; cần kiểm tra")
    result["tender_index"] = index_tender_documents(result["tender_documents"])
    for issue in result["tender_index"]["unassigned"]:
        result["warnings"].append(
            f'{issue["filename"]}: tài liệu liên quan chưa xác định duy nhất mã BP')
    result["quality_gate"] = audit_ehsmt(result)
    return result


def render_ehsmt_workbench() -> None:
    st.markdown("### E-HSMT · SEE PRO – Tiếp nhận, đọc và kiểm toán hồ sơ")
    st.caption("Một luồng cho PDF, Word, Excel, CSV và ảnh. Dữ liệu đọc được là sơ bộ, có chứng cứ; không tự duyệt thầu.")
    scope = validate_scope(st.session_state.get("tdv_see_pro_active_scope"))
    if not scope:
        st.warning("Chọn dự án / BP / phiên bản E-HSMT trước khi nạp để đối chiếu.")
        return
    files = st.file_uploader(
        "Tải một hoặc nhiều tài liệu E-HSMT / hồ sơ thuốc / GMP / báo giá",
        type=list(ACCEPTED), accept_multiple_files=True,
        key="tdv_see_pro_documents_" + "_".join(scope.values()))
    ocr = st.checkbox(
        "Bật OCR cục bộ cho ảnh và trang PDF không có chữ (cần kiểm tra lại nguồn)",
        value=False, key="tdv_see_pro_ocr")
    deep = st.checkbox("Đối chiếu sâu bảng kỹ thuật PDF G1 theo vị trí cột (chỉ áp dụng khi nhận diện đúng mẫu)",
                       value=False, key="tdv_see_pro_deep")
    if files:
        digest = hashlib.sha256()
        for f in files:
            digest.update(f.name.encode("utf-8"))
            digest.update(f.getvalue())
        digest.update(str(ocr).encode())
        digest.update(str(deep).encode())
        signature = digest.hexdigest()
        if st.session_state.get("tdv_see_pro_signature") != signature:
            st.session_state.pop("tdv_see_pro_analysis", None)
        if st.button("Đọc và kiểm toán bộ hồ sơ", key="tdv_see_pro_execute", type="primary"):
            with st.spinner("Đang đọc tài liệu và lập danh mục chứng cứ..."):
                result = analyze_uploads(
                    [(f.name, f.getvalue()) for f in files], enable_ocr=ocr,
                    deep_technical=deep)
            st.session_state["tdv_see_pro_signature"] = signature
            st.session_state["tdv_see_pro_analysis"] = result
    else:
        st.info("Tải hồ sơ để bắt đầu. Tài liệu không được tự gửi ra Google Sheets hoặc API bên ngoài.")
        return

    analysis = st.session_state.get("tdv_see_pro_analysis")
    if not analysis or st.session_state.get("tdv_see_pro_signature") != signature:
        return
    docs = pd.DataFrame(analysis["documents"])
    rows = pd.DataFrame(analysis["rows"])
    pdfs = pd.DataFrame(analysis["pdf_reports"])
    a, b, c = st.columns(3)
    a.metric("Tệp đã đọc", len(docs))
    b.metric("Mặt hàng / mã ứng viên", len(rows))
    c.metric("Cảnh báo", len(analysis["warnings"]))
    st.warning("Đây là bản trích xuất để đối chiếu, KHÔNG phải kết quả kiểm chứng kỹ thuật, GMP hay giá chào.")
    quality = analysis.get("quality_gate") or audit_ehsmt(analysis)
    st.markdown("**SEE PRO · Kiểm toán chất lượng đầu vào**")
    st.caption(quality["note"] + " Mốc 99,9999% là mục tiêu, chưa nghiệm thu.")
    st.caption(f'Tệp đầu vào: {quality["files"]} · Mã/dòng trích xuất: {quality["entries"]} · '
               f'Vấn đề phát hiện: {quality["issue_count"]}')
    render_readable_table(st, pd.DataFrame([{
        "Trường E-HSMT": key, "Có giá trị": value["values"],
        "Có nguồn riêng": value["field_cited"],
        "Thiếu nguồn riêng": value["values"]-value["field_cited"],
    } for key,value in quality["coverage"].items()]),
        key="tdv_ehsmt_quality_visible", label="Kiểm toán độ phủ chứng cứ",
        page_size=25, min_width=720)
    if quality["issues"]:
        with st.expander("Chi tiết tệp lỗi, mã trùng và nguồn chưa đầy đủ"):
            st.dataframe(pd.DataFrame(quality["issues"]),hide_index=True,use_container_width=True)
    if not docs.empty:
        st.markdown("**Tệp và nguồn chứng cứ**")
        render_readable_table(st, docs, key="tdv_ehsmt_source_files_visible",
                              label="Tệp và nguồn chứng cứ E-HSMT", page_size=20,
                              min_width=1000)
    render_original_pdf_viewer(files, analysis)
    if analysis.get("tender_documents"):
        st.markdown("**Tài liệu liên quan cùng gói thầu (tự nhận diện)**")
        related = pd.DataFrame([{
            "Tệp": d["filename"], "Loại": d["kind"],
            "Mã BP": ", ".join(d["package_ids"]),
            "Phiên bản": d["revision_status"], "Hướng xử lý": d["suggested_action"],
            "SHA256": d["sha256"],
        } for d in analysis["tender_documents"]])
        render_readable_table(st, related, key="tdv_ehsmt_related_visible",
                              label="Tài liệu cùng gói thầu tự nhận diện",
                              page_size=20, min_width=1080)
    if analysis.get("structured_tables"):
        st.markdown("**Danh sách phần/lô theo từng mã gói thầu**")
        st.dataframe(pd.DataFrame(analysis["structured_tables"]), hide_index=True, use_container_width=True)
    if analysis.get("notices"):
        st.markdown("**Thông báo mời thầu đã nhận diện**")
        meta = [{"Tệp": notice["file"], "Mã gói BP": notice["package_id"],
                 **{key: info["value"] for key, info in notice["evidence"].items()},
                 "Trạng thái danh mục": notice.get("lot_list_status", "Chưa kiểm tra")}
                for notice in analysis["notices"]]
        st.dataframe(pd.DataFrame(meta), hide_index=True, use_container_width=True)
        st.caption("Số lô công bố trong thông báo không phải số lô đã trích xuất. Chỉ liên kết các tài liệu cùng mã BP.")
    if not pdfs.empty:
        st.markdown("**Kiểm kê bảng tổng hợp PDF E-HSMT**")
        render_readable_table(st, pdfs, key="tdv_ehsmt_inventory_visible",
                              label="Kiểm kê bảng tổng hợp PDF E-HSMT",
                              page_size=20, min_width=1320)
    if not rows.empty:
        evidence_rows = rows.drop(columns=["EVIDENCE", "EVIDENCE_KY_THUAT", "verified"], errors="ignore")
        term = st.text_input("Tìm theo mã G1, mã PP, hoạt chất hoặc chứng cứ", key="tdv_see_pro_keyword")
        if term.strip():
            mask = evidence_rows.fillna("").astype(str).apply(
                lambda col: col.str.contains(term.strip(), case=False, regex=False)).any(axis=1)
            shown = evidence_rows[mask]
        else:
            shown = evidence_rows
        render_readable_table(st, shown.fillna(""), key="tdv_ehsmt_lots_visible",
                              label="Danh mục mã thuốc và chứng cứ",
                              page_size=25, min_width=1450)
        st.download_button("Tải bảng kiểm kê CSV (chưa xác minh)",
                           data=evidence_rows.fillna("").to_csv(index=False).encode("utf-8-sig"),
                           file_name="TDV_SEE_PRO_KIEM_KE.csv", mime="text/csv",
                           key="tdv_see_pro_csv")
        st.download_button("Tải Excel kiểm toán và chất lượng (6 Sheet)",
                           data=build_audit_workbook(analysis),
                           file_name="TDV_SEE_PRO_KIEM_TOAN_CHUNG_CU.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="tdv_see_pro_excel")
    if analysis["warnings"]:
        with st.expander(f"Cảnh báo và dòng cần xem lại ({len(analysis['warnings'])})"):
            for warning in analysis["warnings"][:150]:
                st.warning(warning)
    st.download_button(
        "Tải báo cáo JSON (chưa xác minh)",
        data=json.dumps(analysis, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name="TDV_SEE_PRO_AUDIT.json", mime="application/json",
        key="tdv_see_pro_json")

    render_ai_evidence_review(files, ocr=ocr, upload_signature=signature)


def render_ai_evidence_review(files, *, ocr: bool, upload_signature: str) -> None:
    """Optional second-stage analysis within the EXISTING E-HSMT page.

    Source snippets are previewed locally before user-triggered external request.
    No raw file is sent to Google and no model output is marked verified.
    """
    from see_pro_ai_review import (
        SUPPORTED_MODELS, prepare_context, review_with_gemini, export_review_xlsx,
    )
    import os

    with st.expander("🧠 SEE PRO · Đối chiếu chứng cứ bằng AI (tùy chọn)", expanded=False):
        st.info(
            "Bộ đọc PDF/Excel/Word vẫn hoạt động độc lập, không cần Gemini. "
            "AI chỉ gợi ý đối chiếu cho MỘT mã thuốc hoặc phần/lô mỗi lượt; "
            "không quyết định đạt thầu, không tự ghi Sheets."
        )
        st.warning(
            "Nếu bật Gemini, các ĐOẠN TRÍCH hiển thị bên dưới sẽ được gửi đến "
            "Google để phân tích và có thể phát sinh chi phí API. "
            "Không dùng dữ liệu bí mật trên dịch vụ miễn phí: theo điều khoản Google, "
            "dữ liệu API miễn phí có thể được dùng để cải thiện dịch vụ. "
            "Khi không bật Gemini, tài liệu chỉ được xử lý tại máy chủ ứng dụng Streamlit; "
            "không chủ động chuyển tiếp đến Gemini."
        )
        code = st.text_input(
            "Mã thuốc hoặc mã phần/lô cần đối chiếu (ví dụ: G1.362, GE841.001, PP2600428741)",
            key="tdv_see_pro_ai_lot",
        ).strip()
        model = st.selectbox("Mô hình Gemini", SUPPORTED_MODELS,
                             key="tdv_see_pro_ai_model")
        packet = st.session_state.get("tdv_see_pro_ai_packet")
        selection = (upload_signature, code.lower())
        if packet and packet.get("selection") != selection:
            packet = None
            st.session_state.pop("tdv_see_pro_ai_packet", None)
            st.session_state.pop("tdv_see_pro_ai_result", None)

        if st.button("1. Xem trước các đoạn trích sẽ gửi", disabled=not bool(code),
                     key="tdv_see_pro_ai_prepare"):
            try:
                candidate = prepare_context(
                    [(f.name, f.getvalue()) for f in files],
                    lot_code=code, enable_ocr=ocr,
                )
                packet = {"selection": selection, "context": candidate}
                st.session_state["tdv_see_pro_ai_packet"] = packet
                st.session_state.pop("tdv_see_pro_ai_result", None)
            except (ValueError, RuntimeError, OSError, ImportError) as exc:
                st.error(f"Chưa tạo được trích đoạn: {type(exc).__name__}: {exc}")
                packet = None

        if packet:
            context = packet["context"]
            st.caption(
                f"{len(context['excerpts'])} đoạn được chọn · "
                f"{context['matching_lines']} dòng chứa mã · "
                f"SHA256 gói bằng chứng: {context['context_sha256'][:20]}…"
            )
            if context["context_truncated"]:
                st.warning(
                    "Trích đoạn đã bị giới hạn để kiểm soát chi phí. "
                    "Đây KHÔNG phải kiểm tra toàn bộ hồ sơ."
                )
            for warning in context["warnings"]:
                st.warning(warning)
            st.dataframe([{
                "ID": e["source_id"],
                "Tệp": e["filename"],
                "Trang/Sheet/Dòng": e["locator"],
                "Đúng nguyên văn sẽ gửi": e["text"],
            } for e in context["excerpts"]], use_container_width=True, hide_index=True)
            consent = st.checkbox(
                "Tôi đã xem các đoạn trích, được phép chia sẻ dữ liệu này với Google Gemini "
                "và chấp nhận khả năng phát sinh chi phí API.",
                value=False,
                key=f"tdv_see_pro_ai_approve_{context['context_sha256'][:16]}",
            )
            if st.button(
                "2. Gửi đoạn trích cho Gemini và kiểm chứng nguồn",
                disabled=not consent or context["matching_lines"] == 0,
                key="tdv_see_pro_ai_execute",
            ):
                try:
                    try:
                        key = st.secrets.get("GEMINI_API_KEY", "")
                    except Exception:
                        key = ""
                    key = key or os.getenv("GEMINI_API_KEY", "")
                    if not key:
                        st.error(
                            "Chưa cấu hình GEMINI_API_KEY ở Streamlit Secrets hoặc "
                            "biến môi trường. Không gửi dữ liệu."
                        )
                    else:
                        with st.spinner("Gemini đang đề xuất đối chiếu; Python kiểm tra lại trích dẫn…"):
                            report = review_with_gemini(
                                context, api_key=key, model=model,
                                explicitly_authorized=True,
                            )
                        st.session_state["tdv_see_pro_ai_result"] = {
                            "selection": selection, "model": model, "report": report,
                        }
                except Exception:
                    # Do not echo exception text: provider errors can expose request content.
                    st.error("Lần gọi Gemini chưa hoàn tất. Không ghi nhận kết quả; hãy kiểm tra API/giới hạn và thử lại.")

            stored = st.session_state.get("tdv_see_pro_ai_result")
            if stored and stored["selection"] == selection and stored["model"] == model:
                report = stored["report"]
                st.warning(
                    "Đây là GỢI Ý của AI. 'Trích dẫn khớp' chỉ xác nhận đoạn chữ "
                    "có thật trong nguồn, KHÔNG chứng minh yêu cầu kỹ thuật đã đạt."
                )
                st.caption(report.get("model_note", ""))
                grid = [{
                    "Mã": f["MA_THUOC_HOAC_LO"],
                    "Trường": f["TRUONG"],
                    "Gợi ý AI": f["AI_DE_XUAT"],
                    "Bộ kiểm tra độc lập": f["TRANG_THAI"],
                    "Trích dẫn HSMT": f["CHUNG_CU_YEU_CAU"].get("locator", ""),
                    "Trích dẫn hồ sơ đáp ứng": f["CHUNG_CU_DE_XUAT"].get("locator", ""),
                } for f in report["findings"]]
                if grid:
                    st.dataframe(grid, use_container_width=True, hide_index=True)
                else:
                    st.info("Chưa có đủ cặp chứng cứ để đề xuất đối chiếu cho mã này.")
                for warning in report["warnings"]:
                    st.warning(warning)
                st.download_button(
                    "Tải Excel gợi ý và nguồn chứng cứ (chưa xác minh)",
                    data=export_review_xlsx(report),
                    file_name="SEE_PRO_AI_CAN_DUYET.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="tdv_see_pro_ai_excel",
                )
                st.download_button(
                    "Tải JSON truy xuất nguồn của AI (chưa xác minh)",
                    data=json.dumps(report, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
                    file_name="SEE_PRO_AI_CAN_DUYET.json",
                    mime="application/json",
                    key="tdv_see_pro_ai_json",
                )
