# TDV QC7 ONLINE – IDP 3.0 Preview / trạng thái ngày 20-10-2026

## Luồng DEMO thống nhất

1. **E-HSMT**: tạo PDF mẫu 2 trang hoặc tải PDF *giả lập* (dữ liệu không thật); PyMuPDF đọc lớp chữ, pdfplumber đối chiếu, thử OCR Tesseract cục bộ khi không có chữ; trích mã thuốc + hoạt chất + hàm lượng + dạng bào chế + đường dùng + số lượng. Trả về mã nguồn SHA-256, trang, phương pháp, trích dẫn; không xác nhận độ chính xác.
2. **Hồ sơ NSX**: tạo bộ mẫu sản phẩm + GMP + báo giá + giấy ủy quyền, hoặc nạp PDF DEMO cho từng loại. Đối chiếu định danh sản phẩm – nhà máy – nhà sản xuất, chặn sai liên kết. Không xác thực văn bản pháp lý.
3. **Báo cáo lãnh đạo**: đối chiếu 4 trường kỹ thuật; báo cáo các mã sơ bộ khớp, mã xung đột, chứng cứ còn thiếu; xuất bản TXT và JSON chưa phê duyệt trong phiên Streamlit; không ghi dữ liệu ngoài.

**Bộ tạo dữ liệu chỉ tạo tài liệu nhân tạo không dựa trên hồ sơ khách hàng.** File tải lên chỉ dành cho dữ liệu đã làm giả lập; người dùng phải xác nhận không có dữ liệu thật. Không tự upload, không lưu file đầu vào ra GitHub/Drive/Sheets, không gọi dịch vụ OCR bên thứ ba.

## Quy tắc chặn

- Không lặng lẽ chấp nhận tài liệu PDF lỗi, quá 25 MB, quá 80 trang, không có lớp chữ hoặc thiếu trang. Trường hợp không đọc đầy đủ phải đánh dấu chưa hoàn thiện.
- OCR là **cục bộ và tùy khả dụng**, kết quả phải so lại ảnh gốc. Không suy ra đọc đúng 100%.
- Không gán GMP khác nhà máy; không biến công văn thành chứng nhận; không gán báo giá khác sản phẩm; không gán ủy quyền khác nhà sản xuất.
- Đối chiếu hoạt chất – hàm lượng – dạng bào chế – đường dùng chỉ là **khớp kỹ thuật sơ bộ**. Giá, GMP, điều kiện dự thầu **đều CHƯA PHÊ DUYỆT**.
- Mã định danh sử dụng trong PDF DEMO chỉ do bộ tạo mẫu cấp. Nếu E-HSMT thật là bảng Excel/Word, phụ lục ZIP, ảnh scan kém hoặc diễn đạt tự do, prototype có thể không nhận dạng được.

## Kiểm thử

python -m unittest discover -s tests -p 'test_*.py' -v

Chỉ tính mức đạt dựa trên kiểm thử GitHub Actions cụ thể; **không** công bố phần trăm độ chính xác của E-HSMT thật. Không được nghiệm thu khi chưa có tập chuẩn thực tế có người xác minh độc lập.

## Chưa triển khai hoặc nghiệm thu

- Trình đọc bảng E-HSMT thật (Word/Excel/ZIP), phụ lục, sửa đổi HSMT, liên kết nhiều mã với nhiều sản phẩm.
- Định vị chính xác ô bảng, phân đoạn nội dung nhiều LOT trên cùng một trang, tái dựng bảng OCR và độ tin cậy.
- Kiểm chứng chữ ký, nguồn cấp, hiệu lực/phạm vi GMP, phạm vi/thời hạn ủy quyền, độ tin cậy giá; xác thực người duyệt.
- Kho chứng cứ bền vững, phân quyền nội bộ/nhật ký sửa đổi, luồng duyệt, cơ sở dữ liệu nghiệp vụ và Google Sheets.
- Nghiệm thu trình duyệt thật với tài khoản Streamlit được cấp quyền, banner/khung cố định và hai vùng cuộn.

## Mốc nghiệm thu

1. Đạt kiểm thử với bộ hồ sơ nhân tạo, có case đối kháng và đo độ phủ.
2. Có kho lưu, phân quyền, xác minh doanh nghiệp và nhật ký nghiệp vụ.
3. Nạp **E-HSMT mới** trong môi trường an toàn được cấp phép, so sánh với đáp án chuẩn do chuyên gia xác nhận.
4. Hội đồng/nhân sự có thẩm quyền mới duyệt GMP, giá và quyết định tham gia thầu.

Không đụng main, không cập nhật Google Sheets gốc, không đưa hồ sơ thật vào Preview công khai mã nguồn.
