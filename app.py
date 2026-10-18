import streamlit as st
import pandas as pd
import numpy as np
import requests
from difflib import SequenceMatcher
from datetime import datetime

st.set_page_config(
    page_title="DUBIPHARMA DŨNG BÍCH - Quản Lý Đấu Thầu & Phân Bổ Thuốc",
    page_icon="💊",
    layout="wide"
)

st.title("💊 DUBIPHARMA DŨNG BÍCH - HỆ THỐNG ĐẤU THẦU & PHÂN BỔ THUỐC TÂN DƯỢC")
st.caption("Tự động hóa Đối chiếu % Đáp ứng E-HSMT (Fuzzy Logic) | Cảnh báo Giá & Năng lực Bảng X | Đóng gói Hồ sơ | Theo dõi Phân bổ & Lô/Hạn dùng")

def fuzzy_score(s1, s2):
    if pd.isna(s1) or pd.isna(s2):
        return 0.0
    a = str(s1).strip().lower()
    b = str(s2).strip().lower()
    if a == b or (a in b) or (b in a):
        return 1.0
    return SequenceMatcher(None, a, b).ratio()

# ================= KHỞI TẠO DỮ LIỆU MẶC ĐỊNH TRONG SESSION =================
if "hsmt_df" not in st.session_state:
    st.session_state.hsmt_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "STT": 1, "Mã Phần (Lô)": "PP2600428380", "Mã Thuốc": "G1.001", "Tên Hoạt Chất": "Acarbose", "Nồng Độ, Hàm Lượng": "50mg", "Đường Dùng": "Uống", "Dạng Bào Chế": "Viên", "Đơn Vị Tính": "Viên", "Số Lượng Mời Thầu": 42000, "Đơn Giá Kế Hoạch": 1650, "Nhóm Thuốc Y/C": 2, "Tiền BĐDT": 1039500, "SL Mua Thêm 30%": 12600, "Y/C Doanh Thu BQ": 49376250, "Y/C HĐ Tương Tự": 48510000},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 2, "Mã Phần (Lô)": "PP2600428381", "Mã Thuốc": "G1.002", "Tên Hoạt Chất": "Aceclofenac", "Nồng Độ, Hàm Lượng": "100mg", "Đường Dùng": "Uống", "Dạng Bào Chế": "Viên", "Đơn Vị Tính": "Viên", "Số Lượng Mời Thầu": 121000, "Đơn Giá Kế Hoạch": 4450, "Nhóm Thuốc Y/C": 2, "Tiền BĐDT": 8076750, "SL Mua Thêm 30%": 36300, "Y/C Doanh Thu BQ": 383645625, "Y/C HĐ Tương Tự": 376915000},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 6, "Mã Phần (Lô)": "PP2600428385", "Mã Thuốc": "G1.006", "Tên Hoạt Chất": "Acetyl leucin", "Nồng Độ, Hàm Lượng": "1g/10ml", "Đường Dùng": "Tiêm", "Dạng Bào Chế": "Thuốc tiêm", "Đơn Vị Tính": "Chai/Lọ/Ống/Túi/Gói", "Số Lượng Mời Thầu": 351390, "Đơn Giá Kế Hoạch": 24000, "Nhóm Thuốc Y/C": 4, "Tiền BĐDT": 126500400, "SL Mua Thêm 30%": 105417, "Y/C Doanh Thu BQ": 6008769000, "Y/C HĐ Tương Tự": 5903352000},
    ])

if "bids_df" not in st.session_state:
    st.session_state.bids_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.001", "Tên Đơn Vị": "DUBIPHARMA", "Tên Thuốc Chào": "Dubi-Acarbose 50", "Hoạt Chất Chào": "Acarbose", "Hàm Lượng Chào": "50mg", "Đường Dùng Chào": "Uống", "Nhóm Thuốc Chào": 2, "SĐK Hợp Lệ": "Có", "Số Lượng Chào": 42000, "Đơn Giá Chào": 1550, "Ưu Đãi Nội Địa": "Có", "Điểm KT (Mẫu 15)": 90.0},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.001", "Tên Đơn Vị": "Nhà Thầu B", "Tên Thuốc Chào": "Acarbose Stada", "Hoạt Chất Chào": "Acarbose", "Hàm Lượng Chào": "50mg", "Đường Dùng Chào": "Uống", "Nhóm Thuốc Chào": 2, "SĐK Hợp Lệ": "Có", "Số Lượng Chào": 42000, "Đơn Giá Chào": 1520, "Ưu Đãi Nội Địa": "Không", "Điểm KT (Mẫu 15)": 80.0},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.002", "Tên Đơn Vị": "DUBIPHARMA", "Tên Thuốc Chào": "Dubi-Aceclofenac 100", "Hoạt Chất Chào": "Aceclofenac", "Hàm Lượng Chào": "100mg", "Đường Dùng Chào": "Uống", "Nhóm Thuốc Chào": 3, "SĐK Hợp Lệ": "Có", "Số Lượng Chào": 121000, "Đơn Giá Chào": 4200, "Ưu Đãi Nội Địa": "Có", "Điểm KT (Mẫu 15)": 88.0},
    ])

if "packaging_df" not in st.session_state:
    st.session_state.packaging_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "STT": 1, "Mã Biểu Mẫu": "Mẫu số 01", "Tên Tài Liệu": "Đơn dự thầu (Hiệu lực >= 90 ngày)", "Hình Thức": "Webform", "Bắt Buộc": "Bắt buộc", "Phụ Trách": "Phòng Thầu", "Hạn Hoàn Thành": "25/10/2026", "Trạng Thái": "Hoàn thành", "Tiến Độ (%)": 100},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 2, "Mã Biểu Mẫu": "Mẫu số 04a/b", "Tên Tài Liệu": "Bảo lãnh dự thầu (Hiệu lực >= 120 ngày)", "Hình Thức": "Điện tử / Scan", "Bắt Buộc": "Bắt buộc", "Phụ Trách": "Kế toán", "Hạn Hoàn Thành": "26/10/2026", "Trạng Thái": "Đang xử lý", "Tiến Độ (%)": 50},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 3, "Mã Biểu Mẫu": "Mẫu số 05", "Tên Tài Liệu": "Bảng giá dự thầu & GĐKLH, GMP", "Hình Thức": "Webform", "Bắt Buộc": "Bắt buộc", "Phụ Trách": "Phòng Thầu", "Hạn Hoàn Thành": "26/10/2026", "Trạng Thái": "Đang xử lý", "Tiến Độ (%)": 80},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 4, "Mã Biểu Mẫu": "Mẫu số 06a/b", "Tên Tài Liệu": "Kê khai chi phí SX trong nước (Ưu đãi 7.5%)", "Hình Thức": "Scan đính kèm", "Bắt Buộc": "Nếu có ưu đãi", "Phụ Trách": "Kế toán SX", "Hạn Hoàn Thành": "26/10/2026", "Trạng Thái": "Đang xử lý", "Tiến Độ (%)": 60},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 5, "Mã Biểu Mẫu": "Mẫu số 08, 09", "Tên Tài Liệu": "Hợp đồng tương tự (>=70%) & BCTC 3 năm", "Hình Thức": "Webform & Scan", "Bắt Buộc": "Bắt buộc", "Phụ Trách": "Kế toán", "Hạn Hoàn Thành": "25/10/2026", "Trạng Thái": "Hoàn thành", "Tiến Độ (%)": 100},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 6, "Mã Biểu Mẫu": "Mẫu số 15, 16", "Tên Tài Liệu": "Bảng tự chấm điểm KT & Cam kết giao hàng", "Hình Thức": "Scan đính kèm", "Bắt Buộc": "Bắt buộc", "Phụ Trách": "Phòng Thầu", "Hạn Hoàn Thành": "25/10/2026", "Trạng Thái": "Hoàn thành", "Tiến Độ (%)": 100},
    ])

if "alloc_df" not in st.session_state:
    st.session_state.alloc_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "Mã Phần (Lô)": "PP2600428380", "Mã Thuốc": "G1.001", "Tên Thuốc": "Dubi-Acarbose 50", "Đơn Vị Trúng": "DUBIPHARMA", "Cơ Sở Y Tế Nhận Phân Bổ": "BV Đa khoa tỉnh Tuyên Quang", "Đơn Giá Trúng": 1550, "SL Phân Bổ HĐ Chính": 25000, "SL Đã Giao": 21000},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Phần (Lô)": "PP2600428380", "Mã Thuốc": "G1.001", "Tên Thuốc": "Dubi-Acarbose 50", "Đơn Vị Trúng": "DUBIPHARMA", "Cơ Sở Y Tế Nhận Phân Bổ": "TTYT TP Tuyên Quang", "Đơn Giá Trúng": 1550, "SL Phân Bổ HĐ Chính": 17000, "SL Đã Giao": 10000},
    ])

if "batch_df" not in st.session_state:
    st.session_state.batch_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.001", "Số Lô": "DB-2610-01", "Ngày SX": "2026-10-10", "Hạn Sử Dụng": "2029-10-10", "Kho/CSYT Đang Tồn": "Kho Bệnh Viện Tỉnh"},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.002", "Số Lô": "DB-2501-09", "Ngày SX": "2025-01-15", "Hạn Sử Dụng": "2026-12-20", "Kho/CSYT Đang Tồn": "TTYT Sơn Dương"},
    ])

if "addendum_df" not in st.session_state:
    st.session_state.addendum_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "Số Phụ Lục": "PL-01/2027", "Ngày Ký": "2027-11-15", "Mã Thuốc": "G1.001", "Loại Điều Chỉnh": "Tăng 30% tùy chọn mua thêm", "Khối Lượng Bổ Sung": 7500, "Lý Do": "BV Đa khoa tỉnh vượt kế hoạch", "Trạng Thái": "Đã Ký"}
    ])

# ================= SIDEBAR ĐỒNG BỘ 2 CHIỀU VỚI GOOGLE SHEETS =================
with st.sidebar:
    st.header("🔗 Đồng Bộ Google Sheets")
    gas_url = st.text_input("Dán Web App URL (Apps Script):", placeholder="https://script.google.com/macros/s/.../exec")
    c_s1, c_s2 = st.columns(2)
    with c_s1:
        if st.button("📥 Tải từ Sheet", use_container_width=True):
            if gas_url:
                try:
                    res = requests.get(gas_url, params={"sheet": "ALL"}, timeout=15).json()
                    if res.get("status") == "success":
                        st.success("Đã tải dữ liệu từ Google Sheets!")
                    else:
                        st.error(res.get("message", "Lỗi tải dữ liệu"))
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")
            else:
                st.warning("Vui lòng nhập Web App URL.")
    with c_s2:
        if st.button("📤 Đẩy lên Sheet", use_container_width=True):
            if gas_url:
                try:
                    payload = {
                        "action": "OVERWRITE_DATA",
                        "sheetName": "6_Theo_Doi_Phan_Bo",
                        "rows": st.session_state.alloc_df.values.tolist()
                    }
                    res = requests.post(gas_url, json=payload, timeout=15).json()
                    if res.get("status") == "success":
                        st.success("Đã cập nhật lên Google Sheets!")
                    else:
                        st.error(res.get("message", "Lỗi đẩy dữ liệu"))
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")
            else:
                st.warning("Vui lòng nhập Web App URL.")

# ================= 5 TAB NGHIỆP VỤ XUYÊN SUỐT =================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 1. Danh Mục HSMT",
    "⚖️ 2. So Sánh & % Đáp Ứng Thông Minh",
    "📦 3. Đóng Gói & Năng Lực Bảng X",
    "🚚 4. Tiến Độ Phân Bổ & Phụ Lục 30%",
    "⏳ 5. Quản Lý Lô & Cảnh Báo Hạn Dùng"
])

with tab1:
    st.subheader("Danh Mục Yêu Cầu Từ Hồ Sơ Mời Thầu (Mẫu 00, BĐDT, Mua thêm 30%, Bảng X)")
    ed_hsmt = st.data_editor(st.session_state.hsmt_df, num_rows="dynamic", use_container_width=True, key="t1_hsmt")
    st.session_state.hsmt_df = ed_hsmt

with tab2:
    st.subheader("Đối Chiếu Thuốc Dự Thầu (Fuzzy Matching), Cảnh Báo Giá (<60%) & Tự Động Xếp Hạng")
    ed_bids = st.data_editor(st.session_state.bids_df, num_rows="dynamic", use_container_width=True, key="t2_bids")
    st.session_state.bids_df = ed_bids

    merged = pd.merge(
        ed_bids,
        st.session_state.hsmt_df[["Mã Thuốc", "Tên Hoạt Chất", "Nồng Độ, Hàm Lượng", "Đường Dùng", "Nhóm Thuốc Y/C", "Đơn Giá Kế Hoạch"]],
        on="Mã Thuốc",
        how="left"
    )

    def eval_bid(r):
        if pd.isna(r["Tên Hoạt Chất"]):
            return pd.Series([0.0, 0.0, 0.0, "Không tìm thấy Mã Thuốc", "-", r["Đơn Giá Chào"]])
        s_hc = fuzzy_score(r["Hoạt Chất Chào"], r["Tên Hoạt Chất"])
        s_hl = fuzzy_score(r["Hàm Lượng Chào"], r["Nồng Độ, Hàm Lượng"])
        s_dd = fuzzy_score(r["Đường Dùng Chào"], r["Đường Dùng"])

        c_hc = 1 if s_hc >= 0.75 else 0
        c_hl = 1 if s_hl >= 0.75 else 0
        c_dd = 1 if s_dd >= 0.75 else 0
        c_nhom = 1 if float(r["Nhóm Thuốc Chào"]) <= float(r["Nhóm Thuốc Y/C"]) else 0
        c_gia_sdk = 1 if (str(r["SĐK Hợp Lệ"]).strip().lower() == "có" and float(r["Đơn Giá Chào"]) <= float(r["Đơn Giá Kế Hoạch"])) else 0

        hard_pct = ((c_hc + c_hl + c_dd + c_nhom + c_gia_sdk) / 5.0) * 50.0
        soft_pct = (float(r["Điểm KT (Mẫu 15)"]) / 97.0) * 50.0
        total_pct = round(hard_pct + soft_pct, 2)

        price_warn = "🚨 GIÁ THẤP BẤT THƯỜNG (<60%)" if float(r["Đơn Giá Chào"]) < float(r["Đơn Giá Kế Hoạch"]) * 0.6 else "🟢 Hợp lý"
        eval_price = float(r["Đơn Giá Chào"]) if str(r["Ưu Đãi Nội Địa"]).strip().lower() == "có" else float(r["Đơn Giá Chào"]) * 1.075

        reasons = []
        if not c_hc: reasons.append("Lệch hoạt chất")
        if not c_hl: reasons.append("Lệch hàm lượng")
        if not c_dd: reasons.append("Lệch đường dùng")
        if not c_nhom: reasons.append(f"Sai Nhóm (Chào N{r['Nhóm Thuốc Chào']} > Y/C N{r['Nhóm Thuốc Y/C']})")
        if not c_gia_sdk: reasons.append("Vượt giá KH / SĐK KHL")
        if float(r["Điểm KT (Mẫu 15)"]) < 70: reasons.append("Điểm KT < 70")

        ket_luan = "✅ ĐẠT - ĐỦ ĐK XÉT GIÁ" if len(reasons) == 0 else "❌ LOẠI (" + ", ".join(reasons) + ")"
        return pd.Series([hard_pct, round(soft_pct, 2), total_pct, ket_luan, price_warn, round(eval_price, 2)])

    if not merged.empty:
        merged[["% Tiêu Chí Cứng (50%)", "% Điểm KT (50%)", "TỔNG % ĐÁP ỨNG HSMT", "Kết Luận Đấu Thầu", "Cảnh Báo Giá", "Giá Đánh Giá (Sau Ưu Đãi)"]] = merged.apply(eval_bid, axis=1)
        merged["Xếp Hạng"] = "-"
        mask_ok = merged["Kết Luận Đấu Thầu"] == "✅ ĐẠT - ĐỦ ĐK XÉT GIÁ"
        if mask_ok.any():
            merged.loc[mask_ok, "Xếp Hạng"] = merged[mask_ok].groupby("Mã Thuốc")["Giá Đánh Giá (Sau Ưu Đãi)"].rank(method="min").astype(int).astype(str)

        st.dataframe(merged[[
            "Mã Thuốc", "Tên Đơn Vị", "Tên Thuốc Chào", "Nhóm Thuốc Chào", "Nhóm Thuốc Y/C",
            "Đơn Giá Chào", "Đơn Giá Kế Hoạch", "Giá Đánh Giá (Sau Ưu Đãi)", "Cảnh Báo Giá",
            "TỔNG % ĐÁP ỨNG HSMT", "Kết Luận Đấu Thầu", "Xếp Hạng"
        ]], use_container_width=True)

with tab3:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Checklist Đóng Gói Hồ Sơ E-HSDT")
        ed_pack = st.data_editor(st.session_state.packaging_df, num_rows="dynamic", use_container_width=True, key="t3_pack")
        st.session_state.packaging_df = ed_pack
        avg_p = ed_pack["Tiến Độ (%)"].mean() if not ed_pack.empty else 0
        st.progress(int(avg_p), text=f"Tiến độ đóng gói toàn dự án: {avg_p:.1f}%")
    with col2:
        st.subheader("Kiểm Tra Năng Lực Bảng X")
        v_name = st.text_input("Đơn vị kiểm tra:", value="DUBIPHARMA")
        v_rev = st.number_input("Doanh thu BQ 3 năm (VND):", value=50000000000, step=1000000000)
        v_con = st.number_input("Hợp đồng tương tự lớn nhất (VND):", value=10000000000, step=500000000)
        v_codes = st.session_state.bids_df[st.session_state.bids_df["Tên Đơn Vị"] == v_name]["Mã Thuốc"].unique()
        sub = st.session_state.hsmt_df[st.session_state.hsmt_df["Mã Thuốc"].isin(v_codes)]
        req_rev = sub["Y/C Doanh Thu BQ"].sum() if not sub.empty else 0
        req_con = sub["Y/C HĐ Tương Tự"].max() if not sub.empty else 0
        req_bddt = sub["Tiền BĐDT"].sum() if not sub.empty else 0
        st.write(f"- Tổng BĐDT: **{req_bddt:,.0f} VND**")
        st.write(f"- Tổng Doanh thu BQ yêu cầu: **{req_rev:,.0f} VND** -> " + ("✅ ĐẠT" if v_rev >= req_rev else "❌ THIẾU"))
        st.write(f"- HĐ tương tự lớn nhất yêu cầu: **{req_con:,.0f} VND** -> " + ("✅ ĐẠT" if v_con >= req_con else "❌ THIẾU"))

with tab4:
    st.subheader("Theo Dõi Tiến Độ Phân Bổ Hợp Đồng & Phụ Lục Mua Thêm 30%")
    ed_alloc = st.data_editor(st.session_state.alloc_df, num_rows="dynamic", use_container_width=True, key="t4_alloc")
    st.session_state.alloc_df = ed_alloc
    if not ed_alloc.empty:
        ac = ed_alloc.copy()
        ac["SL Mua Thêm 30%"] = (ac["SL Phân Bổ HĐ Chính"] * 0.30).astype(int)
        ac["Tổng Trần Cung Ứng (130%)"] = ac["SL Phân Bổ HĐ Chính"] + ac["SL Mua Thêm 30%"]
        ac["SL Còn Lại (HĐ Chính)"] = ac["SL Phân Bổ HĐ Chính"] - ac["SL Đã Giao"]
        ac["% Thực Hiện"] = ((ac["SL Đã Giao"] / ac["SL Phân Bổ HĐ Chính"]) * 100).round(1)
        ac["Cảnh Báo"] = np.where(ac["% Thực Hiện"] >= 80, "⚠️ Đạt >=80% - Chuẩn bị Phụ lục mua thêm 30%", "🟢 Bình thường")
        st.dataframe(ac, use_container_width=True)

    st.markdown("#### 📜 Danh Sách Phụ Lục Hợp Đồng Đã Ký")
    ed_add = st.data_editor(st.session_state.addendum_df, num_rows="dynamic", use_container_width=True, key="t4_add")
    st.session_state.addendum_df = ed_add

with tab5:
    st.subheader("Quản Lý Lô Sản Xuất, Hạn Dùng & Truy Vết Thuốc Lưu Hành")
    ed_batch = st.data_editor(st.session_state.batch_df, num_rows="dynamic", use_container_width=True, key="t5_batch")
    st.session_state.batch_df = ed_batch
    if not ed_batch.empty:
        bc = ed_batch.copy()
        bc["Hạn Dùng (Date)"] = pd.to_datetime(bc["Hạn Sử Dụng"], errors="coerce")
        bc["Số Ngày Còn Lại"] = (bc["Hạn Dùng (Date)"] - pd.Timestamp(datetime.now())).dt.days
        bc["Cảnh Báo Hạn Dùng"] = np.where(bc["Số Ngày Còn Lại"] < 90, "🚨 CẬN DATE (<3 THÁNG)", "🟢 An Toàn")
        st.dataframe(bc[["Mã Dự Án", "Mã Thuốc", "Số Lô", "Ngày SX", "Hạn Sử Dụng", "Số Ngày Còn Lại", "Cảnh Báo Hạn Dùng", "Kho/CSYT Đang Tồn"]], use_container_width=True)
