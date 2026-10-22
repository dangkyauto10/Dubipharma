# TDV QC7 ONLINE — Hoàn thiện đăng nhập Google OIDC

**Ngày 22/10/2026.** Cấu hình cho **chính ứng dụng** đang triển khai tại:

https://dangkyauto10-dubipharma-app-tdv-qc7-online-preview-20261-k4zpor.streamlit.app/

## Phạm vi an toàn đã mã hóa

- Chặn toàn bộ trang nghiệp vụ trước khi Google OIDC xác thực; **mặc định KHÓA** nếu thiếu/mất cấu hình.
- Chỉ email đã được Google xác minh, token có issuer/audience đúng và còn hiệu lực, trong **danh sách email được duyệt** mới được xem tài liệu.
- Phân vai: `admin` quản trị giao diện, `analyst` xử lý hồ sơ, `viewer` chỉ xem trang tổng quan/so sánh/báo cáo/tình trạng. Quyền phê duyệt pháp lý và ghi Google Drive vẫn chưa tích hợp.
- Đăng xuất Google khỏi ứng dụng, chống tái sử dụng dữ liệu `st.session_state` qua danh tính khác.
- Không lưu mật khẩu Google, OAuth Client Secret hoặc Cookie Secret trong GitHub; không viết tài liệu NSX lên repo.
- Đây **không phải** kiểm soát quyền từng dự án và không bảo đảm Streamlit Community Cloud phù hợp lưu hồ sơ mật/giá nội bộ lâu dài.

## Hai phần V phải cấu hình trong các tài khoản hiện có

### A. Google Cloud Console — lập OAuth Client ID cho chính app này

1. Đăng nhập tài khoản Google Cloud V đang quản lý, mở https://console.cloud.google.com/auth/clients và chọn **dự án Cloud đã được V phê duyệt**. Không cần lập tài khoản Google thứ hai, repo thứ hai hoặc app Streamlit thứ hai.
2. Cấu hình **Google Auth Platform → Branding/Audience**. Nếu còn **Testing**, thêm 2–3 tài khoản vào **Test users**.
3. **Clients → Create client → Web application**. Tên nội bộ ví dụ `TDV-QC7-LOGIN`.
4. Trong **Authorized redirect URIs**, nhập nguyên văn URL:
   `https://dangkyauto10-dubipharma-app-tdv-qc7-online-preview-20261-k4zpor.streamlit.app/oauth2callback`
5. Sao lưu an toàn **Client ID** và **Client secret** vào trình quản lý mật khẩu. **Không gửi cho B qua chat và không đưa lên GitHub.**

### B. Streamlit Community Cloud → Settings → Secrets

1. Mở **https://share.streamlit.io/** với tài khoản quản trị bản Preview hiện có.
2. Chọn đúng ứng dụng TDV QC7 hiện tại → menu `...` → **Settings → Secrets**.
3. Điền mẫu TOML sau, thay giá trị trong dấu nháy bằng khóa thực. Tự tạo `cookie_secret` bằng bộ sinh ngẫu nhiên bảo mật tối thiểu 32 byte (ví dụ 64 ký tự hex) và giữ riêng tư:

```toml
[auth]
redirect_uri = "https://dangkyauto10-dubipharma-app-tdv-qc7-online-preview-20261-k4zpor.streamlit.app/oauth2callback"
cookie_secret = "GAN_CHUOI_NGAU_NHIEN_DAI_TOI_THIEU_32_BYTES"
client_id = "CLIENT_ID_GOOGLE_CUA_V"
client_secret = "CLIENT_SECRET_GOOGLE_CUA_V"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

[tdv_access.roles]
"nguoiquantri@example.com" = "admin"
"nhanvien1@example.com" = "analyst"
"nhanvien2@example.com" = "viewer"
```

4. Thay các email ví dụ bằng **đúng 2–3 địa chỉ Google thực tế**, viết chữ thường; phải có ít nhất một tài khoản `admin`.
5. Lưu Secrets. Kiểm tra Google redirect URI và `redirect_uri` trong TOML khớp **100%**. Không thay đổi domain hoặc /oauth2callback.
6. Dùng cửa sổ ẩn danh và thử: chưa đăng nhập → chỉ thấy màn hình đăng nhập; email không trong danh sách → bị chặn; tài khoản được duyệt → đúng menu; đăng xuất → chặn trở lại.
7. Đề nghị trong phần **Sharing** của Streamlit Cloud đặt ứng dụng ở chế độ **Private** nếu tài khoản hỗ trợ và xác định rõ ai được phép truy cập. Nhưng **Private không thay thế OIDC**, và OIDC không thay thế quyền dự án.

### LƯU Ý QUAN TRỌNG

- **Sau khi mã cập nhật lên Preview mà Secrets chưa được nhập, toàn bộ trang sẽ KHÓA**. Đây là thiết kế bảo mật cố ý để không còn cửa Upload công khai.
- Login OIDC không phải quyền Google Drive: app không tự có quyền truy xuất kho Drive chỉ vì người dùng đăng nhập.
- Phiên đăng nhập có thể yêu cầu đăng nhập lại khi token Google hết hạn; tệp đang nằm trong RAM có thể mất. Cơ chế TDV RECOVERY phải được nghiệm thu riêng trước khi chạy dự án lớn.
- Không bật tự ghi Drive, phê duyệt SĐK/GMP, công khai báo giá hoặc thanh toán Cloud do bước này.
- Nếu lỗi cấu hình, **đừng bỏ cổng xác thực**. Sửa Secrets/redirect URI, hoặc quay về bản backup khi V đã duyệt kế hoạch khôi phục; quay về mã công khai sẽ mất tác dụng khóa.
- Tài liệu thực sự nhạy cảm vẫn cần tầng lưu trữ/ủy quyền theo dự án và kiểm thử an toàn riêng, không chỉ Google đăng nhập.

## Tiêu chí nghiệm thu

- Thiếu Secrets → **KHÓA**, không thấy trang, menu Upload hay dữ liệu hồ sơ.
- Chưa login → chỉ có nút Google; không có trang nghiệp vụ.
- Email Google lạ; `email_verified=false`; issuer/audience lạ; token hết hạn → **TỪ CHỐI**.
- `admin/analyst` được xem menu nghiệp vụ; `viewer` không được mở E-HSMT, NSX, upload, khu vực Google Sheets.
- Chuyển tài khoản phải xóa dữ liệu phiên làm việc từ tài khoản trước.
- Mất Google Cloud/Secrets tạm thời → fail-closed, không chuyển sang đăng nhập mật khẩu yếu hay URL bí mật.
- Đăng xuất xong phải yêu cầu Google đăng nhập lại.
- Tài liệu cũ không tự động được chuyển sang Google Drive hoặc GitHub.
