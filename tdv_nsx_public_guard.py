"""SEE PRO / NSX: avoid promoting PUBLIC REFERENCE documents to primary proof.

Source-informed guardrails derived from openly indexed issuer/regulator pages:
- DAV lists of foreign manufacturing sites publicised as meeting GMP standards;
- DAV decisions publishing registration lists;
- issuer quotation invitations and blank quotation templates;
- EMA EudraGMDP GMP non-compliance notices and general GMP guidance.

A document can be authentic and useful WITHOUT being a supplier's own certificate,
authorisation or signed quotation. Classification is about document *role*, not
whether a claim is legally true. No networking, auto-PASS, storage or extra UI.
"""
from __future__ import annotations

from typing import Any

from tdv_nsx_adaptive import normalize


# Stable category codes for regression, not regulatory conclusions.
PUBLIC_GMP_LIST = "GMP_PUBLIC_REGISTER"
PUBLIC_GMP_BLANK_TEMPLATE = "GMP_BLANK_TEMPLATE"
PUBLIC_REGISTRATION_DECISION = "REGISTRATION_PUBLIC_DECISION"
PUBLIC_GMP_NONCOMPLIANCE = "GMP_NONCOMPLIANCE_REFERENCE"
PUBLIC_GMP_GUIDANCE = "GMP_GUIDANCE_REFERENCE"
QUOTE_INVITATION = "QUOTE_INVITATION"
QUOTE_BLANK_TEMPLATE = "QUOTE_BLANK_TEMPLATE"

CATEGORY_NOTES = {
    PUBLIC_GMP_LIST: (
        "Danh sách công bố về GMP: tài liệu tham khảo, không thay thế việc "
        "xác minh chứng nhận GMP gốc của đúng nhà máy và phạm vi."
    ),
    PUBLIC_GMP_BLANK_TEMPLATE: (
        "Mẫu định dạng chứng nhận GMP chưa điền: không phải chứng chỉ "
        "được cơ quan có thẩm quyền cấp cho một nhà máy."
    ),
    PUBLIC_REGISTRATION_DECISION: (
        "Quyết định/danh sách cấp hoặc gia hạn SĐK: không tự coi là "
        "giấy chứng nhận hiệu lực của một thuốc cụ thể."
    ),
    PUBLIC_GMP_NONCOMPLIANCE: (
        "Nguồn ghi nhận không tuân thủ GMP: tuyệt đối không sử dụng "
        "như chứng chỉ GMP đạt."
    ),
    PUBLIC_GMP_GUIDANCE: (
        "Hướng dẫn quy trình GMP: không phải giấy chứng nhận của nhà máy."
    ),
    QUOTE_INVITATION: (
        "Thư mời báo giá chỉ là yêu cầu cung cấp giá, không phải "
        "báo giá đã gửi của nhà cung cấp."
    ),
    QUOTE_BLANK_TEMPLATE: (
        "Mẫu báo giá/phụ lục chưa điền, không có đơn giá thương mại "
        "đã được đơn vị cung cấp xác nhận."
    ),
}


def _has(text: str, *phrases: str) -> bool:
    return any(normalize(p) in text for p in phrases)


def detect_nonprimary_document(lines: list[dict[str, Any]]) -> dict | None:
    """Identify source-document classes that MUST NOT auto-link as primary proof.

    Looks at the textual content/heading only, not filenames or download URLs.
    Does not perform entity matching or make decisions about legal validity.
    """
    if not lines:
        return None
    selected = [str(r.get("text", "") or "") for r in lines[:70]]
    head = normalize(" ".join(selected))
    chosen = None
    if _has(head, "danh sách cơ sở sản xuất thuốc nước ngoài đạt tiêu chuẩn gmp",
            "danh sách cơ sở sản xuất thuốc đạt tiêu chuẩn gmp",
            "danh sách cơ sở sản xuất đạt tiêu chuẩn gmp",
            "danh sách cơ sở sản xuất thuốc nước ngoài đáp ứng gmp",
            "danh sách các cssx trong nước đạt tiêu chuẩn nguyên tắc gmp",
            "danh sách các cơ sở trong nước đạt tiêu chuẩn nguyên tắc gmp",
            "danh sách cơ sở trong nước đạt tiêu chuẩn nguyên tắc gmp",
            "danh sách các cơ sở sản xuất thuốc trong nước đạt tiêu chuẩn nguyên tắc gmp",
            "danh sách cssx trong nước đạt tiêu chuẩn nguyên tắc gmp"):
        chosen = PUBLIC_GMP_LIST

    elif _has(head,
              "union format for a gmp certificate",
              "union format for a good manufacturing practice gmp certificate",
              "union format for good manufacturing practice gmp certificate"):
        # EMA publishes an unfilled certification *format* for regulators.
        # Do not mistake the regulator template for an issued certificate.
        chosen = PUBLIC_GMP_BLANK_TEMPLATE

    elif (_has(head, "statement of non-compliance with gmp",
               "statements of non-compliance with gmp",
               "không đáp ứng thực hành tốt sản xuất thuốc",
               "thông báo không tuân thủ gmp")
          or (_has(head, "non-compliance with good manufacturing practice")
              and _has(head, "statement", "statements"))):
        chosen = PUBLIC_GMP_NONCOMPLIANCE

    elif (_has(head, "the issue and update of gmp certificates",
               "quy trình cấp giấy chứng nhận gmp",
               "hướng dẫn việc cấp giấy chứng nhận gmp",
               "guideline on gmp certification",
               "interpretation of the union format for gmp certificate",
               "interpretation of the union format for good manufacturing practice gmp certificate")):
        chosen = PUBLIC_GMP_GUIDANCE

    # Whole procurement notice takes precedence over a blank template contained
    # in the same PDF. Both remain non-primary evidence.
    elif (_has(head, "thư mời báo giá", "thông báo mời báo giá",
               "thư mời cung cấp báo giá", "thông báo yêu cầu báo giá")
          or (_has(head, "kính mời", "trân trọng kính mời")
              and _has(head, "cung cấp báo giá", "gửi báo giá"))):
        chosen = QUOTE_INVITATION

    elif (_has(head, "mẫu báo giá", "mẫu bảng chào giá", "quotation template")
          and (_has(head, "phụ lục", "mẫu", "form")
               or _has(head, "nhà thầu", "đơn vị cung cấp"))):
        chosen = QUOTE_BLANK_TEMPLATE

    elif (_has(head, "quyết định số", "quyết định về việc", "quyết định")
          and _has(head, "danh mục", "danh sách")
          and _has(head, "đăng ký lưu hành", "giấy đăng ký lưu hành")
          and _has(head, "thuốc")):
        chosen = PUBLIC_REGISTRATION_DECISION

    if chosen is None:
        return None

    # Cite a source-local excerpt that includes relevant detection evidence
    # where possible. Report content is intentionally cropped, NOT verified.
    evidence = selected[:8]
    return {
        "class": chosen,
        "source_type": "PUBLIC_REFERENCE_NOT_PRIMARY_PROOF",
        "reason": CATEGORY_NOTES[chosen],
        "example_source": " | ".join(evidence)[:550],
        "verified": False,
        "automatic_primary_link_allowed": False,
    }
