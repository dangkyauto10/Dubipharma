"""Leadership price comparison: no invented prices, bid prices are explicit human input."""
from __future__ import annotations
from decimal import Decimal, InvalidOperation
import re

def parse_vnd(value):
    if value is None or str(value).strip() == "":
        return None
    if isinstance(value, bool):
        return None
    raw = str(value).strip().replace("₫", "").replace("VND", "").replace("đ", "").replace(" ", "")
    # Monetary inputs are integer VND; dots and commas are thousands separators.
    if not re.fullmatch(r"\d{1,3}([.,]\d{3})+|\d+", raw):
        return None
    try:
        n = int(raw.replace(".", "").replace(",", ""))
        return n if n >= 0 else None
    except ValueError:
        return None

def compare_prices(rows):
    """Rows retain all source and verification flags; never auto-approve."""
    out = []
    for row in rows:
        record = dict(row)
        planned = parse_vnd(record.get("Giá định mức E-HSMT"))
        supplier = parse_vnd(record.get("Giá báo NSX"))
        bid = parse_vnd(record.get("Giá chào thầu (LĐ nhập)"))
        record["Giá định mức E-HSMT"] = planned
        record["Giá báo NSX"] = supplier
        record["Giá chào thầu (LĐ nhập)"] = bid
        record["Chênh lệch chào - định mức"] = bid - planned if bid is not None and planned is not None else None
        record["Chênh lệch chào - NSX"] = bid - supplier if bid is not None and supplier is not None else None
        record["Cảnh báo"] = ("CHƯA XÁC MINH NGUỒN GIÁ"
            if record.get("Xác minh giá") != "ĐÃ XÁC MINH"
            else ("CHÀO VƯỢT ĐỊNH MỨC" if bid is not None and planned is not None and bid > planned
                  else "CHỜ LÃNH ĐẠO PHÊ DUYỆT"))
        out.append(record)
    return out
