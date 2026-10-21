"""Conservative reconciliation of catalogue tabs within ONE uploaded source file.

This is a table-layout normalization, NOT product registration, GMP validity,
bid eligibility, regulatory identity resolution or a source approval.
Never use an unmatched brand name alone to silently fuse drug records.
"""
from __future__ import annotations

from collections import Counter, defaultdict
import re

from tdv_nsx_adaptive import normalize

IDENTITY = ("PRODUCT_ID", "REGISTRATION_NO", "FACTORY", "MANUFACTURER")
NAME_KEY = "PRODUCT_NAME"


def _normalized_name(value: str) -> str:
    """Ignore line wraps but retain every alphanumeric character."""
    return re.sub(r"\s+", "", normalize(value))


def _sheet(record: dict) -> str:
    return str(record.get("origin") or "").split(", dòng ", 1)[0]


def _is_ghost(record: dict) -> bool:
    fields = record.get("fields") or {}
    name = str(fields.get(NAME_KEY) or "").strip()
    return bool(name and not any(char.isalpha() for char in name)
                and not fields.get("PRODUCT_ID") and not fields.get("REGISTRATION_NO"))


def _original(record: dict) -> dict:
    return {
        "file": record.get("file", ""), "sha256": record.get("sha256", ""),
        "origin": record.get("origin", ""), "fields": dict(record.get("fields") or {}),
        "evidence": dict(record.get("evidence") or {}),
    }


def _compatible(a: dict, b: dict) -> bool:
    fa, fb = a.get("fields") or {}, b.get("fields") or {}
    if not (_normalized_name(fa.get(NAME_KEY))
            and _normalized_name(fa.get(NAME_KEY)) == _normalized_name(fb.get(NAME_KEY))):
        return False
    # Never reconcile conflicting source IDs, registration, factories or makers.
    for key in IDENTITY:
        va, vb = fa.get(key), fb.get(key)
        if va and vb and normalize(va) != normalize(vb):
            return False
    # Independent corroboration IN THE SAME ORIGINAL FILE is mandatory.
    return any(fa.get(key) and fb.get(key)
               and normalize(fa[key]) == normalize(fb[key]) for key in IDENTITY)


def reconcile_product_rows(records: list[dict]) -> tuple[list[dict], dict]:
    """Merge only unique, corroborated, cross-sheet catalogue rows.

    Multiple occurrences of a name inside one sheet remain separate, including
    repeat strengths/forms; never pair them arbitrarily by row order.
    Every field observation survives in source_rows, even conflicting values.
    """
    clean = []
    excluded = []
    for p in records:
        if _is_ghost(p):
            excluded.append(_original(p))
        else:
            item = dict(p)
            item["fields"] = dict(p.get("fields") or {})
            item["evidence"] = dict(p.get("evidence") or {})
            item["conflicts"] = dict(p.get("conflicts") or {})
            item["source_rows"] = [_original(p)]
            clean.append(item)
    buckets = defaultdict(list)
    for index, item in enumerate(clean):
        name = _normalized_name(item["fields"].get(NAME_KEY))
        if name:
            buckets[(item["sha256"], name)].append(index)
    paired = set()
    result = []
    merges = 0
    review_names = []
    for i, p in enumerate(clean):
        if i in paired:
            continue
        key = (p["sha256"], _normalized_name(p["fields"].get(NAME_KEY)))
        others = buckets.get(key) or []
        candidate = [clean[j] for j in others]
        sheet_counts = Counter(_sheet(x) for x in candidate)
        # All rows must be unique on their OWN sheet, not just in the batch.
        allowed = (len(candidate) > 1 and len(sheet_counts) == len(candidate)
                   and all(_compatible(candidate[0], x) for x in candidate[1:]))
        if len(candidate) > 1 and not allowed:
            if i == others[0]:
                review_names.append(p["fields"].get(NAME_KEY, ""))
            result.append(p)
            continue
        if allowed and i == others[0]:
            root = dict(p)
            root["fields"] = dict(p["fields"])
            root["evidence"] = dict(p["evidence"])
            root["conflicts"] = dict(p.get("conflicts") or {})
            root["source_rows"] = list(p["source_rows"])
            for j in others[1:]:
                extra = clean[j]
                paired.add(j)
                merges += 1
                root["source_rows"].extend(extra["source_rows"])
                for field, value in extra["fields"].items():
                    old = root["fields"].get(field)
                    if not old:
                        root["fields"][field] = value
                        root["evidence"][field] = extra["evidence"][field]
                    elif ((field == NAME_KEY and
                           _normalized_name(old) == _normalized_name(value))
                          or normalize(old) == normalize(value)):
                        continue
                    else:
                        root["conflicts"].setdefault(field, []).append(
                            extra["evidence"][field])
            root["reconciled_tabs"] = True
            result.append(root)
        elif not allowed:
            result.append(p)
        # other corroborated sheets were consumed by first entry
    audit = {
        "source_rows": len(records), "excluded_ghost_rows": excluded,
        "merged_secondary_rows": merges, "remaining_products": len(result),
        "ambiguous_name_groups": len(review_names),
        "review_names": review_names, "verified": False,
    }
    return result, audit
