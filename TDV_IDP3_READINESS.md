# TDV-IDP 3.0 – Cửa kiểm soát trước E-HSMT thật (Preview)

**Trạng thái:** mô hình kiểm chứng GIẢ LẬP / chưa nghiệm thu nghiệp vụ.

1. Giữ nguyên \`main\`; chỉ thử tại \`tdv-qc7-online-preview-20261020\`.
2. Không tải E-HSMT, báo giá, GMP, giấy ủy quyền hoặc hồ sơ NSX thật lên Preview.
3. Hai bộ đọc PyMuPDF và pdfplumber đều thường phụ thuộc lớp chữ gốc. Việc trùng kết quả **không** xác nhận độ chính xác. Trang trống bắt buộc gắn cờ cần OCR; OCR chưa chạy trong bản này.
4. Chứng cứ phải có tối thiểu \`source_id\`, \`sha256\`, \`page\`, \`method\`, \`excerpt\`. Cần bảo quản bản gốc để kiểm lại hash; metadata không đủ chứng minh tính xác thực.
5. Gắn chứng cứ đúng \`product_id\`, \`factory_id\` và khi cần \`manufacturer_id\`. Sai bất kỳ định danh nào thì **chặn liên kết**.
6. Công văn giải trình GMP không thể tự biến thành chứng nhận gia hạn; GMP cùng nhà máy vẫn phải kiểm tra hiệu lực, phạm vi, cơ sở và cơ quan cấp.
7. Báo giá và giấy ủy quyền dù khớp mã vẫn cần xác minh nội dung và phê duyệt bởi người có thẩm quyền.
8. Mọi hàm rà soát luôn trả về \`verified=False\`, \`gmp_confirmed=False\`, \`price_approved=False\`, \`bid_eligible=False\`.

## Chưa được nghiệm thu

- OCR hình ảnh thực tế, ảnh mờ/lệch, bảng nhiều trang và phụ lục.
- Đọc toàn bộ E-HSMT thực, kiểm tra độ phủ và đối chiếu chuẩn có đánh dấu trang/ô.
- Chuẩn hóa đa dạng hàm lượng/đường dùng/nhóm thuốc/tên đơn vị/cơ sở sản xuất.
- Lưu trữ và truy xuất bền vững bản gốc, phiên bản, lịch sử phê duyệt.
- Xác thực, phân quyền nghiệp vụ và tích hợp Google Sheets theo nguyên tắc chỉ ghi khi có duyệt.
- Nghiệm thu giao diện thực tế trên trình duyệt được cấp quyền, gồm hai vùng cuộn độc lập.

## Điều kiện mở bước kiểm thử E-HSMT mới

Có môi trường nghiệp vụ được phân quyền; kho chứng cứ độc lập bảo mật; quy trình duyệt giá và GMP; bộ mẫu kiểm thử theo từng loại E-HSMT; đánh giá sai sót với người phụ trách nghiệp vụ. Không tiếp nhận dữ liệu thật vào bản demo hiện tại.

**QA:** \`python -m unittest discover -s tests -p 'test_*.py' -v\`; CI chỉ chạy mã đọc/soát, không ghi hệ thống thật.
