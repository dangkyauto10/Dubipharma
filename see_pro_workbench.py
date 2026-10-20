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
from see_pro_structured import identify_document, parse_excel_lots, reconcile_notice


def analyze_uploads(uploaded: list[tuple[str, bytes]], *, enable_ocr: bool = False) -> dict:
    """Classify before reading. Do not force every PDF to use G1.xxx."""
    result = {"documents": [], "rows": [], "warnings": [],
              "pdf_reports": [], "notices": [], "structured_tables": []}
    for filename, data in uploaded:
        try:
            classification = identify_document(filename, data)
            role = classification["type"]
            source = extract_file(filename, data, ocr=enable_ocr)
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

            if filename.lower().endswith(".xlsx"):
                parsed = parse_excel_lots(filename, data)
                result["structured_tables"].append({
                    "Tệp": filename, "Mã gói BP": parsed["package_id"],
                    "Số lô": parsed["total_lots"], "Nhận diện cấu trúc": parsed["complete"],
                    "Số cảnh báo": len(parsed["issues"]),
                    "Các Sheet": ", ".join(x["sheet"] for x in parsed["sheets"]),
                })
                if not parsed["complete"]:
                    result["warnings"].append(
                        f"{filename}: không nhận diện đầy đủ bảng nghiệp vụ; cần đối chiếu tên cột")
                for issue in parsed["issues"]:
                    result["warnings"].append(f"{filename}: {issue['type']}: {issue}")
                for row in parsed["rows"]:
                    result["rows"].append({
                        **row,
                        "TRANG_VI_TRI": f"{row['SHEET']} – dòng {row['DONG_NGUON']}",
                        "TRICH_DAN": str(row.get("HOAT_CHAT_HSMT") or "")[:350],
                    })
                continue

            if role == "BANG_EHSMT_PDF":
                report = inspect_ehsmt_pdf(data)
                result["pdf_reports"].append({
                    "Tệp": filename, "Số trang": report["total_pages"],
                    "Trang đã đọc": report["pages_processed"],
                    "Mã G1 nhận diện": report["lot_count"],
                    "Dòng tổng hợp": report["summary_rows"],
                    "Chưa tách được": len(report["missing_summary"]),
                    "Mã chưa tách": ", ".join(report["missing_summary"][:20]),
                    "SHA256": report["sha256"],
                })
                result["warnings"].extend(f"{filename}: {w}" for w in report["warnings"])
                for lot in report["lots"]:
                    result["rows"].append({
                        "FILE_NGUON": filename, "MA_GOI_THAU": "",
                        "MA_THUOC": lot["MA_THUOC"],
                        "MA_PHAN_LO": lot.get("MA_PHAN_LO", ""),
                        "HOAT_CHAT_HSMT": lot.get("HOAT_CHAT_CHUAN"),
                        "GIA_UOC_TINH_PHAN": lot.get("GIA_TRI_UOC_TINH"),
                        "TIEN_BAO_DAM_DU_THAU": lot.get("BAO_DAM_DU_THAU"),
                        "TRANG_VI_TRI": lot.get("TRANG_BANG_TONG_HOP"),
                        "TRICH_DAN": lot.get("CHUNG_CU_BANG_TONG_HOP")
                                       or lot.get("TRICH_DOAN", ""),
                        "TRANG_THAI": lot.get("TRANG_THAI", "CAN_XAC_MINH"),
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
            result["warnings"].append(
                f"{filename}: không thể đọc ({type(exc).__name__}: {exc})")
    for notice in result["notices"]:
        bp = notice.get("package_id")
        # Only link tables with the same identified BP; never combine unrelated packages.
        related = [t for t in result["structured_tables"] if t["Mã gói BP"] == bp]
        if not related:
            result["warnings"].append(
                f"{notice['file']}: chưa có bảng phần/lô khớp gói {bp}")
            continue
        expected = (notice.get("evidence", {}).get("SO_PHAN_LO") or {}).get("value")
        if expected and expected.isdigit():
            actual = sum(t["Số lô"] for t in related)
            if int(expected) != actual:
                result["warnings"].append(
                    f"{notice['file']}: số lô thông báo {expected}, bảng khớp {actual}; cần kiểm tra")
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
    b.metric("Mặt hàng / mã ứng viên", len(rows))
    c.metric("Cảnh báo", len(analysis["warnings"]))
    st.warning("Đây là bản trích xuất để đối chiếu, KHÔNG phải kết quả kiểm chứng kỹ thuật, GMP hay giá chào.")
    if not docs.empty:
        st.markdown("**Tệp và nguồn chứng cứ**")
        st.dataframe(docs, hide_index=True, use_container_width=True)
    if analysis.get("structured_tables"):
        st.markdown("**Danh sách phần/lô theo từng mã gói thầu**")
        st.dataframe(pd.DataFrame(analysis["structured_tables"]), hide_index=True, use_container_width=True)
    if analysis.get("notices"):
        st.markdown("**Thông báo mời thầu đã nhận diện**")
        meta = [{"Tệp": notice["file"], "Mã gói BP": notice["package_id"],
                 **{key: info["value"] for key, info in notice["evidence"].items()}}
                for notice in analysis["notices"]]
        st.dataframe(pd.DataFrame(meta), hide_index=True, use_container_width=True)
    if not pdfs.empty:
        st.markdown("**Kiểm kê bảng tổng hợp PDF E-HSMT**")
        st.dataframe(pdfs, hide_index=True, use_container_width=True)
    if not rows.empty:
        evidence_rows = rows.drop(columns=["EVIDENCE", "verified"], errors="ignore")
        term = st.text_input("Tìm theo mã G1, mã PP, hoạt chất hoặc chứng cứ", key="tdv_see_pro_keyword")
        if term.strip():
            mask = evidence_rows.fillna("").astype(str).apply(
                lambda col: col.str.contains(term.strip(), case=False, regex=False)).any(axis=1)
            shown = evidence_rows[mask]
        else:
            shown = evidence_rows
        st.dataframe(shown.fillna(""), hide_index=True, use_container_width=True)
        st.download_button("Tải bảng kiểm kê CSV (chưa xác minh)",
                           data=evidence_rows.fillna("").to_csv(index=False).encode("utf-8-sig"),
                           file_name="TDV_SEE_PRO_KIEM_KE.csv", mime="text/csv",
                           key="tdv_see_pro_csv")
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            evidence_rows.fillna("").to_excel(writer, sheet_name="DANH_MUC_UNG_VIEN", index=False)
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
        data=json.dumps(analysis, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name="TDV_SEE_PRO_AUDIT.json", mime="application/json",
        key="tdv_see_pro_json")
