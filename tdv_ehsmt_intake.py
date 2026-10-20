"""Read-only, evidence-first E-HSMT PDF intake. No AI approvals, no external writes."""
from __future__ import annotations
import hashlib
import re

SUMMARY_ROW = re.compile(
    r'^\s*(\d{1,4})\s+(PP\d{10})\s+(G1\.\d{3})\s+(.+?)\s{2,}(\d[\d.]*)\s+(\d[\d.]*)\s*r'(?<!\w)G\s*1\s*[.．]\s*(\d{1,4})(?!\d)', re.I)
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
    summary_conflicts = []
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
                key = row['MA_THUOC']
                if key in summary and summary[key] != row:
                    summary_conflicts.append(key)
                else:
                    summary[key] = row
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
    for key, entry in results.items():
        if key in summary:
            entry.update(summary[key])
            entry['TRICH_DOAN'] = summary[key]['CHUNG_CU_BANG_TONG_HOP']
            entry['TRANG_THAI'] = 'DA_TRICH_XUAT_BANG_TONG_HOP_CHUA_XAC_MINH'
        else:
            entry['TRANG_THAI'] = 'THIEU_DONG_BANG_TONG_HOP_CAN_KIEM_TRA'
    if summary_conflicts:
        warnings.append(f'{len(set(summary_conflicts))} mã có dòng bảng tổng hợp mâu thuẫn')
    if len(summary) != len(results):
        warnings.append(f'Bảng tổng hợp trích xuất chắc chắn {len(summary)}/{len(results)} mã; các mã còn lại cần kiểm tra thủ công')
    if blank_pages:
        warnings.append(f'{len(blank_pages)} trang không có lớp chữ: cần OCR/đối chiếu ảnh gốc')
    if not results:
        warnings.append('Không nhận diện được mã G1.xxx; chưa thể trích xuất danh mục')
    return {
        'sha256': hashlib.sha256(data).hexdigest(), 'total_pages': total,
        'pages_processed': total, 'pages_without_text': blank_pages,
        'lot_count': len(results), 'summary_rows': len(summary),
        'missing_summary': sorted(set(results) - set(summary)),
        'lots': sorted(results.values(), key=lambda r: int(r['MA_THUOC'].split('.')[1])),
        'warnings': warnings, 'verified': False,
        'note': 'Hoạt chất và giá trị ước tính lấy từ bảng tổng hợp khi nhận dạng đủ một dòng; giá trị ước tính KHÔNG phải giá đơn vị. Hàm lượng, dạng bào chế, số lượng, giá kế hoạch và nhóm thuốc vẫn cần đối chiếu bảng chi tiết.'
    }

def export_ehsmt_csv(result: dict) -> bytes:
    import pandas as pd
    rows = [{**x, 'TRANG_NGUON': ', '.join(map(str, x['TRANG_NGUON']))} for x in result['lots']]
    return pd.DataFrame(rows, columns=[
        'MA_THUOC', 'MA_PHAN_LO', 'STT', 'HOAT_CHAT_CHUAN', 'GIA_TRI_UOC_TINH', 'BAO_DAM_DU_THAU', 'TRANG_BANG_TONG_HOP', 'TRANG_NGUON', 'TRICH_DOAN', 'TRANG_THAI'
    ]).to_csv(index=False).encode('utf-8-sig')
,
    re.M,
)
def _summary_rows(raw: str, page_no: int) -> list:
    rows = []
    for m in SUMMARY_ROW.finditer(raw):
        stt, part, code, ingredient, value, guarantee = m.groups()
        rows.append({
            'MA_THUOC': code, 'MA_PHAN_LO': part, 'STT': int(stt),
            'HOAT_CHAT_CHUAN': ingredient.strip(),
            'GIA_TRI_UOC_TINH': int(value.replace('.', '')),
            'BAO_DAM_DU_THAU': int(guarantee.replace('.', '')),
            'TRANG_BANG_TONG_HOP': page_no,
            'CHUNG_CU_BANG_TONG_HOP': m.group(0).strip(),
        })
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
    if blank_pages:
        warnings.append(f'{len(blank_pages)} trang không có lớp chữ: cần OCR/đối chiếu ảnh gốc')
    if not results:
        warnings.append('Không nhận diện được mã G1.xxx; chưa thể trích xuất danh mục')
    return {
        'sha256': hashlib.sha256(data).hexdigest(), 'total_pages': total,
        'pages_processed': total, 'pages_without_text': blank_pages,
        'lot_count': len(results),
        'lots': sorted(results.values(), key=lambda r: int(r['MA_THUOC'].split('.')[1])),
        'warnings': warnings, 'verified': False,
        'note': 'Mã danh mục ứng viên; chưa xác minh hoạt chất, số lượng, giá, nhóm thuốc và tính đầy đủ.'
    }

def export_ehsmt_csv(result: dict) -> bytes:
    import pandas as pd
    rows = [{**x, 'TRANG_NGUON': ', '.join(map(str, x['TRANG_NGUON']))} for x in result['lots']]
    return pd.DataFrame(rows, columns=[
        'MA_THUOC', 'MA_PHAN_LO', 'TRANG_NGUON', 'TRICH_DOAN', 'TRANG_THAI'
    ]).to_csv(index=False).encode('utf-8-sig')
