import streamlit as st
import pandas as pd
import numpy as np
import re
import urllib.parse
import requests
from difflib import SequenceMatcher
from datetime import datetime

st.set_page_config(
    page_title="DUBIPHARMA DŨNG BÍCH - Hệ Thống Đấu Thầu & Đối Chiếu Nhà Sản Xuất",
    page_icon="💊",
    layout="wide"
)

st.title("💊 CÔNG TY DƯỢC PHẨM DŨNG BÍCH (DUBIPHARMA) - HỆ THỐNG ĐẤU THẦU THUỐC")
st.caption("Tự động Bóc tách E-HSMT -> Phân loại Nhóm & Gợi ý Nhà Sản Xuất (Link Web/DAV) -> Đối chiếu Đáp ứng (Chữ Xanh / Đỏ) -> Đóng gói & Phân bổ")

# ================= 1. CƠ SỞ DỮ LIỆU GỢI Ý NHÀ SẢN XUẤT & LINK WEB =================
SUPPLIER_DIRECTORY = [
    {"Tên Nhà Sản Xuất": "Imexpharm (Công ty CP Dược phẩm Imexpharm)", "Nhóm Đáp Ứng": [1, 2, 3, 4, 5], "Thế Mạnh": "Kháng sinh tiêm/uống, Tim mạch (Dây chuyền EU-GMP)", "Website": "https://www.imexpharm.com"},
    {"Tên Nhà Sản Xuất": "Stada Việt Nam / Pymepharco", "Nhóm Đáp Ứng": [1, 2, 3, 4, 5], "Thế Mạnh": "Đa nhóm điều trị, viên nén, viên nang (EU-GMP)", "Website": "https://www.stada.vn"},
    {"Tên Nhà Sản Xuất": "Savipharm (Công ty CP Dược phẩm SaVi)", "Nhóm Đáp Ứng": [1, 2, 3, 4, 5], "Thế Mạnh": "Thuốc tim mạch, tiểu đường, huyết áp (EU-GMP / PIC/S)", "Website": "https://savipharm.com.vn"},
    {"Tên Nhà Sản Xuất": "Hasan - Dermapharm", "Nhóm Đáp Ứng": [2, 3, 4, 5], "Thế Mạnh": "Tim mạch, huyết áp, tiểu đường (WHO-GMP / TĐSH)", "Website": "https://hasandermapharm.com"},
    {"Tên Nhà Sản Xuất": "Dược Hậu Giang (DHG Pharma)", "Nhóm Đáp Ứng": [2, 3, 4, 5], "Thế Mạnh": "Kháng sinh, giảm đau hạ sốt, tiêu hóa (Japan-GMP / PIC/S / TĐSH)", "Website": "https://www.dhgpharma.com.vn"},
    {"Tên Nhà Sản Xuất": "Traphaco", "Nhóm Đáp Ứng": [3, 4, 5], "Thế Mạnh": "Tân dược, thuốc nhỏ mắt, ống uống, đông dược (WHO-GMP / TĐSH)", "Website": "https://traphaco.com.vn"},
    {"Tên Nhà Sản Xuất": "Boston Pharma", "Nhóm Đáp Ứng": [3, 4, 5], "Thế Mạnh": "Viên uống, viên sủi, hỗn dịch, TĐSH (EU-GMP / WHO-GMP)", "Website": "https://bostonpharma.com.vn"},
    {"Tên Nhà Sản Xuất": "Vinphaco (Dược phẩm Vĩnh Phúc)", "Nhóm Đáp Ứng": [3, 4, 5], "Thế Mạnh": "Thuốc tiêm, thuốc tiêm đông khô, dịch truyền (WHO-GMP)", "Website": "https://vinphaco.com.vn"},
    {"Tên Nhà Sản Xuất": "Bidiphar (Dược - Trang thiết bị Y tế Bình Định)", "Nhóm Đáp Ứng": [2, 3, 4, 5], "Thế Mạnh": "Thuốc ung thư, thuốc tiêm đông khô, dịch truyền", "Website": "https://bidiphar.com"},
    {"Tên Nhà Sản Xuất": "Fresenius Kabi Việt Nam", "Nhóm Đáp Ứng": [1, 2, 3, 4, 5], "Thế Mạnh": "Dịch truyền, Acid amin, Nhũ dịch lipid, Nước cất, Thuốc tiêm", "Website": "https://www.fresenius-kabi.com/vn"},
    {"Tên Nhà Sản Xuất": "CPC1 Hà Nội", "Nhóm Đáp Ứng": [3, 4, 5], "Thế Mạnh": "Thuốc nhỏ mắt công nghệ BFS, ống uống, khí dung, tiêm truyền", "Website": "https://cpc1hn.com.vn"},
]

def suggest_manufacturers(nhom_yc, duong_dung, hoat_chat, ham_luong):
    """Tự động tìm và gợi ý Nhà sản xuất phù hợp kèm Link Website & Link tra cứu DAV"""
    nhom = int(nhom_yc) if pd.notna(nhom_yc) and str(nhom_yc).isdigit() else 4
    dd = str(duong_dung).lower()
    
    if nhom == 1:
        nsx = "Imexpharm (EU-GMP), Stada/Pymepharco (EU-GMP), Sanofi, AstraZeneca"
        web = "https://www.imexpharm.com"
    elif nhom == 2:
        nsx = "Stada VN, Pymepharco, Savipharm (PIC/S-GMP), Imexpharm"
        web = "https://savipharm.com.vn"
    elif nhom == 3:
        nsx = "Dược Hậu Giang (DHG), Boston Pharma, Hasan-Dermapharm, Davipharm (Có TĐSH)"
        web = "https://www.dhgpharma.com.vn"
    else:
        if "tiêm" in dd or "truyền" in dd:
            nsx = "Vinphaco (Vĩnh Phúc), Bidiphar, Fresenius Kabi VN, CPC1 Hà Nội"
            web = "https://vinphaco.com.vn"
        elif "mắt" in dd or "mũi" in dd or "hô hấp" in dd:
            nsx = "CPC1 Hà Nội, Traphaco, Dược Khoa (DK Pharma), Mekophar"
            web = "https://cpc1hn.com.vn"
        else:
            nsx = "Dược Hậu Giang, Traphaco, Boston Pharma, Nam Hà, Pharbaco"
            web = "https://traphaco.com.vn"

    query = urllib.parse.quote(f"site:dav.gov.vn OR site:dichvucong.dav.gov.vn {hoat_chat} {ham_luong}")
    dav_link = f"https://www.google.com/search?q={query}"
    return pd.Series([nsx, web, dav_link])

# ================= 2. BỘ BÓC TÁCH TỰ ĐỘNG FILE EXCEL E-HSMT NGUYÊN BẢN =================
def clean_vn_number(val):
    if pd.isna(val):
        return 0
    s = re.sub(r"[^\d]", "", str(val))
    return int(s) if s.isdigit() else 0

def parse_raw_ehsmt_excel(uploaded_file):
    """
    Tự động đọc file Excel E-HSMT nguyên bản (như file 'Hồ sơ mời thầu (G1-SYT).xlsx' của Sở Y tế Tuyên Quang),
    bóc tách và ghép nối các bảng: Mẫu số 00 (770 mặt hàng) + Mục 18.2 (BĐDT) + Bảng X (Doanh thu & HĐ tương tự).
    """
    raw_df = pd.read_excel(uploaded_file, header=None)
    
    # Nếu là bảng danh mục chuẩn đã có sẵn cột "Mã Thuốc" ở dòng đầu
    first_row_str = " ".join(raw_df.iloc[0].dropna().astype(str).tolist()).lower()
    if "mã thuốc" in first_row_str or "tên hoạt chất" in first_row_str:
        df_std = pd.read_excel(uploaded_file)
        return df_std

    # Quét toàn bộ các dòng trong file E-HSMT xuất từ e-GP
    bddt_map = {}      # Mã phần -> Tiền BĐDT
    bangx_map = {}     # Mã phần -> (Doanh thu BQ, HĐ tương tự)
    mau00_items = []   # Danh sách mặt hàng từ Mẫu số 00

    in_mau00 = False
    current_item = None

    for idx, row in raw_df.iterrows():
        vals = [str(v).strip() if pd.notna(v) else "" for v in row.values]
        non_empty = [v for v in vals if v != ""]
        if not non_empty:
            continue
        joined = " ".join(non_empty)

        # Bỏ qua dòng footer in từ muasamcong hoặc số trang
        if "Tài liệu được in từ Hệ thống e-GP" in joined or (len(non_empty) == 1 and non_empty[0].isdigit()):
            continue
        if "Mã phần" in joined and ("Tên hoạt chất" in joined or "Tên phần" in joined or "Đơn vị tính" in joined):
            continue

        # Kiểm tra bắt đầu/kết thúc Mẫu số 00
        if "BẢNG PHẠM VI CUNG CẤP" in joined or "Đối với gói thầu thuốc generic" in joined:
            in_mau00 = True
            continue
        if in_mau00 and ("Mẫu số 01" in joined or "ĐƠN DỰ THẦU" in joined):
            if current_item:
                mau00_items.append(current_item)
                current_item = None
            in_mau00 = False
            continue

        # 1. Thu thập bảng BĐDT & Bảng X (Các bảng có mã PP26... nằm gọn trên 1 dòng 6 cột)
        if not in_mau00:
            col1_clean = re.sub(r"\s+", "", vals[1]) if len(vals) > 1 else ""
            if col1_clean
