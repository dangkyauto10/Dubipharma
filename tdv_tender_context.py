"""Read-only procurement document context for TDV QC7 tender audit.

Never treats public information as legal approval or guesses package affiliation.
A document's category is extracted from its text, NOT from the filename.
No HTTP requests and no private uploads to a public evidence catalogue.
"""
from __future__ import annotations

import re
import unicodedata

PUBLIC_REFERENCES = (
    {"name": "Hệ thống mạng đấu thầu quốc gia",
     "url": "https://muasamcong.mpi.gov.vn/",
     "purpose": "Tra thông báo, E-HSMT, văn bản sửa đổi/làm rõ và kết quả thầu",
     "authority": "Cổng thông tin nguồn — tài liệu cụ thể cần kiểm tra"},
    {"name": "Cục Quản lý Dược — thông tin đăng ký thuốc",
     "url": "https://dav.gov.vn/dang-ki-thuoc-cn6.html",
     "purpose": "Tra quyết định cấp/gia hạn/thu hồi/điều chỉnh SĐK",
     "authority": "Nguồn tham khảo; không tự xác nhận SĐK"},
    {"name": "DAV — công khai cơ sở sản xuất trong nước được cấp GMP",
     "url": "https://dav.gov.vn/danh-sach-cssx-duoc-cap-gmp-cua-dav-cn92.html",
     "purpose": "Đối chiếu cơ sở, địa chỉ, phạm vi, kỳ công bố",
     "authority": "Danh sách công khai không thay giấy chứng nhận gốc"},
    {"name": "DAV — tra cơ sở nước ngoài đáp ứng GMP",
     "url": "https://dichvucong.dav.gov.vn/DanhSachCoSoSanXuatNuocNgoaiDapUngGMP/",
     "purpose": "Tra cơ sở, nguyên tắc GMP, chứng nhận, thời hạn",
     "authority": "Phải kiểm tra từng cơ sở, thời hạn và phạm vi"},
    {"name": "Cơ sở dữ liệu văn bản pháp luật",
     "url": "https://vbpl.vn/",
     "purpose": "Tra các quy định áp dụng theo thời điểm và gói thầu",
     "authority": "Không tự xác định hồ sơ bắt buộc cho gói thầu"},
)

DOCUMENT_KINDS = (
    ("SUA_DOI_EHSMT", (
        "sua doi e hsmt", "dieu chinh e hsmt", "dinh chinh e hsmt",
        "quyet dinh sua doi ho so moi thau", "quyet dinh dieu chinh e hsmt")),
    ("LAM_RO_EHSMT", (
        "lam ro e hsmt", "tra loi lam ro ho so moi thau",
        "van ban lam ro e hsmt", "yeu cau lam ro e hsmt")),
    ("THONG_BAO_MOI_THAU", ("thong bao moi thau", "thong bao moi thau qua mang")),
    ("E_HSMT", ("ho so moi thau qua mang", "ho so moi thau e hsmt",
                 "ho so moi thau thuoc")),
    ("PHU_LUC_KY_THUAT", ("yeu cau ky thuat thuoc",
                          "bang yeu cau ky thuat",
                          "danh muc thuoc moi thau", "bang thong so ky thuat")),
    ("TIEU_CHI_DANH_GIA", ("tieu chuan danh gia e hsdt",
                           "tieu chuan danh gia ho so du thau",
                           "tieu chi danh gia ho so du thau")),
    ("BAO_DAM_DU_THAU", ("thu bao lanh du thau", "bao dam du thau",
                         "chung thu bao lanh du thau")),
    ("BIEN_BAN_MO_THAU", ("bien ban mo thau",)),
    ("KET_QUA_LCNT", ("ket qua lua chon nha thau",)),
    ("HOP_DONG_THAU", ("hop dong cung cap thuoc", "hop dong mua sam thuoc")),
)
KNOWN = {k for k, _ in DOCUMENT_KINDS}
_BP = re.compile(r"(?<![A-Za-z0-9])BP\s*(\d{10,})(?!\d)", re.I)
_IB = re.compile(r"(?<![A-Za-z0-9])IB\s*(\d{10,})(?!\d)", re.I)
_G1 = re.compile(r"\bG1[.．]\d{3}\b", re.I)


def _norm(s: str) -> str:
    chars = unicodedata.normalize("NFKD", s.replace("Đ", "D").replace("đ", "d"))
    chars = "".join(c for c in chars if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", chars.lower())).strip()


def detect_procurement_document(lines: list[dict]) -> dict | None:
    """Classify positive, specific tender signatures; remain conservative."""
    text_raw = " ".join(str(line.get("text", "")) for line in lines[:3000])
    text = _norm(text_raw)
    kind = None
    for category, phrases in DOCUMENT_KINDS:
        if any(p in text for p in phrases):
            kind = category
            break
    if kind is None:
        return None
    packages = sorted({"BP" + m for m in _BP.findall(text_raw)})
    notices = sorted({"IB" + m for m in _IB.findall(text_raw)})
    lots = sorted({m.upper().replace("．", ".") for m in _G1.findall(text_raw)})[:500]
    return {
        "kind": kind, "package_ids": packages, "notice_ids": notices,
        "lot_codes": lots, "source_scope": "văn bản đã nạp",
        "verified": False,
        "warning": ("Chỉ phân loại chứng cứ văn bản. Không tự kết luận "
                    "tính bắt buộc, hiệu lực, hoặc phiên bản mới nhất."),
    }


def index_tender_documents(documents: list[dict]) -> dict:
    """Group by explicit ID; do not merge unanchored or mixed-package docs."""
    by_package = {}
    unassigned = []
    for doc in documents:
        ids = doc.get("package_ids") or []
        if len(ids) != 1:
            unassigned.append({
                "filename": doc.get("filename", ""),
                "reason": ("KHONG_CO_MA_BP" if not ids else
                           "NHIEU_MA_BP_TRONG_MOT_TAI_LIEU"),
                "status": "CAN_XAC_MINH_MA_GOI",
            })
            continue
        code = ids[0]
        by_package.setdefault(code, []).append(doc)
    return {
        "by_package": by_package, "unassigned": unassigned,
        "verified": False,
        "note": "Chỉ nối tài liệu theo mã BP trích trong nội dung gốc.",
    }
