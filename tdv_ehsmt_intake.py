"""Read-only, evidence-first E-HSMT PDF intake. No AI approvals, no external writes."""
from __future__ import annotations
import hashlib
import re


def _summary_rows(raw: str, page_no: int) -> list:
    """Parse only unambiguous same-line table records; never invent missing values."""
    pattern = re.compile(r"^\\s*(\\d{1,4})\\s+(PP\\d{10})\\s+(G1\\.\\d{3})\\s+(.+?)\\s{2,}(\\d[\\d.]*)\\s+(\\d[\\d.]*)\\s*$")
    rows = []
    for line in raw.splitlines():
        match = pattern.fullmatch(line)
        if match:
            stt, part, code, ingredient, amount, guarantee = match.groups()
            rows.append({"MA_THUOC": code, "MA_PHAN_LO": part, "STT": int(stt),
                         "HOAT_CHAT_CHUAN": ingredient.strip(),
                         "GIA_TRI_UOC_TINH": int(amount.replace(".", "")),
                         "BAO_DAM_DU_THAU": int(guarantee.replace(".", "")),
                         "TRANG_BANG_TONG_HOP": page_no,
                         "CHUNG_CU_BANG_TONG_HOP": line.strip()})
    return rows

LOT = re.compile(r'(?<!\w)G\s*1\s*[.．]\s*(\d{1,4})(?!\d)', re.I)
PART = re.compile(r'(?<!\w)PP\s*(\d{10})(?!\d)', re.I)

def inspect_ehsmt_pdf(data: bytes, *, max_bytes: int = 40 * 1024 * 1024,
                      max_pages: int = 1200) -> dict:
    if not isinstance(data, bytes) or not data.startswith(b'%PDF-') or len(data) > max_bytes:
        raise ValueError('Chỉ chấp nhận PDF hợp lệ, tối đa 40 MB')
    import pymupdf
    results = {}
    warnings = []
    blank_pages = []
    summary = {}
    conflicts = set()
    with pymupdf.open(stream=data, filetype='pdf') as pdf:
        if pdf.needs_pass or not pdf.page_count:
            raise ValueError('PDF rỗng hoặc cần mật khẩu')
        if pdf.page_count > max_pages:
            raise ValueError(f'PDF có {pdf.page_count} trang, vượt giới hạn {max_pages}; không báo đủ')
        total = pdf.page_count
        for idx, page in enumerate(pdf):
            page_no = idx + 1
            raw = page.get_text('text', sort=True) or ''
            if not raw.strip():
                blank_pages.append(page_no)
                continue
            for row in _summary_rows(raw, page_no):
                code = row['MA_THUOC']
                if code in summary and summary[code] != row:
                    conflicts.add(code)
                else:
                    summary[code] = row
            for m in LOT.finditer(raw):
                key = f'G1.{int(m.group(1)):03d}'
                entry = results.setdefault(key, {
                    'MA_THUOC': key, 'MA_PHAN_LO': '', 'TRANG_NGUON': [],
                    'TRICH_DOAN': '', 'TRANG_THAI': 'CAN_XAC_MINH'})
                if page_no not in entry['TRANG_NGUON']:
                    entry['TRANG_NGUON'].append(page_no)
                if not entry['TRICH_DOAN']:
                    entry['TRICH_DOAN'] = re.sub(r'\s+', ' ', raw[max(0, m.start()-90):m.end()+220])[:320]
                # Only use immediately adjacent PP code; never assign an unrelated code.
                before = raw[max(0, m.start()-25):m.start()]
                pm = list(PART.finditer(before))
                if pm and not entry['MA_PHAN_LO']:
                    entry['MA_PHAN_LO'] = 'PP' + pm[-1].group(1)
    for code, entry in results.items():
        if code in summary and code not in conflicts:
            entry.update(summary[code])
            entry['TRICH_DOAN'] = summary[code]['CHUNG_CU_BANG_TONG_HOP']
            entry['TRANG_THAI'] = 'TRICH_XUAT_SO_BO_CHUA_XAC_MINH'
        else:
            entry['TRANG_THAI'] = 'CAN_KIEM_TRA_DONG_GOC'
    if conflicts:
        warnings.append(f'{len(conflicts)} mã có dòng bảng tổng hợp mâu thuẫn')
    if len(summary) != len(results):
        warnings.append(f'Chỉ nhận dạng rõ {len(summary)}/{len(results)} dòng bảng tổng hợp; không tự điền dữ liệu thiếu')
    if blank_pages:
        warnings.append(f'{len(blank_pages)} trang không có lớp chữ: cần OCR/đối chiếu ảnh gốc')
    if not results:
        warnings.append('Không nhận diện được mã G1.xxx; chưa thể trích xuất danh mục')
    return {
        'sha256': hashlib.sha256(data).hexdigest(), 'total_pages': total,
        'pages_processed': total, 'pages_without_text': blank_pages,
        'lot_count': len(results), 'summary_rows': len(summary) - len(conflicts),
        'missing_summary': sorted(set(results) - set(summary) | conflicts),
        'lots': sorted(results.values(), key=lambda r: int(r['MA_THUOC'].split('.')[1])),
        'warnings': warnings, 'verified': False,
        'note': 'Mã danh mục ứng viên; chưa xác minh hoạt chất, số lượng, giá, nhóm thuốc và tính đầy đủ.'
    }

def export_ehsmt_csv(result: dict) -> bytes:
    import pandas as pd
    rows = [{**x, 'TRANG_NGUON': ', '.join(map(str, x['TRANG_NGUON']))} for x in result['lots']]
    return pd.DataFrame(rows, columns=[
        'MA_THUOC', 'MA_PHAN_LO', 'STT', 'HOAT_CHAT_CHUAN', 'GIA_TRI_UOC_TINH', 'BAO_DAM_DU_THAU', 'TRANG_BANG_TONG_HOP', 'TRANG_NGUON', 'TRICH_DOAN', 'TRANG_THAI'
    ]).to_csv(index=False).encode('utf-8-sig')
