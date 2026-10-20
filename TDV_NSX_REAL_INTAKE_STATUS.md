# TDV QC7 ONLINE · NSX & Báo giá · Giai đoạn 1

**Nhánh phát triển:** `tdv-nsx-real-intake-20261021` từ Preview commit `444f4b0b58e733d78de59f4ccd6ed3f9e26d1740`.

## Đã xây dựng và nối vào `app.py` trên nhánh riêng

- `tdv_nsx_intake.py`: đọc tài liệu PDF, DOCX, XLSX, XLS, CSV, ảnh khi bật OCR (tận dụng `see_pro_multiformat.extract_file`), trích các cặp trường–giá trị có nhãn rõ ràng, lưu SHA256 tệp và vị trí chứng cứ.
- `tdv_nsx_workbench.py`: giao diện tại **Báo giá & hồ sơ NSX**, mỗi lượt một hồ sơ sản phẩm kèm tài liệu GMP, giải trình GMP, SĐK, ủy quyền, báo giá, catalogue.
- `app.py`: giữ bộ DEMO cũ phía dưới, chỉ hiện khi bật checkbox, không thay các phân hệ SEE PRO và báo cáo lãnh đạo cũ.
- Kiểm tra liên kết theo mã sản phẩm / SĐK / nhà máy / nhà sản xuất, đối chiếu chuỗi chính xác sơ bộ. Nếu khác hoặc thiếu trường bắt buộc, không tự suy luận.
- Phát hiện thông tin xung đột xuất hiện nhiều lần, không tự ghi đè.
- Excel báo cáo **4 Sheet**: tài liệu nguồn, đối chiếu định danh, chứng cứ từng trường, giới hạn kết luận. JSON cho kiểm toán; chặn chuỗi giống công thức Excel.

## Nghiêm cấm kết luận tự động

- `verified`, `gmp_confirmed`, `quote_approved`, `registration_confirmed`, `bid_eligible` luôn **False**.
- Cần kiểm tra bản gốc, nhà máy, phạm vi GMP, thời hạn/nguồn cấp SĐK và chuỗi ủy quyền.
- Đơn giá báo giá là **thông tin nguồn**, không phải giá chào thầu đã duyệt.
- Dữ liệu chỉ được trích xuất trong phiên Streamlit; **không** tự ghi Drive/Sheets, không gửi Gemini, không gắn quyết định xét thầu.
- Tệp Streamlit được xử lý tại máy chủ đám mây của ứng dụng nếu chạy trên Streamlit Cloud, không phải thuần máy Windows. Không nạp dữ liệu mật nếu công ty chưa cho phép.

## Điểm chưa hoàn thiện / cần nguồn nghiệm thu

1. Hiện hỗ trợ **một sản phẩm mỗi lượt**; chưa tự tách an toàn bảng catalogue nhiều sản phẩm.
2. Nhận diện theo nhãn trường rõ ràng; bảng không nhãn, scan OCR, văn bản pháp lý diễn đạt tự do vẫn có thể cần kiểm tra thủ công.
3. Chưa đối chiếu thực sự với **770 lô** SEE PRO và chưa nối báo cáo lãnh đạo bằng dữ liệu thật.
4. Chưa xác minh SĐK/GMP/giấy ủy quyền tại cơ quan cấp hoặc chữ ký số.
5. Chưa thiết lập kho tài liệu doanh nghiệp có phân quyền, ghi nhật ký, lưu phiên bản, cơ chế xóa/lưu giữ.
6. Chưa kiểm thử giao diện trực tiếp qua trình duyệt với tệp thực tế do doanh nghiệp cho phép.
7. Chưa triển khai vào Preview hoặc main. Cần thống nhất lưu trữ/quyền dữ liệu và nghiệm thu bộ hồ sơ thực tế trước khi cập nhật.

## Kiểm thử

`python -m unittest discover -s tests -p 'test_*.py' -v`

GitHub Actions trên nhánh riêng: 120/120 đạt vào ngày 20–21/10/2026 (tại lượt CI `39487764212`). Đây là **độ phủ hồi quy mã**, không phải độ chính xác thẩm định hồ sơ thật.

## Tiếp theo được đề xuất

1. Kiểm tra một bộ hồ sơ sản phẩm tân dược thật đã được phép dùng, được ẩn những trường bí mật không cần thiết.
2. Hoàn thiện liên kết nhiều sản phẩm/nhà máy và so sánh tiêu chí từ E-HSMT.
3. Nghiệm thu trên trình duyệt Preview trước khi bàn giao.
