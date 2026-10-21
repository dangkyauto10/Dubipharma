# TDV QC7 ONLINE — SỔ MỐC SAO LƯU & PHIÊN BẢN

> Lưu trong CÙNG repository `dangkyauto10/Dubipharma`; chỉ metadata mã nguồn. Không chứa hồ sơ E-HSMT/NSX, PDF, giá chào hoặc dữ liệu mật.
>
> **Thời gian:** ghi UTC+07 từ *commit mốc*, không đánh đồng với thời điểm thực tế nhấn tạo nhánh backup (GitHub branch API không trả về giờ tạo chính xác).

| Số | Nhánh backup | Commit mốc | Giờ commit (VN) | Hạng mục/lý do | Mục đích |
|---|---|---|---|---|---|
| 001 | `TDV_BACKUP_001_20261021` | `0a494e29da5fd157e0ccfcafabd9c9cb512b1f1b` | 21/10/2026 03:35:13 | Trước khi đưa bộ đọc bảng tổng hợp E-HSMT XLSX vào Preview | Khôi phục nền ban đầu |
| 002 | `TDV_BACKUP_002_20261021` | `83d2b463fd1f7c2021cb8df62870f173dc04a4be` | 21/10/2026 07:53:54 | SEE PRO đọc PDF/XLSX tự động tại phân hệ E-HSMT | Khôi phục bản E-HSMT sơ bộ |
| 003 (DEV) | `TDV_DEV_BACKUP_003_20261021` | `4381c6d8d765491f1423c5b9117aa99ea3f8cda8` | 21/10/2026 08:48:23 | NSX tự nhận diện SĐK/GMP; truy ngược đơn vị, nhà máy, chứng cứ; phân loại văn bản gói thầu | Mốc nghiên cứu riêng, **chưa triển khai lên Preview** |
| 004 | `TDV_BACKUP_004_BEFORE_REAL_COMPARISON_20261021` | `83d2b463fd1f7c2021cb8df62870f173dc04a4be` | 21/10/2026 07:53:54 (*mốc mã nguồn*) | Ngay trước tích hợp NSX và SO SÁNH thật vào cùng Preview | Điểm rollback an toàn (nội dung trùng 002) |
| 005 | `TDV_BACKUP_005_COMPARISON_20261021` | `fa0c430f7c159f510a2aa3ec6886411339e62c17` | 21/10/2026 12:02:20 (*mốc mã nguồn*) | SEE PRO chung + E-HSMT + NSX + so sánh có ba màu, báo cáo Word/Excel hai nguồn | Mốc khôi phục phiên bản tích hợp trước khi cập nhật sổ lần cuối |

| 006 | `TDV_BACKUP_006_BEFORE_NSX_DIAGNOSTIC_20261021` | `09c92d259011d7ba9148d2ad5f1d77efc993db2b` | 21/10/2026 12:03:36 (*mốc mã nguồn*) | Trước sửa lỗi hiển thị 0% khi chưa có ứng viên NSX; tài liệu NSX chưa tạo được bản ghi thuốc | Khôi phục nguyên trạng Preview ngay trước chẩn đoán |
| 007 | `TDV_BACKUP_007_NSX_DIAGNOSTIC_20261021` | `56b92e45e4645743323b5fff2e4b14511d124e8a` | 21/10/2026 12:37:20 (*mốc mã nguồn*) | Bổ sung chẩn đoán từng nguồn NSX; phân biệt `N/A` với 0%; không lộ dữ liệu chi tiết. GitHub QA: 145/145, khởi động AppTest đạt | Mốc rollback sau khi sửa hiển thị/chẩn đoán, **chưa chứng minh PDF NSX thật đã nhận diện đúng** |

## Trạng thái đã kiểm thử và giới hạn

- 001/002/004 chỉ là các điểm khôi phục mã nguồn; không chứa tệp riêng tư.
- NSX 003 phát triển: GitHub Actions đã kiểm thử 171/171 bài (dữ liệu kiểm thử giả lập), **không thay thế kiểm tra tài liệu NSX thật**.
- Phiên bản tích hợp sau 004: bộ đọc E-HSMT và NSX sử dụng cùng lớp trích xuất SEE PRO, không yêu cầu nộp tay nhãn loại tài liệu. SO SÁNH: chuẩn bên E-HSMT, quy chiếu NSX theo từng trường gốc, có SHA/trang/dòng, ba màu xanh/vàng/đỏ **sơ bộ**.
- **Lưu ý quan trọng:** tỷ lệ màu xanh là % tiêu chí khớp dữ liệu trích xuất, **không phải % đủ điều kiện dự thầu**; đỏ là không khớp, không tự tuyên bố nhà thầu bị loại. Trường chưa đọc/không có/đa ứng viên phải giữ vàng.
- Quyền lãnh đạo hiệu chỉnh và duyệt: **CHƯA BẬT** cho đến khi có đăng nhập, kiểm soát quyền theo dự án, xác minh chứng cứ và nhật ký chỉnh sửa bất biến.
- `main` không được cập nhật. Streamlit Cloud có thể cần vài phút để tải mã sau thay đổi nhánh; CI mã nguồn không phải bằng chứng đã triển khai sản xuất.

## Quy trình tiếp theo cho mọi mốc

1. Kiểm tra SHA bản đang chạy và tạo `TDV_BACKUP_###` từ đúng SHA.
2. Ghi mã nguồn, nguyên nhân, tệp sửa, bài kiểm thử và kết quả trong mốc tương ứng.
3. Chạy toàn bộ CI + Streamlit UI smoke + kiểm tra trên tệp gốc (nếu có quyền và nguồn).
4. Chỉ chuyển bản đã kiểm thử lên **cùng Preview**, không tạo app/tài khoản thứ hai; xác nhận rollback.
5. Chỉ kết luận sau nghiệm thu thực tế bởi người được phân quyền.
