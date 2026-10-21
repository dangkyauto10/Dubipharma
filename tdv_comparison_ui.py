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
    d.metric("Khớp sơ bộ / tiêu chí có nguồn", f"{ratio:.1f}%" if ratio is not None else "N/A")
    if not s["lots_uniquely_linked"]:
        st.warning(
            "Chưa có mã E-HSMT nào gắn duy nhất với một sản phẩm NSX "
            "có nguồn chứng cứ. Chưa có mẫu số so sánh hợp lệ; "
            "N/A không phải 0% đáp ứng."
        )
    st.caption(f'Đã phát hiện {s["ehsmt_lots"]} mã E-HSMT · '
               f'{s["nsx_products"]} dòng sản phẩm NSX · '
               f'{s["criteria_ehsmt_available"]} tiêu chí E-HSMT đã đọc được · '
               f'{s["linked_requirements"]} tiêu chí thuộc các cặp thuốc có '
               'đủ nguồn để đối chiếu sơ bộ.')
    if s.get("lots_with_title_hints"):
        st.info(
            f'Có {s["lots_with_title_hints"]} mã E-HSMT có gợi ý từ tên thuốc NSX. '
            'Đây là tìm kiếm văn bản, KHÔNG chứng minh hoạt chất, '
            'KHÔNG tính là liên kết hoặc tiêu chí đạt.'
        )
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
            "Gợi ý từ tên thuốc":r.get("SO_GOI_Y_TEN_NSX",0),
            "Tên NSX":r["TEN_THUOC_NSX"],
            "Mã / SĐK":r["SO_DANG_KY"],
            "Khớp":r["SO_TIEU_CHI_DAT"],
            "Chưa đủ":r["SO_TIEU_CHI_CHUA_DAT"],
            "Không khớp":r["SO_TIEU_CHI_KHONG_KHOP"],
            "Yêu cầu E-HSMT đọc được / 4":f'{r.get("SO_TIEU_CHI_EHSMT_DOC_DUOC",0)}/4',
            "% khớp của yêu cầu đọc được":r["TY_LE_KHOP_SO_BO"],
            "Kết quả":r["TRANG_THAI_DOI_CHIEU"],
        })
    if display:
        frame=pd.DataFrame(display)
        st.dataframe(frame,hide_index=True,use_container_width=True,
                     column_config={"% khớp của yêu cầu đọc được":st.column_config.ProgressColumn(
                        "% khớp của yêu cầu đọc được",min_value=0,max_value=100,format="%.1f%%")})
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
    field_rows = [{
        "Tiêu chí": f["label"],
        "E-HSMT — yêu cầu gốc": f["ehsmt"] or "CHƯA ĐỌC ĐƯỢC",
        "NSX — nội dung chứng cứ": f["nsx"] or "CHƯA CÓ",
        "Kết quả": PALETTE[f["status"]][2],
    } for f in r["criteria"]]
    if field_rows:
        frame = pd.DataFrame(field_rows)
        states = [f["status"] for f in r["criteria"]]
        def style(row):
            fg, bg, _ = PALETTE[states[row.name]]
            return [f"background-color:{bg};color:{fg};font-weight:600"] * len(row)
        st.dataframe(frame.style.apply(style, axis=1),
                     hide_index=True, use_container_width=True)
    if r.get("GOI_Y_TEN_NSX"):
        st.warning(
            "Gợi ý tên thuốc tương tự hoạt chất E-HSMT — CHƯA PHẢI KẾT QUẢ "
            "SO SÁNH. Cần chứng cứ hoạt chất/SĐK gắn đích danh; "
            "không được tự tô xanh hoặc gán sản phẩm."
        )
        st.dataframe([{
            "Mã NSX": item["product_id"],
            "Tên thuốc trong nguồn": item["product_name"],
            "Tệp nguồn": item["source_file"],
            "Dòng nguồn": item["source_location"],
            "Trạng thái": "GỢI Ý VĂN BẢN — CHƯA XÁC MINH",
        } for item in r["GOI_Y_TEN_NSX"]],
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
    from tdv_review_priorities import build_review_priorities
    priority = build_review_priorities(report, max_rows=250)
    st.markdown("**Bảng công việc ưu tiên theo chứng cứ**")
    st.caption(priority["note"])
    levels = priority["by_priority"]
    a1, a2, a3 = st.columns(3)
    a1.metric("Mức 1 · chênh lệch/mâu thuẫn", levels["1"])
    a2.metric("Mức 2 · chứng cứ cần đối chiếu", levels["2"])
    a3.metric("Mức 3 · thiếu ứng viên", levels["3"])
    chosen_priority = st.selectbox(
        "Xem theo mức xử lý",
        ["Tất cả", "1", "2", "3"],
        format_func=lambda x: "Tất cả" if x=="Tất cả" else f"Mức {x}",
        key="tdv_leadership_priority_filter",
    )
    issues = [
        issue for issue in priority["rows"]
        if chosen_priority == "Tất cả" or
        str(issue["muc_uu_tien"]) == chosen_priority
    ]
    if issues:
        st.dataframe(pd.DataFrame([{
            "Ưu tiên": issue["muc_uu_tien"],
            "Nhóm": issue["van_de"], "Mã / nhà máy": issue["ma"],
            "Chi tiết": issue["chi_tiet"],
            "Tệp nguồn": issue["tai_lieu"],
            "Trang/dòng": issue["vi_tri_nguon"],
            "Cần làm": issue["viec_can_lam"],
            "Tình trạng": "CHƯA XÁC MINH",
        } for issue in issues[:100]]), hide_index=True, use_container_width=True)
    else:
        st.info("Chưa phát hiện vấn đề thuộc mức đã lọc trong các dòng đang hiển thị.")
    if priority["truncated"]:
        st.warning(
            f'Đã tổng hợp {priority["total_issues"]} vấn đề; màn hình chỉ '
            f'giữ {priority["shown_issues"]} mục đầu. '
            'Để xuất toàn bộ, dùng Excel báo cáo ở cuối trang.'
        )
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
