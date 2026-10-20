"""TDV QC7 Online · isolated real-document NSX intake UI.

The old DEMO remains available and unchanged under its own expander.
The new view is source-first, provisional and read-only.
"""
from __future__ import annotations

import hashlib
import json

import streamlit as st

from see_pro_multiformat import ACCEPTED
from tdv_nsx_intake import (
    KINDS, analyze_nsx_documents, export_nsx_xlsx,
)


def _uploads_signature(assets: list[tuple[str, str, bytes]], ocr: bool) -> str:
    digest = hashlib.sha256()
    digest.update(b"OCR-ON" if ocr else b"OCR-OFF")
    for kind, name, raw in assets:
        digest.update(kind.encode("utf-8"))
        digest.update(name.encode("utf-8"))
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(hashlib.sha256(raw).digest())
    return digest.hexdigest()


def render_nsx_workbench() -> None:
    st.markdown("### Hồ sơ NSX và Báo giá · Tiếp nhận tài liệu thật")
    st.info(
        "**Giai đoạn 1 – đọc, kiểm kê và liên kết chứng cứ sơ bộ.** "
        "Chấp nhận PDF, DOCX, XLSX, XLS, CSV và ảnh khi bật OCR. "
        "KHÔNG tự xác nhận GMP, SĐK, hiệu lực ủy quyền hoặc giá chào thầu."
    )
    st.warning(
        "Tệp được chuyển tới **máy chủ ứng dụng Streamlit** để xử lý trong phiên; "
        "chưa có kho lưu có phân quyền của doanh nghiệp. "
        "Chỉ tải hồ sơ mà V có quyền xử lý trên máy chủ này. "
        "Chế độ này không tự gửi tới Gemini hoặc ghi Google Drive/Sheets."
    )
    allowed = st.checkbox(
        "Tôi xác nhận tài liệu dùng thử là tài liệu công khai hoặc đã ẩn thông tin nhạy cảm, "
        "và được phép xử lý trên máy chủ Preview này.",
        value=False, key="tdv_nsx_real_allowed_preview",
    )
    if not allowed:
        st.info(
            "Chức năng đọc hồ sơ thật đã có, nhưng Preview chưa tích hợp đăng nhập và "
            "phân quyền doanh nghiệp. Hãy xác nhận phạm vi dữ liệu được phép thử "
            "trước khi chọn tệp. Không đưa tài liệu mật hoặc báo giá nội bộ lên Preview."
        )
        st.session_state.pop("tdv_nsx_real_report", None)
        st.session_state.pop("tdv_nsx_real_signature", None)
        return

    product = st.file_uploader(
        "1. Hồ sơ sản phẩm tân dược (mỗi lần một sản phẩm)",
        type=list(ACCEPTED), key="tdv_nsx_real_product",
        help="Hãy chọn hồ sơ có tên thuốc, SĐK/mã sản phẩm, NSX, nhà máy nếu có.",
    )
    st.caption("Các hồ sơ bổ sung có thể thiếu; hệ thống sẽ ghi đúng là chưa đủ chứng cứ.")
    attachments: list[tuple[str, object]] = []
    for kind, caption in (
        ("REGISTRATION", "2. Đăng ký lưu hành / tài liệu SĐK"),
        ("GMP_CERT", "3. Giấy chứng nhận GMP"),
        ("GMP_EXPLANATION", "4. Giải trình về GMP"),
        ("AUTHORIZATION", "5. Giấy ủy quyền"),
        ("QUOTE", "6. Báo giá nhà cung cấp"),
        ("OTHER", "7. Catalogue và tài liệu khác"),
    ):
        files = st.file_uploader(
            caption, type=list(ACCEPTED), accept_multiple_files=True,
            key=f"tdv_nsx_real_{kind}",
        )
        attachments.extend((kind, file) for file in files or [])
    ocr = st.checkbox(
        "Bật OCR trên ảnh/PDF scan (phải xem lại hình gốc)",
        value=False, key="tdv_nsx_real_ocr",
    )

    assets = []
    if product is not None:
        assets.append(("PRODUCT", product.name, product.getvalue()))
    for kind, entry in attachments:
        assets.append((kind, entry.name, entry.getvalue()))
    if len(assets) > 24:
        st.error("Tối đa 24 tệp mỗi lần phân tích. Hãy chia theo sản phẩm.")
        return
    if not assets:
        st.caption("Chưa có hồ sơ; V có thể thử bộ DEMO cũ ở phần bên dưới.")
        return

    signature = _uploads_signature(assets, ocr)
    if st.session_state.get("tdv_nsx_real_signature") != signature:
        st.session_state.pop("tdv_nsx_real_report", None)
    if st.button(
        "Đọc hồ sơ NSX và lập bản kiểm toán nguồn",
        type="primary", disabled=product is None,
        key="tdv_nsx_real_analyze",
    ):
        with st.spinner("Đọc từng tệp và kiểm tra định danh, chứng cứ..."):
            report = analyze_nsx_documents(assets, enable_ocr=ocr)
        st.session_state["tdv_nsx_real_report"] = report
        st.session_state["tdv_nsx_real_signature"] = signature

    report = st.session_state.get("tdv_nsx_real_report")
    if not report or st.session_state.get("tdv_nsx_real_signature") != signature:
        return

    product_preview = report["product"]
    candidates = product_preview.get("catalogue_candidates") or []
    if candidates:
        st.markdown("**Danh mục sản phẩm nhận diện theo cột – không tự chọn nhầm thuốc**")
        st.dataframe([{
            "Dòng": item["row"], "Bảng/Sheet": item["table"],
            "Mã sản phẩm": item["fields"].get("PRODUCT_ID", ""),
            "SĐK": item["fields"].get("REGISTRATION_NO", ""),
            "Tên thuốc": item["fields"].get("PRODUCT_NAME", ""),
            "Hoạt chất": item["fields"].get("INGREDIENT", ""),
            "Hàm lượng": item["fields"].get("STRENGTH", ""),
            "Nhà sản xuất": item["fields"].get("MANUFACTURER", ""),
            "Nhà máy": item["fields"].get("FACTORY", ""),
        } for item in candidates], hide_index=True, use_container_width=True)
        st.caption(
            "Các mã thuốc lấy từ đúng hàng/cột trong tài liệu; "
            "chưa được coi là đã xác minh nghiệp vụ.")
        if len(candidates) > 1:
            choices = list(range(len(candidates)))
            chosen = st.selectbox(
                "Chọn dòng sản phẩm để kiểm tra liên kết GMP/SĐK/báo giá",
                choices,
                format_func=lambda i: (
                    f"{candidates[i]['table']}, dòng {candidates[i]['row']} · "
                    f"{candidates[i]['fields'].get('PRODUCT_NAME') or candidates[i]['fields'].get('PRODUCT_ID') or candidates[i]['fields'].get('REGISTRATION_NO') or 'Chưa đủ mã'}"
                ),
                index=(report["product"].get("catalogue_selected_index") or 0),
                key=f"tdv_nsx_real_pick_{signature[:14]}",
            )
            if st.button(
                "Xác nhận dòng đã chọn và đối chiếu lại chứng cứ",
                key="tdv_nsx_real_recheck_selected",
            ):
                with st.spinner("Kiểm tra lại đúng sản phẩm được chọn..."):
                    report = analyze_nsx_documents(
                        assets, enable_ocr=ocr, selected_product_index=chosen,
                    )
                st.session_state["tdv_nsx_real_report"] = report
                st.session_state["tdv_nsx_real_signature"] = signature
            if report["product"].get("catalogue_selection_required"):
                st.warning(
                    "Chưa chọn sản phẩm cụ thể: mọi chứng cứ GMP/báo giá phải ở trạng thái CHƯA LIÊN KẾT."
                )

    summary = report["summary"]
    a, b, c, d = st.columns(4)
    a.metric("Tài liệu", summary["files_received"])
    b.metric("Đọc được", summary["files_parsed"])
    c.metric("Liên kết sơ bộ", summary["links_provisional"])
    d.metric("Xung đột định danh", summary["links_conflicted"])
    st.warning(
        "Ngay cả khi định danh khớp, đó chỉ là liên kết sơ bộ. "
        "Chưa kiểm chứng chữ ký, thời hạn, phạm vi, cơ quan cấp hoặc tính hợp pháp."
    )

    product_data = report["product"]
    if "error" in product_data:
        st.error("Hồ sơ sản phẩm không đọc được. Không có liên kết nào được xác nhận.")
    else:
        p = product_data["fields"]
        st.markdown("**Thông tin sản phẩm nhận diện từ nguồn**")
        st.dataframe([{
            "Mã sản phẩm": p.get("PRODUCT_ID", ""),
            "SĐK": p.get("REGISTRATION_NO", ""),
            "Tên thuốc": p.get("PRODUCT_NAME", ""),
            "Hoạt chất": p.get("INGREDIENT", ""),
            "Hàm lượng": p.get("STRENGTH", ""),
            "Dạng bào chế": p.get("DOSAGE_FORM", ""),
            "Đường dùng": p.get("ROUTE", ""),
            "Nhà sản xuất": p.get("MANUFACTURER", ""),
            "Nhà máy": p.get("FACTORY", ""),
            "Trạng thái": "CHƯA XÁC MINH",
        }], hide_index=True, use_container_width=True)
        if product_data["conflicts"]:
            st.error("Có trường sản phẩm mâu thuẫn trong chính hồ sơ: " +
                     ", ".join(product_data["conflicts"]))

    st.markdown("**Kiểm kê tài liệu và tình trạng liên kết**")
    inventory = [{
        "Loại": item["kind_label"] if "kind_label" in item else KINDS.get(item["kind"], ""),
        "Tệp": item["filename"],
        "Định dạng": item.get("type", ""),
        "SHA256": item["sha256"],
        "Đọc đầy đủ": item.get("complete_read", False),
        "Xác minh": "CHƯA",
    } for item in [report["product"]] + report["documents"]]
    st.dataframe(inventory, hide_index=True, use_container_width=True)

    if report["links"]:
        st.markdown("**Đối chiếu định danh giữa hồ sơ sản phẩm và chứng cứ**")
        st.dataframe([{
            "Tệp chứng cứ": c["filename"],
            "Loại": KINDS.get(c["kind"], c["kind"]),
            "Kết quả": c["status"],
            "Trường khớp": ", ".join(c.get("matching_fields", [])),
            "Trường xung đột": ", ".join(c.get("conflicting_fields", [])),
            "Cần xác minh": "; ".join(c["reasons"]),
        } for c in report["links"]], hide_index=True, use_container_width=True)

    with st.expander("Xem chứng cứ theo từng trường và vị trí nguồn"):
        rows = []
        for item in [report["product"]] + report["documents"]:
            for field, proof in item.get("evidence", {}).items():
                rows.append({
                    "Tệp": item["filename"], "Trường": field,
                    "Giá trị": proof["value"], "Vị trí": proof["source"],
                    "Trích gốc": proof["raw"], "Xác minh": "CHƯA",
                })
            for field, proofs in item.get("conflicts", {}).items():
                for proof in proofs:
                    rows.append({
                        "Tệp": item["filename"], "Trường": field + " / MÂU THUẪN",
                        "Giá trị": proof["value"], "Vị trí": proof["source"],
                        "Trích gốc": proof["raw"], "Xác minh": "CHƯA",
                    })
        if rows:
            st.dataframe(rows, hide_index=True, use_container_width=True)
        else:
            st.info("Chưa trích được trường có nhãn rõ ràng; cần so ảnh/bảng nguồn.")

    if report["warnings"]:
        with st.expander(f"Cảnh báo và phần cần xem lại ({len(report['warnings'])})"):
            for warning in report["warnings"][:100]:
                st.warning(warning)

    st.download_button(
        "Xuất Excel NSX có chứng cứ (4 Sheet, chưa xác minh)",
        data=export_nsx_xlsx(report),
        file_name="TDV_NSX_BAO_GIA_KIEM_TOAN_CHUNG_CU.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="tdv_nsx_real_excel",
    )
    st.download_button(
        "Xuất JSON kiểm toán nguồn (chưa xác minh)",
        data=json.dumps(report, ensure_ascii=False, indent=2, default=str).encode("utf-8"),
        file_name="TDV_NSX_BAO_GIA_CHUNG_CU.json",
        mime="application/json", key="tdv_nsx_real_json",
    )
