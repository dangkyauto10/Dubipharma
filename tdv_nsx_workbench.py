"""TDV QC7 · NSX automatic, source-first batch review (read-only).

Same operational approach as SEE PRO: upload a batch once, autodetect document
roles and products, link only unambiguous evidence, export traceable results.
No manual preclassification, product picker, cloud writes, or business approval.
"""
from __future__ import annotations

import hashlib
import json

import streamlit as st
import pandas as pd
from tdv_readable_tables import render_readable_table
from tdv_nsx_source_diff import compare_conflict_sources
from tdv_manufacturer_evidence import audit_manufacturer_evidence

from see_pro_multiformat import ACCEPTED
from tdv_see_pro_scope import bind_report, validate_scope
from tdv_nsx_auto import export_auto_xlsx
from tdv_nsx_gmp_guarded_auto import analyze_auto
from tdv_nsx_intake import KINDS
import tdv_nsx_auto as _runtime_auto
import tdv_nsx_intake as _runtime_intake
import tdv_nsx_proof_hints as _runtime_hints

MAX_FILES = 24
NSX_EXPECTED_PIPELINE_VERSION = "2026-10-22J"


def _runtime_revisions() -> dict:
    """Versions of modules actually imported in this Streamlit process."""
    return {
        "intake": getattr(_runtime_intake, "NSX_INTAKE_RUNTIME_REV", None),
        "hints": getattr(_runtime_hints, "NSX_HINTS_RUNTIME_REV", None),
        "auto": getattr(_runtime_auto, "NSX_AUTO_RUNTIME_REV", None),
    }


def _runtime_is_consistent() -> bool:
    return all(value == NSX_EXPECTED_PIPELINE_VERSION
               for value in _runtime_revisions().values())


def _report_from_current_pipeline(report: dict | None, fingerprint: str) -> bool:
    return bool(
        isinstance(report, dict)
        and report.get("analysis_version") == NSX_EXPECTED_PIPELINE_VERSION
        and report.get("analysis_fingerprint") == fingerprint
    )


def _signature(files: list[tuple[str, bytes]]) -> str:
    digest = hashlib.sha256()
    digest.update(b"TDV-QC7-NSX-ANALYSIS\\0")
    digest.update(NSX_EXPECTED_PIPELINE_VERSION.encode("utf-8"))
    digest.update(b"\\0")
    for name, data in files:
        digest.update(name.encode("utf-8"))
        digest.update(len(data).to_bytes(8, "big"))
        digest.update(hashlib.sha256(data).digest())
    return digest.hexdigest()


def diagnose_extracted_documents(report: dict) -> list[dict]:
    """Explain why a parsed file did not yield a product, without exposing
    any unprotected raw NSX/private text in the preview diagnostics."""
    out = []
    for meta, source in zip(report.get("files", []), report.get("sources", [])):
        fields = source.get("fields") or {}
        conflicts = source.get("conflicts") or {}
        kind = meta.get("kind", "OTHER")
        product_ready = (
            kind == "PRODUCT"
            and any(fields.get(k) for k in ("PRODUCT_NAME", "REGISTRATION_NO",
                                            "PRODUCT_ID"))
            and not conflicts
        ) or (
            kind == "REGISTRATION"
            and bool(fields.get("PRODUCT_NAME")) and bool(fields.get("REGISTRATION_NO"))
            and not any(conflicts.get(k) for k in ("PRODUCT_NAME", "REGISTRATION_NO"))
        )
        if meta.get("role_confidence") == "KHÔNG_ĐỌC_ĐƯỢC":
            reason = "TỆP KHÔNG ĐỌC ĐƯỢC"
        elif not source.get("complete_read", False):
            reason = "ĐỌC CHƯA ĐỦ / OCR CẦN XEM"
        elif kind not in ("PRODUCT", "REGISTRATION"):
            reason = "KHÔNG PHẢI NGUỒN DANH MỤC THUỐC TRỰC TIẾP"
        elif conflicts:
            reason = "TRƯỜNG GHI NHIỀU GIÁ TRỊ MÂU THUẪN"
        elif not product_ready:
            reason = "THIẾU TÊN THUỐC HOẶC SĐK CÓ NHÃN / CHỨNG CỨ"
        else:
            reason = "ĐÃ CÓ TRƯỜNG ĐỊNH DANH SƠ BỘ"
        out.append({
            "Tệp": meta.get("filename", ""),
            "Loại nhận diện": meta.get("kind_label", kind),
            "Tên thuốc trong nội dung": "CÓ" if fields.get("PRODUCT_NAME") else "CHƯA TRÍCH",
            "SĐK trong nội dung": "CÓ" if fields.get("REGISTRATION_NO") else "CHƯA TRÍCH",
            "Hoạt chất trong nội dung": "CÓ" if fields.get("INGREDIENT") else "CHƯA TRÍCH",
            "Hàm lượng trong nội dung": "CÓ" if fields.get("STRENGTH") else "CHƯA TRÍCH",
            "Nguyên nhân / bước tiếp": reason,
        })
    return out


def summarize_product_field_coverage(report: dict) -> dict:
    """Count extracted and cited fields per catalogued NSX product.

    Counts are extraction coverage only, not valid registration, legal proof,
    clinical equivalence or tender qualification. Do not leak raw values.
    """
    products = report.get("products") or []
    keys = ("PRODUCT_NAME", "INGREDIENT", "STRENGTH", "DOSAGE_FORM",
            "ROUTE", "REGISTRATION_NO", "MANUFACTURER", "FACTORY")
    counts = {
        key: sum(bool(p.get("fields", {}).get(key)) and
                 bool(p.get("evidence", {}).get(key, {}).get("source"))
                 and key not in (p.get("conflicts") or {})
                 for p in products)
        for key in keys
    }
    return {
        "total": len(products), "fields": counts,
        "linked_evidence": len(report.get("links") or []),
        "source_anchored": True, "verified": False,
    }


def render_nsx_conflict_review(conflicts: list[dict], st_module=None) -> None:
    """Front-end business QA: always show original paired source values first."""
    st_ui = st_module if st_module is not None else st
    st_ui.warning(
        f'{len(conflicts)} ứng viên có trường khác nhau giữa các sheet. '
        'Các trường mâu thuẫn phải giữ trạng thái CHƯA ĐỦ CĂN CỨ '
        'cho đến khi so bản gốc; không tự tô xanh/đỏ.'
    )
    st_ui.caption(
        "NSX · PHIÊN BẢN ĐỐI CHIẾU NGUỒN 2026-10-22B. "
        "Nếu không thấy dòng này, ứng dụng vẫn đang chạy mã cũ."
    )
    source_pairs = compare_conflict_sources(conflicts)
    with st_ui.expander(
        "ĐỐI CHIẾU 2 NGUỒN GỐC — GIÁ TRỊ THỰC TẾ CỦA TỪNG TRƯỜNG",
        expanded=True,
    ):
        if source_pairs:
            st_ui.info(
                f"Đã xuất {len(source_pairs)} cặp giá trị khác nhau. "
                "Mỗi cặp hiển thị nguyên văn hai nguồn và vị trí ô; "
                "KHÔNG tự xác nhận đúng/sai hay gộp thuốc."
            )
            # Display the actual two-sided values FIRST, not after a
            # scrolling 29-product index. Users should never have to
            # guess where the comparison is buried.
            focus_cols = [
                "Mã NSX", "Tên thuốc", "Trường cần đối chiếu",
                "Giá trị nguồn 1", "Ô nguồn 1",
                "Giá trị nguồn 2", "Ô nguồn 2", "Kết luận",
            ]
            st_ui.dataframe(
                pd.DataFrame(source_pairs)[focus_cols],
                hide_index=True, use_container_width=True,
                height=420,
            )
            st_ui.caption(
                "Tên tệp và SHA256 đầy đủ của cả hai nguồn ở bảng chứng cứ "
                "chi tiết phía dưới và sheet Excel MAU_THUAN_GIA_TRI_GOC."
            )
            with st_ui.container(border=True):
                st_ui.markdown("**Nguồn chi tiết: tệp, SHA256 và ô gốc**")
                st_ui.dataframe(
                    pd.DataFrame(source_pairs), hide_index=True,
                    use_container_width=True, height=270,
                )
        else:
            st_ui.error(
                "Có ứng viên mâu thuẫn nhưng KHÔNG TẠO ĐƯỢC BẢNG "
                "GIÁ TRỊ HAI NGUỒN. Đây là lỗi trích dẫn cần kiểm tra, "
                "không được đánh dấu đã xác minh."
            )
    with st_ui.expander(
        "Danh sách tổng hợp 29 ứng viên cần kiểm tra (xem sau bảng hai nguồn)",
        expanded=False,
    ):
        st_ui.dataframe([{
            "Mã": p["uid"], "Tên sản phẩm": p["fields"].get("PRODUCT_NAME", ""),
            "Trường mâu thuẫn": ", ".join(sorted(p["conflicts"])),
            "Số dòng nguồn": len(p.get("source_rows") or []),
            "Trạng thái": "CHƯA XÁC MINH",
        } for p in conflicts], hide_index=True, use_container_width=True)




def render_manufacturer_evidence_review(report: dict, st_module=None) -> None:
    """Integrated read-only audit over the SAME uploaded NSX batch."""
    st_ui = st_module if st_module is not None else st
    audit = audit_manufacturer_evidence(report)
    st_ui.markdown("**3B. Kiểm tra chứng cứ nhà sản xuất trên hồ sơ NSX thật**")
    st_ui.caption(
        "Tự kiểm tra ngay sau khi đọc bộ hồ sơ: SĐK, GMP, giải trình GMP, "
        "ủy quyền và báo giá. Dùng chính tệp nguồn, SHA256 và vị trí trích xuất; "
        "không tải lại hồ sơ và không tự xác minh hiệu lực pháp lý."
    )
    if not audit["rows"]:
        st_ui.info(
            "Chưa phân loại được giấy SĐK/GMP/ủy quyền/báo giá trong bộ hồ sơ. "
            "Không suy luận rằng hồ sơ thiếu giấy tờ; cần kiểm tra tệp gốc."
        )
        return
    st_ui.caption(
        f'Giấy tờ được kiểm tra sơ bộ: {audit["documents_reviewed"]} · '
        f'Liên kết đề xuất: {audit["provisional_links"]} · '
        'Giấy tờ đã xác minh pháp lý: 0. '
        'Không có kết quả tự phê duyệt.'
    )
    st_ui.dataframe(
        pd.DataFrame(audit["rows"]),
        hide_index=True,
        use_container_width=True,
        height=min(470, 65 + 35 * len(audit["rows"])),
    )
    st_ui.warning(
        "Giấy cùng nhà máy chưa chứng minh đúng phạm vi GMP cho từng thuốc. "
        "Công văn giải trình không thay thế chứng nhận GMP. "
        "SĐK, giá và ủy quyền phải được đối chiếu bản gốc và cơ quan có thẩm quyền."
    )
    hints = [
        {"Tệp nguồn": source.get("filename", ""),
         "Loại tài liệu": KINDS.get(source.get("kind", ""), source.get("kind", "")),
         "Trường có nhãn": item.get("field", ""),
         "Giá trị gợi ý": item.get("value", ""),
         "Trang/nguồn": item.get("source", ""),
         "Trích nguyên văn": item.get("raw", ""),
         "Cách đọc": item.get("reading_method", ""),
         "Trạng thái": item.get("status", ""),
         "SHA256 tệp": item.get("sha256", "")}
        for source in report.get("sources") or []
        for item in source.get("proof_hints") or []
    ]
    if hints:
        with st_ui.expander(
            f"Giá trị SĐK/GMP có nhãn nhưng chưa được trích chắc chắn ({len(hints)})",
            expanded=True,
        ):
            st_ui.caption(
                "Chỉ là GIÁ TRỊ GỢI Ý có vị trí nguồn, chưa kiểm chứng PDF/OCR. "
                "Không ghi vào SĐK/GMP của sản phẩm và không dùng tạo liên kết."
            )
            st_ui.dataframe(
                pd.DataFrame(hints), hide_index=True, use_container_width=True
            )


def render_nsx_workbench() -> None:
    scope = validate_scope(st.session_state.get("tdv_see_pro_active_scope"))
    st.markdown("### SEE PRO · Hồ sơ NSX & Báo giá — đọc tự động")
    if not scope:
        st.warning("Chọn dự án / BP / phiên bản E-HSMT trước khi đọc hồ sơ NSX.")
        return
    st.caption(
        "PHIÊN BẢN NGHIỆP VỤ NSX: 2026-10-22J · "
        "Đối chiếu giá trị hai nguồn đặt trước danh sách mâu thuẫn. "
        "Nếu chưa thấy mã này, Streamlit Cloud chưa nạp đúng bản mã mới."
    )
    st.caption(
        "Nạp cả bộ hồ sơ một lần. SEE PRO tự nhận diện tài liệu, phát hiện "
        "các thuốc, đối chiếu định danh và đưa các vấn đề chưa rõ vào danh sách cần xem lại."
    )
    st.warning(
        "Preview đã có Google OIDC và vai trò cơ bản nhưng chưa có phân quyền "
        "theo dự án/kho hồ sơ đạt chuẩn doanh nghiệp. Tệp xử lý trên máy chủ "
        "Streamlit; chỉ dùng tài liệu đã được phép và không có dữ liệu mật. "
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

    revisions = _runtime_revisions()
    if not _runtime_is_consistent():
        st.error(
            "Bộ đọc tài liệu đang nạp khác phiên bản với giao diện; "
            "hệ thống tạm khóa xử lý để tránh xuất báo cáo cũ dưới mã phiên bản mới. "
            "Không nạp lại tài liệu; cần đồng bộ tiến trình Streamlit Cloud."
        )
        st.caption(
            "Phiên bản bộ đọc đã nạp: " +
            ", ".join(f"{name}={rev or 'CHUA_NAP'}"
                      for name, rev in revisions.items())
        )
        return

    uploads = st.file_uploader(
        "Nạp cả bộ hồ sơ NSX / GMP / SĐK / ủy quyền / báo giá",
        type=list(ACCEPTED), accept_multiple_files=True,
        key="tdv_nsx_auto_batch_" + "_".join(scope.values()),
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
    old_report = st.session_state.get("tdv_nsx_auto_report")
    if (st.session_state.get("tdv_nsx_auto_signature") != digest
            or (old_report and not _report_from_current_pipeline(old_report, digest))):
        if old_report:
            st.info(
                "Báo cáo trong phiên làm việc là kết quả của bộ tệp hoặc phiên bản "
                "phân tích cũ; đã bỏ khỏi phiên. Nhấn Đọc và kiểm toán để phân tích "
                "bằng đúng phiên bản đang hiển thị."
            )
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
                if report.get("analysis_version") != NSX_EXPECTED_PIPELINE_VERSION:
                    st.error(
                        "Bộ đọc trả về báo cáo từ phiên bản không khớp; "
                        "kết quả bị loại, không xuất Excel."
                    )
                    return
                report["analysis_fingerprint"] = digest
            except Exception as exc:
                st.error(
                    f"Không hoàn tất lượt đọc ({type(exc).__name__}). "
                    "Tệp nguồn vẫn được giữ nguyên; kiểm tra định dạng và dung lượng."
                )
                return
        st.session_state["tdv_nsx_auto_report"] = report
        st.session_state["tdv_nsx_auto_signature"] = digest

    report = st.session_state.get("tdv_nsx_auto_report")
    if (not _report_from_current_pipeline(report, digest)
            or st.session_state.get("tdv_nsx_auto_signature") != digest):
        return
    st.caption(
        f"Phiên bản thực sự xử lý báo cáo: {report['analysis_version']} "
        f"· Dấu vân tay dữ liệu: {digest[:12]}…"
    )

    from see_pro_quality_gate import audit_nsx
    quality = audit_nsx(report)
    stats = report["summary"]
    st.caption(f'SEE PRO · Tệp NSX: {quality["files"]}, sản phẩm ứng viên: '
               f'{quality["entries"]}, lỗi/điểm cần kiểm tra chất lượng: '
               f'{quality["issue_count"]}. 99,9999% chỉ là mục tiêu, chưa nghiệm thu.')
    with st.expander("Kiểm toán chất lượng trích xuất NSX theo từng trường"):
        st.dataframe([{"Trường":k,"Có nội dung":v["values"],
                      "Có nguồn riêng":v["field_cited"],
                      "Thiếu nguồn/đang mâu thuẫn":v["values"]-v["field_cited"]}
                      for k,v in quality["coverage"].items()],
                     hide_index=True,use_container_width=True)
        if quality["issues"]:
            st.dataframe(quality["issues"],hide_index=True,use_container_width=True)
    metrics = st.columns(5)
    for col, (label, value) in zip(metrics, (
        ("Tài liệu", stats["files"]),
        ("Đọc được", stats["parsed"]),
        ("Dòng sản phẩm trích xuất", stats["products"]),
        ("Liên kết sơ bộ", stats["linked"]),
        ("Cần kiểm tra", stats["review"]),
    )):
        col.metric(label, value)

    if stats.get("source_product_rows", 0) > stats["products"]:
        st.info(
            f'Danh mục nguồn có {stats["source_product_rows"]} dòng trên các sheet; '
            f'sau đối chiếu nguồn nội bộ còn {stats["products"]} dòng ứng viên. '
            f'Đã gộp {stats.get("reconciled_rows", 0)} dòng có tên + '
            'định danh nhà máy/NSX trùng trong cùng tệp, '
            f'loại {stats.get("excluded_ghost_rows", 0)} dòng tiêu đề số. '
            'Các dòng trùng tên nhưng chưa phân biệt được vẫn giữ riêng; '
            'không xem đây là số thuốc đã xác minh.'
        )
    if any(p.get("conflicts") for p in report.get("products", [])):
        conflicts = [p for p in report["products"] if p.get("conflicts")]
        render_nsx_conflict_review(conflicts)

    if stats["products"] == 0:
        st.error(
            "ĐÃ ĐỌC TỆP nhưng CHƯA TRÍCH ĐƯỢC THUỐC có đủ định danh. "
            "Trang SO SÁNH chưa có dữ liệu NSX; không được hiểu 0% là không đạt."
        )
        with st.expander("Chẩn đoán tự động: vì sao chưa nhận diện được thuốc?", expanded=True):
            st.dataframe(
                diagnose_extracted_documents(report),
                hide_index=True, use_container_width=True,
            )
            st.caption(
                "Chỉ hiển thị tình trạng trích xuất, không hiển thị dữ liệu mật. "
                "Tệp PDF không có lớp chữ hoặc OCR thiếu trường cần kiểm tra từ nguồn gốc."
            )

    coverage = summarize_product_field_coverage(report)
    if stats["products"] and (not stats["linked"] or
                             coverage["fields"]["INGREDIENT"] < stats["products"] or
                             coverage["fields"]["REGISTRATION_NO"] < stats["products"]):
        st.warning(
            "Máy đã lập được danh sách sản phẩm, nhưng CHƯA ĐỦ TRƯỜNG "
            "để chứng minh thuốc tương ứng với yêu cầu E-HSMT "
            "hoặc để liên kết duy nhất chứng nhận SĐK/GMP. "
            "0 liên kết KHÔNG đồng nghĩa không có hồ sơ; không tự gắn "
            "giấy GMP cho tất cả thuốc cùng nhà máy."
        )
        st.markdown("**Độ phủ dữ liệu trích xuất từ toàn bộ danh mục (tự động)**")
        labels = {
            "PRODUCT_NAME": "Tên thuốc", "INGREDIENT": "Hoạt chất",
            "STRENGTH": "Hàm lượng", "DOSAGE_FORM": "Dạng bào chế",
            "ROUTE": "Đường dùng", "REGISTRATION_NO": "SĐK",
            "MANUFACTURER": "NSX", "FACTORY": "Nhà máy",
        }
        st.dataframe([
            {"Trường": labels[key], "Có nội dung + nguồn": count,
             "Chưa trích được": coverage["total"] - count,
             "Tổng số dòng sản phẩm": coverage["total"],
             "Xác minh pháp lý": "CHƯA"}
            for key, count in coverage["fields"].items()
        ], hide_index=True, use_container_width=True)
        with st.expander("Chẩn đoán từng tài liệu chứng cứ NSX"):
            st.dataframe(diagnose_extracted_documents(report),
                         hide_index=True, use_container_width=True)
        st.caption(
            "Độ phủ chỉ phản ánh có trường dữ liệu gắn nguồn; chưa xác minh "
            "SĐK, GMP, hiệu lực, nhà máy hay điều kiện dự thầu."
        )

    st.markdown("**1. Tài liệu tự nhận diện**")
    nsx_files_frame = pd.DataFrame([
        {
            "Tệp": d["filename"],
            "Loại gợi ý": d["kind_label"],
            "Trạng thái phân loại": d["role_confidence"],
            "Đọc đủ": d["complete_read"],
            "SHA256": d["sha256"],
            "Lưu Drive": "KHÓA",
        }
        for d in report["files"]
    ])
    render_readable_table(st, nsx_files_frame, key="tdv_nsx_sources_readable",
                          label="NSX: phân loại và nguồn tài liệu",
                          page_size=20, min_width=1050)

    st.markdown("**2. Danh mục thuốc phát hiện trong bộ hồ sơ**")
    if report["products"]:
        nsx_products_frame = pd.DataFrame([
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
                "Trạng thái": ("CÓ MÂU THUẪN NGUỒN — CHƯA XÁC MINH"
                              if p.get("conflicts") else "CHƯA XÁC MINH"),
            } for p in report["products"]
        ])
        render_readable_table(st, nsx_products_frame,
                              key="tdv_nsx_products_readable",
                              label="NSX: danh mục sản phẩm",
                              page_size=25, min_width=1450)
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

    st.markdown("**3A. Truy tìm chứng cứ SĐK/GMP theo đúng nguồn (chưa xác minh)**")
    suggestions = report.get("evidence_candidates") or {}
    sample = suggestions.get("summary") or {}
    st.caption(
        f'Gợi ý đối chiếu tên thuốc: {sample.get("registration_hints", 0)} · '
        f'Nhóm GMP cùng tên nhà máy: {sample.get("factory_source_groups", 0)} · '
        f'Tài liệu SĐK/GMP chưa ghép: {sample.get("unresolved_evidence", 0)}. '
        'Không tính các gợi ý này vào liên kết chứng cứ đã xác minh hoặc tỷ lệ đáp ứng.'
    )
    if suggestions.get("registrations"):
        with st.expander("Giấy đăng ký — gợi ý theo tên nguồn, không tự gán SĐK", expanded=True):
            st.dataframe([{
                "Mã NSX": e["product_id"], "Tên trên giấy": e["product_name"],
                "SĐK trích từ giấy": e["registration_no_in_proof"] or "CHƯA TRÍCH",
                "Nguồn danh mục": e["product_source"]["file"],
                "Vị trí danh mục": e["product_source"]["location"],
                "Nguồn giấy SĐK": e["document_source"]["file"],
                "Vị trí trên giấy": e["document_source"]["location"],
                "Trường cùng khớp": ", ".join(e["supporting_fields"]),
                "Trường mâu thuẫn": ", ".join(e["conflict_fields"]),
                "Tình trạng": e["status"],
            } for e in suggestions["registrations"]],
                hide_index=True, use_container_width=True)
    if suggestions.get("factories"):
        with st.expander("GMP — chứng cứ theo nhà máy, KHÔNG phải chứng nhận cho mọi thuốc",
                         expanded=True):
            st.dataframe([{
                "Nhà máy theo giấy": e["factory"], "Nguồn": e["document_file"],
                "Vị trí": e["factory_source"]["location"],
                "Số GMP trong giấy": e["gmp_number_in_proof"] or "CHƯA TRÍCH",
                "Phạm vi trong giấy": e["gmp_scope_in_proof"] or "CHƯA TRÍCH",
                "Hết hạn ghi trên giấy": e["expiry_in_proof"] or "CHƯA TRÍCH",
                "Cảnh báo": e["expiry_observation"],
                "Số thuốc cùng tên nhà máy": e["related_product_count"],
                "Mã tham chiếu": ", ".join(e["related_product_ids"]),
                "Xác minh": "CHƯA",
            } for e in suggestions["factories"]],
                hide_index=True, use_container_width=True)
    if suggestions.get("unresolved"):
        with st.expander("Giấy SĐK/GMP chưa tìm được nguồn định danh chung",
                         expanded=True):
            st.dataframe([{
                "Tệp": e["file"],
                "Loại": KINDS.get(e["type"], e["type"]),
                "Trạng thái": e["status"], "Nguyên nhân": e["reason"],
            } for e in suggestions["unresolved"]],
                hide_index=True, use_container_width=True)
    st.caption(
        "Ngay cả khi ghi cùng một nhà máy, vẫn phải kiểm tra số GMP, "
        "phạm vi dây chuyền/sản phẩm, hiệu lực, thay đổi/thu hồi và yêu cầu "
        "riêng của E-HSMT. Ngày ghi trên giấy không tự chứng minh hiệu lực pháp lý."
    )

    render_manufacturer_evidence_review(report)

    st.markdown("**4. Các điểm chưa rõ và cần xác minh**")
    if report["review_queue"]:
        nsx_review_frame = pd.DataFrame([
            {
                "Tệp": item["file"],
                "Loại": KINDS.get(item["kind"], item["kind"]),
                "Vị trí": item["origin"],
                "Trạng thái": item["status"],
                "Thuốc liên quan": ", ".join(item["candidate_products"]),
                "Lý do": item["reason"],
            } for item in report["review_queue"]
        ])
        render_readable_table(st, nsx_review_frame,
                              key="tdv_nsx_review_readable",
                              label="NSX: danh sách chưa xác minh",
                              page_size=25, min_width=1250)
    else:
        st.success("Không phát sinh mục mơ hồ trong các kiểm tra định danh đã thực hiện.")
    st.caption(
        "Không có cảnh báo định danh không đồng nghĩa hồ sơ đáp ứng E-HSMT. "
        "GMP, SĐK, ủy quyền và giá chưa được thẩm định hoặc phê duyệt."
    )

    st.markdown("**5. Hồ sơ thầu theo thuốc · Truy xuất ngược cho Lãnh đạo**")
    st.caption(
        "Tra theo tên thuốc, SĐK hoặc mã nội bộ; máy đưa lên đơn vị cung cấp, "
        "nhà thầu, cơ sở đăng ký, NSX, nhà máy, giấy tờ và chứng cứ còn thiếu. "
        "Mọi kết quả CHƯA XÁC MINH."
    )
    trace = report.get("traceability") or {}
    dossiers = trace.get("products") or []
    needle = st.text_input(
        "Tìm sản phẩm trong hồ sơ thầu", key="tdv_nsx_leadership_drug_search",
        placeholder="Tên thuốc, số đăng ký, mã thuốc..."
    ).strip().casefold()
    displayed = [
        p for p in dossiers
        if not needle or needle in (" ".join(
            str(p.get(k, "")) for k in (
                "product_id", "product_name", "registration_no", "product_code",
            )).casefold())
    ]
    if dossiers:
        st.dataframe([
            {
                "Thuốc": p["product_name"], "SĐK": p["registration_no"],
                "Mã": p["product_id"],
                "Nhà thầu": p["parties"]["BIDDER"]["value"],
                "Đơn vị cung cấp": p["parties"]["SUPPLIER"]["value"],
                "Đơn vị đăng ký": p["parties"]["REGISTRATION_HOLDER"]["value"],
                "NSX": p["parties"]["MANUFACTURER"]["value"],
                "Nhà máy": p["parties"]["FACTORY"]["value"],
                "Tệp gốc": p["origin_file"], "Vị trí": p["origin"],
                "Tình trạng": "CHƯA XÁC MINH",
            } for p in displayed
        ], hide_index=True, use_container_width=True)
        st.markdown("**Giấy tờ / chứng cứ gắn riêng với từng thuốc**")
        st.dataframe([
            {
                "Thuốc": p["product_name"], "SĐK": p["registration_no"],
                "Loại tài liệu cần rà soát": proof["label"],
                "Có chứng cứ liên kết": proof["status"],
                "Yêu cầu của E-HSMT": proof["requirement_status"],
                "Tệp": source["file"], "Vị trí": source["location"],
                "SHA256": source["sha256"], "Trích gốc": source.get("excerpt", ""),
            }
            for p in displayed for proof in p["proofs"]
            for source in (proof["sources"] or [{
                "file": "", "location": "", "sha256": "", "excerpt": "",
            }])
        ], hide_index=True, use_container_width=True)
        st.warning(
            "Chưa thể kết luận tài liệu nào bắt buộc/đủ/hợp lệ cho từng gói "
            "nếu chưa đọc và đối chiếu phiên bản E-HSMT cùng các văn bản sửa đổi, làm rõ."
        )
    else:
        st.info("Chưa phát hiện thuốc có định danh gốc, nên chưa thể lập truy xuất ngược.")
    tender_docs = report.get("tender_documents") or []
    if tender_docs:
        st.markdown("**Tài liệu khác cùng gói thầu được tự phát hiện**")
        st.dataframe([
            {
                "Tệp": doc["filename"], "Loại": doc["kind"],
                "BP đọc trong hồ sơ": ", ".join(doc["package_ids"]),
                "TBMT": ", ".join(doc["notice_ids"]),
                "Số mã G1 phát hiện": len(doc["lot_codes"]),
                "Đã đọc đầy đủ": doc["complete_read"],
                "SHA256": doc["sha256"], "Xác minh": "CHƯA",
            } for doc in tender_docs
        ], hide_index=True, use_container_width=True)
    with st.expander("Nguồn công khai để SEE PRO tra cứu theo từng loại chứng cứ"):
        from tdv_tender_context import PUBLIC_REFERENCES
        st.caption("Chỉ là danh mục nguồn tra cứu. Chưa tự tải về hoặc xác thực chứng nhận.")
        for ref in PUBLIC_REFERENCES:
            st.markdown(f'- [{ref["name"]}]({ref["url"]}) — {ref["purpose"]}')

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
        "Tải Excel NSX + chứng cứ nguồn và đối chiếu mâu thuẫn",
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
