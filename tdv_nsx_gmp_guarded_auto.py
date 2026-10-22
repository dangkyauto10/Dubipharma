"""Fail-closed GMP role reconciliation over an existing NSX batch report.

Preserves all original products, source evidence and hashes. Reclassifies an
uncertain GMP document for review; never promotes a filename into legal proof.
"""
from __future__ import annotations

import hashlib
from collections import Counter

from tdv_nsx_auto import analyze_auto as _analyze_original
from tdv_nsx_gmp_role_guard import inspect_gmp_role
from tdv_nsx_evidence_candidates import discover_evidence_candidates
from tdv_tender_trace import build_reverse_dossiers


def _pdf_heading_lines(filename: str, raw: bytes) -> list[dict]:
    """Read accessible text on first two PDF pages; no OCR/network/storage."""
    if not filename.lower().endswith(".pdf"):
        return []
    try:
        import pymupdf
        lines: list[dict] = []
        with pymupdf.open(stream=raw, filetype="pdf") as pdf:
            for i in range(min(2, len(pdf))):
                for line in pdf[i].get_text("text", sort=True).splitlines()[:90]:
                    if line.strip():
                        lines.append({"source": f"Trang {i + 1}", "text": line[:500]})
        return lines
    except (ImportError, RuntimeError, ValueError, OSError):
        # A failed text read must never cause a certificate to be approved.
        return []


def reconcile_gmp_roles(report: dict, files: list[tuple[str, bytes]],
                        *, heading_reader=None) -> dict:
    """Downgrade suspicious provisional GMP roles, preserving every source.

    Uses document text as a positive hint for supplemental role only when the
    text is unambiguous. Filename alone can only cause a manual review.
    """
    heading_reader = heading_reader or _pdf_heading_lines
    originals: dict[tuple[str, str], bytes] = {
        (name, hashlib.sha256(raw).hexdigest()): raw for name, raw in files
    }
    modified = False
    # Review queue entries carry only filenames, not hashes; rewrite them
    # only when filenames are unique within the actual uploaded batch.
    filename_counts = Counter(m.get("filename") for m in report.get("files") or [])
    for meta, source in zip(report.get("files") or [], report.get("sources") or []):
        if meta.get("kind") != "GMP_CERT" or source.get("error"):
            continue
        name = str(meta.get("filename") or "")
        sha = str(meta.get("sha256") or "")
        raw = originals.get((name, sha))
        if raw is None:
            # Fail closed when metadata and uploaded source bytes do not agree.
            guard = {"status": "NEEDS_REVIEW", "reason":
                     "Không đối chiếu được SHA256 của giấy GMP với tệp tải lên; "
                     "không được liên kết chứng cứ này."}
        else:
            guard = inspect_gmp_role(name, heading_reader(name, raw))
        if guard["status"] not in ("SUPPLEMENT", "NEEDS_REVIEW"):
            continue
        kind = "GMP_EXPLANATION" if guard["status"] == "SUPPLEMENT" else "OTHER"
        meta["original_kind"] = "GMP_CERT"
        meta["kind"] = kind
        meta["kind_label"] = (
            "Văn bản giải trình/duy trì GMP (chưa xác minh)"
            if kind == "GMP_EXPLANATION" else
            "Chưa xác định loại văn bản GMP"
        )
        meta["role_confidence"] = "CHƯA_XÁC_MINH_LOẠI"
        meta["role_safety_review"] = guard["reason"]
        meta.setdefault("reasons", []).append(guard["reason"])
        source["original_kind"] = "GMP_CERT"
        source["kind"] = kind
        source["role_safety_review"] = guard["reason"]
        # Any link made under the former certificate role is unsafe.
        report["links"] = [link for link in (report.get("links") or [])
                           if not (link.get("source_evidence") == name
                                   and link.get("source_sha256") == sha)]
        if filename_counts.get(name, 0) == 1:
            for queued in report.get("review_queue") or []:
                # A warning from the first pass MUST NOT continue to label an
                # explanation/maintenance letter as a GMP certificate.
                if queued.get("file") == name and queued.get("kind") == "GMP_CERT":
                    queued["original_kind"] = "GMP_CERT"
                    queued["kind"] = kind
                    queued["reason"] = (
                        str(queued.get("reason") or "") +
                        " [Vai trò giấy GMP ban đầu đã bị hủy sau kiểm tra "
                        "bổ sung; KHÔNG dùng làm chứng nhận GMP.]"
                    ).strip()
        else:
            report.setdefault("warnings", []).append(
                f"{name}: có tệp trùng tên, không đổi nhãn dòng kiểm toán "
                "không có SHA256; cần đối chiếu tên+SHA từng nguồn."
            )
        report.setdefault("review_queue", []).append({
            "file": name, "kind": kind, "origin": "Trang đầu / tên tệp",
            "status": "CAN_XAC_DINH_LOAI_GMP",
            "candidate_products": [], "reason": guard["reason"],
        })
        report.setdefault("warnings", []).append(f"{name}: {guard['reason']}")
        modified = True
    if modified:
        report["evidence_candidates"] = discover_evidence_candidates(
            report.get("products") or [], report.get("files") or [],
            report.get("sources") or [],
        )
        stats = report.setdefault("summary", {})
        stats["linked"] = len(report.get("links") or [])
        stats["review"] = len(report.get("review_queue") or [])
        hints = (report["evidence_candidates"].get("summary") or {})
        for key in ("registration_hints", "factory_source_groups", "unresolved_evidence"):
            stats[key] = hints.get(key, 0)
        report["traceability"] = build_reverse_dossiers(report)
    # The wrapper does not set verified flags or claim regulatory validity.
    return report


def analyze_auto(files: list[tuple[str, bytes]], *, enable_ocr: bool = True) -> dict:
    report = _analyze_original(files, enable_ocr=enable_ocr)
    return reconcile_gmp_roles(report, files)
