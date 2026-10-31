"""Private password-and-permission UI for SEE PRO Preview J.

No default credentials, no plaintext password persistence, no public Admin
bootstrap. Verified Google Admin performs first setup. PostgreSQL is required.
"""
from __future__ import annotations

from tdv_access_store import (
    ADMIN, ALLOWED_GRANTS, SecurityNotConfigured, database_url,
    initialize, has_admin, bootstrap_admin, sign_in, check_session, logout,
    change_password, users, create_member, update_member,
    reset_member_password, valid_password,
)


def local_identity(st):
    """Revalidate the opaque session against the DB on every Streamlit rerun."""
    try:
        token=st.session_state.get("seepro_local_token")
        if not token:
            return None
        identity=check_session(database_url(st), token)
        if identity is None:
            st.session_state.pop("seepro_local_token",None)
        return identity
    except Exception:
        st.session_state.pop("seepro_local_token",None)
        return None


def render_local_login(st):
    st.markdown("**Tài khoản SEE PRO nội bộ**")
    try:
        dsn=database_url(st)
    except SecurityNotConfigured:
        st.caption("Đăng nhập nội bộ chưa kích hoạt: Admin cần cấu hình kho "
                   "bảo mật trung tâm trước. Dùng thử mẫu vẫn không cần tài khoản.")
        return
    with st.form("seepro_password_login"):
        username=st.text_input("Tên đăng nhập",key="seepro_login_name")
        password=st.text_input("Mật khẩu",type="password",key="seepro_login_password")
        clicked=st.form_submit_button("Đăng nhập SEE PRO")
    if clicked:
        try:
            token=sign_in(dsn,username,password)
            if not token:
                st.error("Thông tin không đúng, tài khoản bị khóa hoặc hết quyền.")
            else:
                st.session_state["seepro_local_token"]=token
                st.rerun()
        except Exception:
            st.error("Kho bảo mật chưa hoạt động. Vui lòng liên hệ Admin.")


def render_password_change(st, identity, *, forced=False):
    name=identity["username"]
    st.subheader("🔐 Đổi mật khẩu SEE PRO")
    if forced:
        st.warning("Mật khẩu tạm phải được thay trước khi sử dụng phân hệ nghiệp vụ.")
    with st.form("seepro_change_password"):
        old=st.text_input("Mật khẩu hiện tại",type="password",
                          key="seepro_old_password")
        new=st.text_input("Mật khẩu mới (12–128 ký tự)",
                          type="password",key="seepro_new_password")
        again=st.text_input("Nhập lại mật khẩu mới",type="password",
                            key="seepro_confirm_password")
        submit=st.form_submit_button("Lưu mật khẩu mới")
    if submit:
        if new!=again or not valid_password(new):
            st.error("Mật khẩu mới chưa đủ 12 ký tự hoặc xác nhận không khớp.")
            return
        if new==old:
            st.error("Mật khẩu mới phải khác mật khẩu hiện tại.")
            return
        try:
            updated=change_password(database_url(st),name,old,new)
        except Exception:
            st.error("Chưa lưu được mật khẩu. Kho bảo mật không sẵn sàng.")
            return
        if updated:
            st.session_state.pop("seepro_local_token",None)
            st.success("Đổi mật khẩu thành công. Các phiên cũ đã bị thu hồi; "
                       "hãy đăng nhập lại bằng mật khẩu mới.")
            st.stop()
        else:
            st.error("Mật khẩu hiện tại không chính xác.")


def render_local_logout(st):
    if st.button("Đăng xuất tài khoản SEE PRO",key="seepro_logout"):
        token=st.session_state.pop("seepro_local_token",None)
        if token:
            try:
                logout(database_url(st),token)
            except Exception:
                pass
        st.rerun()


def render_admin_security(st, *, is_google_admin=False, local=None):
    if not is_google_admin and not (local and local["role"]==ADMIN):
        st.error("Chỉ Admin đã xác thực được quản lý tài khoản và phân quyền.")
        return
    st.markdown("### 🔐 QUẢN TRỊ BẢO MẬT · SEE PRO")
    st.caption("Mật khẩu Argon2id · PostgreSQL qua TLS · phân quyền có nhật ký. "
               "Chế độ dùng thử công khai không được vào đây.")
    try:
        dsn=database_url(st)
    except SecurityNotConfigured:
        st.error("Chưa có cơ sở dữ liệu bảo mật trung tâm.")
        st.info("Admin cần cấu hình mục [seepro_admin_db] trong Streamlit Cloud "
                "Secrets bằng URL PostgreSQL qua TLS trước khi tạo mật khẩu. "
                "Không nhập mật khẩu hoặc địa chỉ kết nối vào chat/GitHub.")
        return
    try:
        available=has_admin(dsn)
    except Exception:
        if not is_google_admin:
            st.error("Kho tài khoản chưa được khởi tạo; đăng nhập Google Admin để thiết lập.")
            return
        st.info("Thiết lập bảng dữ liệu bảo mật lần đầu (chỉ Google Admin).")
        if st.button("Khởi tạo kho tài khoản",key="seepro_init_db"):
            try:
                initialize(dsn)
                st.success("Đã tạo bảng quản trị. Tiếp tục đặt mật khẩu Admin.")
                st.rerun()
            except Exception:
                st.error("Không khởi tạo được cơ sở dữ liệu. Kiểm tra quyền cơ sở dữ liệu.")
        return
    if not available:
        if not is_google_admin:
            st.error("Chưa có Admin. Vui lòng dùng Google Admin để đặt mật khẩu đầu tiên.")
            return
        st.warning("Đặt mật khẩu Admin lần đầu. Không có mật khẩu mặc định.")
        with st.form("seepro_bootstrap_admin"):
            password=st.text_input("Mật khẩu Admin mới",type="password")
            confirm=st.text_input("Nhập lại mật khẩu",type="password")
            setup=st.form_submit_button("Kích hoạt tài khoản Admin")
        if setup:
            if password!=confirm or not valid_password(password):
                st.error("Mật khẩu phải dài 12–128 ký tự và nhập khớp.")
            else:
                try:
                    bootstrap_admin(dsn,password,google_admin_verified=True)
                    st.success("Admin đã được tạo. Có thể đăng nhập bằng mật khẩu "
                               "SEE PRO trên PC khác.")
                    st.rerun()
                except Exception:
                    st.error("Không tạo được Admin. Kiểm tra kho bảo mật hoặc tài khoản đã có.")
        return
    if local and local["role"]==ADMIN:
        with st.expander("Đổi mật khẩu Admin",expanded=False):
            render_password_change(st,local)
    st.markdown("#### Danh sách tài khoản và quyền")
    try:
        accounts=users(dsn)
    except Exception:
        st.error("Không lấy được danh sách tài khoản từ kho bảo mật.")
        return
    st.dataframe([{"Tài khoản":a["username"],
                   "Vai trò":a["role"],
                   "Trạng thái":"Hoạt động" if a["active"] else "Đã khóa",
                   "Buộc đổi mật khẩu":a["must_change"],
                   "Phân hệ được cấp":", ".join(a["grants"])}
                  for a in accounts],hide_index=True,use_container_width=True)
    with st.expander("➕ Thêm thành viên",expanded=False):
        with st.form("seepro_create_member"):
            username=st.text_input("Tên tài khoản mới",key="seepro_create_username")
            temporary=st.text_input("Mật khẩu tạm cho thành viên",
                                    type="password",key="seepro_create_password")
            grants=st.multiselect("Cấp quyền các phân hệ",
                                  sorted(ALLOWED_GRANTS),key="seepro_create_grants")
            add=st.form_submit_button("Tạo tài khoản và cấp quyền")
        if add:
            try:
                create_member(dsn,username,temporary,grants,
                              actor=local["username"] if local else "google-admin")
                st.success("Đã tạo thành viên, bắt buộc thay mật khẩu lần đầu.")
                st.rerun()
            except (ValueError,PermissionError) as exc:
                st.error(str(exc))
            except Exception:
                st.error("Không tạo được thành viên; tài khoản có thể đã tồn tại.")
    member_names=[a["username"] for a in accounts if a["role"]=="member"]
    if member_names:
        st.markdown("#### Cấp/thu hồi quyền và khóa thành viên")
        selected=st.selectbox("Chọn thành viên",member_names,key="seepro_member_pick")
        member=next(x for x in accounts if x["username"]==selected)
        with st.form("seepro_update_member"):
            grants=st.multiselect("Các chức năng thành viên được phép truy cập",
                                  sorted(ALLOWED_GRANTS),
                                  default=member["grants"],key="seepro_edit_grants")
            active=st.checkbox("Tài khoản đang hoạt động",
                               value=member["active"],key="seepro_member_active")
            update=st.form_submit_button("Lưu phân quyền và thu hồi phiên cũ")
        if update:
            try:
                update_member(dsn,selected,grants,active,
                              actor=local["username"] if local else "google-admin")
                st.success("Đã cập nhật và thu hồi các phiên đăng nhập cũ.")
                st.rerun()
            except Exception:
                st.error("Không thể cập nhật quyền. Kiểm tra kho bảo mật.")
        with st.expander("Đặt lại mật khẩu tạm cho thành viên",expanded=False):
            with st.form("seepro_reset_member"):
                temp=st.text_input("Mật khẩu tạm mới",type="password",
                                   key="seepro_reset_temp")
                reset=st.form_submit_button("Đặt lại và thu hồi phiên cũ")
            if reset:
                try:
                    reset_member_password(dsn,selected,temp,
                        actor=local["username"] if local else "google-admin")
                    st.success("Đã đặt lại mật khẩu. Thành viên phải đổi mật khẩu khi vào.")
                    st.rerun()
                except Exception:
                    st.error("Không đặt lại được mật khẩu tạm.")
