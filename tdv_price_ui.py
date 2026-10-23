"""Private SEE PRO price balance page — Streamlit QA only.

All calculations/drafts remain within authenticated user's RAM session.
No automatic quote extraction as trusted price, no final approvals, no cloud writes.
"""
from __future__ import annotations

import pandas as pd
from tdv_price_controls import (
    PRICE_PAGE, price_permission, may_price, calculate_price, append_draft,
    draft_in_scope,
)
from tdv_see_pro_scope import validate_scope, check_scope
from tdv_leadership_report import compare_sources


def _vnd(value):
    if not str(value).strip():
        return "—"
    try:
        from decimal import Decimal
        return f"{Decimal(str(value)):,.0f} đ".replace(",", ".")
    except Exception:
        return "—"


def _draft_table(st, rows):
    if not rows:
        st.info("Chưa có đề xuất giá nào được lưu trong phiên này.")
        return
    st.dataframe(pd.DataFrame([{
        "Mã E-HSMT":r["lot_id"], "Mã NSX":r["nsx_id"],
        "Lần":r["revision"], "Giá chào sau VAT":_vnd(r["pricing"]["proposed_bid_gross"]),
        "Tổng giá chào":_vnd(r["pricing"]["estimated_total_bid_gross"]),
        "So mức tham chiếu":r["pricing"]["comparison_status"],
        "Người lập":r["author_email"], "Thời điểm UTC":r["created_at_utc"],
        "Trạng thái":"DỰ THẢO — CHƯA PHÊ DUYỆT",
    } for r in rows]), hide_index=True, use_container_width=True)


def render_price_workspace(st, *, email, role, grant_config):
    """Authorization is re-evaluated here, beyond navigation/menu hiding."""
    scope=validate_scope(st.session_state.get("tdv_see_pro_active_scope"))
    grant=price_permission(email,role,scope,grant_config)
    if not may_price(grant,"view",role):
        st.error("Không có quyền xem giá của dự án/gói/phiên bản này.")
        return
    st.markdown("### 💰 Cân đối & phê duyệt giá chào")
    st.caption("Phân hệ giá riêng · quyền theo dự án/gói/phiên bản · chỉ dùng "
               "nguồn hồ sơ đã được phép xử lý trên Preview.")
    st.warning("CHƯA MỞ PHÊ DUYỆT CHÍNH THỨC: hệ thống chưa có kho dữ liệu và "
               "nhật ký bất biến dùng chung. Mọi giá tính toán là DỰ THẢO "
               "trong bộ nhớ phiên, không tự ghi vào hồ sơ dự thầu.")
    st.caption(f"Quyền được cấp trong phiên: {grant} · phạm vi: "
               f"{scope['project_id']} / {scope['package_id']} / {scope['ehsmt_revision_id']}")

    ehsmt=st.session_state.get("tdv_see_pro_analysis")
    nsx=st.session_state.get("tdv_nsx_auto_report")
    ok,message=check_scope(scope,ehsmt,nsx)
    if not ok:
        st.error("Không thể lập giá: "+message)
        return

    # Never quote a product without unambiguous project-scoped comparison link.
    comparison=compare_sources(ehsmt,nsx)
    unique=[r for r in comparison.get("comparison",[]) if r.get("MA_THUOC_NSX")
            and r.get("SO_UNG_VIEN_NSX")==1]
    if not unique:
        st.info("Chưa có mặt hàng E-HSMT liên kết duy nhất tới sản phẩm NSX. "
                "Không nhập giá khi định danh chưa rõ.")
        return

    st.markdown("**1. Chọn mặt hàng để cân đối**")
    labels=[f"{r['MA_THUOC_EHSMT']} · {r['HOAT_CHAT_EHSMT']} · "
            f"{r['TEN_THUOC_NSX']}" for r in unique]
    idx=st.selectbox("Mặt hàng E-HSMT / NSX đã liên kết sơ bộ",
                     range(len(unique)),format_func=lambda i:labels[i],
                     key="tdv_price_lot")
    selected=unique[idx]
    lot=selected["MA_THUOC_EHSMT"]
    product=selected["MA_THUOC_NSX"]
    st.caption(f"E-HSMT: {selected.get('NGUON_EHSMT','')} · "
               f"{selected.get('VI_TRI_EHSMT','')} | NSX: "
               f"{selected.get('NGUON_THUOC_NSX','')} · "
               f"SHA: {selected.get('SHA256_NSX','')}")
    st.info("Liên kết thuốc và thông số vẫn sơ bộ; không đồng nghĩa đã đạt "
            "yêu cầu kỹ thuật, SĐK/GMP hoặc đủ điều kiện dự thầu.")

    drafts=st.session_state.get("tdv_price_drafts",[])
    existing=[x for x in draft_in_scope(drafts,scope)
              if x["lot_id"]==lot and x["nsx_id"]==product]
    st.markdown("**2. Lịch sử đề xuất giá trong phiên**")
    _draft_table(st,existing)
    if not may_price(grant,"prepare",role):
        st.info("Tài khoản này chỉ được xem dự thảo; không được thay đổi giá.")
        return

    st.markdown("**3. Nhập và tính giá dự thảo (đơn giá tính theo VND)**")
    st.caption("Tất cả ô tiền đều để trống: cán bộ nhập theo đúng báo giá đã "
               "xem bản gốc. Không tự coi giá kế hoạch là trần pháp lý.")
    # Every submission uses explicit source references and confirms units.
    with st.form("tdv_price_draft_form"):
        c1,c2,c3=st.columns(3)
        with c1:
            before=st.text_input("Giá NSX trước VAT (đ)",placeholder="Ví dụ 9000")
            after=st.text_input("Giá NSX sau VAT (đ)",placeholder="Hoặc nhập giá sau VAT")
            vat=st.text_input("VAT NSX (%)",placeholder="Theo báo giá; không mặc định")
        with c2:
            quantity=st.text_input("Số lượng theo E-HSMT",placeholder="Nhập số nguyên")
            extra=st.text_input("Chi phí cộng thêm/đơn vị (đ, đã gồm thuế áp dụng)",
                                placeholder="Nhập 0 nếu đã kiểm tra không phát sinh")
            offered=st.text_input("Giá chào dự kiến/đơn vị sau VAT (đ)",
                                  placeholder="Giá do người có quyền đề xuất")
        with c3:
            reference=st.text_input("Giá tham chiếu E-HSMT/đơn vị (nếu đã đối chiếu)",
                                    placeholder="Để trống nếu chưa xác minh")
            refbasis=st.selectbox("Cơ sở VAT của mức giá E-HSMT",
                                  ["unknown","vat_included","vat_excluded"],
                                  format_func=lambda x:{
                                      "unknown":"CHƯA XÁC ĐỊNH",
                                      "vat_included":"ĐÃ GỒM VAT",
                                      "vat_excluded":"CHƯA GỒM VAT"}[x])
            bidvat=st.text_input("VAT giá chào (%) nếu cần so với giá E-HSMT chưa VAT",
                                 placeholder="Không tự dùng VAT NSX")
        origin=st.text_input("Báo giá NSX — tên tệp, phiên bản, trang/ô nguồn",
                             placeholder="Bắt buộc để lưu dự thảo")
        refsource=st.text_input("Mức giá E-HSMT — tên tệp, trang/ô nguồn",
                                placeholder="Bắt buộc nếu nhập mức giá tham chiếu")
        verified_units=st.checkbox(
            "Tôi đã đối chiếu cùng đơn vị tính, quy cách và số lượng ở hai phía")
        confirmed=st.checkbox(
            "Tôi hiểu đây là dự thảo trong phiên, không phải giá phê duyệt")
        submit=st.form_submit_button("Tính và lưu ĐỀ XUẤT GIÁ (chưa phê duyệt)")
    if submit:
        # Recheck both permissions and scope after user click.
        live_scope=validate_scope(st.session_state.get("tdv_see_pro_active_scope"))
        current_grant=price_permission(email,role,live_scope,grant_config)
        current_ok,_=check_scope(live_scope,
                                st.session_state.get("tdv_see_pro_analysis"),
                                st.session_state.get("tdv_nsx_auto_report"))
        if not current_ok or live_scope!=scope or not may_price(current_grant,"prepare",role):
            st.error("Phạm vi/quyền đã thay đổi; không ghi dự thảo.")
            return
        if not verified_units or not confirmed:
            st.error("Cần xác nhận đơn vị tính và tính chất dự thảo.")
            return
        try:
            calc=calculate_price(
                quote_before=before,quote_after=after,
                supplier_vat_percent=vat, extra_cost=extra,
                proposed_bid_gross=offered,quantity=quantity,
                ehsmt_reference=reference,reference_basis=refbasis,
                bid_vat_percent=bidvat)
            new_drafts=append_draft(
                st.session_state.get("tdv_price_drafts",[]),
                permission=current_grant,global_role=role,scope=scope,
                lot_id=lot,nsx_id=product,author_email=email,
                result=calc,quote_reference=origin,tender_reference=refsource)
        except (ValueError,PermissionError) as exc:
            st.error(str(exc))
            return
        st.session_state["tdv_price_drafts"]=new_drafts
        st.success("Đã ghi ĐỀ XUẤT GIÁ trong RAM, chưa phê duyệt hoặc xuất hồ sơ.")
        a,b,c=st.columns(3)
        a.metric("Giá NSX sau VAT",_vnd(calc["quote_after_vat"]))
        b.metric("Giá chào dự kiến",_vnd(calc["proposed_bid_gross"]))
        c.metric("Tổng giá chào",_vnd(calc["estimated_total_bid_gross"]))
        for msg in calc["warnings"]:
            st.warning(msg)
        st.caption("Mức giá E-HSMT chỉ là tham chiếu do người nhập xác minh; "
                   "SEE PRO chưa xác nhận đây là trần giá pháp lý.")
    st.divider()
    st.button("Chốt/PHÊ DUYỆT GIÁ CHÀO",disabled=True,
              help="Khóa đến khi có quyền phê duyệt thực, kho chứng cứ và nhật ký bền vững")
    st.caption("Không có đường phê duyệt ẩn. Quyền approve trong Secrets hiện chỉ "
               "cấp xem/lập dự thảo; chức năng chốt chưa kích hoạt.")
