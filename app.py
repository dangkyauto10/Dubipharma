import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
from io import BytesIO

st.set_page_config(
    page_title="Hệ Thống Quản Lý Đấu Thầu & Phân Bổ Thuốc Tân Dược",
    page_icon="💊",
    layout="wide"
)

# ================= CẤU HÌNH GIAO DIỆN & STATE =================
st.title("💊 HỆ THỐNG QUẢN LÝ ĐẤU THẦU, ĐÓNG GÓI & PHÂN BỔ THUỐC TÂN DƯỢC")
st.caption("Chuyên dụng cho Dự án Thuốc Tây (DUBIPHARMA) | Tự động hóa Đánh giá % Đáp ứng E-HSMT - Đóng gói Hồ sơ - Theo dõi Tiến độ Phân bổ")

if "hsmt_df" not in st.session_state:
    st.session_state.hsmt_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "STT": 1, "Mã Phần (Lô)": "PP2600428380", "Mã Thuốc": "G1.001", "Tên Hoạt Chất": "Acarbose", "Nồng Độ, Hàm Lượng": "50mg", "Đường Dùng": "Uống", "Dạng Bào Chế": "Viên", "Đơn Vị Tính": "Viên", "Số Lượng Mời Thầu": 42000, "Đơn Giá Kế Hoạch": 1650, "Nhóm Thuốc Y/C": 2, "Tiền BĐDT": 1039500, "SL Mua Thêm 30%": 12600, "Y/C Doanh Thu BQ": 49376250, "Y/C HĐ Tương Tự": 48510000},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 2, "Mã Phần (Lô)": "PP2600428381", "Mã Thuốc": "G1.002", "Tên Hoạt Chất": "Aceclofenac", "Nồng Độ, Hàm Lượng": "100mg", "Đường Dùng": "Uống", "Dạng Bào Chế": "Viên", "Đơn Vị Tính": "Viên", "Số Lượng Mời Thầu": 121000, "Đơn Giá Kế Hoạch": 4450, "Nhóm Thuốc Y/C": 2, "Tiền BĐDT": 8076750, "SL Mua Thêm 30%": 36300, "Y/C Doanh Thu BQ": 383645625, "Y/C HĐ Tương Tự": 376915000},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 3, "Mã Phần (Lô)": "PP2600428382", "Mã Thuốc": "G1.003", "Tên Hoạt Chất": "Acenocoumarol", "Nồng Độ, Hàm Lượng": "1mg", "Đường Dùng": "Uống", "Dạng Bào Chế": "Viên", "Đơn Vị Tính": "Viên", "Số Lượng Mời Thầu": 267000, "Đơn Giá Kế Hoạch": 120, "Nhóm Thuốc Y/C": 4, "Tiền BĐDT": 480600, "SL Mua Thêm 30%": 80100, "Y/C Doanh Thu BQ": 22828500, "Y/C HĐ Tương Tự": 22428000},
        {"Mã Dự Án": "DA-TQ-2027", "STT": 6, "Mã Phần (Lô)": "PP2600428385", "Mã Thuốc": "G1.006", "Tên Hoạt Chất": "Acetyl leucin", "Nồng Độ, Hàm Lượng": "1g/10ml", "Đường Dùng": "Tiêm", "Dạng Bào Chế": "Thuốc tiêm", "Đơn Vị Tính": "Chai/Lọ/Ống/Túi/Gói", "Số Lượng Mời Thầu": 351390, "Đơn Giá Kế Hoạch": 24000, "Nhóm Thuốc Y/C": 4, "Tiền BĐDT": 126500400, "SL Mua Thêm 30%": 105417, "Y/C Doanh Thu BQ": 6008769000, "Y/C HĐ Tương Tự": 5903352000},
    ])

if "bids_df" not in st.session_state:
    st.session_state.bids_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.001", "Tên Đơn Vị": "DUBIPHARMA", "Tên Thuốc Chào": "Dubi-Acarbose 50", "Hoạt Chất Chào": "Acarbose", "Hàm Lượng Chào": "50mg", "Đường Dùng Chào": "Uống", "Nhóm Thuốc Chào": 2, "SĐK Hợp Lệ": "Có", "Đơn Giá Chào": 1550, "Ưu Đãi Nội Địa": "Có", "Điểm KT (Mẫu 15)": 90.0},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.001", "Tên Đơn Vị": "Nhà Thầu B", "Tên Thuốc Chào": "Acarbose Stada", "Hoạt Chất Chào": "Acarbose", "Hàm Lượng Chào": "50mg", "Đường Dùng Chào": "Uống", "Nhóm Thuốc Chào": 2, "SĐK Hợp Lệ": "Có", "Đơn Giá Chào": 1520, "Ưu Đãi Nội Địa": "Không", "Điểm KT (Mẫu 15)": 80.0},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.002", "Tên Đơn Vị": "DUBIPHARMA", "Tên Thuốc Chào": "Dubi-Aceclofenac", "Hoạt Chất Chào": "Aceclofenac", "Hàm Lượng Chào": "100mg", "Đường Dùng Chào": "Uống", "Nhóm Thuốc Chào": 3, "SĐK Hợp Lệ": "Có", "Đơn Giá Chào": 4200, "Ưu Đãi Nội Địa": "Có", "Điểm KT (Mẫu 15)": 88.0},
    ])

if "packaging_df" not in st.session_state:
    st.session_state.packaging_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "Mã Biểu Mẫu": "Mẫu số 01", "Tên Tài Liệu": "Đơn dự thầu (Hiệu lực >= 90 ngày)", "Hình Thức": "Webform", "Phụ Trách": "Phòng Thầu", "Trạng Thái": "Hoàn thành", "Tiến Độ (%)": 100},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Biểu Mẫu": "Mẫu số 04a/b", "Tên Tài Liệu": "Bảo lãnh dự thầu (Hiệu lực >= 120 ngày)", "Hình Thức": "Điện tử / Scan", "Phụ Trách": "Kế toán", "Trạng Thái": "Đang xử lý", "Tiến Độ (%)": 60},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Biểu Mẫu": "Mẫu số 05", "Tên Tài Liệu": "Bảng giá dự thầu & GĐKLH, GMP", "Hình Thức": "Webform", "Phụ Trách": "Phòng Thầu", "Trạng Thái": "Đang xử lý", "Tiến Độ (%)": 80},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Biểu Mẫu": "Mẫu số 06a/b", "Tên Tài Liệu": "Kê khai chi phí SX trong nước (Ưu đãi 7.5%)", "Hình Thức": "Scan đính kèm", "Phụ Trách": "Kế toán SX", "Trạng Thái": "Đang xử lý", "Tiến Độ (%)": 70},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Biểu Mẫu": "Mẫu số 08, 09", "Tên Tài Liệu": "Hợp đồng tương tự (>=70%) & BCTC 3 năm", "Hình Thức": "Webform & Scan", "Phụ Trách": "Kế toán & Thầu", "Trạng Thái": "Hoàn thành", "Tiến Độ (%)": 100},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Biểu Mẫu": "Mẫu số 15, 16", "Tên Tài Liệu": "Bảng tự chấm điểm KT & Cam kết giao hàng", "Hình Thức": "Scan đính kèm", "Phụ Trách": "Phòng Thầu", "Trạng Thái": "Hoàn thành", "Tiến Độ (%)": 100},
    ])

if "alloc_df" not in st.session_state:
    st.session_state.alloc_df = pd.DataFrame([
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.001", "Tên Thuốc": "Dubi-Acarbose 50", "Đơn Vị Trúng": "DUBIPHARMA", "Cơ Sở Y Tế Nhận Phân Bổ": "BV Đa khoa tỉnh Tuyên Quang", "Đơn Giá Trúng": 1550, "SL Phân Bổ Hợp Đồng": 25000, "SL Đã Giao": 21000, "Hạn Dùng Lô Giao": "15/08/2029"},
        {"Mã Dự Án": "DA-TQ-2027", "Mã Thuốc": "G1.001", "Tên Thuốc": "Dubi-Acarbose 50", "Đơn Vị Trúng": "DUBIPHARMA", "Cơ Sở Y Tế Nhận Phân Bổ": "TTYT TP Tuyên Quang", "Đơn Giá Trúng": 1550, "SL Phân Bổ Hợp Đồng": 17000, "SL Đã Giao": 10000, "Hạn Dùng Lô Giao": "15/08/2029"},
    ])

# ================= SIDEBAR: KẾT NỐI GOOGLE SHEETS API =================
with st.sidebar:
    st.header("🔗 Đồng Bộ Google Sheets")
    gas_url = st.text_input("Dán Web App URL (Apps Script):", placeholder="https://script.google.com/macros/s/.../exec")
    project_filter = st.text_input("Mã Dự Án Đang Làm Việc:", value="DA-TQ-2027")
    
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("📥 Tải từ Sheet", use_container_width=True):
            if gas_url:
                try:
                    res = requests.get(gas_url, params={"sheet": "ALL"}, timeout=15).json()
                    if res.get("status") == "success":
                        st.success("Đã tải dữ liệu thành công!")
                    else:
                        st.error(res.get("message", "Lỗi tải dữ liệu"))
                except Exception as ex:
                    st.error(f"Lỗi kết nối: {ex}")
            else:
                st.warning("Vui lòng dán Web App URL trước.")
    with col_s2:
        if st.button("📤 Đẩy lên Sheet", use_container_width=True):
            if gas_url:
                try:
                    payload = {
                        "action": "OVERWRITE_DATA",
                        "sheetName": "3_So_Sanh_Dap_Ung",
                        "rows": st.session_state.bids_df.values.tolist()
                    }
                    res = requests.post(gas_url, json=payload, timeout=15).json()
                    if res.get("status") == "success":
                        st.success("Đã đồng bộ lên Google Sheets!")
                    else:
                        st.error(res.get("message", "Lỗi ghi dữ liệu"))
                except Exception as ex:
                    st.error(f"Lỗi kết nối: {ex}")
            else:
                st.warning("Vui lòng dán Web App URL trước.")

# ================= 4 PHÂN HỆ NGHIỆP VỤ CHÍNH =================
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 1. Danh Mục HSMT & Bóc Tách",
    "⚖️ 2. So Sánh Thuốc & % Đáp Ứng",
    "📦 3. Quản Lý Đóng Gói & Năng Lực",
    "🚚 4. Theo Dõi Tiến Độ Phân Bổ"
])

# ----------------- TAB 1: DANH MỤC HSMT -----------------
with tab1:
    st.subheader("1. Danh Mục Yêu Cầu Từ Hồ Sơ Mời Thầu (Mẫu số 00, BĐDT, Mua thêm 30%, Bảng X)")
    st.info("Anh có thể chỉnh sửa trực tiếp trên bảng dưới đây hoặc tải file Excel danh mục thuốc lên.")
    
    uploaded_hsmt = st.file_uploader("Tải lên file Excel Danh mục HSMT chuẩn (nếu muốn nạp mới):", type=["xlsx", "csv"])
    if uploaded_hsmt:
        try:
            if uploaded_hsmt.name.endswith(".csv"):
                df_up = pd.read_csv(uploaded_hsmt)
            else:
                df_up = pd.read_excel(uploaded_hsmt)
            st.dataframe(df_up.head(20), use_container_width=True)
            st.caption("Xem trước 20 dòng đầu của file vừa tải lên.")
        except Exception as e:
            st.error(f"Không thể đọc file: {e}")

    edited_hsmt = st.data_editor(st.session_state.hsmt_df, num_rows="dynamic", use_container_width=True, key="ed_hsmt")
    st.session_state.hsmt_df = edited_hsmt

    # Tổng hợp nhanh chỉ số gói thầu
    c1, c2, c3, c4 = st.columns(4)
    total_plan_val = (edited_hsmt["Số Lượng Mời Thầu"] * edited_hsmt["Đơn Giá Kế Hoạch"]).sum()
    c1.metric("Số mặt hàng đang quản lý", f"{len(edited_hsmt):,}")
    c2.metric("Tổng Giá Kế Hoạch (VND)", f"{total_plan_val:,.0f}")
    c3.metric("Tổng Bảo Đảm Dự Thầu (1.5%)", f"{edited_hsmt['Tiền BĐDT'].sum():,.0f}")
    c4.metric("Tổng Doanh Thu BQ Yêu Cầu", f"{edited_hsmt['Y/C Doanh Thu BQ'].sum():,.0f}")

# ----------------- TAB 2: SO SÁNH & TÍNH % ĐÁP ỨNG -----------------
with tab2:
    st.subheader("2. Nhập Thông Tin Thuốc Các Đơn Vị & Tự Động Chấm % Đáp Ứng HSMT")
    st.markdown("""
    **Quy tắc tính % Đáp ứng tự động:**
    * **5 Tiêu chí Kỹ thuật Bắt buộc (Trọng số 50% - mỗi tiêu chí 10%):** Khớp Hoạt chất (10%) + Khớp Hàm lượng (10%) + Khớp Đường dùng (10%) + Đạt Nhóm thuốc $\le$ Nhóm HSMT yêu cầu (10%) + Có SĐK hợp lệ & Giá chào $\le$ Giá kế hoạch (10%).
    * **Điểm Kỹ thuật Chi tiết Mẫu 15 (Trọng số 50%):** $(\text{Điểm KT đạt được} / 97) \times 50\%$.
    * **Ưu đãi thuốc nội địa:** Nếu không thuộc đối tượng ưu đãi, Giá đánh giá = Giá chào $\times 107,5\%$.
    """)

    edited_bids = st.data_editor(st.session_state.bids_df, num_rows="dynamic", use_container_width=True, key="ed_bids")
    st.session_state.bids_df = edited_bids

    # Thực hiện đối chiếu tự động với HSMT
    merged = pd.merge(
        edited_bids,
        st.session_state.hsmt_df[["Mã Thuốc", "Tên Hoạt Chất", "Nồng Độ, Hàm Lượng", "Đường Dùng", "Nhóm Thuốc Y/C", "Đơn Giá Kế Hoạch", "Số Lượng Mời Thầu"]],
        on="Mã Thuốc",
        how="left"
    )

    def evaluate_row(r):
        if pd.isna(r["Tên Hoạt Chất"]):
            return pd.Series([0.0, 0.0, 0.0, "Không tìm thấy Mã Thuốc trong HSMT", r["Đơn Giá Chào"]])
        
        c_act = 1 if str(r["Hoạt Chất Chào"]).strip().lower() == str(r["Tên Hoạt Chất"]).strip().lower() else 0
        c_conc = 1 if str(r["Hàm Lượng Chào"]).strip().lower() == str(r["Nồng Độ, Hàm Lượng"]).strip().lower() else 0
        c_route = 1 if str(r["Đường Dùng Chào"]).strip().lower() == str(r["Đường Dùng"]).strip().lower() else 0
        c_group = 1 if float(r["Nhóm Thuốc Chào"]) <= float(r["Nhóm Thuốc Y/C"]) else 0
        c_price_sdk = 1 if (str(r["SĐK Hợp Lệ"]).strip().lower() == "có" and float(r["Đơn Giá Chào"]) <= float(r["Đơn Giá Kế Hoạch"])) else 0

        hard_pct = ((c_act + c_conc + c_route + c_group + c_price_sdk) / 5.0) * 50.0
        soft_pct = (float(r["Điểm KT (Mẫu 15)"]) / 97.0) * 50.0
        total_pct = round(hard_pct + soft_pct, 2)

        reasons = []
        if not c_act: reasons.append("Sai hoạt chất")
        if not c_conc: reasons.append("Sai hàm lượng")
        if not c_route: reasons.append("Sai đường dùng")
        if not c_group: reasons.append(f"Không đạt Nhóm (Chào N{r['Nhóm Thuốc Chào']} > Y/C N{r['Nhóm Thuốc Y/C']})")
        if not c_price_sdk: reasons.append("Vượt giá KH hoặc SĐK KHL")
        if float(r["Điểm KT (Mẫu 15)"]) < 70: reasons.append("Điểm KT < 70")

        status = "✅ ĐẠT - ĐỦ ĐK XÉT GIÁ" if len(reasons) == 0 else "❌ LOẠI (" + ", ".join(reasons) + ")"
        eval_price = float(r["Đơn Giá Chào"]) if str(r["Ưu Đãi Nội Địa"]).strip().lower() == "có" else float(r["Đơn Giá Chào"]) * 1.075

        return pd.Series([hard_pct, round(soft_pct, 2), total_pct, status, round(eval_price, 2)])

    if not merged.empty:
        merged[["% Tiêu Chí Cứng (50%)", "% Điểm KT (50%)", "TỔNG % ĐÁP ỨNG HSMT", "Kết Luận Đấu Thầu", "Giá Đánh Giá (Sau Ưu Đãi)"]] = merged.apply(evaluate_row, axis=1)
        
        # Xếp hạng theo từng Mã Thuốc cho các đơn vị ĐẠT
        merged["Xếp Hạng"] = "-"
        valid_mask = merged["Kết Luận Đấu Thầu"] == "✅ ĐẠT - ĐỦ ĐK XÉT GIÁ"
        if valid_mask.any():
            merged.loc[valid_mask, "Xếp Hạng"] = merged[valid_mask].groupby("Mã Thuốc")["Giá Đánh Giá (Sau Ưu Đãi)"].rank(method="min").astype(int).astype(str)

        st.markdown("#### 📊 Bảng Kết Quả So Sánh, Tỷ Lệ % Đáp Ứng & Xếp Hạng Các Đơn Vị")
        display_cols = [
            "Mã Thuốc", "Tên Đơn Vị", "Tên Thuốc Chào", "Nhóm Thuốc Chào", "Nhóm Thuốc Y/C",
            "Đơn Giá Chào", "Đơn Giá Kế Hoạch", "Giá Đánh Giá (Sau Ưu Đãi)",
            "% Tiêu Chí Cứng (50%)", "% Điểm KT (50%)", "TỔNG % ĐÁP ỨNG HSMT", "Kết Luận Đấu Thầu", "Xếp Hạng"
        ]
        st.dataframe(merged[display_cols], use_container_width=True)

# ----------------- TAB 3: QUẢN LÝ ĐÓNG GÓI & NĂNG LỰC -----------------
with tab3:
    st.subheader("3. Kiểm Soát Đóng Gói Hồ Sơ Dự Thầu (Checklist Chương IV) & Năng Lực Tài Chính")
    col_p1, col_p2 = st.columns([2, 1])
    
    with col_p1:
        st.markdown("##### 📦 Checklist Tiến Độ Đóng Gói Tài Liệu E-HSDT")
        edited_pack = st.data_editor(st.session_state.packaging_df, num_rows="dynamic", use_container_width=True, key="ed_pack")
        st.session_state.packaging_df = edited_pack
        avg_pack = edited_pack["Tiến Độ (%)"].mean() if not edited_pack.empty else 0
        st.progress(int(avg_pack), text=f"Tiến độ đóng gói hồ sơ toàn dự án: {avg_pack:.1f}%")

    with col_p2:
        st.markdown("##### 💰 Kiểm Tra Đáp Ứng Năng Lực Nhà Thầu (Bảng X)")
        selected_vendor = st.text_input("Nhập Tên Đơn Vị cần kiểm tra năng lực:", value="DUBIPHARMA")
        vendor_rev = st.number_input("Doanh thu bình quân 3 năm gần nhất của Đơn vị (VND):", value=50000000000, step=1000000000)
        vendor_contract = st.number_input("Giá trị Hợp đồng tương tự lớn nhất đã thực hiện (VND):", value=10000000000, step=500000000)
        
        vendor_codes = st.session_state.bids_df[st.session_state.bids_df["Tên Đơn Vị"] == selected_vendor]["Mã Thuốc"].unique()
        sub_hsmt = st.session_state.hsmt_df[st.session_state.hsmt_df["Mã Thuốc"].isin(vendor_codes)]
        
        req_rev_sum = sub_hsmt["Y/C Doanh Thu BQ"].sum() if not sub_hsmt.empty else 0
        req_cont_max = sub_hsmt["Y/C HĐ Tương Tự"].max() if not sub_hsmt.empty else 0
        req_bddt_sum = sub_hsmt["Tiền BĐDT"].sum() if not sub_hsmt.empty else 0

        st.write(f"- Số phần (mặt hàng) **{selected_vendor}** tham dự: **{len(sub_hsmt)} phần**")
        st.write(f"- Tổng Bảo đảm dự thầu cần làm: **{req_bddt_sum:,.0f} VND** " + ("*(< 50tr: Chỉ cần cam kết trong Đơn dự thầu)*" if req_bddt_sum < 50000000 else "*(>= 50tr: Phải có Thư bảo lãnh Ngân hàng/Bảo hiểm)*"))
        st.write(f"- Tổng Doanh thu BQ yêu cầu: **{req_rev_sum:,.0f} VND** $\rightarrow$ " + ("✅ **ĐẠT**" if vendor_rev >= req_rev_sum else "❌ **THIẾU DOANH THU**"))
        st.write(f"- Quy mô HĐ tương tự lớn nhất yêu cầu: **{req_cont_max:,.0f} VND** $\rightarrow$ " + ("✅ **ĐẠT**" if vendor_contract >= req_cont_max else "❌ **THIẾU HĐ TƯƠNG TỰ**"))

# ----------------- TAB 4: THEO DÕI TIẾN ĐỘ PHÂN BỔ XUYÊN SUỐT DỰ ÁN -----------------
with tab4:
    st.subheader("4. Theo Dõi Tiến Độ Phân Bổ & Thực Hiện Hợp Đồng Tại Các Cơ Sở Y Tế")
    st.caption("Kiểm soát chặt chẽ khối lượng phân bổ theo Thỏa thuận khung, tiến độ giao hàng thực tế và hạn mức tùy chọn mua thêm 30%.")
    
    edited_alloc = st.data_editor(st.session_state.alloc_df, num_rows="dynamic", use_container_width=True, key="ed_alloc")
    st.session_state.alloc_df = edited_alloc

    if not edited_alloc.empty:
        alloc_calc = edited_alloc.copy()
        alloc_calc["SL Mua Thêm Tối Đa (30%)"] = (alloc_calc["SL Phân Bổ Hợp Đồng"] * 0.30).astype(int)
        alloc_calc["Tổng Trần Cung Ứng (130%)"] = alloc_calc["SL Phân Bổ Hợp Đồng"] + alloc_calc["SL Mua Thêm Tối Đa (30%)"]
        alloc_calc["SL Còn Lại (HĐ Chính)"] = alloc_calc["SL Phân Bổ Hợp Đồng"] - alloc_calc["SL Đã Giao"]
        alloc_calc["% Thực Hiện HĐ Chính"] = ((alloc_calc["SL Đã Giao"] / alloc_calc["SL Phân Bổ Hợp Đồng"]) * 100).round(1)
        alloc_calc["Giá Trị Đã Giao (VND)"] = alloc_calc["SL Đã Giao"] * alloc_calc["Đơn Giá Trúng"]
        alloc_calc["Cảnh Báo Điều Phối"] = np.where(
            alloc_calc["% Thực Hiện HĐ Chính"] >= 100, "🚨 Đã giao hết HĐ chính - Kích hoạt phụ lục mua thêm 30%",
            np.where(alloc_calc["% Thực Hiện HĐ Chính"] >= 80, "⚠️ Đạt >=80% tiến độ - Chuẩn bị hồ sơ mua thêm 30%", "🟢 Đang cung ứng trong hạn mức")
        )

        st.markdown("#### 📈 Bảng Tổng Hợp Trạng Thái Phân Bổ & Cảnh Báo Tùy Chọn Mua Thêm 30%")
        st.dataframe(alloc_calc, use_container_width=True)
