"""TDV QC7 ONLINE — bản giao diện DEMO công khai.

KHÔNG kết nối dữ liệu thật, KHÔNG nhận hồ sơ mật, KHÔNG ghi Google Sheets.
Mã nguồn thử nghiệm được đặt trên nhánh riêng, không ảnh hưởng main.
"""
from __future__ import annotations

import re
import unicodedata
from decimal import Decimal, InvalidOperation

import streamlit as st

st.set_page_config(
    page_title="TDV QC7 ONLINE | DUBIPHARMA",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
[data-testid="stAppViewContainer"] {background: #f4f7fb;}
[data-testid="stSidebar"] {background: #eef4fa;}
.block-container {padding-top: 1.65rem; max-width: 1420px;}
.hero {
 background: linear-gradient(115deg,#10345f,#14548a 70%,#178ca0);
 color:white; padding:2.25rem 2.6rem; border-radius:20px;
 margin-bottom:1.5rem; box-shadow: 0 10px 28px #0b31582c;
}
.hero h1 {color:white; font-size:2.2rem; margin:.3rem 0;}
.hero p {color:#dcebf7; font-size:1.05rem; margin-bottom:0;}
.eyebrow {letter-spacing:.13em; color:#9ee0d1; font-weight:700; font-size:.79rem;}
.panel {background:white; border:1px solid #dfe8f3; border-radius:15px;
 padding:1.3rem; min-height:150px; margin-bottom:.65rem;}
.panel h3 {color:#1a446c; font-size:1.05rem; margin-top:.2rem;}
.note {background:#fff6e2; border:1px solid #eac77a; color:#734e07;
 border-radius:12px; padding:.9rem 1.2rem; margin-bottom:1.1rem;}
.muted {font-size:.9rem; color:#57708b;}
</style>
""", unsafe_allow_html=True)

PAGES = [
    "🏠 Trung tâm điều hành",
    "📄 E-HSMT",
    "💊 Hồ sơ nhà sản xuất",
    "🔬 TDV-IDP 3.0",
    "🛡️ GMP & chứng cứ",
    "⚖️ So sánh kỹ thuật",
    "📈 Báo cáo lãnh đạo",
    "🔗 Google Sheets",
    "☁️ Tình trạng Online",
]

with st.sidebar:
    st.markdown("### 💊 DUBIPHARMA DŨNG BÍCH")
    st.caption("TDV QC7 ONLINE · BẢN XEM TRƯỚC")
    st.warning("DEMO CÔNG KHAI · Không nhập hồ sơ hoặc thông tin mật.")
    page = st.radio("ĐIỀU HÀNH", PAGES, label_visibility="collapsed")
    st.divider()
    st.caption("Quyền truy cập: chưa tích hợp xác thực doanh nghiệp")
    st.caption("Kho dữ liệu: chưa kết nối")
    st.caption("Bản thử: PREVIEW; không phải hệ thống dự thầu chính thức")

st.markdown("""
<div class="hero">
 <div class="eyebrow">DUBIPHARMA DŨNG BÍCH · TDV QC7 ONLINE</div>
 <h1>TRUNG TÂM ĐIỀU HÀNH ĐẤU THẦU</h1>
 <p>Quản lý hồ sơ tập trung · Đối chiếu có chứng cứ · Kiểm soát phê duyệt</p>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<div class="note"><b>BẢN XEM TRƯỚC KHÔNG CÓ DỮ LIỆU THẬT.</b>
 Chưa bật đăng nhập, phân quyền, lưu trữ bền vững hoặc kết nối Google Sheets.
 Không tải PDF/Excel hồ sơ NSX, GMP, báo giá hay tài liệu dự thầu lên bản này.</div>
""", unsafe_allow_html=True)


def card(title: str, body: str, icon: str = "▸") -> None:
    st.markdown(
        f'<div class="panel"><h3>{icon} {title}</h3>'
        f'<div class="muted">{body}</div></div>',
        unsafe_allow_html=True,
    )


def norm(text: str) -> str:
    value = unicodedata.normalize("NFKC", text).strip().lower()
    return re.sub(r"\s+", " ", value)


def strength(text: str) -> tuple[str, str] | None:
    """Recognize one simple mg strength, without guessing drugs or units."""
    m = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*(mg|g|mcg|µg)\s*", text, re.I)
    if not m:
        return None
    try:
        amount = Decimal(m.group(1).replace(",", "."))
    except InvalidOperation:
        return None
    unit = m.group(2).lower()
    multiplier = {"mg": Decimal("1"), "g": Decimal("1000"),
                  "mcg": Decimal("0.001"), "µg": Decimal("0.001")}[unit]
    if amount <= 0:
        return None
    return (str(amount * multiplier), "mg")


if page == PAGES[0]:
    st.subheader("Tổng quan điều hành · dữ liệu thử nghiệm")
    a, b, c, d = st.columns(4)
    for col, label in zip((a,b,c,d), (
        "Dự án xác minh", "Sản phẩm NSX", "Bằng chứng GMP", "Ứng viên đã duyệt")):
        with col:
            st.metric(label, "—", help="Chưa kết nối nguồn nghiệp vụ chính thức")
    left, right = st.columns(2)
    with left:
        card("TDV-IDP 3.0", "Đọc đa tầng và xác minh theo từng trường; đang xây dựng và nghiệm thu", "🔬")
        card("E-HSMT & danh mục dự thầu", "Liên kết lô thầu với chứng cứ nguồn, không tự coi dữ liệu OCR là kết luận", "📄")
    with right:
        card("Nhà sản xuất, GMP, báo giá", "Quản lý theo pháp nhân, nhà máy, sản phẩm và lịch sử hồ sơ", "🏭")
        card("Phê duyệt lãnh đạo", "Giá dự thầu và kết luận pháp lý phải qua người có thẩm quyền", "🛡️")
    st.info("Các chỉ số sẽ chỉ hiển thị sau khi xác thực người dùng và kết nối kho dữ liệu đã nghiệm thu.")

elif page == PAGES[3]:
    st.subheader("TDV-IDP 3.0 · Kiểm tra quy tắc hàm lượng")
    st.write("Đây là phép thử đơn giản ngay trong trình duyệt; **không** xử lý hồ sơ thật và không thay thế kiểm chứng dược.")
    col1, col2 = st.columns(2)
    with col1:
        active_a = st.text_input("Hoạt chất từ E-HSMT (ví dụ minh họa)", value="Acenocoumarol")
        dose_a = st.text_input("Hàm lượng E-HSMT", value="1 mg")
    with col2:
        active_b = st.text_input("Hoạt chất từ NSX (ví dụ minh họa)", value="Acenocoumarol")
        dose_b = st.text_input("Hàm lượng NSX", value="4 mg")
    if st.button("Kiểm tra hai trường mẫu", type="primary"):
        sa, sb = strength(dose_a), strength(dose_b)
        if not active_a.strip() or not active_b.strip() or not sa or not sb:
            st.warning("Chưa đủ trường hoặc đơn vị không được hỗ trợ: KHÔNG ĐƯỢC KẾT LUẬN.")
        elif norm(active_a) == norm(active_b) and sa == sb:
            st.success("Hai trường mẫu trùng nhau. Chưa đủ căn cứ để kết luận thuốc đáp ứng E-HSMT.")
        else:
            st.error("CÓ SAI KHÁC hoạt chất hoặc hàm lượng: KHÔNG TỰ GHÉP ỨNG VIÊN.")
    st.caption("Quy tắc demo chỉ kiểm một tên hoạt chất và một hàm lượng đơn giản; chưa xử lý muối, tỷ lệ, phối hợp hay dạng bào chế.")

elif page == PAGES[-1]:
    st.subheader("Tình trạng chuyển đổi Online")
    st.table([
        {"Hạng mục":"Giao diện Streamlit", "Tình trạng":"Bản demo — có mã triển khai"},
        {"Hạng mục":"Đăng nhập và phân quyền", "Tình trạng":"CHƯA TÍCH HỢP"},
        {"Hạng mục":"Google Sheets", "Tình trạng":"CHƯA KẾT NỐI · KHÔNG GHI"},
        {"Hạng mục":"Kho tài liệu & cơ sở dữ liệu", "Tình trạng":"CHƯA KẾT NỐI"},
        {"Hạng mục":"IDP 3.0 đa tầng", "Tình trạng":"ĐANG KIỂM THỬ · Chưa nghiệm thu"},
        {"Hạng mục":"Đưa nghiệp vụ thật lên mạng", "Tình trạng":"CHƯA ĐƯỢC PHÊ DUYỆT"},
    ])
    st.warning("Chỉ chuyển sang chế độ nghiệp vụ thật khi đã có đăng nhập, phân quyền, kho dữ liệu bền vững và kiểm thử an toàn.")
else:
    st.subheader(page.split(" ", 1)[1])
    st.info("Phân hệ đang được tích hợp. Bản demo công khai không đọc hoặc hiển thị thông tin nhà sản xuất và hồ sơ đấu thầu thật.")
    st.markdown("**Yêu cầu trước khi sử dụng:** xác thực người dùng, kiểm tra nguồn dữ liệu, phân quyền nghiệp vụ và nhật ký đối chiếu.")

st.divider()
st.caption("© DUBIPHARMA DŨNG BÍCH · TDV QC7 · DEMO giao diện, không phải hệ thống được nghiệm thu")
