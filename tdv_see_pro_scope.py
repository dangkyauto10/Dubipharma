"""SEE PRO: add-only boundary by project, tender package and E-HSMT revision.
Hashes identify consumed files. User-entered scope never proves legal validity.
"""
import hashlib
import re

FIELDS=("project_id","package_id","ehsmt_revision_id")

def validate_scope(value):
    if not isinstance(value,dict): return None
    out={k:str(value.get(k) or "").strip() for k in FIELDS}
    if not all(re.fullmatch(r"[A-Za-z0-9_.-]{2,80}",v) for v in out.values()): return None
    return out

def bind_report(report, scope, files):
    scoped=validate_scope(scope)
    if not scoped or not files: raise ValueError("Thiếu phạm vi hoặc hồ sơ")
    bind=[{"name":name,"sha256":hashlib.sha256(data).hexdigest(),**scoped}
          for name,data in files if data]
    if len(bind)!=len(files) or len(set(x["sha256"] for x in bind))!=len(bind):
        raise ValueError("Tệp nguồn rỗng hoặc trùng nội dung")
    return {**report,"_tdv_scope":scoped,
            "_tdv_source_bindings":bind,
            "_tdv_consumed_sha256":[x["sha256"] for x in bind],
            "_tdv_scope_verified":False}

def check_scope(active, ehsmt, nsx):
    wanted=validate_scope(active)
    if not wanted: return False,"Chưa chọn đủ dự án/gói/phiên bản E-HSMT"
    for label,report in (("E-HSMT",ehsmt),("NSX",nsx)):
        if not isinstance(report,dict) or not report: return False,f"Thiếu dữ liệu {label}"
        if validate_scope(report.get("_tdv_scope"))!=wanted:
            return False,f"{label} khác dự án/gói/phiên bản hoặc chưa gắn phạm vi"
        binds=report.get("_tdv_source_bindings")
        consumed=report.get("_tdv_consumed_sha256")
        if not isinstance(binds,list) or not binds or not isinstance(consumed,list):
            return False,f"{label} thiếu manifest chứng cứ"
        hashes=[]
        for b in binds:
            if not isinstance(b,dict) or validate_scope(b)!=wanted:
                return False,f"{label} có chứng cứ sai phạm vi"
            sha=str(b.get("sha256") or "")
            if not re.fullmatch(r"[0-9a-fA-F]{64}",sha):
                return False,f"{label} thiếu SHA-256 hợp lệ"
            hashes.append(sha.lower())
        if len(hashes)!=len(set(hashes)) or sorted(hashes)!=sorted(str(h).lower() for h in consumed):
            return False,f"{label} có nguồn lặp hoặc chưa gắn phạm vi"
    # Known explicit package in structured tender rows must agree.
    for row in ehsmt.get("rows") or []:
        package=str(row.get("MA_GOI_THAU") or "").strip()
        if package and package!=wanted["package_id"]:
            return False,f"E-HSMT có mã gói {package} khác phạm vi đã chọn"
    return True,"Đủ điều kiện đối chiếu SƠ BỘ phạm vi; chưa xác minh nghiệp vụ"

def switch_workspace(session, target):
    """Swap scoped RAM-only reports; never carry active data across workspaces."""
    chosen=validate_scope(target)
    if not chosen: raise ValueError("Phạm vi không hợp lệ")
    old=validate_scope(session.get("tdv_see_pro_active_scope"))
    if old==chosen: return
    cache=session.setdefault("tdv_see_pro_ram_cache",{})
    pairs=(("tdv_see_pro_analysis","tdv_see_pro_signature"),
           ("tdv_nsx_auto_report","tdv_nsx_auto_signature"))
    if old:
        old_key="::".join(old[k] for k in FIELDS)
        snapshot={}
        for data_key,sig_key in pairs:
            value=session.get(data_key)
            if (isinstance(value,dict) and
                    validate_scope(value.get("_tdv_scope"))==old and
                    isinstance(value.get("_tdv_source_bindings"),list) and
                    value.get("_tdv_source_bindings")):
                snapshot[data_key]=value
                snapshot[sig_key]=session.get(sig_key)
        if snapshot: cache[old_key]=snapshot
    for data_key,sig_key in pairs:
        session.pop(data_key,None)
        session.pop(sig_key,None)
    session["tdv_see_pro_active_scope"]=chosen
    target_key="::".join(chosen[k] for k in FIELDS)
    for data_key,sig_key in pairs:
        report=cache.get(target_key,{}).get(data_key)
        if (isinstance(report,dict)
                and validate_scope(report.get("_tdv_scope"))==chosen
                and report.get("_tdv_source_bindings")):
            session[data_key]=report
            session[sig_key]=cache[target_key].get(sig_key)

def render_scope_selector(st, role="analyst"):
    s=st.session_state
    saved=s.setdefault("tdv_see_pro_workspaces",{})
    current=s.get("tdv_see_pro_active_scope")
    st.markdown("**📁 SEE PRO · Phạm vi dự án và gói thầu**")
    if current:
        st.caption("Đang chọn: "+ " / ".join(current[k] for k in FIELDS))
    else:
        st.warning("Chưa khóa phạm vi: Báo cáo đối chiếu bị chặn.")
    if role=="viewer": return
    with st.expander("Tạo/chuyển phạm vi (tối đa 5 dự án)",expanded=not bool(current)):
        with st.form("tdv_scope_form"):
            project=st.text_input("Mã dự án",value=current["project_id"] if current else "")
            package=st.text_input("Mã gói BP",value=current["package_id"] if current else "")
            revision=st.text_input("Phiên bản E-HSMT",value=current["ehsmt_revision_id"] if current else "")
            create=st.form_submit_button("Kích hoạt dự án/gói/phiên bản")
        if create:
            candidate=validate_scope(dict(project_id=project,package_id=package,ehsmt_revision_id=revision))
            projects={x["project_id"] for x in saved.values()}
            if not candidate:
                st.error("Mỗi mã 2–80 ký tự, chỉ dùng chữ, số, dấu chấm/gạch/gạch dưới")
            elif candidate["project_id"] not in projects and len(projects)>=5:
                st.error("Đã có 5 dự án trong phiên")
            else:
                key="::".join(candidate.values())
                saved[key]=candidate
                switch_workspace(s,candidate)
                st.success("Đã chọn phạm vi, nạp E-HSMT và NSX trong đúng gói này.")
        if saved:
            chosen=st.selectbox("Các gói đã mở trong phiên",list(saved),
                                format_func=lambda x:x.replace("::"," / "),key="tdv_scope_choice")
            if st.button("Chuyển gói đã chọn",key="tdv_scope_switch"):
                selected=saved[chosen]
                switch_workspace(s,selected)
                st.info("Đã chuyển phạm vi. Chỉ phục hồi báo cáo thuộc đúng gói này nếu còn trong phiên RAM.")
    st.caption("Preview: dữ liệu chỉ trong phiên RAM; chưa có lưu trữ bền vững/phân quyền dự án.")