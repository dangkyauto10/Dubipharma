# TDV QC7 ONLINE · SEE PRO · NSX tự động — mốc phát triển 21/10/2026

## Mục tiêu bất biến do V chỉ đạo

**TOOL phải tự làm việc, không chuyển việc của máy sang người dùng.**

Một lần nhận **toàn bộ bộ hồ sơ** → **tự đọc → tự phân loại**
→ **tự nhận diện thuốc/nhà máy/NSX** → **tự liên kết chứng cứ đúng định danh**
→ **tự chỉ ra chỗ thiếu, mâu thuẫn, chưa đọc đủ** → **xuất kiểm toán**.

- **CẤM** thay thế bằng DEMO ở luồng nghiệp vụ.
- **CẤM** giao diện có nhiều ô yêu cầu người dùng tự gắn nhãn GMP/quote/SĐK.
- **CẤM** buộc người dùng chọn từng dòng thuốc trước khi máy chịu phân tích.
- **CẤM** tự động duyệt tính hợp lệ GMP/SĐK/ủy quyền/giá khi chưa xác minh.
- **CẤM** tự ý cập nhật Preview, main, đổi cấu trúc tổng thể hoặc ghi Drive.
- Mọi thay đổi ngoài phạm vi đã thống nhất phải có V duyệt trước.

## Thực hiện trong nhánh phát triển độc lập

Nhánh `tdv-nsx-automatic-intake-20261021` bắt đầu từ Preview mốc
`0a494e29da5fd157e0ccfcafabd9c9cb512b1f1b`.

- `tdv_nsx_auto.py`: xử lý cả bộ hồ sơ, **không dùng nhãn tệp do người chọn**; tự đoán loại từ nội dung và tên cột, tách danh sách thuốc và dòng báo giá, ghép nếu định danh **duy nhất**.
- `tdv_nsx_workbench.py`: thay 7 ô phân loại bằng **một nơi tải nhiều tệp**, một nút phân tích, bảng tự nhận diện, thuốc, liên kết chứng cứ, hàng chờ xem lại, Excel/JSON.
- `tdv_nsx_intake.py`: kế thừa bộ đọc PDF/Word/Excel/CSV/ảnh SEE PRO, bổ sung tái sử dụng dữ liệu đã trích để tránh đọc cùng tệp hai lần.
- `app.py`: mục **Báo giá & hồ sơ NSX** không còn luồng DEMO hay phân loại thủ công. Các phân hệ còn lại giữ nguyên trên nhánh.
- `tests/test_tdv_nsx_auto.py`: hồi quy mẫu nhiều thuốc, GMP, SĐK, ủy quyền, bảng giá, mã không khớp, cùng nhà máy, không nhận diện, lỗi tệp, giới hạn số dòng, bằng chứng nguyên bản.
- `tdv_nsx_drive_vault.py`: mã lưu trữ tương lai vẫn nằm riêng; **chưa gọi, chưa kích hoạt**, `cloud_write_enabled=False`.

## Kiểm thử và những gì có thể khẳng định

GitHub Actions chạy hồi quy **148/148 đạt** trên nhánh phát triển.
Đã thử với **tài liệu thử do kiểm thử tự tạo**, không phải toàn bộ tài liệu doanh nghiệp thực tế.

Phần đã chứng minh bằng kiểm thử:
- Một lượt có thể tự nhận nhiều loại tệp và tự phát hiện **2 thuốc** từ một bảng, không yêu cầu người chọn dòng.
- Ghép hồ sơ GMP/giấy phép/ủy quyền/báo giá theo định danh duy nhất; khi cùng nhà máy nhiều thuốc hoặc báo giá có mã mâu thuẫn thì **không gán bừa**.
- Bảng báo giá thuốc nhiều dòng có trích chứng cứ đến ô nguồn và SHA-256.
- Tệp không đọc được và bảng cắt giới hạn phải bị báo riêng; không được tuyên bố đã đọc hết.
- Excel 6 Sheet gồm nhận diện, danh mục thuốc, liên kết, điểm chưa rõ, từng trường chứng cứ, giới hạn kiểm toán.
- `gmp_confirmed`, `quote_approved`, `bid_eligible` luôn False.

## Chưa triển khai, chưa nghiệm thu nghiệp vụ

- **Preview vẫn ở mốc cũ** `0a494e29da5fd157e0ccfcafabd9c9cb512b1f1b`. Không có deploy mới trong công việc này.
- **main không đổi**.
- Chưa thử đầy đủ với bộ hồ sơ NSX thật ở các nhà sản xuất trên thị trường.
- Chưa so sánh sâu hồ sơ NSX với từng tiêu chí kỹ thuật của E-HSMT.
- Chưa xác thực độc lập hiệu lực SĐK, GMP, ủy quyền hoặc chứng thư số.
- Cần nghiệm thu chức năng mới bằng bộ hồ sơ được phép dùng, trên môi trường có kiểm soát, rồi mới trình V việc đưa vào Preview.

## Bảo mật

Preview hiện chưa có xác thực doanh nghiệp. Khi V cho phép thử giao diện
của chức năng mới, chỉ dùng tài liệu công khai hoặc đã che thông tin nhạy cảm.
Một checkbox xác nhận *phạm vi dữ liệu được phép tải* không phải bước phân
loại tài liệu — máy vẫn tự làm toàn bộ công việc nghiệp vụ.

Không tự gửi tài liệu sang Gemini, Google Drive, Google Sheets hoặc dịch vụ khác.
Không lưu nguồn lên đĩa theo thiết kế hiện tại.
