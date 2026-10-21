"""Real E-HSMT↔NSX decision-support UI in the existing TDV QC7 Streamlit app.

Displays BOTH sides, provisional 3-state criterion comparison, original page /
row references and per-source SHA. No external writes or impersonated approvals.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from tdv_leadership_report import (
    compare_sources, export_leadership_xlsx, export_leadership_docx,
    GREEN, YELLOW, RED,
)

PALETTE = {
    GREEN: ("#176b41", "#e7f7ed", "🟢 KHỚP SƠ BỘ"),
    YELLOW: ("#90620c", "#fff4d5", "🟡 CHƯA ĐỦ CĂN CỨ"),
    RED: ("#af3030", "#fde9e9", "🔴 CHƯA KHỚP"),
}


def _live_report():
    tender = st.session_state.get("tdv_see_pro_analysis")
    supplier = st.session_state.get("tdv_nsx_auto_report")
    return tender, supplier, compare_sources(tender, supplier)


def _summary(report):
    s=report["summary"]
    a,b,c,d=st.columns(4)
    a.metric("Tiêu chí khớp sơ bộ",s["green_criteria_preliminary"])
    b.metric("Tiêu chí chưa đủ căn cứ",s["yellow_criteria"])
    c.metric("Tiêu chí không khớp",s["red_mismatch_preliminary"])
    ratio = s["matching_percent_preliminary"]
    d.metric("Tỷ lệ khớp sơ bộ (%)", f"{ratio:.1f}%" if ratio is not None else "N/A")
    if not s["lots_uniquely_linked"]:
        st.warning(
            "Chưa có mã E-HSMT nào gắn duy nhất với một sản phẩm NSX "
            "có nguồn chứng cứ. Chưa có mẫu số so sánh hợp lệ; "
            "N/A không phải 0% đáp ứng."
        )
    st.caption(f'Đã phát hiện {s["ehsmt_lots"]} mã E-HSMT · '
               f'{s["nsx_products"]} sản phẩm NSX · '
               f'{s["criteria_ehsmt_available"]}/{s["total_criteria"]} '
               'tiêu chí có yêu cầu đọc được từ E-HSMT.')
    st.warning(report["note"])
    st.error(
        "KHÔNG kết luận ĐỦ ĐIỀU KIỆN DỰ THẦU từ tỷ lệ %. "
        "Mọi thông số và điều kiện bắt buộc vẫn cần kiểm tra nguồn gốc/hiệu lực."
    )


def _records(report):
    display=[]
    for r in report["comparison"]:
        display.append({
            "Mã E-HSMT":r["MA_THUOC_EHSMT"],
            "Hoạt chất (chuẩn E-HSMT)":r["HOAT_CHAT_EHSMT"],
            "Hàm lượng (chuẩn E-HSMT)":r["HAM_LUONG_EHSMT"],
            "Số ứng viên NSX":r["SO_UNG_VIEN_NSX"],
            "Tên NSX":r["TEN_THUOC_NSX"],
            "Mã / SĐK":r["SO_DANG_KY"],
            "Khớp":r["SO_TIEU_CHI_DAT"],
            "Chưa đủ":r["SO_TIEU_CHI_CHUA_DAT"],
            "Không khớp":r["SO_TIEU_CHI_KHONG_KHOP"],
            "% sơ bộ":r["TY_LE_KHOP_SO_BO"],
            "Kết quả":r["TRANG_THAI_DOI_CHIEU"],
        })
    if display:
        frame=pd.DataFrame(display)
        st.dataframe(frame,hide_index=True,use_container_width=True,
                     column_config={"% sơ bộ":st.column_config.ProgressColumn(
                        "% sơ bộ",min_value=0,max_value=100,format="%.1f%%")})
    else:
        st.info("Chưa có mã E-HSMT đủ định danh để lập bảng so sánh.")


def _source_text(ev):
    if not ev or not ev.get("file"):
        return "Chưa có chứng cứ gốc đủ rõ"
    text=f'{ev.get("file","")} · {ev.get("location","")}'
    if ev.get("sha256"):
        text+=f' · SHA256: {ev["sha256"]}'
    return text


def _criteria(r):
    st.markdown("**Hai nội dung gốc theo từng tiêu chí (E-HSMT ← NSX)**")
    frame=pd.DataFrame([
        {
            "Tiêu chí":f["label"],
            "E-HSMT — yêu cầu gốc":f["ehsmt"] or "CHƯA ĐỌC ĐƯỢC",
            "NSX — nội dung chứng cứ":f["nsx"] or "CHƯA CÓ",
            "Kết quả":PALETTE[f["status"]][2],
            "_code":f["status"],
        } for f in r["criteria"]
    ])
    if not frame.empty:
        def style(row):
            fg,bg,_=PALETTE[row["_code"]]
            return [f"background-color:{bg};color:{fg};font-weight:600"]*len(row)
        st.dataframe(frame.style.apply(style,axis=1).hide(axis="columns",subset=["_code"]),
                     hide_index=True,use_container_width=True)
    with st.expander("Kiểm tra chứng cứ gốc của cả hai phía",expanded=True):
        for f in r["criteria"]:
            st.markdown(f'**{f["label"]} — {PALETTE[f["status"]][2]}**')
            left,right=st.columns(2)
            with left:
                st.caption("E-HSMT · chuẩn bắt buộc khi xác minh")
                st.write(f["ehsmt"] or "CHƯA ĐỌC ĐƯỢC")
                st.caption(_source_text(f["ehsmt_evidence"]))
                if f["ehsmt_evidence"].get("raw"):
                    st.code(str(f["ehsmt_evidence"]["raw"])[:700],language=None)
            with right:
                st.caption("Tài liệu NSX · nguồn đối chiếu")
                st.write(f["nsx"] or "CHƯA CÓ")
                st.caption(_source_text(f["nsx_evidence"]))
                if f["nsx_evidence"].get("raw"):
                    st.code(str(f["nsx_evidence"]["raw"])[:700],language=None)
            st.caption(f["note"])
    st.info(
        "Hiệu chỉnh/phê duyệt của Lãnh đạo CHƯA KÍCH HOẠT: "
        "Preview chưa có đăng nhập phân quyền xác thực và nhật ký duyệt bất biến. "
        "Không cho sửa dữ liệu gốc hoặc nâng trạng thái xanh thủ công."
    )


def render_comparison_view():
    st.markdown("### ⚖️ SO SÁNH E-HSMT ↔ NSX · Hai nguồn chứng cứ")
    t,n,report=_live_report()
    if not t or not n:
        st.warning(
            "Chưa có đủ HAI bộ dữ liệu thật trong phiên. "
            "Vào E-HSMT tải/đọc hồ sơ gốc, rồi vào Hồ sơ NSX nạp cả bộ "
            "và bấm đọc. Không dùng dữ liệu DEMO để tính tỷ lệ."
        )
        st.write("E-HSMT:", "ĐÃ CÓ" if t else "CHƯA CÓ")
        st.write("Hồ sơ NSX:", "ĐÃ CÓ" if n else "CHƯA CÓ")
        return
    _summary(report)
    _records(report)
    records=report["comparison"]
    if records:
        names=[f'{r["MA_THUOC_EHSMT"]} — {r["HOAT_CHAT_EHSMT"]}'
               for r in records]
        selected=st.selectbox("Xem chứng cứ đối chiếu theo mã E-HSMT",
                              range(len(records)),format_func=lambda i:names[i],
                              key="tdv_comparison_review_code")
        _criteria(records[selected])


def render_leadership_view():
    st.markdown("### 📊 Báo cáo Lãnh đạo · E-HSMT làm chuẩn đối chiếu")
    t,n,report=_live_report()
    if not t or not n:
        st.warning("Chưa đủ E-HSMT và NSX đã đọc từ tài liệu thật; KHÔNG tạo báo cáo giả.")
        return
    _summary(report)
    _records(report)
    st.markdown("**Các trường hợp cần ưu tiên rà soát**")
    at_risk=[r for r in report["comparison"]
             if r["SO_TIEU_CHI_KHONG_KHOP"] or r["SO_TIEU_CHI_CHUA_DAT"]]
    st.caption(f'{len(at_risk)} / {len(report["comparison"])} mã còn ít nhất một tiêu chí chưa thể xác nhận.')
    if at_risk:
        st.dataframe(pd.DataFrame([{
            "Mã":r["MA_THUOC_EHSMT"],"Hoạt chất":r["HOAT_CHAT_EHSMT"],
            "Không khớp":r["SO_TIEU_CHI_KHONG_KHOP"],
            "Chưa đủ":r["SO_TIEU_CHI_CHUA_DAT"],
            "Vị trí chứng cứ":r["VI_TRI_EHSMT"],
            "Lý do":r["TRANG_THAI_DOI_CHIEU"],
        } for r in at_risk[:1000]]),hide_index=True,use_container_width=True)
    st.download_button("Tải Excel đối chiếu và chứng cứ (sơ bộ)",
                       export_leadership_xlsx(report),
                       file_name="TDV_BAO_CAO_DOI_CHIEU_SO_BO.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="tdv_real_report_excel")
    st.download_button("Tải báo cáo Lãnh đạo Word (sơ bộ)",
                       export_leadership_docx(report),
                       file_name="TDV_BAO_CAO_LANH_DAO_SO_BO.docx",
                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                       key="tdv_real_report_word")
    st.caption("Báo cáo sơ bộ trong bộ nhớ phiên, không lưu chứng cứ lên Drive hay GitHub.")
