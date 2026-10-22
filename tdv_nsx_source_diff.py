"""Read-only two-source comparison of manufacturer product catalogue conflicts.

Never resolves differences, writes source files, approves registration/GMP,
or declares two formulations legally or technically equivalent.
"""
from __future__ import annotations

from typing import Any


def _original_field(row: dict, field: str) -> dict:
    evidence = (row.get("evidence") or {}).get(field) or {}
    value = evidence.get("raw")
    if value is None:
        value = evidence.get("value")
    if value is None:
        value = (row.get("fields") or {}).get(field)
    return {
        "value": str(value or ""),
        "source": str(evidence.get("source") or ""),
        "file": str(evidence.get("file") or row.get("file") or ""),
        "sha256": str(evidence.get("sha256") or row.get("sha256") or ""),
    }


def compare_conflict_sources(products: list[dict]) -> list[dict]:
    """For each disputed field show both actual original values and citations.

    If more than two observations exist, compare source 1 against EACH other
    source. A missing field remains explicitly missing; no guessed value.
    """
    results: list[dict] = []
    for product in products:
        conflicts = product.get("conflicts") or {}
        if not conflicts:
            continue
        sources = list(product.get("source_rows") or [])
        for field in sorted(conflicts):
            observations = [_original_field(source, field) for source in sources]
            if not observations:
                observations = [_original_field(product, field)]
            first = observations[0]
            for other in observations[1:] or [{"value": "", "source": "",
                                                "file": "", "sha256": ""}]:
                results.append({
                    "Mã NSX": str(product.get("uid") or ""),
                    "Tên thuốc": str((product.get("fields") or {}).get("PRODUCT_NAME") or ""),
                    "Trường cần đối chiếu": str(field),
                    "Giá trị nguồn 1": first["value"],
                    "Tệp nguồn 1": first["file"],
                    "Ô nguồn 1": first["source"],
                    "SHA256 nguồn 1": first["sha256"],
                    "Giá trị nguồn 2": other["value"],
                    "Tệp nguồn 2": other["file"],
                    "Ô nguồn 2": other["source"],
                    "SHA256 nguồn 2": other["sha256"],
                    "Kết luận": "CHƯA XÁC MINH – CẦN ĐỐI CHIẾU BẢN GỐC",
                })
    return results
