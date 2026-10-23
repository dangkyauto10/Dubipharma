"""Real E-HSMT↔NSX decision-support UI in the existing TDV QC7 Streamlit app.

Displays BOTH sides, provisional 3-state criterion comparison, original page /
row references and per-source SHA. No external writes or impersonated approvals.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from see_pro_quality_gate import audit_comparison
from tdv_see_pro_scope import check_scope
from tdv_see_pro_leadership import build_register, export_xlsx, DAT, CHUA, KHONG, CHO
from tdv_readable_tables import render_readable_table
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
    ok, reason = check_scope(st.session_state.get("tdv_see_pro_active_scope"), tender, supplier)
    if not ok:
        return tender, supplier, {"blocked": True, "block_reason": reason}
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
    check = audit_comparison(report)
    if check["issue_count"]:
        st.error(
            f'SEE PRO phát hiện {check["issue_count"]} tiêu chí đang xanh sơ bộ '
            'nhưng chưa có đủ dấu vết trích dẫn ở cả hai phía. '
            'Không được dùng các dòng này để xác nhận đáp ứng.'
        )
        with st.expander("Kiểm toán dấu vết kết quả xanh sơ bộ"):
            st.dataframe(pd.DataFrame(check["issues"][:150]),
                         hide_index=True,use_container_width=True)
    st.caption("99,9999% là MỤC TIÊU kiểm thử độc lập, không phải tỷ lệ chính xác đã đạt.")
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
    if report.get("blocked"):
        st.error("ĐÃ CHẶN ĐỐI CHIẾU: " + report["block_reason"])
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



def _leader_by_product(report):
    """Project-scoped triage: one E-HSMT lot per row, reasons on click."""
    register = build_register(report, scope_ok=True)
    st.markdown("#### Kết quả từng mặt hàng E-HSMT và sản phẩm NSX")
    st.caption("ĐẠT/CHƯA ĐẠT/KHÔNG ĐẠT chỉ được kết luận từ chứng cứ đã xác minh. "
               "SEE PRO hiện chưa có người duyệt pháp lý; kết quả trích xuất sơ bộ "
               "được ghi CHƯA ĐẠT — CHƯA ĐỦ CĂN CỨ.")
    counts = register["summary"]
    x,y,z,wait,total = st.columns(5)
    x.metric("Đạt đã xác minh", counts[DAT])
    y.metric("Chưa đạt / cần xác minh", counts[CHUA])
    z.metric("Không đạt đã xác minh", counts[KHONG])
    wait.metric("Chờ ghép NSX", counts[CHO])
    total.metric("Mã E-HSMT", register["total"])
    group = st.selectbox("Lọc danh sách theo kết quả",
                         ["TẤT CẢ", DAT, CHUA, KHONG, CHO], key="tdv_leader_result_filter")
    selected_rows = [r for r in register["rows"]
                     if group=="TẤT CẢ" or r["trang_thai"]==group]
    if selected_rows:
        frame = pd.DataFrame([{
            "Mã E-HSMT": r["ma_ehsmt"], "Mã NSX":r["ma_nsx"],
            "Sản phẩm NSX":r["ten_nsx"],"Kết quả":r["trang_thai"],
            "Nguyên nhân / cần làm":r["nguyen_nhan"],
            "Khớp sơ bộ":r["khop_so_bo"],"Thiếu":r["thieu_chung_cu"],
            "Không khớp sơ bộ":r["khac_so_bo"],
        } for r in selected_rows])
        render_readable_table(st,frame,key="tdv_leader_drug_list",
                              label="Danh sách thuốc theo kết quả",
                              page_size=25,min_width=1250)
        chosen = st.selectbox("Chọn mã thuốc để xem lý do và chứng cứ",
                              range(len(selected_rows)),
                              format_func=lambda i: selected_rows[i]["ma_ehsmt"]+
                                  " / "+(selected_rows[i]["ten_nsx"] or "chưa gắn NSX"),
                              key="tdv_leader_select_drug")
        drug=selected_rows[chosen]
        st.warning("Kết quả: "+drug["trang_thai"]+" · "+drug["nguyen_nhan"])
        evidence = [c for c in register["criteria"] if c["ma_ehsmt"]==drug["ma_ehsmt"]]
        for c in evidence:
            with st.expander(c["tieu_chi"]+" · "+c["trang_thai_so_bo"]):
                left,right=st.columns(2)
                with left:
                    st.markdown("**E-HSMT — yêu cầu**")
                    st.write(c["ehsmt"] or "Chưa đọc được")
                    st.caption(c["file_ehsmt"]+" · "+c["vi_tri_ehsmt"]+
                               " · SHA256: "+c["sha_ehsmt"])
                    if c["trich_goc_ehsmt"]:
                        st.code(c["trich_goc_ehsmt"][:700],language=None)
                with right:
                    st.markdown("**NSX — sản phẩm**")
                    st.write(c["nsx"] or "Chưa có")
                    st.caption(c["file_nsx"]+" · "+c["vi_tri_nsx"]+
                               " · SHA256: "+c["sha_nsx"])
                    if c["trich_goc_nsx"]:
                        st.code(c["trich_goc_nsx"][:700],language=None)
                st.info("Nguyên nhân: "+c["nguyen_nhan"])
    else:
        st.info("Nhóm này chưa có thuốc đủ căn cứ phân loại.")
    st.download_button("Tải Excel Lãnh đạo: 3 danh sách và lý do từng tiêu chí",
                       export_xlsx(register,st.session_state["tdv_see_pro_active_scope"]),
                       file_name="SEE_PRO_BAO_CAO_LANH_DAO_THEO_THUOC_SO_BO.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                       key="tdv_leader_per_drug_xlsx")
    st.caption("Mẫu số theo mã E-HSMT, không phải số tài liệu/ứng viên NSX. "
               "Đối chiếu chỉ đang ở mức sơ bộ và phạm vi người dùng khai báo.")


def render_leadership_view():
    st.markdown("### 📊 Báo cáo Lãnh đạo · E-HSMT làm chuẩn đối chiếu")
    t,n,report=_live_report()
    if not t or not n:
        st.warning("Chưa đủ E-HSMT và NSX đã đọc từ tài liệu thật; KHÔNG tạo báo cáo giả.")
        return
    if report.get("blocked"):
        st.error("ĐÃ CHẶN BÁO CÁO: " + report["block_reason"])
        return
    _leader_by_product(report)
    _summary(report)
    _records(report)
    from tdv_review_priorities import build_review_priorities
    priority = build_review_priorities(report, max_rows=10000)
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
        leadership_priorities_frame = pd.DataFrame([{
            "Ưu tiên": issue["muc_uu_tien"],
            "Nhóm": issue["van_de"], "Mã / nhà máy": issue["ma"],
            "Chi tiết": issue["chi_tiet"],
            "Tệp nguồn": issue["tai_lieu"],
            "Trang/dòng": issue["vi_tri_nguon"],
            "Cần làm": issue["viec_can_lam"],
            "Tình trạng": "CHƯA XÁC MINH",
        } for issue in issues[:100]])
        render_readable_table(st, leadership_priorities_frame,
                              key="tdv_leadership_priorities_readable",
                              label="Báo cáo lãnh đạo: việc cần ưu tiên",
                              page_size=25, min_width=1200)
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
        leadership_risks_frame = pd.DataFrame([{
            "Mã":r["MA_THUOC_EHSMT"],"Hoạt chất":r["HOAT_CHAT_EHSMT"],
            "Không khớp":r["SO_TIEU_CHI_KHONG_KHOP"],
            "Chưa đủ":r["SO_TIEU_CHI_CHUA_DAT"],
            "Vị trí chứng cứ":r["VI_TRI_EHSMT"],
            "Lý do":r["TRANG_THAI_DOI_CHIEU"],
        } for r in at_risk[:1000]])
        render_readable_table(st, leadership_risks_frame,
                              key="tdv_leadership_risks_readable",
                              label="Báo cáo lãnh đạo: mã cần kiểm tra",
                              page_size=25, min_width=1050)
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
