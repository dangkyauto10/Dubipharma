"""SEE PRO private pricing permission and exact-decimal draft calculations.

No deployment, automated legal validation, persisted approvals, or shared pricing
storage. Default DENY without per-project, per-package, per-revision grants.
"""
from __future__ import annotations
from collections.abc import Mapping
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import datetime, timezone
import re
from tdv_see_pro_scope import validate_scope

PRICE_PAGE = "💰 Cân đối & phê duyệt giá chào"
PERMISSIONS = ("view", "prepare", "approve")
MONEY = Decimal("1")


def price_permission(email, global_role, scope, config):
    """Return exactly one explicit private grant, otherwise deny by default.

    Existing admin role is NOT a price grant. Viewer cannot gain write rights.
    Ambiguous duplicate grants fail closed; no wildcards, fallback or inheritance.
    """
    bound = validate_scope(scope)
    if not bound or global_role not in ("admin", "analyst", "viewer"):
        return None
    if not isinstance(email, str) or email != email.strip().lower():
        return None
    if not isinstance(config, Mapping) or not isinstance(config.get("grants"), list):
        return None
    matching = []
    for grant in config["grants"]:
        if not isinstance(grant, Mapping):
            return None
        if (grant.get("email") == email and
                all(grant.get(k) == bound[k] for k in
                    ("project_id", "package_id", "ehsmt_revision_id"))):
            matching.append(grant.get("permission"))
    if len(matching) != 1 or matching[0] not in PERMISSIONS:
        return None
    permission = matching[0]
    if global_role == "viewer" and permission != "view":
        return None
    return permission


def may_price(permission, action, global_role):
    if action == "view":
        return permission in PERMISSIONS and global_role in ("admin", "analyst", "viewer")
    if action == "prepare":
        return permission in ("prepare", "approve") and global_role in ("admin", "analyst")
    # A real approval needs durable audit and scope-level review delegation;
    # no role may perform it on this memory-only Preview.
    if action == "final_approve":
        return False
    return False


def _money(value, name, *, required=True, positive=False):
    raw = str(value if value is not None else "").strip()
    if not raw and not required:
        return None
    if not re.fullmatch(r"\d+(?:[.,]\d{1,4})?", raw):
        raise ValueError(name + ": chỉ nhập số dương, dùng dấu chấm thập phân")
    try:
        number = Decimal(raw.replace(",", "."))
    except InvalidOperation as exc:
        raise ValueError(name + ": số không hợp lệ") from exc
    if (positive and number <= 0) or number < 0 or number > Decimal("100000000000000"):
        raise ValueError(name + ": giá trị không hợp lệ")
    return number


def _vnd(amount):
    return amount.quantize(MONEY, rounding=ROUND_HALF_UP)


def _percentage(value, name):
    value = _money(value, name)
    if value > 100:
        raise ValueError(name + ": tỷ lệ vượt 100%")
    return value


def calculate_price(*, quote_before, quote_after, supplier_vat_percent,
                    extra_cost, proposed_bid_gross, quantity,
                    ehsmt_reference="", reference_basis="unknown",
                    bid_vat_percent=""):
    """Arithmetic only; not tender-price eligibility or margin certification.

    All amounts are in VND per aligned tender unit. VAT on seller's purchase
    quote may differ from VAT applicable to bidder; never silently conflate.
    """
    if reference_basis not in ("unknown", "vat_included", "vat_excluded"):
        raise ValueError("Cơ sở VAT mức tham chiếu E-HSMT không hợp lệ")
    before = _money(quote_before, "Giá NSX trước VAT", required=False)
    after = _money(quote_after, "Giá NSX sau VAT", required=False)
    if before is None and after is None:
        raise ValueError("Cần giá NSX trước hoặc sau VAT")
    vat = _percentage(supplier_vat_percent, "VAT báo giá NSX")
    factor = Decimal("1") + vat / Decimal("100")
    if before is None:
        before = _vnd(after / factor)
    if after is None:
        after = _vnd(before * factor)
    if abs(after - _vnd(before * factor)) > MONEY:
        raise ValueError("Giá NSX trước/sau VAT mâu thuẫn với mức VAT khai báo")
    qty = _money(quantity, "Số lượng", positive=True)
    if qty != qty.to_integral_value():
        raise ValueError("Số lượng hiện chỉ hỗ trợ đơn vị nguyên")
    extra = _money(extra_cost, "Chi phí cộng thêm sau VAT")
    bid = _money(proposed_bid_gross, "Giá chào dự kiến sau VAT", positive=True)
    reference = _money(ehsmt_reference, "Giá tham chiếu E-HSMT", required=False)
    bid_vat = (_percentage(bid_vat_percent, "VAT giá chào")
               if str(bid_vat_percent).strip() else None)
    cost = after + extra
    status = "CHUA_CO_CO_SO_SO_SANH"
    bid_base = None
    diff = None
    if reference is not None and reference_basis == "vat_included":
        bid_base = bid
    elif reference is not None and reference_basis == "vat_excluded" and bid_vat is not None:
        bid_base = _vnd(bid / (Decimal("1") + bid_vat/Decimal("100")))
    if bid_base is not None:
        diff = reference - bid_base
        status = "TRONG_MUC_THAM_CHIEU_SO_BO" if diff >= 0 else "VUOT_MUC_THAM_CHIEU_SO_BO"
    messages = []
    if bid < cost:
        messages.append("Giá chào thấp hơn giá vốn tạm tính có VAT và chi phí đã khai báo")
    if status == "VUOT_MUC_THAM_CHIEU_SO_BO":
        messages.append("Giá chào vượt mức tham chiếu trên cùng cơ sở VAT; phải kiểm tra E-HSMT gốc")
    if status == "CHUA_CO_CO_SO_SO_SANH":
        messages.append("Chưa xác định đủ cơ sở VAT để so giá E-HSMT")
    return {
        "quote_before_vat": str(_vnd(before)),
        "quote_after_vat": str(_vnd(after)),
        "supplier_vat_percent": str(vat),
        "extra_cost_gross": str(_vnd(extra)),
        "cost_estimate_gross": str(_vnd(cost)),
        "proposed_bid_gross": str(_vnd(bid)),
        "quantity": str(int(qty)),
        "estimated_total_bid_gross": str(_vnd(bid * qty)),
        "spread_to_cost_gross": str(_vnd(bid-cost)),
        "ehsmt_reference": str(_vnd(reference)) if reference is not None else "",
        "ehsmt_reference_basis": reference_basis,
        "offer_comparison_basis": str(_vnd(bid_base)) if bid_base is not None else "",
        "reference_minus_bid": str(_vnd(diff)) if diff is not None else "",
        "comparison_status": status,
        "warnings": messages,
        "status": "DU_THAO_TINH_TOAN_CHUA_PHE_DUYET",
    }


def append_draft(existing, *, permission, global_role, scope, lot_id, nsx_id,
                 author_email, result, quote_reference, tender_reference):
    """Scoped memory-only draft. Requires re-check of permission at write-time.

    Does not prove signer identity by itself: caller supplies email already
    checked by require_google_access and explicit grant in current request.
    """
    if not may_price(permission, "prepare", global_role):
        raise PermissionError("Không có quyền nhập giá")
    bound = validate_scope(scope)
    if not bound or not re.fullmatch(r"G\d+[.．]\d{2,4}", str(lot_id or "")):
        raise ValueError("Thiếu phạm vi hoặc mã E-HSMT")
    if not nsx_id or not str(nsx_id).strip():
        raise ValueError("Mặt hàng chưa liên kết sản phẩm NSX duy nhất")
    if not isinstance(result, dict) or result.get("status")!="DU_THAO_TINH_TOAN_CHUA_PHE_DUYET":
        raise ValueError("Chưa có tính toán giá hợp lệ")
    if not quote_reference or not str(quote_reference).strip():
        raise ValueError("Phải chỉ rõ báo giá NSX nguồn gốc")
    if (result.get("ehsmt_reference") and not str(tender_reference or "").strip()):
        raise ValueError("Phải chỉ nguồn mức giá E-HSMT trước khi ghi dự thảo")
    previous = list(existing or [])
    key = tuple(bound[k] for k in ("project_id", "package_id", "ehsmt_revision_id"))
    revisions = sum(1 for x in previous if x.get("scope_key")==key and x.get("lot_id")==lot_id)
    row = {
        "scope_key": key,
        "lot_id": str(lot_id), "nsx_id": str(nsx_id),
        "revision": revisions+1,
        "author_email": str(author_email).lower(),
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "quote_reference": str(quote_reference)[:500],
        "tender_reference": str(tender_reference or "")[:500],
        "status": "DRAFT_RAM_ONLY_NOT_APPROVED",
        "pricing": dict(result),
    }
    return previous+[row]


def draft_in_scope(rows, scope):
    bound=validate_scope(scope)
    if not bound:
        return []
    key=tuple(bound[k] for k in ("project_id","package_id","ehsmt_revision_id"))
    return [dict(row) for row in (rows or []) if row.get("scope_key")==key]
