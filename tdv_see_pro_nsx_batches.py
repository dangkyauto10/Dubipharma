"""SEE PRO NSX intake ledger — append-only staged batches inside ONE RAM session.
No external writes, no automatic file replacement, no legal approval.
"""
from __future__ import annotations
from hashlib import sha256
from datetime import datetime, timezone
import re

def _fingerprint(name: str, content: bytes) -> dict:
    name = str(name or "").strip()
    if not name or not isinstance(content, bytes) or not content:
        raise ValueError("Tệp NSX thiếu tên hoặc nội dung")
    return {"filename": name, "sha256": sha256(content).hexdigest(),
            "content": content}

def stage_append(existing, incoming, *, batch_cap=24, combined_cap=24):
    """Plan a read-only append. Caller only commits new ledger AFTER successful reanalysis.

    Current analyzer processes one aggregate up to combined_cap files. For larger
    sets, fail closed without losing the prior committed ledger.
    """
    old = list(existing or [])
    if len(incoming) > batch_cap:
        raise ValueError(f"Mỗi đợt nạp tối đa {batch_cap} tệp")
    fingerprints = [_fingerprint(name, data) for name,data in incoming]
    old_names = {x["filename"]:x["sha256"] for x in old}
    old_hashes = {x["sha256"] for x in old}
    added, repeats, conflicts = [],[],[]
    seen_names = {}
    seen_hashes = set()
    for item in fingerprints:
        name,sha = item["filename"],item["sha256"]
        if name in seen_names and seen_names[name]!=sha:
            conflicts.append(name+": cùng tên nhưng khác nội dung trong đợt nạp")
            continue
        seen_names[name]=sha
        if name in old_names and old_names[name]!=sha:
            conflicts.append(name+": đã có tệp cùng tên nhưng SHA-256 khác; cần đánh số phiên bản")
            continue
        if sha in old_hashes or sha in seen_hashes:
            repeats.append({"filename":name,"sha256":sha,"reason":"Đã có SHA-256; không nạp trùng"})
            continue
        seen_hashes.add(sha)
        added.append(item)
    if conflicts:
        return {"status":"CONFLICT","records":old,"added":[],
                "repeated":repeats,"conflicts":conflicts}
    if len(old)+len(added)>combined_cap:
        return {"status":"LIMIT","records":old,"added":[],
                "repeated":repeats,"conflicts":[
                    f"Đã có {len(old)} tệp; bộ đọc hiện chỉ xử lý đồng thời tối đa {combined_cap} tệp. "
                    "Giữ nguyên bộ đã nghiệm thu, chưa nạp đợt này."]}
    n=max((int(x.get("batch_no") or 0) for x in old),default=0)+1
    stamped=datetime.now(timezone.utc).isoformat(timespec="seconds")
    append=[{**x,"batch_no":n,"received_at_utc":stamped,
             "status":"ACTIVE_CANDIDATE"} for x in added]
    return {"status":"READY" if append else "REPEAT_ONLY",
            "records":old+append,"added":append,
            "repeated":repeats,"conflicts":[]}

def manifest_for_report(records):
    """Metadata only. Never export raw source file content in report metadata."""
    return [{"batch_no":r["batch_no"],"filename":r["filename"],
             "sha256":r["sha256"],"received_at_utc":r["received_at_utc"],
             "status":r["status"]} for r in records]

def payload_for_analysis(records):
    return [(r["filename"],r["content"]) for r in records]

def verify_ledger(records):
    if not records: return False
    hashes=set()
    for item in records:
        if (not isinstance(item.get("content"),bytes)
                or sha256(item["content"]).hexdigest()!=item.get("sha256")
                or item.get("sha256") in hashes):
            return False
        hashes.add(item["sha256"])
    return True
