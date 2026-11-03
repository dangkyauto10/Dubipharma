# SEE PRO READER — BOOX Note Air 5C (Android 15)

## Mục tiêu
Một ứng dụng Android độc lập: mở DOCX, XLSX, PDF, JPG/JPEG/PNG/WEBP và TXT; đọc văn bản bằng TTS tiếng Việt của hệ thống; OCR ảnh và các trang PDF không có lớp chữ (ML Kit Latin, tích hợp sẵn trong APK); thao tác với màn hình cảm ứng và bút.

**Không cần máy chủ, không cần Windows, không kết nối TV trong phiên bản này.** Không có quyền INTERNET, dữ liệu tài liệu không tải lên dịch vụ bên ngoài. Không có cơ chế tự động ký duyệt hồ sơ hay khẳng định OCR chính xác tuyệt đối.

## Nguồn tái sử dụng từ SEE PRO Dubipharma
Được phát triển từ nghiệp vụ nhận tệp đa định dạng và mô hình cảnh báo của `see_pro_multiformat.py` + `tdv_real_intake.py`. Java Android là bản chuyển phù hợp hệ điều hành BOOX, không chạy Python/Streamlit trên máy. Cùng nguyên tắc: chỉ đọc, không ghi Drive/Sheet, không tự khẳng định tài liệu đã xác minh.

## Build APK
Trong GitHub Actions, workflow **SEE PRO BOOX - build Android APK** tạo artifact **SEE_PRO_READER_BOOX_APK**, gồm `app-debug.apk`. Máy Android cần bật quyền cài ứng dụng từ nguồn đã chọn khi cài tệp APK. Debug APK chỉ dùng thử nội bộ, không phát hành công khai.

Nếu build trên máy có Android SDK và Java 17: `cd boox-reader && gradle :app:assembleDebug` (Gradle 8.7; Android SDK 35).

## Hướng dẫn dùng
1. Cài APK trên BOOX. Mở app **SEE PRO READER**.
2. Nếu máy chưa có giọng tiếng Việt: vào Android **Settings → Text-to-speech** để chọn/cài engine và giọng `vi-VN`. Việc tải giọng lần đầu tùy engine, có thể cần mạng.
3. Nhấn **MỞ TÀI LIỆU TỪ BOOX**, chọn file từ bộ nhớ/ứng dụng Files.
4. Xem văn bản đã trích xuất, chọn **▶ ĐỌC**, **TẠM DỪNG**, **TIẾP TỤC**, **DỪNG**, **CHẬM/NHANH**.
5. Với ảnh/PDF quét, đối chiếu phần OCR với hình gốc trước khi sử dụng trong nghiệp vụ.

## Giới hạn bản thử
- DOCX/XLSX chuẩn mới. Chưa hỗ trợ file .DOC/.XLS cũ, file Word/PDF khóa mật khẩu, nội dung bên trong ảnh đặt trong Word/Excel.
- PDF chỉ đọc tối đa 120 trang/lần; OCR tối đa 20 trang thiếu lớp chữ/lần; file tối đa 30 MB; văn bản tối đa 160.000 ký tự; Excel tối đa 4.000 dòng.
- OCR ảnh có thể sai dấu, số, chữ nhỏ, bảng biểu; không dùng để ra quyết định chuyên môn nếu chưa kiểm chứng.
- Trình đọc TTS phụ thuộc engine và gói giọng tiếng Việt có trên BOOX; không cam kết đọc offline nếu engine chưa tải giọng.
- Tạm dừng và tiếp tục sẽ phát lại từ đầu đoạn hiện tại, không từ đúng từ/câu vừa nghe.
- Truyền hình ảnh và âm thanh lên Smart TV được hoãn sang giai đoạn tiếp theo.
