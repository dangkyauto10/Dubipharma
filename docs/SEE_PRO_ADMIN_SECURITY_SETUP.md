# SEE PRO Preview J — Tài khoản nội bộ & phân quyền

## Phạm vi đã xây dựng

- Người dùng không cần đăng nhập được xem **dữ liệu mẫu hoàn toàn giả lập**.
- Admin có thể đặt mật khẩu SEE PRO lần đầu bằng tư cách **Google Admin đã xác thực**.
- Sau khi thiết lập, Admin có thể sử dụng `admin` + mật khẩu SEE PRO trên các PC khác.
- Admin có thể tạo tài khoản thành viên, cấp/thu hồi quyền theo phân hệ,
  khóa tài khoản và đặt lại mật khẩu tạm cho thành viên.
- Người dùng tự thay mật khẩu lần đầu; Admin tự đổi mật khẩu sau khi nhập
  mật khẩu hiện tại. Đổi mật khẩu/đổi quyền thu hồi các phiên cũ.
- Mật khẩu dùng Argon2id, chỉ lưu bản băm kèm muối; lịch sử hoạt động quản trị
  lưu trong PostgreSQL. Không lưu mật khẩu vào GitHub hoặc Streamlit Session State.
- Đăng nhập sai 5 lần bị khóa 15 phút; phiên đăng nhập nội bộ tối đa 8 giờ.
- Chức năng giá dự thầu, Google Sheets/Drive, phê duyệt và chức năng ngoài
  danh sách cấp quyền **không** được trao cho tài khoản thành viên.

## Điều kiện để bật tính năng trên Streamlit Cloud

**Chưa kích hoạt chỉ bằng cách merge mã nguồn.** Phải có PostgreSQL được vận hành
và bảo vệ bởi doanh nghiệp; không sử dụng SQLite trên Streamlit Community Cloud
vì bản lưu trữ cục bộ có thể mất khi triển khai lại hoặc khởi động máy chủ.

1. Chủ hệ thống chuẩn bị PostgreSQL dùng kết nối TLS, tạo cơ sở dữ liệu riêng
   và một tài khoản database có quyền tạo bảng trong schema được phép.
2. Vào **Streamlit Community Cloud → ứng dụng SEE PRO → Settings → Secrets**,
   thêm cấu hình bên dưới (giá trị là ví dụ, thay bằng thông tin riêng):
   ```toml
   [seepro_admin_db]
   url = "postgresql://SEE_PRO_USER:REPLACE_PASSWORD@HOST:5432/SEE_PRO_DB?sslmode=require"
   ```
   Không đặt URL thực, mật khẩu hay khóa truy cập vào chat, mã GitHub,
   ảnh chụp công khai hoặc file hồ sơ.
3. Lưu Secrets và khởi động lại ứng dụng nếu nền tảng yêu cầu.
4. Đăng nhập **Google Admin đã được cấp phép trước đó** và mở menu
   **🔐 Quản trị bảo mật**.
5. Bấm **Khởi tạo kho tài khoản**, rồi đặt mật khẩu Admin tối thiểu 12 ký tự.
   Không có mật khẩu mặc định. Chỉ Google Admin đã được xác minh mới
   thiết lập tài khoản đầu tiên; khách công khai không được tự tạo Admin.
6. Đăng xuất Google. Trên link SEE PRO mở công khai, vào phần
   **Tài khoản SEE PRO nội bộ** để đăng nhập `admin` bằng mật khẩu vừa đặt.
7. Vào **🔐 Quản trị bảo mật** để tạo tài khoản, giao quyền, khóa hoặc đặt
   lại mật khẩu thành viên. Thành viên bị buộc đổi mật khẩu tạm lần đầu.

## Các giới hạn cần nghiệm thu

- Đăng nhập nội bộ sử dụng phiên phía máy chủ, không ghi phiên vào cookie
  dùng chung. Nếu reload làm mất phiên, đăng nhập lại.
- Cơ chế khóa đăng nhập bảo vệ từng tài khoản nhưng chưa có chống bot/
  giới hạn kết nối theo IP ở tầng mạng. Nên bảo vệ thêm bằng WAF/reverse proxy
  trước khi đưa dữ liệu nhạy cảm vào dùng thật.
- Quyền giá dự thầu chính thức vẫn phải qua cơ chế phê duyệt và nhật ký
  chuyên biệt, không thể cấp qua màn hình thành viên.
- Dữ liệu phân tích E-HSMT/NSX của Preview hiện vẫn ở RAM, không tự đồng bộ
  giữa các máy. Kho quản trị mới chỉ lưu tài khoản, quyền và nhật ký quản trị.
- **Chưa được dùng hồ sơ bí mật/thầu chính thức** cho đến khi hoàn tất
  kiểm thử hệ thống và kho lưu trữ nghiệp vụ chuyên biệt.
