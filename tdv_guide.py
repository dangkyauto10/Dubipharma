"""SEE PRO role-based user handbook in a separate authenticated tab.

Bundled HTML is read from the same QA source revision, so opening and
downloading show identical content. No external hosting or login bypass.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import streamlit.components.v1 as components

GUIDE_FILENAME = "SEE_PRO_CAM_NANG_SU_DUNG_THEO_VAI_TRO_QA_20261023.html"
GUIDE_PATH = Path(__file__).resolve().parent / "assets" / "see_pro_cam_nang_qa_20261023.html"
GUIDE_QUERY_KEY = "see_pro_guide"


@lru_cache(maxsize=1)
def handbook_bytes() -> bytes:
    data = GUIDE_PATH.read_bytes()
    if not (data.lstrip().lower().startswith(b"<!doctype html>")
            and b"</html>" in data.lower()
            and b'data-target="leader"' in data
            and b'data-target="pricing"' in data):
        raise ValueError("Cẩm nang SEE PRO không hợp lệ hoặc thiếu nội dung")
    return data


def guide_requested(st) -> bool:
    return str(st.query_params.get(GUIDE_QUERY_KEY, "")) == "1"


def render_handbook_sidebar(st):
    """Place actions after OIDC; the native anchor opens a real new browser tab."""
    try:
        data = handbook_bytes()
    except (OSError, ValueError):
        st.error("Chưa có tệp hướng dẫn trong bản mã đang chạy.")
        return
    st.markdown("**📘 HƯỚNG DẪN SỬ DỤNG**")
    st.markdown(
        '<a href="?see_pro_guide=1" target="_blank" rel="noopener noreferrer" '
        'style="display:block;text-align:center;padding:11px 12px;'
        'background:#125a98;color:white;font-weight:700;text-decoration:none;'
        'border-radius:9px;border:1px solid #0d4d87;margin:6px 0 8px">'
        '📖 Mở cẩm nang ở tab mới ↗</a>',
        unsafe_allow_html=True,
    )
    st.download_button(
        "⬇️ Tải cẩm nang HTML về máy",
        data=data,
        file_name=GUIDE_FILENAME,
        mime="text/html",
        key="tdv_handbook_download_sidebar",
        use_container_width=True,
    )
    st.caption("Mở tab hướng dẫn cạnh SEE PRO để xem và thực hành đồng thời. "
               "Tài khoản vẫn phải đăng nhập Google được cấp quyền.")


def render_handbook_page(st):
    """Dedicated QA handbook route, subject to app-level OIDC before dispatch."""
    data = handbook_bytes()
    st.markdown(
        '<style>[data-testid="stSidebar"]{display:none!important;}'
        '.block-container{max-width:1500px!important;padding-top:.6rem!important;}'
        '</style>',
        unsafe_allow_html=True,
    )
    st.markdown("### 📘 SEE PRO · Cẩm nang sử dụng theo từng vai trò")
    st.caption("Cẩm nang QA 23/10/2026 · 12 mục · có tìm kiếm và hướng dẫn "
               "Lãnh đạo, cán bộ hồ sơ, người lập giá, người duyệt giá, quản trị.")
    left, right = st.columns([2, 3])
    with left:
        st.download_button(
            "⬇️ Tải toàn bộ cẩm nang HTML",
            data=data,
            file_name=GUIDE_FILENAME,
            mime="text/html",
            key="tdv_handbook_download_page",
            use_container_width=True,
        )
    with right:
        st.markdown(
            '<div style="padding:7px 0;font-size:14px;color:#46617b">'
            'Tab SEE PRO trước đó vẫn mở: chuyển qua lại để làm theo từng bước.'
            '</div>', unsafe_allow_html=True,
        )
    # Streamlit markdown/st.html deliberately strips scripts. A sandboxed
    # component keeps the original trusted guide's search/menu/print JS working.
    components.html(data.decode("utf-8"), height=1040, scrolling=True)
    st.caption("Lưu ý: phần đang QA được đánh dấu trong cẩm nang; "
               "tài liệu không đồng nghĩa hệ thống đã nghiệm thu vận hành.")
