"""Evidence-first review queue for TDV leadership, not bid adjudication.

Only summarizes *existing* source-linked observations from two already-read
workbenches. Does not invent dates, products, pages, thresholds or decisions.
Do not use for compliance approval; legal review remains mandatory.
"""
from __future__ import annotations

from collections import Counter

PRIORITY = {
    "CHENH_LECH_KY_THUAT": (1, "Chênh lệch thông số cần so gốc"),
    "SDK_MAU_THUAN": (1, "Giấy SĐK gợi ý có định danh khác nhau"),
    "NHIEU_UNG_VIEN": (2, "Có nhiều ứng viên NSX"),
    "CHUA_DU_TIEU_CHI": (2, "Có ứng viên nhưng thiếu chứng cứ"),
    "SDK_CHUA_XAC_MINH": (2, "Gợi ý giấy SĐK chưa xác minh"),
    "GMP_CHUA_XAC_MINH": (2, "GMP theo nhà máy chưa xác minh"),
    "CHUNG_CU_CHUA_GHEP": (2, "Tài liệu NSX chưa ghép được"),
    "GOI_Y_TEN": (3, "Gợi ý từ tên, chưa chứng minh hoạt chất"),
    "CHUA_CO_UNG_VIEN": (3, "Chưa có ứng viên NSX"),
}


def build_review_priorities(report: dict, *, max_rows: int = 250) -> dict:
    """Build all issue counts while limiting only displayed/exported examples.

    Issues are *not* a count of disqualified medicines. E-HSMT is normative;
    source candidates and factory name coincidences never increase green or
    registration/GMP confirmation.
    """
    if max_rows < 1 or max_rows > 10000:
        raise ValueError("Giới hạn hiển thị phải từ 1 đến 10.000")
    queue = []

    def put(category: str, code: str, detail: str, document: str,
            action: str, *, location: str = "") -> None:
        tier, label = PRIORITY[category]
        queue.append({
            "muc_uu_tien": tier,
            "nhom": category,
            "van_de": label,
            "ma": str(code or ""),
            "chi_tiet": str(detail or "")[:500],
            "tai_lieu": str(document or "")[:300],
            "vi_tri_nguon": str(location or "")[:300],
            "viec_can_lam": action,
            "trang_thai": "CAN_XAC_MINH",
        })

    for record in report.get("comparison") or []:
        code = record.get("MA_THUOC_EHSMT", "")
        for criterion in record.get("criteria") or []:
            if criterion.get("status") != "KHONG_KHOP_CAN_XAC_MINH":
                continue
            left, right = (
                criterion.get("ehsmt_evidence") or {},
                criterion.get("nsx_evidence") or {},
            )
            put(
                "CHENH_LECH_KY_THUAT", code,
                f'{criterion.get("label", "")}: E-HSMT «{criterion.get("ehsmt", "")}» '
                f'↔ NSX «{criterion.get("nsx", "")}»',
                f'{left.get("file", "")} / {right.get("file", "")}',
                "Mở đúng trang/dòng hai nguồn, xác định chênh lệch trước khi đánh giá.",
                location=f'{left.get("location", "")} / {right.get("location", "")}',
            )
        candidates = int(record.get("SO_UNG_VIEN_NSX") or 0)
        if candidates > 1:
            put("NHIEU_UNG_VIEN", code, f"{candidates} ứng viên NSX cùng nhóm hoạt chất",
                record.get("NGUON_EHSMT", ""),
                "Phân biệt đúng SĐK, hàm lượng, nhà máy; không tự chọn thuốc đầu tiên.",
                location=record.get("VI_TRI_EHSMT", ""))
        elif candidates == 1 and record.get("SO_TIEU_CHI_CHUA_DAT", 0):
            put("CHUA_DU_TIEU_CHI", code,
                f'{record["SO_TIEU_CHI_CHUA_DAT"]} tiêu chí chưa đủ căn cứ',
                record.get("NGUON_THUOC_NSX", ""),
                "Bổ sung chứng cứ cho tiêu chí đang vàng, kiểm tra từng giá trị gốc.",
                location=record.get("VI_TRI_EHSMT", ""))
        elif candidates == 0:
            hints = int(record.get("SO_GOI_Y_TEN_NSX") or 0)
            if hints:
                examples = record.get("GOI_Y_TEN_NSX") or []
                put("GOI_Y_TEN", code,
                    f"{hints} gợi ý tên thuốc, chưa chứng minh hoạt chất/định danh",
                    examples[0].get("source_file", "") if examples else "",
                    "Kiểm tra hoạt chất, SĐK, nhà máy trên giấy gốc; không dùng tên để tự ghép.",
                    location=examples[0].get("source_location", "") if examples else "")
            else:
                put("CHUA_CO_UNG_VIEN", code,
                    "Chưa tìm được ứng viên có chứng cứ hoạt chất tương ứng",
                    record.get("NGUON_EHSMT", ""),
                    "Kiểm tra đã nạp đầy đủ danh mục NSX và trường hoạt chất có nguồn.",
                    location=record.get("VI_TRI_EHSMT", ""))

    evidence = report.get("nsx_evidence_candidates") or {}
    for hint in evidence.get("registrations") or []:
        conflicts = hint.get("conflict_fields") or []
        category = "SDK_MAU_THUAN" if conflicts else "SDK_CHUA_XAC_MINH"
        source = hint.get("document_source") or {}
        put(category, hint.get("product_id", ""),
            ("Trường mâu thuẫn: " + ", ".join(conflicts)) if conflicts
            else str(hint.get("status", "CHUA_XAC_MINH")),
            source.get("file") or hint.get("document_file", ""),
            "So giấy SĐK gốc, định danh sản phẩm và cập nhật hiệu lực trước khi liên kết.",
            location=source.get("location", ""))

    for site in evidence.get("factories") or []:
        source = site.get("factory_source") or {}
        put("GMP_CHUA_XAC_MINH", site.get("factory", ""),
            f'{site.get("expiry_observation", "")}; '
            f'{site.get("related_product_count", 0)} thuốc trùng nhà máy (không phải đã đạt)',
            source.get("file") or site.get("document_file", ""),
            "Kiểm tra số GMP, cơ sở, dây chuyền, phạm vi, hiệu lực và gia hạn/thu hồi.",
            location=source.get("location", ""))

    for item in evidence.get("unresolved") or []:
        put("CHUNG_CU_CHUA_GHEP", "", item.get("reason", ""),
            item.get("file", ""),
            "Xem lại loại tài liệu và các nhãn trường chưa trích được; không ép liên kết.")

    queue.sort(key=lambda item: (item["muc_uu_tien"], item["nhom"], item["ma"]))
    counts = Counter(x["nhom"] for x in queue)
    tiers = Counter(x["muc_uu_tien"] for x in queue)
    return {
        "total_issues": len(queue),
        "shown_issues": min(len(queue), max_rows),
        "truncated": len(queue) > max_rows,
        "by_category": dict(sorted(counts.items())),
        "by_priority": {str(level): tiers.get(level, 0) for level in (1, 2, 3)},
        "rows": queue[:max_rows],
        "verified": False,
        "bid_eligible": False,
        "note": (
            "Ưu tiên xử lý là thứ tự rà soát do phần mềm đề xuất, "
            "không phải mức độ vi phạm hay kết luận đủ điều kiện dự thầu. "
            "Số mục có thể lớn hơn số mã thuốc."
        ),
    }
