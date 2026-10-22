"""TDV QC7 readable, source-preserving tabular presentation.

HTML is used only for display because Streamlit's canvas dataframe cannot
guarantee table-cell text alignment and wrapping via CSS. Every value/header
is HTML-escaped, no Javascript, no file or network operations.
The original native dataframe remains available separately for exploration.
"""
from __future__ import annotations

from html import escape
from math import ceil, isnan
from typing import Any, Sequence

LONG_COLUMNS = (
    "SHA256", "TRICH_DAN", "TRÍCH DẪN", "HƯỚNG XỬ LÝ", "FILE_NGUON",
    "TỆP", "TÊN TÀI LIỆU", "NGUỒN", "VĂN BẢN", "CHI TIẾT",
    "REASON", "MÔ TẢ", "GIẢI THÍCH", "CẢNH BÁO",
)


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and isnan(value):
        return ""
    if isinstance(value, bool):
        return "Có" if value else "Không"
    return str(value)


def _is_wide(column: str) -> bool:
    return any(x in column.upper() for x in LONG_COLUMNS)


def build_table_html(
    columns: Sequence[str],
    records: Sequence[dict],
    *,
    label: str = "Bảng dữ liệu",
    min_width: int = 800,
) -> str:
    """Return scoped accessible table markup, no hidden data transformations.

    Labels and values, including user-supplied PDF names and excerpts, must
    remain inert and readable. Long cells wrap, not clipped or discarded.
    """
    keys = [str(column) for column in columns]
    heads = "".join(
        '<th scope="col" class="' + ("tdv-wide" if _is_wide(key) else "tdv-center") +
        '">' + escape(key) + "</th>" for key in keys
    )
    body = []
    for record in records:
        cells = []
        for key in keys:
            source = _as_text(record.get(key, ""))
            wide = _is_wide(key)
            cls = "tdv-wide" if wide else "tdv-center"
            # The title tooltip preserves access to full hashes/document names.
            cells.append(
                '<td class="' + cls + '" title="' + escape(source, quote=True) +
                '">' + (escape(source) if source else '<span class="tdv-missing">—</span>') +
                "</td>"
            )
        body.append("<tr>" + "".join(cells) + "</tr>")
    if not body:
        body = ['<tr><td colspan="' + str(max(1, len(keys))) +
                '" class="tdv-empty">Không có dòng dữ liệu phù hợp</td></tr>']
    # CSS styles are scoped to this component class; no global Streamlit hacks.
    style = """
<style>
.tdv-proof-scroll{max-height:510px;overflow:auto;width:100%;border:1px solid #cadae8;
 border-radius:12px;background:#fff;box-shadow:0 2px 7px rgba(24,58,92,.05);}
.tdv-proof-table{border-collapse:separate;border-spacing:0;table-layout:auto;
 font-family:system-ui,-apple-system,'Segoe UI',sans-serif;font-size:14px;
 line-height:1.48;color:#182f49;width:100%;}
.tdv-proof-table th{position:sticky;top:0;z-index:2;background:#e8f1fc;color:#103a6f;
 font-size:13.5px;font-weight:750;text-align:center!important;vertical-align:middle;
 letter-spacing:0.01em;line-height:1.45;white-space:normal;
 padding:12px 11px;border-right:1px solid #c8d9eb;border-bottom:2px solid #9bbddd;}
.tdv-proof-table td{font-size:14px;color:#182f49;font-weight:550;line-height:1.5;
 padding:11px 11px;border-right:1px solid #e2eaf3;border-bottom:1px solid #e4edf5;
 vertical-align:middle!important;white-space:normal;overflow-wrap:anywhere;}
.tdv-proof-table th.tdv-wide,.tdv-proof-table td.tdv-wide{min-width:185px;max-width:330px;
 text-align:left;}
.tdv-proof-table th.tdv-wide{text-align:center!important;}
.tdv-proof-table th.tdv-center,.tdv-proof-table td.tdv-center{text-align:center!important;
 min-width:112px;max-width:215px;}
.tdv-proof-table tbody tr:nth-child(even){background:#f6f9fd;}
.tdv-proof-table tbody tr:hover{background:#e9f4ff;}
.tdv-proof-table .tdv-missing{color:#74889d;font-weight:450;}
.tdv-proof-table .tdv-empty{text-align:center;padding:22px;}
@media(max-width:650px){
 .tdv-proof-table{font-size:13px;}
 .tdv-proof-table td{font-size:13px;padding:9px;}
 .tdv-proof-table th{font-size:12.5px;padding:9px;}
}
</style>"""
    table = (
        '<div class="tdv-proof-scroll" role="region" tabindex="0" aria-label="' +
        escape(label, quote=True) + '"><table class="tdv-proof-table" style="min-width:' +
        str(max(320, int(min_width))) + 'px"><thead><tr>' + heads +
        '</tr></thead><tbody>' + "".join(body) + "</tbody></table></div>"
    )
    return style + table


def render_readable_table(st, frame, *, key: str, label: str,
                          page_size: int = 25, min_width: int = 800) -> None:
    """Centered read-only first view; paginated for large tables.

    Keeps full records untouched and an independent native dataframe with
    original source strings, searches and downloads outside this renderer.
    """
    if frame is None or frame.empty:
        st.info("Không có dòng phù hợp để hiển thị.")
        return
    if page_size < 1:
        raise ValueError("page_size phải dương")
    pages = max(1, ceil(len(frame) / page_size))
    page_key = key + "_page"
    if page_key in st.session_state and st.session_state[page_key] not in range(1, pages + 1):
        st.session_state[page_key] = 1
    if pages > 1:
        page = st.selectbox(
            "Trang bảng kết quả", list(range(1, pages + 1)),
            format_func=lambda v: f"Trang {v}/{pages}",
            key=page_key, label_visibility="visible",
        )
    else:
        page = 1
    start = (page - 1) * page_size
    end = min(start + page_size, len(frame))
    subset = frame.iloc[start:end].fillna("")
    html = build_table_html(
        [str(c) for c in frame.columns],
        subset.to_dict(orient="records"), label=label, min_width=min_width)
    st.markdown(html, unsafe_allow_html=True)
    st.caption(
        f"Đang xem dòng {start + 1}–{end} / {len(frame)}. "
        "Các giá trị đầy đủ và chứng cứ gốc không bị thay đổi."
    )
    with st.expander("Bảng gốc: sắp xếp, sao chép và xem đủ nội dung"):
        st.dataframe(frame, hide_index=True, use_container_width=True)
