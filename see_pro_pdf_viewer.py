"""Original-PDF evidence viewer for SEE PRO, not based on AI-created images.

Pages are rasterized from the exact PDF bytes still in the user's upload.
No remote fetch, API upload, PDF modification or document persistence.
"""
from __future__ import annotations

import hashlib
from typing import Any

MAX_PDF_BYTES = 40 * 1024 * 1024


def read_original_pdf_page(
    content: bytes, page_number: int, *,
    expected_sha256: str | None = None, dpi: int = 120,
) -> dict:
    import pymupdf

    if not isinstance(content, bytes) or not content.startswith(b"%PDF-"):
        raise ValueError("Tệp không có định dạng PDF hợp lệ")
    if not content or len(content) > MAX_PDF_BYTES:
        raise ValueError("Tệp PDF rỗng hoặc vượt giới hạn 40 MB")
    if not isinstance(page_number, int) or isinstance(page_number, bool):
        raise ValueError("Số trang không hợp lệ")
    if not isinstance(dpi, int) or not 72 <= dpi <= 160:
        raise ValueError("Độ phân giải trang không hợp lệ")
    digest = hashlib.sha256(content).hexdigest()
    if expected_sha256 and expected_sha256 != digest:
        raise ValueError("SHA256 không khớp với tệp nguồn ban đầu")
    with pymupdf.open(stream=content, filetype="pdf") as doc:
        if doc.needs_pass or not doc.page_count:
            raise ValueError("PDF bị khóa hoặc không có trang")
        if doc.page_count > 1_200:
            raise ValueError("PDF vượt giới hạn 1.200 trang")
        if page_number < 1 or page_number > doc.page_count:
            raise ValueError(f"Trang yêu cầu nằm ngoài phạm vi 1–{doc.page_count}")
        page = doc[page_number - 1]
        pix = page.get_pixmap(dpi=dpi, alpha=False)
        if pix.width * pix.height > 4_000_000:
            raise ValueError("Ảnh trang vượt giới hạn an toàn")
        return {
            "png": pix.tobytes("png"),
            "page": page_number, "total_pages": doc.page_count,
            "sha256": digest, "width": pix.width, "height": pix.height,
            "verified_technical": False,
        }


def _integer_page(value: Any) -> int | None:
    try:
        if isinstance(value, bool):
            return None
        if isinstance(value, int):
            return value if value > 0 else None
        if isinstance(value, str) and value.isdigit():
            number = int(value)
            return number if number > 0 else None
    except (ValueError, TypeError):
        pass
    return None


def render_original_pdf_viewer(uploaded_files, analysis: dict) -> None:
    """Accessible PDF and lot-linked evidence lookup inside existing E-HSMT."""
    import streamlit as st

    pdfs = []
    for index, item in enumerate(uploaded_files):
        if item.name.lower().endswith(".pdf"):
            data = item.getvalue()
            pdfs.append({"label": f"{item.name}  [tệp {index+1}, {hashlib.sha256(data).hexdigest()[:10]}]",
                         "filename": item.name, "sha256": hashlib.sha256(data).hexdigest(),
                         "content": data})
    if not pdfs:
        return
    with st.expander("🔍 SEE PRO · Xem trang PDF gốc và truy xuất chứng cứ", expanded=False):
        st.caption("Ảnh được kết xuất trực tiếp từ PDF gốc V đã tải. Không dùng ảnh AI tự tạo và không chỉnh sửa nội dung tệp.")
        titles = [x["label"] for x in pdfs]
        selected = st.selectbox("Chọn tài liệu PDF nguồn", titles, key="tdv_see_pro_source_file")
        file_info = pdfs[titles.index(selected)]
        raw = file_info["content"]
        # Check page count without rendering every page.
        try:
            import pymupdf
            with pymupdf.open(stream=raw, filetype="pdf") as pdf:
                if pdf.needs_pass or not pdf.page_count:
                    st.warning("PDF cần mật khẩu hoặc rỗng.")
                    return
                page_total = pdf.page_count
        except (ValueError, RuntimeError, OSError) as exc:
            st.warning(f"Không mở được tệp nguồn: {type(exc).__name__}")
            return

        # Selectable anchors are populated ONLY from locally extracted rows.
        # Repeated page citations are harmless; duplicates are deduplicated.
        seen = set()
        references = []
        for row in analysis.get("rows", []):
            if row.get("FILE_NGUON") != file_info["filename"]:
                continue
            candidate = _integer_page(row.get("TRANG_BANG_KY_THUAT"))
            position = "Bảng kỹ thuật"
            if candidate is None:
                candidate = _integer_page(row.get("TRANG_VI_TRI"))
                position = "Bảng tổng hợp"
            if candidate is None or candidate > page_total:
                continue
            key = (row.get("MA_THUOC"), row.get("MA_PHAN_LO"), candidate)
            if key in seen:
                continue
            seen.add(key)
            references.append({
                "label": f"{row.get('MA_THUOC') or row.get('MA_PHAN_LO') or 'Mã chưa rõ'} · "
                         f"Trang {candidate} ({position})",
                "page": candidate,
            })
        direct_label = "Chọn trang thủ công"
        jump = st.selectbox(
            "Nhảy đến trang nguồn theo mã thuốc/phần",
            [direct_label] + [ref["label"] for ref in references],
            key=f"tdv_see_pro_source_lot_{file_info['sha256'][:12]}",
        )
        if jump == direct_label:
            wanted = st.number_input("Số trang PDF (đánh số từ 1)", min_value=1,
                                     max_value=page_total, value=1, step=1,
                                     key=f"tdv_see_pro_source_page_{file_info['sha256'][:12]}")
        else:
            wanted = references[[ref["label"] for ref in references].index(jump)]["page"]
        sharp = st.checkbox("Hiển thị rõ hơn (150 dpi)", value=False,
                            key="tdv_see_pro_source_high_res")
        try:
            displayed = read_original_pdf_page(
                raw, int(wanted), expected_sha256=file_info["sha256"],
                dpi=150 if sharp else 110,
            )
            st.image(displayed["png"], caption=(
                f"{file_info['filename']} · Trang {displayed['page']}/"
                f"{displayed['total_pages']} · SHA256 {displayed['sha256'][:16]}…"),
                use_container_width=True)
            st.caption("Kiểm tra bằng mắt thường trên bản gốc; việc trích dẫn đúng trang chưa xác nhận đáp ứng kỹ thuật.")
        except (ValueError, RuntimeError, OSError) as exc:
            st.warning(f"Không hiển thị được trang gốc: {type(exc).__name__}: {exc}")
