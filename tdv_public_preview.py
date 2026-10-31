"""Public, strictly synthetic SEE PRO preview. No sensitive data or uploads.

This route is separate from the authenticated tender/NSX workbench.
Nothing here reads authenticated workspace state, Drive, Sheets or user files.
"""
from __future__ import annotations

from tdv_auth import valid_configuration
from tdv_leadership_report import compare_sources

DEMO_PROJECT = "DEMO-SEE-PRO"
DEMO_PACKAGE = "BP-DEMO-001"
DEMO_REVISION = "E-HSMT-MAU-01"

MENU = (
    "🏠 Giới thiệu",
    "📄 E-HSMT mẫu",
    "💊 Hồ sơ NSX mẫu",
    "⚖️ So sánh kỹ thuật mẫu",
    "📊 Báo cáo mẫu",
)


def is_public_visitor(st) -> bool:
    """Only unlogged visitors use the separate read-only synthetic route."""
    try:
        return not bool(st.user.is_logged_in)
    except (AttributeError, KeyError, RuntimeError):
        return True


def _field(value: str, source: str) -> dict:
    return {"file": source, "source": source, "row": 2,
            "raw": value, "sha256": "0" * 64}


def demo_sources() -> tuple[dict, dict]:
    """In-code fabricated rows; never load user data or live content."""
    tender = [
        ("G1.001", "Acarbose", "50mg", "Viên nén", "Uống"),
        ("G1.002", "Metformin", "500mg", "Viên nén", "Uống"),
        ("G1.003", "Insulin", "100 IU/ml", "Dung dịch tiêm", "Tiêm"),
    ]
    nsx = [
        ("P-MAU-01", "Thuốc mẫu A", "Acarbose", "50mg", "Viên nén", "Uống"),
        ("P-MAU-02", "Thuốc mẫu B", "Metformin", "850mg", "Viên nén", "Uống"),
    ]
    trows = []
    for idx, (code, ingredient, strength, form, route) in enumerate(tender, 2):
        fields = {"HOAT_CHAT_HSMT": ingredient, "NONG_DO_HAM_LUONG": strength,
                  "DANG_BAO_CHE": form, "DUONG_DUNG": route}
        evidence = {name: {**_field(value, "E-HSMT GIẢ LẬP"), "row": idx}
                    for name, value in fields.items()}
        trows.append({"MA_THUOC": code, "MA_GOI_THAU": DEMO_PACKAGE,
                      "FILE_NGUON": "E-HSMT GIẢ LẬP",
                      "TRANG_VI_TRI": f"Dòng {idx}",
                      **fields, "EVIDENCE": evidence})
    products = []
    for idx, (uid, name, ingredient, strength, form, route) in enumerate(nsx, 2):
        fields = {"PRODUCT_NAME": name, "INGREDIENT": ingredient,
                  "STRENGTH": strength, "DOSAGE_FORM": form, "ROUTE": route}
        products.append({"uid": uid, "file": "NSX GIẢ LẬP",
                         "sha256": "1" * 64, "fields": fields,
                         "evidence": {k: {**_field(v, "NSX GIẢ LẬP"), "row": idx}
                                      for k, v in fields.items()},
                         "conflicts": {}})
    return {"rows": trows, "warnings": []}, {"products": products, "warnings": []}


def _admin_entry(st) -> None:
    """Admin still uses the verified Google sign-in already implemented."""
    if st.button("🔐 Đăng nhập dành cho Admin", key="public_demo_admin_login"):
        try:
            configured = valid_configuration(
                st.secrets.get("auth"), st.secrets.get("tdv_access"))
        except (AttributeError, KeyError, RuntimeError):
            configured = False
        if not configured:
            st.error("Chưa cấu hình quyền quản trị; không thể đăng nhập Admin.")
            return
        st.login()


def render_public_preview(st) -> None:
    """Synthetic UI only. No upload, AI calls, persistence or business approvals."""
    st.title("SEE PRO · DUBIPHARMA DŨNG BÍCH")
    st.caption("Chế độ dùng thử trực tuyến · Mở ngay trên PC hoặc iPhone · KHÔNG cần đăng nhập")
    st.warning(
        "ĐÂY LÀ DỮ LIỆU MẪU GIẢ LẬP. Không nhập hồ sơ thầu thật, tài liệu NSX mật "
        "hoặc thông tin giá chào trên chế độ công khai."
    )
    with st.sidebar:
        st.markdown("### SEE PRO · DÙNG THỬ")
        page = st.radio("Chọn bước kiểm thử", MENU, key="see_pro_public_demo_page")
        st.divider()
        _admin_entry(st)
        st.caption("Admin có xác thực riêng. Dữ liệu chính thức và chức năng "
                   "quản trị không có trên màn hình công khai.")

    ehsmt, supplier = demo_sources()
    report = compare_sources(ehsmt, supplier)
    if page == MENU[0]:
        st.subheader("Quy trình kiểm thử mẫu E-HSMT → NSX → So sánh → Báo cáo")
        st.write("Truy cập trực tiếp qua link, chọn từng mục bên trái để xem "
                 "cách SEE PRO xử lý các tình huống khớp, sai khác và thiếu chứng cứ.")
        a, b, c = st.columns(3)
        a.metric("Mã E-HSMT mẫu", len(ehsmt["rows"]))
        b.metric("Sản phẩm NSX mẫu", len(supplier["products"]))
        c.metric("Hồ sơ đã xác minh", 0)
        st.info("Để nạp tài liệu thử từ máy, cần vào khu vực quản trị đã "
                "xác thực; bản mở công khai chỉ trình diễn dữ liệu giả lập.")
    elif page == MENU[1]:
        st.subheader("📄 Danh mục E-HSMT · DỮ LIỆU MẪU")
        st.dataframe([{"Mã": r["MA_THUOC"], "Hoạt chất": r["HOAT_CHAT_HSMT"],
                       "Hàm lượng": r["NONG_DO_HAM_LUONG"],
                       "Dạng bào chế": r["DANG_BAO_CHE"],
                       "Đường dùng": r["DUONG_DUNG"],
                       "Nguồn": "GIẢ LẬP"} for r in ehsmt["rows"]],
                     hide_index=True, use_container_width=True)
        st.caption("Chỉ là 3 dòng viết sẵn để kiểm tra hiển thị; không phải kết quả đọc PDF.")
    elif page == MENU[2]:
        st.subheader("💊 Danh mục NSX · DỮ LIỆU MẪU")
        st.dataframe([{"Mã NSX": p["uid"], "Tên thuốc": p["fields"]["PRODUCT_NAME"],
                       "Hoạt chất": p["fields"]["INGREDIENT"],
                       "Hàm lượng": p["fields"]["STRENGTH"],
                       "Dạng bào chế": p["fields"]["DOSAGE_FORM"],
                       "Nguồn": "GIẢ LẬP"} for p in supplier["products"]],
                     hide_index=True, use_container_width=True)
        st.caption("Có chủ ý thiếu sản phẩm Insulin và sai hàm lượng Metformin để kiểm thử.")
    elif page == MENU[3]:
        st.subheader("⚖️ Đối chiếu kỹ thuật · DỮ LIỆU MẪU")
        st.caption("Áp dụng hàm so sánh sơ bộ của SEE PRO cho dữ liệu tự tạo; "
                   "màu xanh không xác nhận đủ điều kiện dự thầu.")
        st.dataframe([{"Mã": r["MA_THUOC_EHSMT"],
                       "NSX ghép duy nhất": r["TEN_THUOC_NSX"] or "CHƯA CÓ",
                       "Khớp sơ bộ": r["SO_TIEU_CHI_DAT"],
                       "Thiếu căn cứ": r["SO_TIEU_CHI_CHUA_DAT"],
                       "Không khớp": r["SO_TIEU_CHI_KHONG_KHOP"],
                       "Trạng thái": r["TRANG_THAI_DOI_CHIEU"]}
                      for r in report["comparison"]],
                     hide_index=True, use_container_width=True)
        codes = [r["MA_THUOC_EHSMT"] for r in report["comparison"]]
        code = st.selectbox("Xem chi tiết mã mẫu", codes, key="see_pro_demo_code")
        item = next(r for r in report["comparison"] if r["MA_THUOC_EHSMT"] == code)
        st.dataframe([{"Tiêu chí": c["label"], "Yêu cầu E-HSMT": c["ehsmt"],
                       "Thông tin NSX": c["nsx"] or "CHƯA CÓ",
                       "Kết quả sơ bộ": c["status"]}
                      for c in item["criteria"]],
                     hide_index=True, use_container_width=True)
    else:
        st.subheader("📊 Báo cáo tổng hợp · DỮ LIỆU MẪU")
        summary = report["summary"]
        a, b, c = st.columns(3)
        a.metric("Khớp sơ bộ", summary["green_criteria_preliminary"])
        b.metric("Chưa đủ căn cứ", summary["yellow_criteria"])
        c.metric("Không khớp", summary["red_mismatch_preliminary"])
        st.caption("Chỉ báo cáo mẫu, không phải kết luận nghiệp vụ hay hồ sơ thật.")
        st.dataframe([{"Mã E-HSMT": r["MA_THUOC_EHSMT"],
                       "Kết quả": r["TRANG_THAI_DOI_CHIEU"],
                       "Xác minh": "CHƯA"}
                      for r in report["comparison"]],
                     hide_index=True, use_container_width=True)
    st.divider()
    st.caption("Chế độ khách: chỉ đọc dữ liệu mẫu · Không tải tệp lên · "
               "Không kết nối Drive/Sheets · Không quản trị hoặc phê duyệt giá.")
