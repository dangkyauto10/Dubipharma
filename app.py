"""TDV QC7 Online — giao diện lãnh đạo, bản thử KHÔNG CHỨA DỮ LIỆU THẬT."""
from __future__ import annotations
import re
import unicodedata
from decimal import Decimal, InvalidOperation
from pathlib import Path
import streamlit as st

st.set_page_config(
    page_title="TDV QC7 ONLINE | DUBIPHARMA DŨNG BÍCH",
    page_icon="💊", layout="wide", initial_sidebar_state="expanded"
)

ROOT = Path(__file__).resolve().parent

def asset_base64(filename: str) -> str:
    """Local public-safe branding only; never load remote files or secret keys."""
    path = ROOT / "assets" / filename
    try:
        data = path.read_text(encoding="ascii").strip()
        if len(data) > 256 and re.fullmatch(r"[A-Za-z0-9+/=\s]+", data):
            return data
    except OSError:
        pass
    return ""

LOGO_DATA = asset_base64("tdv_logo.webp.b64")
ART_DATA = asset_base64("tdv_art.webp.b64")

STYLE = """
<style>
:root {--navy:#0c3167;--blue:#1966b5;--border:#dce8f4;--soft:#f3f8fe;}
html,body,[data-testid="stAppViewContainer"] {background:#f3f7fc;color:#193b63;}
[data-testid="stHeader"] {background:#f3f7fc; z-index:1000;}
[data-testid="stSidebar"] {background:linear-gradient(160deg,#f5faff,#eaf3fe);border-right:1px solid #d9e7f5;}
.block-container {max-width:1650px;padding-top:0.6rem;padding-bottom:.4rem;padding-left:1.3rem;padding-right:1.3rem;}
h1,h2,h3 {color:#0b316b;}
[data-testid="stMetric"] {padding:12px 14px;background:#fff;border:1px solid var(--border);border-radius:15px;}
.tdv-left-head {padding:12px 9px 16px;border-bottom:1px solid #cfdfed;background:#eff7ff;}
.tdv-left-brand {display:flex;align-items:center;justify-content:center;gap:9px;}
.tdv-logo-word {font-size:1.62rem;line-height:1.05;letter-spacing:-.06em;font-weight:900;
 background:linear-gradient(135deg,#f5c829 0%,#e42f4a 48%,#1c9857 88%);
 color:transparent;background-clip:text;-webkit-background-clip:text;}
.tdv-sidebar-name {font-size:.97rem;color:#103b75;font-weight:850;text-align:center;margin-top:9px;}
.tdv-sidebar-sub {font-size:.76rem;color:#607b98;text-align:center;}
.tdv-left-note {background:#fff8df;border:1px solid #e4d9ab;color:#805b16;
 border-radius:10px;padding:9px 11px;font-size:.79rem;margin-top:12px;}
.tdv-heading-section {font-size:.74rem;color:#647b94;letter-spacing:.08em;font-weight:800;padding:14px 4px 2px;}
.tdv-main-hero {background:linear-gradient(105deg,#fff 0%,#f0f8ff 57%,#d3eaf9 100%);
 border:1px solid #d5e7f6;box-shadow:0 4px 18px #173b710c;border-radius:18px;
 position:relative;overflow:hidden;min-height:148px;display:flex;align-items:center;gap:18px;
 padding:18px 22px;margin:0 0 6px;}
.tdv-main-logo {width:128px;min-width:128px;display:flex;justify-content:center;align-items:center;
 border-right:1px solid #c8dced;padding-right:16px;min-height:99px;}
.tdv-main-body {min-width:0;max-width:900px;position:relative;z-index:2;}
.tdv-pill {display:inline-block;background:#d7f2e2;color:#09623d;border-radius:24px;
 padding:4px 11px;font-weight:780;font-size:.7rem;}
.tdv-main-title {font-size:clamp(1.18rem,2vw,2rem);line-height:1.16;font-weight:900;color:#102f65;
 margin:8px 0 6px;letter-spacing:.01em;}
.tdv-main-subtitle {color:#4b6b87;font-size:.85rem;}
.tdv-main-art {position:absolute;right:0;top:0;bottom:0;width:24%;
 background:radial-gradient(circle at 78% 29%,#d6fbff 0 10%,transparent 11%),
 radial-gradient(circle at 65% 76%,#61a9d066 0 17%,transparent 18%);
 opacity:.75;}
.tdv-main-art:before{content:"✚";position:absolute;right:21%;top:17%;color:#fff;
 font-size:4.8rem;text-shadow:0 1px 19px #0d74a4;font-weight:800;}
.tdv-tags {display:flex;flex-wrap:wrap;gap:7px;margin-top:8px;}
.tdv-tags span {background:#ffffffdb;border:1px solid #e0eaf3;border-radius:10px;
 padding:4px 8px;font-size:.7rem;color:#28547d;font-weight:700;}
.tdv-notice {background:#fff9e8;border:1px solid #efdfb1;border-radius:11px;
 color:#795714;padding:10px 13px;font-size:.83rem;margin:6px 0 10px;}
.tdv-crumb{color:#647d99;font-size:.78rem;padding:2px 1px 9px;}
.tdv-panel {background:#fff;border:1px solid #dce8f4;border-radius:16px;
 padding:17px 19px;min-height:118px;margin-bottom:9px;box-shadow:0 3px 14px #23456a09;}
.tdv-panel h3{font-size:1.06rem;margin:0 0 10px;color:#174474;}
.tdv-panel p{font-size:.89rem;color:#5f7692;margin:0;}
.tdv-empty {border:1px dashed #c7d9e9;background:#fff;border-radius:12px;
 padding:17px;color:#52718c;}
.tdv-page-title{font-size:1.4rem;font-weight:790;color:#123d76;margin:7px 0 10px;}
.st-key-tdv_sidebar_scroll [data-testid="stRadio"] label {font-size:.91rem;}
.st-key-tdv_sidebar_scroll [data-testid="stRadio"] div[role="radiogroup"] {gap:.15rem;}
/* DESKTOP: two separately scrolling business areas with stationary brand/header.
   Keep Streamlit's own sidebar collapse/expand control clickable. */
@media (min-width: 900px) and (min-height: 570px) {
 [data-testid="stSidebar"] [data-testid="stSidebarContent"]{overflow:hidden!important;}
 [data-testid="stSidebar"] [data-testid="stSidebarUserContent"]{
    height:100%!important;min-height:0!important;overflow:hidden!important;}
 [data-testid="stSidebar"] [data-testid="stSidebarUserContent"] > [data-testid="stVerticalBlock"] {
    display:flex!important;flex-direction:column!important;height:100%!important;min-height:0!important;
    overflow:hidden!important;gap:0!important;}
 .st-key-tdv_sidebar_brand{flex:0 0 auto!important;min-height:0;position:relative;z-index:3;}
 .st-key-tdv_sidebar_scroll {flex:1 1 auto!important;min-height:0!important;
    overflow-y:auto!important;overscroll-behavior-y:contain;padding:0 8px 16px 2px;}
 [data-testid="stMain"]{overflow:hidden!important;}
 [data-testid="stMainBlockContainer"]{
    height:calc(100dvh - 3.25rem)!important;max-height:calc(100dvh - 3.25rem)!important;
    display:flex!important;flex-direction:column!important;min-height:0!important;overflow:hidden!important;}
 [data-testid="stMainBlockContainer"] > [data-testid="stVerticalBlock"]{
    height:100%!important;min-height:0!important;display:flex!important;
    flex-direction:column!important;overflow:hidden!important;gap:0!important;}
 .st-key-tdv_main_fixed{flex:0 0 auto!important;min-height:0!important;position:relative;z-index:5;}
 .st-key-tdv_main_scroll {flex:1 1 auto!important;min-height:0!important;
    overflow-y:auto!important;overscroll-behavior:contain;padding:0 7px 20px 1px;}
 .st-key-tdv_sidebar_scroll::-webkit-scrollbar,
 .st-key-tdv_main_scroll::-webkit-scrollbar{width:7px;}
 .st-key-tdv_sidebar_scroll::-webkit-scrollbar-thumb,
 .st-key-tdv_main_scroll::-webkit-scrollbar-thumb{background:#c4d4e5;border-radius:9px;}
}
/* Compact windows keep normal page scrolling rather than risk inaccessible content. */
@media (max-width:899px), (max-height:569px){
 [data-testid="stMain"]{overflow-y:auto!important;}
 .st-key-tdv_main_fixed {position:sticky;top:0;z-index:5;background:#f3f7fc;padding-bottom:3px;}
 .tdv-main-hero {min-height:100px;padding:11px;gap:11px;}
 .tdv-main-logo{width:73px;min-width:73px;min-height:64px;padding-right:8px;}
 .tdv-main-title{font-size:1.07rem;}
 .tdv-main-art,.tdv-tags{display:none;}
 .tdv-main-subtitle{font-size:.72rem;}
}
</style>
"""
st.markdown(STYLE, unsafe_allow_html=True)

PAGES = [
    "🏠 Trang chủ / Dự án",
    "📄 E-HSMT",
    "💊 Báo giá & hồ sơ NSX",
    "🔬 TDV-IDP 3.0 · Đọc đa tầng",
    "🛡️ Chứng cứ nhà sản xuất",
    "⚖️ So sánh kỹ thuật",
    "📊 Báo cáo lãnh đạo",
    "🔗 Google Sheets",
    "☁️ Tình trạng Online",
]

if "tdv_section" not in st.session_state:
    st.session_state.tdv_section = PAGES[0]

logo = (f'<img alt="Logo DUBIPHARMA" style="width:110px;max-height:92px;object-fit:contain" '
        f'src="data:image/webp;base64,{LOGO_DATA}">' if LOGO_DATA else
        '<div class="tdv-logo-word" aria-label="Logo DUBI">DB<br>DUBI</div>')
art = (f'<div class="tdv-main-art" style="opacity:.77;'
       f'background-image:linear-gradient(to right,#eaf4fd00,#d9ecfa18),'
       f'url(data:image/webp;base64,{ART_DATA});'
       f'background-size:cover;background-position:center"></div>' if ART_DATA else
       '<div class="tdv-main-art" aria-hidden="true"></div>')

with st.sidebar:
    with st.container(key="tdv_sidebar_brand"):
        st.markdown(
            '<div class="tdv-left-head"><div class="tdv-left-brand">' + logo +
            '</div><div class="tdv-sidebar-name">DUBIPHARMA DŨNG BÍCH</div>'
            '<div class="tdv-sidebar-sub">TDV QC7 ONLINE · IDP 3.0</div></div>',
            unsafe_allow_html=True,
        )
    with st.container(key="tdv_sidebar_scroll"):
        st.markdown('<div class="tdv-heading-section">ĐIỀU HÀNH & NGHIỆP VỤ</div>',
                    unsafe_allow_html=True)
        page = st.radio(
            "Chọn chức năng",
            PAGES, key="tdv_sidebar_nav", label_visibility="collapsed"
        )
        st.markdown('<div class="tdv-left-note">🔒 BẢN XEM TRƯỚC RIÊNG TƯ.'
                    ' Chưa nhập hồ sơ NSX, GMP, báo giá hoặc thông tin mật.</div>',
                    unsafe_allow_html=True)
        st.divider()
        st.caption("Ứng dụng: Streamlit Preview")
        st.caption("Dữ liệu nghiệp vụ: CHƯA KẾT NỐI")
        st.caption("Tài khoản nội bộ: CHƯA TÍCH HỢP")
        st.caption("Báo cáo: chỉ để xem cấu trúc giao diện")

with st.container(key="tdv_main_fixed"):
    st.markdown(
        '<section class="tdv-main-hero">' + art +
        '<div class="tdv-main-logo">' + logo + '</div>'
        '<div class="tdv-main-body">'
        '<span class="tdv-pill">HỆ THỐNG QUẢN LÝ ĐẤU THẦU CHUYÊN NGHIỆP</span>'
        '<div class="tdv-main-title">TRUNG TÂM ĐIỀU HÀNH ĐẤU THẦU'
        '<br>DUBIPHARMA DŨNG BÍCH</div>'
        '<div class="tdv-main-subtitle">Quản lý tập trung · Minh bạch · Hiệu quả · Vì sức khỏe cộng đồng</div>'
        '<div class="tdv-tags"><span>🎯 Chủ động kế hoạch</span>'
        '<span>📊 Tối ưu hiệu quả</span><span>🛡️ Minh bạch & tuân thủ</span></div>'
        '</div></section>', unsafe_allow_html=True,
    )

def panel(title: str, description: str) -> None:
    st.markdown('<div class="tdv-panel"><h3>'+title+'</h3><p>'+description+'</p></div>',
                unsafe_allow_html=True)

def normalized(text: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", text).strip().casefold())

def exact_simple_dose(text: str):
    match = re.fullmatch(r"\s*(\d+(?:[.,]\d+)?)\s*(mg|g|mcg|µg)\s*", text, re.I)
    if not match:
        return None
    try:
        value = Decimal(match.group(1).replace(",", "."))
        mul = {"mg":Decimal("1"),"g":Decimal("1000"),
               "mcg":Decimal("0.001"),"µg":Decimal("0.001")}[match.group(2).lower()]
        return value*mul if value>0 else None
    except (InvalidOperation, ValueError):
        return None

with st.container(key="tdv_main_scroll"):
    st.markdown('<div class="tdv-notice">🛡️ <b>TDV QC7 ONLINE — BẢN DEMO ĐANG NGHIỆM THU.</b>'
                ' Chưa có xác thực nghiệp vụ, kho dữ liệu dùng chung hoặc đồng bộ Google Sheets.'
                ' Tuyệt đối không tải hồ sơ đấu thầu, GMP hay báo giá thật vào bản này.</div>',
                unsafe_allow_html=True)
    st.markdown(f'<div class="tdv-crumb">🏠 TDV QC7 &nbsp;›&nbsp; {page}</div>',
                unsafe_allow_html=True)
    if page == PAGES[0]:
        st.markdown('<div class="tdv-page-title">🏛️ Tổng quan điều hành · Dữ liệu của dự án</div>',
                    unsafe_allow_html=True)
        cols = st.columns(4)
        for col, name in zip(cols,
            ["Mã E-HSMT xác minh","Sản phẩm NSX","Chứng cứ GMP","Ứng viên đã duyệt"]):
            col.metric(name,"—",help="Chưa kết nối dữ liệu nghiệp vụ đã kiểm chứng")
        a,b=st.columns(2)
        with a:
            panel("📄 E-HSMT và danh mục thầu",
                  "Đọc đa tầng; kiểm chứng hoạt chất, hàm lượng, nhóm, số lượng, đơn giá và chứng cứ nguồn.")
            panel("🔬 TDV-IDP 3.0",
                  "Phát hiện mâu thuẫn; lưu vị trí trang/ô; đưa trường chưa chắc chắn vào luồng xác minh.")
        with b:
            panel("🏭 Hồ sơ NSX, GMP và báo giá",
                  "Liên kết đúng pháp nhân, nhà máy, dây chuyền, SĐK và lịch sử văn bản.")
            panel("🛡️ Phê duyệt và báo cáo lãnh đạo",
                  "Phân quyền duyệt, nhật ký thay đổi; giá dự thầu chỉ do người có thẩm quyền quyết định.")
        st.info("Các số liệu E-HSMT và NSX sẽ chỉ hiện sau khi kết nối kho nghiệp vụ và nghiệm thu phân quyền.")
    elif page == PAGES[3]:
        st.markdown('<div class="tdv-page-title">🔬 TDV-IDP 3.0 · Kiểm chứng dữ liệu</div>',
                    unsafe_allow_html=True)
        st.info("Chế độ trình diễn một quy tắc nhỏ; không phải bộ đọc PDF/OCR hoàn chỉnh.")
        left,right=st.columns(2)
        with left:
            a=st.text_input("Hoạt chất E-HSMT (dữ liệu mẫu)",value="Acenocoumarol")
            x=st.text_input("Hàm lượng E-HSMT",value="1 mg")
        with right:
            b=st.text_input("Hoạt chất NSX (dữ liệu mẫu)",value="Acenocoumarol")
            y=st.text_input("Hàm lượng NSX",value="4 mg")
        if st.button("Kiểm tra mẫu",type="primary"):
            dx,dy=exact_simple_dose(x),exact_simple_dose(y)
            if not a.strip() or not b.strip() or dx is None or dy is None:
                st.warning("Không đủ dữ liệu/đơn vị chưa hỗ trợ — cần xác minh.")
            elif normalized(a)==normalized(b) and dx==dy:
                st.success("Hai trường mẫu khớp; chưa đủ để kết luận đáp ứng E-HSMT.")
            else:
                st.error("Sai khác hoạt chất hoặc hàm lượng — không tự ghép ứng viên.")
        st.caption("Chưa xử lý tên muối, phối hợp hoạt chất, dạng bào chế, đường dùng và pháp lý GMP.")
    elif page == PAGES[-1]:
        st.markdown('<div class="tdv-page-title">☁️ Tiến độ Online</div>',unsafe_allow_html=True)
        st.table([
            {"Hạng mục":"Giao diện / menu","Trạng thái":"Preview có giao diện"},
            {"Hạng mục":"Quyền xem Streamlit","Trạng thái":"Thiết lập riêng tư; cần duy trì kiểm tra"},
            {"Hạng mục":"GitHub","Trạng thái":"Nhánh thử nghiệm, không chứa dữ liệu mật"},
            {"Hạng mục":"Đăng nhập và phân quyền nghiệp vụ","Trạng thái":"CHƯA TÍCH HỢP"},
            {"Hạng mục":"Google Sheets","Trạng thái":"CHƯA KẾT NỐI / KHÔNG GHI"},
            {"Hạng mục":"Dữ liệu và kho chứng cứ","Trạng thái":"CHƯA KẾT NỐI"},
            {"Hạng mục":"Bộ đọc đa tầng IDP 3.0","Trạng thái":"CHƯA TÍCH HỢP BẢN CLOUD"},
        ])
        st.warning("Không cho phép vận hành hồ sơ thật khi chưa hoàn thành dữ liệu, xác thực và kiểm thử an toàn.")
    else:
        st.markdown('<div class="tdv-page-title">'+page+'</div>',unsafe_allow_html=True)
        st.markdown('<div class="tdv-empty"><b>Phân hệ đang tích hợp trên TDV QC7 Online.</b>'
                    '<br>Không nhập hoặc hiển thị dữ liệu nhà sản xuất, E-HSMT hoặc giá dự thầu thật ở bản này.'
                    '</div>',unsafe_allow_html=True)
        for name, desc in [
            ("📁 Tiếp nhận và lưu hồ sơ gốc", "Dự kiến: phát hiện file trùng, ghi dấu SHA-256, lịch sử."),
            ("🔎 Đọc – kiểm chứng – chuẩn hóa", "Dự kiến: nhiều bộ đọc, chứng cứ trang/ô, cảnh báo."),
            ("✅ Xét duyệt và báo cáo", "Dự kiến: quy trình người duyệt, phiên bản và nhật ký.")]:
            panel(name, desc)
    st.divider()
    st.caption("© DUBIPHARMA DŨNG BÍCH · TDV QC7 / IDP 3.0 · Bản xem trước bảo mật")
