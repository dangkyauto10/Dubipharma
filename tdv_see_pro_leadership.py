"""Read-only SEE PRO leadership views, with no legal approval."""
from collections import Counter
from io import BytesIO

DAT="ĐẠT"
CHUA="CHƯA ĐẠT"
KHONG="KHÔNG ĐẠT"
CHO="CHỜ ĐỐI CHIẾU"

def _s(value):
    return str(value).strip() if value is not None else ""

def _reason(field):
    a,b=_s(field.get("ehsmt")),_s(field.get("nsx"))
    if not a: return "Thiếu yêu cầu E-HSMT đã đọc"
    if not b: return "Thiếu thông số NSX có căn cứ"
    if field.get("status")=="KHONG_KHOP_CAN_XAC_MINH":
        return "Khác thông số sơ bộ: E-HSMT "+a+" / NSX "+b+"; phải so hai bản gốc"
    if field.get("status")=="DAT_SO_BO":
        return "Trùng dữ liệu sơ bộ; chưa xác minh mọi yêu cầu"
    return _s(field.get("note")) or "Thiếu chứng cứ, chưa được xác minh"

def build_register(report,scope_ok=False,reason=""):
    if not scope_ok:
        return {"blocked":True,"reason":reason,"rows":[],"criteria":[],
                "summary":{DAT:0,CHUA:0,KHONG:0,CHO:0},"total":0}
    seen=set();rows=[];criteria=[]
    for drug in report.get("comparison") or []:
        code=_s(drug.get("MA_THUOC_EHSMT"))
        if not code or code in seen: raise ValueError("Mã E-HSMT trùng hoặc thiếu")
        seen.add(code)
        fields=drug.get("criteria") or []
        red=[x for x in fields if x.get("status")=="KHONG_KHOP_CAN_XAC_MINH"]
        yellow=[x for x in fields if x.get("status")=="CHUA_DU_CAN_CU"]
        if not drug.get("MA_THUOC_NSX"):
            why="Chưa liên kết duy nhất sản phẩm NSX vào mã E-HSMT"
        elif red: why="; ".join(_s(x.get("label"))+": "+_reason(x) for x in red)
        elif yellow: why=f"{len(yellow)} tiêu chí còn thiếu chứng cứ; xem hai nguồn"
        else: why="Khớp sơ bộ 4 tiêu chí; chưa xác minh tiêu chí khác, SĐK/GMP, pháp lý"
        # No final verified decisions are emitted by the current engine.
        rows.append({"ma_ehsmt":code,"ma_lo":_s(drug.get("MA_PHAN_LO")),
                     "hoat_chat":_s(drug.get("HOAT_CHAT_EHSMT")),
                     "ma_nsx":_s(drug.get("MA_THUOC_NSX")),
                     "ten_nsx":_s(drug.get("TEN_THUOC_NSX")),
                     "trang_thai":CHO if not drug.get("MA_THUOC_NSX") else CHUA,"nguyen_nhan":why,
                     "khop_so_bo":sum(f.get("status")=="DAT_SO_BO" for f in fields),
                     "thieu_chung_cu":len(yellow),"khac_so_bo":len(red),
                     "file_ehsmt":_s(drug.get("NGUON_EHSMT")),
                     "vi_tri_ehsmt":_s(drug.get("VI_TRI_EHSMT")),
                     "file_nsx":_s(drug.get("NGUON_THUOC_NSX")),
                     "sha256_nsx":_s(drug.get("SHA256_NSX"))})
        for field in fields:
            a,b=field.get("ehsmt_evidence") or {},field.get("nsx_evidence") or {}
            criteria.append({"ma_ehsmt":code,"ma_nsx":_s(drug.get("MA_THUOC_NSX")),
                             "tieu_chi":_s(field.get("label")),
                             "ehsmt":_s(field.get("ehsmt")),"nsx":_s(field.get("nsx")),
                             "so_bo":_s(field.get("status")),"nguyen_nhan":_reason(field),
                             "file_ehsmt":_s(a.get("file")),"vi_tri_ehsmt":_s(a.get("location")),
                             "trich_goc_ehsmt":_s(a.get("raw")),"sha_ehsmt":_s(a.get("sha256")),
                             "file_nsx":_s(b.get("file")),"vi_tri_nsx":_s(b.get("location")),
                             "trich_goc_nsx":_s(b.get("raw")),"sha_nsx":_s(b.get("sha256"))})
    count=Counter(x["trang_thai"] for x in rows)
    return {"blocked":False,"rows":rows,"criteria":criteria,
            "summary":{key:count[key] for key in (DAT,CHUA,KHONG,CHO)},
            "total":len(rows)}

def export_xlsx(report,scope):
    from openpyxl import Workbook
    from openpyxl.styles import PatternFill,Font,Alignment
    from openpyxl.utils import get_column_letter
    from see_pro_traceability import safe_cell
    wb=Workbook();overview=wb.active;overview.title="01_TONG_QUAN"
    overview.append(["Báo cáo SEE PRO - CHƯA PHÊ DUYỆT",""])
    for label,key in (("Dự án","project_id"),("Mã gói","package_id"),("Phiên bản","ehsmt_revision_id")):
        overview.append([label,scope[key]])
    overview.append(["Đơn vị thống kê","Mã mặt hàng E-HSMT không trùng"])
    for state in (DAT,CHUA,KHONG,CHO): overview.append([state,report["summary"][state]])
    overview.append(["Tổng đã phân nhóm",report["total"]])
    overview.append(["Giới hạn","Khớp/khác sơ bộ chưa phải quyết định đủ điều kiện"])
    rows=report["rows"];keys=list(rows[0]) if rows else ["ma_ehsmt","trang_thai","nguyen_nhan"]
    for state,name in ((DAT,"02_DAT"),(CHUA,"03_CHUA_DAT"),(KHONG,"04_KHONG_DAT"),(CHO,"05_CHO_DOI_CHIEU")):
        ws=wb.create_sheet(name);ws.append(keys)
        for x in rows:
            if x["trang_thai"]==state: ws.append([safe_cell(x.get(k)) for k in keys])
        ws.freeze_panes="D2";ws.auto_filter.ref=ws.dimensions
    ws=wb.create_sheet("06_HAI_NGUON_LY_DO")
    cols=list(report["criteria"][0]) if report["criteria"] else ["ma_ehsmt","tieu_chi","ehsmt","nsx","nguyen_nhan"]
    ws.append(cols)
    for x in report["criteria"]: ws.append([safe_cell(x.get(k)) for k in cols])
    ws.freeze_panes="D2";ws.auto_filter.ref=ws.dimensions
    for ws in wb:
        for c in ws[1]:
            c.font=Font(bold=True,color="FFFFFF");c.fill=PatternFill("solid",fgColor="164065")
        for col in ws.columns:
            w=max(len(str(c.value or "")) for c in list(col)[:120])
            ws.column_dimensions[get_column_letter(col[0].column)].width=min(65,max(14,w+2))
        for row in ws.iter_rows(min_row=2):
            for cell in row:cell.alignment=Alignment(wrap_text=True,vertical="top")
    out=BytesIO();wb.save(out);return out.getvalue()

def export_docx(register, scope):
    """Word executive summary; full two-source audit always in matching Excel."""
    from docx import Document
    from docx.shared import Pt
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    doc=Document()
    section=doc.sections[0]
    section.header.paragraphs[0].text="TDV QC7 ONLINE  |  SEE PRO"
    doc.add_heading("BÁO CÁO LÃNH ĐẠO — ĐỐI CHIẾU TỪNG MẶT HÀNG",0)
    doc.add_paragraph("BÁO CÁO SƠ BỘ — KHÔNG PHẢI KẾT LUẬN ĐỦ ĐIỀU KIỆN DỰ THẦU")
    doc.add_paragraph("Dự án: "+scope["project_id"]+"  |  Gói: "+scope["package_id"]+
                      "  |  Phiên bản E-HSMT: "+scope["ehsmt_revision_id"])
    doc.add_paragraph("Đơn vị đếm: một mã mặt hàng E-HSMT; không đếm trùng các ứng viên NSX.")
    table=doc.add_table(rows=1,cols=2);table.style="Light Shading Accent 1"
    table.rows[0].cells[0].text="Nhóm";table.rows[0].cells[1].text="Số mặt hàng"
    for key in (DAT,CHUA,KHONG,CHO):
        cells=table.add_row().cells;cells[0].text=key;cells[1].text=str(register["summary"][key])
    doc.add_paragraph("Tổng mã E-HSMT đã phân nhóm: "+str(register["total"]))
    doc.add_paragraph("Mọi mục đã ghép NSX chưa được xác minh đầy đủ đều thuộc CHƯA ĐẠT; "
                      "chưa ghép NSX được xếp CHỜ ĐỐI CHIẾU. Không tự kết luận KHÔNG ĐẠT.")
    for status in (DAT,CHUA,KHONG,CHO):
        group=[x for x in register["rows"] if x["trang_thai"]==status]
        doc.add_heading(status+" — "+str(len(group))+" mặt hàng",level=1)
        if not group:
            doc.add_paragraph("Chưa có mặt hàng đủ căn cứ xếp nhóm này.")
            continue
        for r in group:
            doc.add_paragraph(r["ma_ehsmt"]+" / "+(r["ten_nsx"] or "chưa ghép NSX")+
                              ": "+r["nguyen_nhan"],style="List Bullet")
    doc.add_heading("Các tiêu chí cần truy cứu và chứng cứ",level=1)
    doc.add_paragraph("Bảng đầy đủ tất cả tiêu chí nằm tại sheet 06_HAI_NGUON_LY_DO "
                      "của Excel xuất kèm. Dưới đây là tối đa 20 điểm cần rà soát.")
    needs=[x for x in register["criteria"] if x["so_bo"]!="DAT_SO_BO"][:20]
    for f in needs:
        doc.add_heading(f["ma_ehsmt"]+" — "+f["tieu_chi"],level=2)
        doc.add_paragraph("E-HSMT: "+(f["ehsmt"] or "CHƯA ĐỌC ĐƯỢC")+" | "+
                          f["file_ehsmt"]+" "+f["vi_tri_ehsmt"])
        doc.add_paragraph("NSX: "+(f["nsx"] or "CHƯA CÓ")+" | "+
                          f["file_nsx"]+" "+f["vi_tri_nsx"])
        doc.add_paragraph("Lý do: "+f["nguyen_nhan"])
    doc.add_heading("Lưu ý xử lý",level=1)
    doc.add_paragraph("Cần kiểm tra đúng trang/ô của hồ sơ gốc, hiệu lực văn bản, SĐK, GMP, "
                      "điều kiện E-HSMT và người phê duyệt. Không dùng phần trăm trích xuất "
                      "làm kết luận dự thầu.")
    normal=doc.styles["Normal"];normal.font.name="Arial";normal.font.size=Pt(10)
    out=BytesIO();doc.save(out);return out.getvalue()
