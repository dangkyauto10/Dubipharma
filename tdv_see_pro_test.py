"""SEE PRO isolated test entrypoint; not a Preview deployment.

Run: streamlit run tdv_see_pro_test.py
No remote APIs or Drive writes. Reads uploaded E-HSMT in memory.
"""
from __future__ import annotations
from io import BytesIO
import hashlib
import json
import pandas as pd
import streamlit as st
from tdv_ehsmt_xlsx import inspect_ehsmt_document

st.set_page_config(page_title="TDV QC7 SEE PRO · Kiểm thử độc lập", layout="wide")
st.title("SEE PRO · Kiểm thử E-HSMT gốc")
st.caption("NHÁNH THỬ NGHIỆM RIÊNG • không tác động main, Preview hoặc Google Drive.")
st.warning("Chỉ trích xuất chứng cứ sơ bộ; chưa chấm kỹ thuật, GMP, số đăng ký hay giá.")
upload = st.file_uploader(
    "Tải E-HSMT PDF hoặc Excel XLSX để hệ thống tự đọc và tự phân loại",
    type=["pdf", "xlsx"], accept_multiple_files=False,
)
if upload is None:
    st.info("Chọn duy nhất tệp gốc, hệ thống tự nhận định dạng và kiểm tra; không nhập từng mã thuốc.")
    st.stop()
data = upload.getvalue()
@st.cache_data(show_spinner=False, max_entries=2)
def analyze(content: bytes):
    return inspect_ehsmt_document(content)
try:
    with st.spinner("Đọc toàn bộ tài liệu, kiểm kê mã thuốc và lập chứng cứ..."):
        result = analyze(data)
except (ValueError, OSError, RuntimeError) as exc:
    st.error(f"Không đọc được hồ sơ: {exc}")
    st.stop()
a, b, c = st.columns(3)
a.metric("Mã thuốc tìm được", result["lot_count"])
b.metric("Dòng tổng hợp rõ", result["summary_rows"])
c.metric("Mã chưa đủ chứng cứ", len(result["missing_summary"]))
st.caption("SHA-256: " + result["sha256"])
for warning in result["warnings"]:
    st.warning(warning)
if result.get("complete_read") is False or result.get("pages_without_text"):
    st.error("Hồ sơ chưa đọc đủ; không được kết luận hồ sơ hoàn chỉnh.")
st.info(result["note"])

rows = []
for item in result["lots"]:
    source = item.get("EVIDENCE") or {}
    cell_refs = item.get("VI_TRI_THAM_CHIEU") or item.get("TRANG_NGUON") or []
    rows.append({
        "Mã thuốc": item["MA_THUOC"],
        "Mã phần": item.get("MA_PHAN_LO", ""),
        "Hoạt chất": item.get("HOAT_CHAT_CHUAN", ""),
        "Giá trị ước tính": item.get("GIA_TRI_UOC_TINH"),
        "Bảo đảm dự thầu": item.get("BAO_DAM_DU_THAU"),
        "Nguồn": f"{source.get('sheet', '')} dòng {source.get('row', '')}" if source else
                 f"Trang {item.get('TRANG_BANG_TONG_HOP','')}",
        "Vị trí mã": json.dumps(cell_refs, ensure_ascii=False),
        "Tình trạng": item.get("TRANG_THAI", ""),
    })
frame = pd.DataFrame(rows)
keyword = st.text_input("Lọc mã thuốc, mã phần hoặc hoạt chất", "")
if keyword and not frame.empty:
    frame = frame[frame.astype(str).apply(
        lambda col: col.str.contains(keyword, case=False, regex=False)).any(axis=1)]
st.dataframe(frame, hide_index=True, use_container_width=True)

def prevent_excel_formula(v):
    return "'" + v if isinstance(v, str) and v[:1] in ("=", "+", "-", "@") else v

out = BytesIO()
with pd.ExcelWriter(out, engine="openpyxl") as writer:
    if rows:
        pd.DataFrame(rows).map(prevent_excel_formula).to_excel(writer,
            index=False, sheet_name="DANH_MUC")
    else:
        pd.DataFrame(columns=["Mã thuốc"]).to_excel(writer,
            index=False, sheet_name="DANH_MUC")
    evidence = []
    for item in result["lots"]:
        e = item.get("EVIDENCE") or {}
        for cell in e.get("cells", []):
            evidence.append({"MA_THUOC": item["MA_THUOC"], "Sheet": e.get("sheet"),
                "Dòng": e.get("row"), "Cột": cell["column"], "Raw": cell["raw"],
                "SHA256": result["sha256"]})
    pd.DataFrame(evidence).map(prevent_excel_formula).to_excel(
        writer, index=False, sheet_name="CHUNG_CU")
    pd.DataFrame({"CAN_KIEM_TRA": result["missing_summary"]}).to_excel(
        writer, index=False, sheet_name="CANH_BAO")
    pd.DataFrame([{"SHA256": result["sha256"], "So_ma": result["lot_count"],
       "So_dong": result["summary_rows"], "Da_xac_minh": False}]).to_excel(
       writer, index=False, sheet_name="TONG_KET")
c1, c2 = st.columns(2)
c1.download_button("Tải Excel kiểm toán và chứng cứ", out.getvalue(),
    file_name="SEE_PRO_KIEM_TOAN_CHUA_XAC_MINH.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
c2.download_button("Tải JSON kiểm toán", json.dumps(
    result, ensure_ascii=False, indent=2).encode("utf-8"),
    file_name="SEE_PRO_KIEM_TOAN_CHUA_XAC_MINH.json", mime="application/json")
