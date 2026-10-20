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


def analyze_uploads(uploaded: list[tuple[str, bytes]], *, enable_ocr: bool = False) -> dict:
    """Keep original files in memory only while running. Return derived data."""
    result = {"documents": [], "rows": [], "warnings": [], "pdf_reports": []}
    for name, content in uploaded:
        try:
            doc = extract_file(name, content, ocr=enable_ocr)
            result["documents"].append({
                "Tệp": name, "Loại": doc["type"].upper(),
                "Đoạn/dòng đọc": len(doc["lines"]), "Số trang": doc["pages"],
                "Đọc toàn bộ": doc["complete"], "SHA256": doc["sha256"],
                "Xác minh": "CHƯA",
            })
            result["warnings"].extend(f"{name}: {w}" for w in doc["warnings"])
            if name.lower().endswith(".pdf"):
                report = inspect_ehsmt_pdf(content)
                result["pdf_reports"].append({
                    "Tệp": name,
                    "Số trang": report["total_pages"],
                    "Trang đã đọc": report["pages_processed"],
                    "Mã G1 nhận diện": report["lot_count"],
                    "Dòng tổng hợp": report["summary_rows"],
                    "Chưa tách được": len(report["missing_summary"]),
                    "Mã chưa tách": ", ".join(report["missing_summary"][:20]),
                    "SHA256": report["sha256"],
                })
                result["warnings"].extend(f"{name}: {w}" for w in report["warnings"])
                for row in report["lots"]:
                    result["rows"].append({
                        "FILE_NGUON": name, "MA_THUOC": row["MA_THUOC"],
                        "MA_PHAN_LO": row.get("MA_PHAN_LO", ""),
                        "HOAT_CHAT_HSMT": row.get("HOAT_CHAT_CHUAN"),
                        "GIA_UOC_TINH_PHAN": row.get("GIA_TRI_UOC_TINH"),
                        "TIEN_BAO_DAM_DU_THAU": row.get("BAO_DAM_DU_THAU"),
                        "TRANG_VI_TRI": row.get("TRANG_BANG_TONG_HOP"),
                        "TRICH_DAN": row.get("CHUNG_CU_BANG_TONG_HOP")
                                    or row.get("TRICH_DOAN", ""),
                        "TRANG_THAI": row.get("TRANG_THAI", "CAN_XAC_MINH"),
                    })
            else:
                for row in identify_codes(doc):
                    result["rows"].append({
                        "FILE_NGUON": name, "MA_THUOC": row["Mã lô"],
                        "MA_PHAN_LO": "", "HOAT_CHAT_HSMT": None,
                        "GIA_UOC_TINH_PHAN": None, "TIEN_BAO_DAM_DU_THAU": None,
                        "TRANG_VI_TRI": row["Nguồn"], "TRICH_DAN": row["Trích dẫn"],
                        "TRANG_THAI": "CAN_XAC_MINH_TRUONG_DU_LIEU",
                    })
        except (ValueError, RuntimeError, OSError, ImportError) as exc:
            result["warnings"].append(f"{name}: không thể xử lý ({type(exc).__name__}: {exc})")
    return result


def render_ehsmt_workbench() -> None:
    st.markdown("### E-HSMT · SEE PRO – Tiếp nhận, đọc và kiểm toán hồ sơ")
    st.caption("Một luồng cho PDF, Word, Excel, CSV và ảnh. Dữ liệu đọc được là sơ bộ, có chứng cứ; không tự duyệt thầu.")
    files = st.file_uploader(
        "Tải một hoặc nhiều tài liệu E-HSMT / hồ sơ thuốc / GMP / báo giá",
        type=list(ACCEPTED), accept_multiple_files=True, key="tdv_see_pro_documents")
    ocr = st.checkbox(
        "Bật OCR cục bộ cho ảnh và trang PDF không có chữ (cần kiểm tra lại nguồn)",
        value=False, key="tdv_see_pro_ocr")
    if files:
        digest = hashlib.sha256()
        for f in files:
            digest.update(f.name.encode("utf-8"))
            digest.update(f.getvalue())
        digest.update(str(ocr).encode())
        signature = digest.hexdigest()
        if st.session_state.get("tdv_see_pro_signature") != signature:
            st.session_state.pop("tdv_see_pro_analysis", None)
        if st.button("Đọc và kiểm toán bộ hồ sơ", key="tdv_see_pro_execute", type="primary"):
            with st.spinner("Đang đọc tài liệu và lập danh mục chứng cứ..."):
                result = analyze_uploads(
                    [(f.name, f.getvalue()) for f in files], enable_ocr=ocr)
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
    b.metric("Mã G1 / bản ghi ứng viên", len(rows))
    c.metric("Cảnh báo", len(analysis["warnings"]))
    st.warning("Đây là bản trích xuất để đối chiếu, KHÔNG phải kết quả kiểm chứng kỹ thuật, GMP hay giá chào.")
    if not docs.empty:
        st.markdown("**Tệp và nguồn chứng cứ**")
        st.dataframe(docs, hide_index=True, use_container_width=True)
    if not pdfs.empty:
        st.markdown("**Kiểm kê bảng tổng hợp PDF E-HSMT**")
        st.dataframe(pdfs, hide_index=True, use_container_width=True)
    if not rows.empty:
        term = st.text_input("Tìm theo mã G1, mã PP, hoạt chất hoặc chứng cứ", key="tdv_see_pro_keyword")
        if term.strip():
            mask = rows.fillna("").astype(str).apply(
                lambda col: col.str.contains(term.strip(), case=False, regex=False)).any(axis=1)
            shown = rows[mask]
        else:
            shown = rows
        st.dataframe(shown.fillna(""), hide_index=True, use_container_width=True)
        st.download_button("Tải bảng kiểm kê CSV (chưa xác minh)",
                           data=rows.fillna("").to_csv(index=False).encode("utf-8-sig"),
                           file_name="TDV_SEE_PRO_KIEM_KE.csv", mime="text/csv",
                           key="tdv_see_pro_csv")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            rows.fillna("").to_excel(writer, sheet_name="DANH_MUC_UNG_VIEN", index=False)
            docs.fillna("").to_excel(writer, sheet_name="NGUON_TAI_LIEU", index=False)
            pd.DataFrame({"CANH_BAO": analysis["warnings"]}).to_excel(
                writer, sheet_name="CANH_BAO", index=False)
        st.download_button("Tải Excel kiểm toán sơ bộ", data=output.getvalue(),
                           file_name="TDV_SEE_PRO_KIEM_TOAN.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           key="tdv_see_pro_excel")
    if analysis["warnings"]:
        with st.expander(f"Cảnh báo và dòng cần xem lại ({len(analysis['warnings'])})"):
            for warning in analysis["warnings"][:150]:
                st.warning(warning)
    st.download_button(
        "Tải báo cáo JSON (chưa xác minh)",
        data=json.dumps(analysis, ensure_ascii=False, indent=2).encode("utf-8"),
        file_name="TDV_SEE_PRO_AUDIT.json", mime="application/json",
        key="tdv_see_pro_json")
