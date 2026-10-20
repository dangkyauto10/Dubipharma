"""SEE PRO: read-only evidence-first validation layer.

No automatic legal conclusions, bidding prices, or Google Sheets writes.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any
import re

SCHEMA_EHSMT = (
    "STT", "MA_PHAN_LO", "MA_THUOC", "HOAT_CHAT_HSMT",
    "NONG_DO_HAM_LUONG", "DUONG_DUNG", "DANG_BAO_CHE",
    "DON_VI_TINH", "NHOM_THUOC", "SO_LUONG_CHINH",
    "DON_GIA_KE_HOACH", "GIA_UOC_TINH_PHAN",
    "TIEN_BAO_DAM_DU_THAU", "CHUNG_CU_TRANG_HSMT",
)
REQUIRED = ("MA_PHAN_LO", "MA_THUOC", "HOAT_CHAT_HSMT", "NONG_DO_HAM_LUONG",
            "DUONG_DUNG", "DANG_BAO_CHE", "DON_VI_TINH",
            "NHOM_THUOC", "SO_LUONG_CHINH", "DON_GIA_KE_HOACH")
CODE = re.compile(r"^G\d+\.\d{3}$")
LOT = re.compile(r"^PP\d{10}$")


@dataclass
class Evidence:
    file_name: str
    page: int
    section: str
    snippet: str


@dataclass
class FieldValue:
    value: Any = None
    evidence: list[Evidence] = field(default_factory=list)
    verified: bool = False


@dataclass
class SeeLot:
    ma_phan_lo: str
    ma_thuoc: str
    fields: dict[str, FieldValue] = field(default_factory=dict)
    findings: list[dict] = field(default_factory=list)


def validate_lots(lots: list[SeeLot]) -> dict:
    """Audit completeness and provenance, never assume missing fields are zero."""
    findings = []
    seen_codes, seen_parts = set(), set()
    valid = 0
    for lot in lots:
        issues = []
        if not CODE.fullmatch(lot.ma_thuoc):
            issues.append("INVALID_DRUG_CODE")
        if not LOT.fullmatch(lot.ma_phan_lo):
            issues.append("INVALID_PART_CODE")
        if lot.ma_thuoc in seen_codes:
            issues.append("DUPLICATE_DRUG_CODE")
        if lot.ma_phan_lo in seen_parts:
            issues.append("DUPLICATE_PART_CODE")
        seen_codes.add(lot.ma_thuoc)
        seen_parts.add(lot.ma_phan_lo)
        for key in REQUIRED:
            v = lot.fields.get(key)
            if not v or v.value in (None, ""):
                issues.append("MISSING:" + key)
            elif not v.evidence:
                issues.append("NO_EVIDENCE:" + key)
            elif not v.verified:
                issues.append("UNVERIFIED:" + key)
        if not issues:
            valid += 1
        for issue in issues:
            findings.append({"MA_PHAN_LO": lot.ma_phan_lo,
                             "MA_THUOC": lot.ma_thuoc, "ISSUE": issue})
    return {"total_lots": len(lots), "fully_verified_lots": valid,
            "verified_ratio": valid / len(lots) if lots else 0.0,
            "findings": findings, "status": "REQUIRES_REVIEW" if findings else "VALIDATED"}


def to_record(lot: SeeLot) -> dict:
    row = {"MA_PHAN_LO": lot.ma_phan_lo, "MA_THUOC": lot.ma_thuoc}
    for key in SCHEMA_EHSMT:
        if key not in row:
            value = lot.fields.get(key)
            row[key] = value.value if value else None
    return row
