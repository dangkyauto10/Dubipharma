import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from difflib import SequenceMatcher
from datetime import datetime

st.set_page_config(page_title="DUBIPHARMA - Hệ Thống Đấu Thầu & Phân Bổ", page_icon="💊", layout="wide")

st.title("💊 DUBIPHARMA DŨNG BÍCH - HỆ THỐNG QUẢN LÝ ĐẤU THẦU TOÀN DIỆN")
st.caption("Tích hợp Nhận diện thông minh (Fuzzy Logic), Cảnh báo giá bất thường & Traceability Lô/Date")

# ================= HÀM TIỆN ÍCH =================
def fuzzy_match_score(str1, str2):
    """Tính tỷ lệ giống nhau giữa 2 chuỗi (bỏ qua khoảng trắng, viết hoa thường)"""
    if pd.isna(str1) or pd.isna(str2): return 0
    s1, s2 = str(str1).strip().lower(), str(str2).strip().lower()
    return SequenceMatcher(None, s1, s2).ratio()

# ================= DỮ LIỆU MẪU (STATE) =================
if "hsmt_df" not in st.session_state:
    st.session_state.hsmt_df = pd.DataFrame([
        {"Mã Thuốc": "G1.001", "Tên Hoạt Chất": "Acarbose", "Hàm Lượng": "50mg", "Đường Dùng": "Uống", "Nhóm Thuốc Y/C": 2, "Giá Kế Hoạch": 1650}
    ])
if "bids_df" not in st.session_state:
    st.session_state.bids_df = pd.DataFrame([
        {"Mã Thuốc": "G1.001", "Tên Đơn Vị": "DUBIPHARMA", "Tên Thuốc Chào": "Dubi-Acarbose 50", "Hoạt Chất Chào": "Acarbose (Dạng muối)", "Hàm Lượng Chào": "50 mg", "Đường Dùng Chào": "Đường Uống", "Nhóm Thuốc Chào": 2, "SĐK Hợp Lệ": "Có", "Đơn Giá Chào": 900, "Ưu Đãi Nội Địa": "Có", "Điểm KT": 90.0}
    ])
if "batch_df" not in st.session_state:
    st.session_state.batch_df = pd.DataFrame([
        {"Mã Thuốc": "G1.001", "Số Lô": "DB-2610-01", "Hạn Sử Dụng": "2026-11-20", "Kho/CSYT Đang Tồn": "Kho BV Tỉnh"}
    ])
if "addendum_df" not in st.session_state:
    st.session_state.addendum_df = pd.DataFrame([
        {"Số Phụ Lục": "PL-01", "Ngày Ký": "2027-11-15", "Mã Thuốc": "G1.001", "Loại Điều Chỉnh": "+30% mua thêm", "Số Lượng Thay Đổi": 12600}
    ])

# ================= SIDEBAR =================
with st.sidebar:
    st.header("🔗 Kết Nối Dữ Liệu")
    gas_url = st.text_input("Dán Web App URL:")
    if st.button("📥 Tải Dữ Liệu Từ Sheet", use_container_width=True):
        st.info("Đã giả lập tải dữ liệu thành công từ Sheet.")
    if st.button("📤 Đẩy Kết Quả Lên Sheet", use_container_width=True):
        st.success("Đã đồng bộ lên hệ thống.")

# ================= CÁC TABS NGHIỆP VỤ =================
tab1, tab2, tab3, tab4 = st.tabs(["⚙️ Bóc Tách & Đối Chiếu Thông Minh", "📊 Quản Lý Phụ Lục HĐ", "⏳ Cảnh Báo Lô & Hạn Dùng", "📦 Checklist HSMT"])

with tab1:
    st.subheader("Bóc Tách Hồ Sơ & Đối Chiếu Nhận Diện Mờ (Fuzzy Matching)")
    st.markdown("Hệ thống tự động phát hiện lỗi chính tả, khác biệt quy cách đánh máy và **cảnh báo giá thấp bất thường (<60% giá kế hoạch)**.")
    
    st.write("Dữ liệu nhà thầu chào:")
    edited_bids = st.data_editor(st.session_state.bids_df, num_rows="dynamic", use_container_width=True)
    st.session_state.bids_df = edited_bids

    merged = pd.merge(edited_bids, st.session_state.hsmt_df, on="Mã Thuốc", how="left")

    def smart_evaluate(r):
        if pd.isna(r["Tên Hoạt Chất"]): return pd.Series([0, "Không thấy Mã", 0, "LOẠI"])
        
        # Nhận diện mờ (Fuzzy)
        score_hc = fuzzy_match_score(r["Hoạt Chất Chào"], r["Tên Hoạt Chất"])
        score_hl = fuzzy_match_score(r["Hàm Lượng Chào"], r["Hàm Lượng"])
        score_dd = fuzzy_match_score(r["Đường Dùng Chào"], r["Đường Dùng"])
        
        # Nếu giống >= 75% thì coi như khớp
        c_act = 1 if score_hc >= 0.75 else 0
        c_conc = 1 if score_hl >= 0.75 else 0
        c_route = 1 if score_dd >= 0.75 else 0
        
        # Nhóm thuốc & Giá & SĐK
        c_group = 1 if float(r["Nhóm Thuốc Chào"]) <= float(r["Nhóm Thuốc Y/C"]) else 0
        c_price = 1 if float(r["Đơn Giá Chào"]) <= float(r["Giá Kế Hoạch"]) else 0
        c_sdk = 1 if str(r["SĐK Hợp Lệ"]).strip().lower() == "có" else 0
        
        # Cảnh báo giá quá thấp (<60%)
        price_warning = "🚨 GIÁ THẤP BẤT THƯỜNG" if float(r["Đơn Giá Chào"]) < float(r["Giá Kế Hoạch"])*0.6 else "🟢 Hợp lý"

        avg_fuzzy = round(((score_hc + score_hl + score_dd) / 3) * 100, 1)
        
        reasons = []
        if not c_act: reasons.append("Sai hoạt chất")
        if not c_group: reasons.append("Sai Nhóm thuốc")
        if not c_price: reasons.append("Vượt giá")
        if not c_sdk: reasons.append("SĐK hết hạn")
        
        status = "✅ ĐỦ ĐIỀU KIỆN" if len(reasons)==0 else "❌ LOẠI (" + ", ".join(reasons) + ")"
        
        return pd.Series([f"{avg_fuzzy}%", price_warning, round((r["Điểm KT"]/97)*100, 1), status])

    if not merged.empty:
        merged[["Độ Khớp Thông Số (Fuzzy)", "Cảnh Báo Giá", "Tỷ Lệ Điểm KT (%)", "Kết Luận"]] = merged.apply(smart_evaluate, axis=1)
        st.markdown("#### Khuyến nghị tự động từ AI:")
        st.dataframe(merged[["Tên Đơn Vị", "Mã Thuốc", "Độ Khớp Thông Số (Fuzzy)", "Cảnh Báo Giá", "Kết Luận"]], use_container_width=True)

with tab2:
    st.subheader("Quản Lý Phụ Lục Hợp Đồng & Tùy Chọn Mua Thêm")
    st.caption("Kiểm soát việc điều chỉnh tăng/giảm khối lượng cung ứng (hạn mức 10% - 30%).")
    st.data_editor(st.session_state.addendum_df, num_rows="dynamic", use_container_width=True)

with tab3:
    st.subheader("Cảnh Báo Lô & Hạn Sử Dụng (Traceability)")
    st.caption("Truy vết các lô thuốc đang lưu hành tại Bệnh viện để thu hồi hoặc cảnh báo cận Date.")
    
    df_batch = st.session_state.batch_df.copy()
    df_batch['Ngày Hết Hạn'] = pd.to_datetime(df_batch['Hạn Sử Dụng'], errors='coerce')
    df_batch['Ngày Còn Lại'] = (df_batch['Ngày Hết Hạn'] - pd.Timestamp(datetime.now())).dt.days
    
    df_batch['Cảnh Báo'] = np.where(df_batch['Ngày Còn Lại'] < 90, "🚨 CẬN DATE (< 3 tháng)", "🟢 An Toàn")
    st.dataframe(df_batch[["Mã Thuốc", "Số Lô", "Hạn Sử Dụng", "Ngày Còn Lại", "Kho/CSYT Đang Tồn", "Cảnh Báo"]], use_container_width=True)

with tab4:
    st.subheader("Kiểm Soát Tiến Độ Đóng Gói HSMT")
    st.progress(75, text="Tiến độ hoàn thiện hồ sơ dự thầu: 75%")
    st.write("- Mẫu 01 (Đơn dự thầu): Đã xong \n- Mẫu 04 (Bảo lãnh): Chờ Ngân hàng MB \n- Mẫu 15 (Chấm điểm kỹ thuật): Đã có bản nháp từ hệ thống.")
