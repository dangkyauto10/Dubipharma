"""TDV QC7 · NSX automatic, source-first batch review (read-only).

Same operational approach as SEE PRO: upload a batch once, autodetect document
roles and products, link only unambiguous evidence, export traceable results.
No manual preclassification, product picker, cloud writes, or business approval.
"""
from __future__ import annotations

import hashlib
import json

import streamlit as st

from see_pro_multiformat import ACCEPTED
from tdv_nsx_auto import analyze_auto, export_auto_xlsx
from tdv_nsx_intake import KINDS

MAX_FILES = 24


def _signature(files: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    for name, data in files:
        digest.update(name.encode("utf-8"))
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def render_nsx_workbench() -> None:
    st.markdown("### SEE PRO · Hồ sơ NSX & Báo giá — đọc tự động")
    st.caption(
        "Nạp cả bộ hồ sơ một lần. SEE PRO tự nhận diện tài liệu, phát hiện "
        "các thuốc, đối chiếu định danh và đưa các vấn đề chưa rõ vào danh sách cần xem lại."
    )
    st.warning(
        "Preview chưa có đăng nhập và phân quyền doanh nghiệp. Tệp được xử lý "
        "trên máy chủ Streamlit. Chỉ sử dụng tài liệu công khai hoặc đã ẩn "
        "thông tin nhạy cảm và được phép xử lý trên Preview này. "
        "Không tự gửi Gemini, không ghi Google Drive hoặc Google Sheets."
    )
    allowed = st.checkbox(
        "Xác nhận bộ hồ sơ được phép xử lý trên máy chủ Preview "
        "và không chứa dữ liệu mật của doanh nghiệp",
        value=False, key="tdv_nsx_real_allowed_preview",
    )
    if not allowed:
        st.session_state.pop("tdv_nsx_auto_report", None)
        st.session_state.pop("tdv_nsx_auto_signature", None)
        st.info("Xác nhận phạm vi bảo mật trước khi nạp một bộ hồ sơ.")
        return

    uploads = st.file_uploader(
        "Nạp cả bộ hồ sơ NSX / GMP / SĐK / ủy quyền / báo giá",
        type=list(ACCEPTED), accept_multiple_files=True,
        key="tdv_nsx_auto_batch",
        help="Chọn nhiều tệp cùng lúc. Không cần phân loại tệp hoặc chọn sản phẩm.",
    )
    files = [(f.name, f.getvalue()) for f in uploads or []]
    if len(files) > MAX_FILES:
        st.error(f"Mỗi lần nhận tối đa {MAX_FILES} tài liệu; cần chia thành các đợt hồ sơ.")
        return
    if not files:
        st.caption("Chưa có tài liệu để đọc.")
        return

    digest = _signature(files)
    if st.session_state.get("tdv_nsx_auto_signature") != digest:
        st.session_state.pop("tdv_nsx_auto_report", None)
        st.session_state.pop("tdv_nsx_auto_signature", None)
    st.caption(
        f"Đã nhận {len(files)} tệp. Loại tài liệu và số thuốc sẽ được nhận diện tự động."
    )
    if st.button(
        "🔍 Đọc và kiểm toán toàn bộ hồ sơ NSX",
        key="tdv_nsx_auto_analyze", type="primary",
    ):
        with st.spinner("Tự phân loại, trích xuất, liên kết và lập kiểm toán nguồn..."):
            try:
                report = analyze_auto(files, enable_ocr=True)
            except Exception as exc:
                st.error(
                    f"Không hoàn tất lượt đọc ({type(exc).__name__}). "
                    "Tệp nguồn vẫn được giữ nguyên; kiểm tra định dạng và dung lượng."
                )
                return
        st.session_state["tdv_nsx_auto_report"] = report
        st.session_state["tdv_nsx_auto_signature"] = digest

    report = st.session_state.get("tdv_nsx_auto_report")
    if not report or st.session_state.get("tdv_nsx_auto_signature") != digest:
        return

    stats = report["summary"]
    metrics = st.columns(5)
    for col, (label, value) in zip(metrics, (
        ("Tài liệu", stats["files"]),
        ("Đọc được", stats["parsed"]),
        ("Thuốc nhận diện", stats["products"]),
        ("Liên kết sơ bộ", stats["linked"]),
        ("Cần kiểm tra", stats["review"]),
    )):
        col.metric(label, value)

    st.markdown("**1. Tài liệu tự nhận diện**")
    st.dataframe([
        {
            "Tệp": d["filename"],
            "Loại gợi ý": d["kind_label"],
            "Trạng thái phân loại": d["role_confidence"],
            "Đọc đủ": d["complete_read"],
            "SHA256": d["sha256"],
            "Lưu Drive": "KHÓA",
        }
        for d in report["files"]
    ], hide_index=True, use_container_width=True)

    st.markdown("**2. Danh mục thuốc phát hiện trong bộ hồ sơ**")
    if report["products"]:
        st.dataframe([
            {
                "Mã": p["uid"],
                "Tên thuốc": p["fields"].get("PRODUCT_NAME", ""),
                "Mã sản phẩm": p["fields"].get("PRODUCT_ID", ""),
                "SĐK": p["fields"].get("REGISTRATION_NO", ""),
                "Hoạt chất": p["fields"].get("INGREDIENT", ""),
                "Hàm lượng": p["fields"].get("STRENGTH", ""),
                "NSX": p["fields"].get("MANUFACTURER", ""),
                "Nhà máy": p["fields"].get("FACTORY", ""),
                "Nguồn": p["file"],
                "Vị trí": p["origin"],
                "Trạng thái": "CHƯA XÁC MINH",
            } for p in report["products"]
        ], hide_index=True, use_container_width=True)
    else:
        st.warning("Chưa nhận diện chắc chắn được danh mục thuốc. Hệ thống không tự tạo sản phẩm giả.")

    st.markdown("**3. Liên kết chứng cứ đề xuất**")
    if report["links"]:
        st.dataframe([
            {
                "Thuốc": link["product_id"],
                "Loại": KINDS.get(link["evidence_kind"], link["evidence_kind"]),
                "Nguồn": link["source_evidence"],
                "Vị trí": link["evidence_origin"],
                "Trường khớp": ", ".join(link["match_fields"]),
                "Kết quả": link["status"],
                "Giải thích": link["reason"],
            } for link in report["links"]
        ], hide_index=True, use_container_width=True)
    else:
        st.info("Chưa có liên kết chứng cứ đủ duy nhất; không tự gán GMP/giá/SĐK.")

    st.markdown("**4. Các điểm chưa rõ và cần xác minh**")
    if report["review_queue"]:
        st.dataframe([
            {
                "Tệp": item["file"],
                "Loại": KINDS.get(item["kind"], item["kind"]),
                "Vị trí": item["origin"],
                "Trạng thái": item["status"],
                "Thuốc liên quan": ", ".join(item["candidate_products"]),
                "Lý do": item["reason"],
            } for item in report["review_queue"]
        ], hide_index=True, use_container_width=True)
    else:
        st.success("Không phát sinh mục mơ hồ trong các kiểm tra định danh đã thực hiện.")
    st.caption(
        "Không có cảnh báo định danh không đồng nghĩa hồ sơ đáp ứng E-HSMT. "
        "GMP, SĐK, ủy quyền và giá chưa được thẩm định hoặc phê duyệt."
    )

    with st.expander("Truy xuất chứng cứ gốc từng trường"):
        traces = []
        for p in report["products"]:
            for field, source in p["evidence"].items():
                traces.append({
                    "Tệp": p["file"], "Thuốc": p["uid"], "Trường": field,
                    "Giá trị": source["value"], "Vị trí": source["source"],
                    "Trích gốc": source["raw"], "SHA256": source["sha256"],
                })
        for d in report["sources"]:
            for field, source in d.get("evidence", {}).items():
                traces.append({
                    "Tệp": d["filename"], "Thuốc": "", "Trường": field,
                    "Giá trị": source["value"], "Vị trí": source["source"],
                    "Trích gốc": source["raw"], "SHA256": source["sha256"],
                })
        if traces:
            st.dataframe(traces, hide_index=True, use_container_width=True)
        else:
            st.info("Chưa có trường dữ liệu với vị trí nguồn đủ rõ.")

    if report["warnings"]:
        with st.expander(f"Cảnh báo kỹ thuật và giới hạn đọc ({len(report['warnings'])})"):
            for warning in report["warnings"][:100]:
                st.warning(warning)

    st.download_button(
        "Tải Excel kiểm toán NSX có chứng cứ (6 Sheet)",
        data=export_auto_xlsx(report),
        file_name="TDV_NSX_SEE_PRO_KIEM_TOAN.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="tdv_nsx_auto_excel",
    )
    st.download_button(
        "Tải JSON chứng cứ có cấu trúc",
        data=json.dumps(report, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name="TDV_NSX_SEE_PRO_KIEM_TOAN.json",
        mime="application/json",
        key="tdv_nsx_auto_json",
    )
