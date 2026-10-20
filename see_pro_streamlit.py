"""SEE PRO preview: evidence-first read-only Streamlit integration.

Uses the existing E-HSMT reader. Never creates bid prices, compliance decisions
or writes to external services. Completeness is not extraction accuracy.
"""
from __future__ import annotations
import io
import json
import pandas as pd
import streamlit as st
from tdv_ehsmt_intake import inspect_ehsmt_pdf
from see_pro_core import Evidence, FieldValue, SeeLot, validate_lots

def audit_result(result: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    records = []
    lots = []
    for item in result.get("lots", []):
        code = item["MA_THUOC"]
        part = item.get("MA_PHAN_LO") or ""
        page = item.get("TRANG_BANG_TONG_HOP")
        excerpt = item.get("CHUNG_CU_BANG_TONG_HOP", "")
        evidence = [Evidence("E-HSMT PDF", int(page), "Bảng tổng hợp", excerpt)] if page and excerpt else []
        fields = {}
        for source, target in [
            ("HOAT_CHAT_CHUAN", "HOAT_CHAT_HSMT"),
            ("GIA_TRI_UOC_TINH", "GIA_UOC_TINH_PHAN"),
            ("BAO_DAM_DU_THAU", "TIEN_BAO_DAM_DU_THAU"),
        ]:
            value = item.get(source)
            if value is not None and value != "":
                fields[target] = FieldValue(value, evidence, False)
        lots.append(SeeLot(part, code, fields))
        records.append({
            "MA_THUOC": code, "MA_PHAN_LO": part,
            "HOAT_CHAT_HSMT": item.get("HOAT_CHAT_CHUAN"),
            "GIA_UOC_TINH_PHAN": item.get("GIA_TRI_UOC_TINH"),
            "TIEN_BAO_DAM_DU_THAU": item.get("BAO_DAM_DU_THAU"),
            "TRANG_BANG_TONG_HOP": page,
            "CHUNG_CU_BANG_TONG_HOP": excerpt,
            "TRANG_THAI": item.get("TRANG_THAI"),
            "NONG_DO_HAM_LUONG": None, "DUONG_DUNG": None,
            "DANG_BAO_CHE": None, "DON_VI_TINH": None,
            "NHOM_THUOC": None, "SO_LUONG_CHINH": None,
            "DON_GIA_KE_HOACH": None,
        })
    report = validate_lots(lots)
    return pd.DataFrame(records), pd.DataFrame(report["findings"]), report

def render_see_pro() -> None:
    st.markdown("### SEE PRO · Kiểm thử tích hợp")
    st.caption("Bản Preview độc lập về dữ liệu, dùng chung TDV QC7 ONLINE. Chưa tự xác minh kỹ thuật, pháp lý hoặc giá dự thầu.")
    upload = st.file_uploader("Tải E-HSMT PDF (tối đa 40 MB / 1.200 trang)", type=["pdf"], key="see_pro_upload")
    if upload is None:
        st.info("Chọn PDF để bắt đầu. Hệ thống chỉ đọc, không gửi hồ sơ ra dịch vụ ngoài.")
        return
    import hashlib
    data = upload.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    if st.session_state.get("see_pro_sha") != digest:
        st.session_state.pop("see_pro_result", None)
    if st.button("Chạy SEE PRO – đọc và kiểm toán", key="see_pro_run", type="primary"):
        try:
            with st.spinner("Đang đọc và lập bảng chứng cứ..."):
                result = inspect_ehsmt_pdf(data)
            st.session_state["see_pro_result"] = result
            st.session_state["see_pro_sha"] = digest
        except (ValueError, RuntimeError, OSError) as exc:
            st.error(f"Không đọc được hồ sơ: {exc}")
    result = st.session_state.get("see_pro_result")
    if not result or st.session_state.get("see_pro_sha") != digest:
        return
    df, findings, report = audit_result(result)
    a,b,c,d = st.columns(4)
    a.metric("Trang xử lý", f"{result['pages_processed']}/{result['total_pages']}")
    b.metric("Mã thuốc nhận diện", len(df))
    c.metric("Dòng tổng hợp rõ", result["summary_rows"])
    d.metric("Bản ghi xác minh đầy đủ", report["fully_verified_lots"])
    st.warning("Các số liệu trên đo độ bao phủ trích xuất, KHÔNG chứng minh độ chính xác của bảng kỹ thuật.")
    for warning in result.get("warnings", []):
        st.warning(warning)
    if result.get("missing_summary"):
        st.error("Cần kiểm tra bảng tổng hợp: " + ", ".join(result["missing_summary"][:25]))
    keyword = st.text_input("Tra mã G1.xxx, PP hoặc hoạt chất", key="see_pro_search").strip().lower()
    shown = df
    if keyword:
        mask = df.fillna("").astype(str).apply(lambda row: keyword in " ".join(row).lower(), axis=1)
        shown = df[mask]
    st.dataframe(shown.fillna(""), use_container_width=True, hide_index=True)
    with st.expander(f"Cảnh báo kiểm toán ({len(findings)})"):
        st.dataframe(findings, use_container_width=True, hide_index=True)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.fillna("").to_excel(writer, sheet_name="SEE_PRO_EHSMT", index=False)
        findings.to_excel(writer, sheet_name="CANH_BAO", index=False)
        pd.DataFrame([{
            "TRANG": result["total_pages"], "MA_NHAN_DIEN": len(df),
            "DONG_TONG_HOP": result["summary_rows"],
            "DA_XAC_MINH": report["fully_verified_lots"],
            "SHA256": result["sha256"],
        }]).to_excel(writer, sheet_name="KIEM_DINH", index=False)
    st.download_button("Tải Excel SEE PRO – dữ liệu và cảnh báo", data=output.getvalue(),
                       file_name="SEE_PRO_PREVIEW_AUDIT.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="see_pro_download")
