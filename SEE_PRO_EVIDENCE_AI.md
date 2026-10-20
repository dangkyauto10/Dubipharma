# SEE PRO: nguồn chứng cứ và AI tùy chọn

## Luồng dữ liệu trong TDV QC7 ONLINE

1. Phân loại tài liệu (thông báo mời thầu, bảng lô, PDF kỹ thuật, hồ sơ chứng minh).
2. Đọc PDF / DOCX / XLSX / XLS / CSV và ảnh khi bật OCR.
3. Liên kết đúng mã IB, BP, PP, mã thuốc; không trộn nhiều gói thầu.
4. Kiểm toán số lượng, đơn giá kế hoạch, thành tiền, trùng mã và khác biệt.
5. Khi có yêu cầu, chỉ lấy các trích đoạn có chứng cứ liên quan một mã thuốc/lô.
6. Hiển thị nội dung và SHA256 để người dùng tự xem trước khi chấp thuận gửi Google Gemini.
7. Pydantic kiểm tra hình thức JSON; Python kiểm tra source_id và quote tồn tại trong nguồn.
8. Xuất Excel và JSON có dấu nguồn, cảnh báo, trạng thái chưa xác minh.

## Quy tắc bảo mật và API

- Chế độ AI mặc định không chạy; toàn bộ tác vụ đọc hồ sơ cơ bản không yêu cầu API key.
- Chỉ gửi văn bản đã được hiển thị khi người dùng đánh dấu đồng ý và bấm nút xác nhận.
- Không dùng Gemini Files API để chuyển bản PDF/XLSX nguyên bản.
- API key cần đặt ở Streamlit Secrets hoặc biến môi trường GEMINI_API_KEY của máy chủ.
- Không lưu key trong mã, kết quả xuất ra, giao diện hoặc GitHub.
- Khi bật Gemini, có thể có chi phí; người dùng phải kiểm tra điều khoản sử dụng dữ liệu.
- Gemini API miễn phí không phù hợp với tài liệu bí mật; không dùng cho hồ sơ mật.
- Streamlit Cloud tiếp nhận tệp tại máy chủ ứng dụng, không phải xử lý hoàn toàn ở máy Windows.
- Không tự gửi dữ liệu sang Google Sheets hoặc sửa dữ liệu nguồn.

## Giới hạn và kiểm thử

- Bản AI hiện kiểm tra một mã thuốc/mã phần mỗi lượt với số đoạn trích có giới hạn, không được nói đã thẩm định toàn bộ E-HSMT hay HSDT.
- Trích dẫn đúng chỉ xác minh văn bản trích thực sự có trong nguồn, không đủ để chứng minh điều kiện kỹ thuật, GMP hoặc pháp lý đã đáp ứng.
- PDF hình học G1 phụ thuộc mẫu bố cục; tùy chọn đọc sâu mặc định tắt.
- OCR luôn cần so sánh với hình ảnh gốc.
- Không suy luận hoặc tự tạo đơn giá dự thầu, không phê duyệt pháp lý, không tự ra quyết định đạt/không đạt.
- Kiểm thử: python -m unittest discover -s tests -p 'test_*.py' -v
- Các bài kiểm thử Gemini dùng client giả lập; chưa có thử nghiệm API thực khi không có key và quyền gửi dữ liệu.

## Cấu hình / vận hành

1. Vào menu E-HSMT trong ứng dụng hiện có.
2. Tải một bộ tài liệu và nhấn nút đọc kiểm toán hiện hành.
3. Mở mục SEE PRO Đối chiếu chứng cứ bằng AI (tùy chọn).
4. Chọn mã cần soi; nhấn (1) xem trước đoạn trích.
5. Kiểm tra từng dòng, rồi mới đồng ý và nhấn (2) gọi Gemini.
6. Kiểm tra trạng thái chứng cứ và xuất Excel/JSON để duyệt thủ công.
