# SEE PRO → NSX: Thư viện nguồn công khai và bài thử chống nhầm chứng cứ

Ngày nghiên cứu: **21/10/2026**. Nhánh: `tdv-nsx-public-evidence-safety-20261021`.

## Nguyên tắc theo chỉ đạo của V

- Giữ nguyên **một lượt nạp toàn bộ hồ sơ → tự nhận diện → phân tích → liên kết → cảnh báo → truy xuất**. Tuyệt đối không yêu cầu người dùng phân loại tài liệu, chọn từng thuốc hoặc nhập dữ liệu thay máy.
- Không đưa dữ liệu DEMO vào giao diện nghiệp vụ. Chỉ dùng **mẫu kiểm thử tổng hợp** trong `tests/`.
- Không tự quyết GMP/SĐK/ủy quyền/giá có hiệu lực; giữ chứng cứ gốc và SHA-256.
- Không tự sửa `main` hay Preview; **Google Drive vẫn khóa ghi**.
- Website có tài liệu công khai không đồng nghĩa PDF đính kèm, chữ ký hoặc giấy phép từng công ty đã xác minh. **Không biến nguồn tham khảo thành giấy tờ của NSX.**

## Nguồn công khai đã tra cứu

| Mã | Nguồn/URL chính thức | Loại nội dung được trang thể hiện | Xử lý trong SEE PRO | Tình trạng mẫu |
|---|---|---|---|---|
| S01 | [Cục QLD - danh sách cơ sở nước ngoài đạt GMP đợt 5](https://dav.gov.vn/upload_images/files/C%C3%B4ng%20b%E1%BB%91%20GMP%20NN%20%C4%90%E1%BB%A3t%205%20-%20Danh%20s%C3%A1ch%20%C4%90%E1%BA%A1t.pdf) | **Danh sách công bố** tên cơ sở, phạm vi, chứng nhận, ngày cấp/hết hạn | `GMP_PUBLIC_REGISTER`: chỉ tham khảo; không coi là giấy GMP gốc còn hiệu lực | Đã đọc cấu trúc qua chỉ mục web; chưa tải bản PDF thành công |
| S02 | [Cục QLD - danh sách cơ sở trong nước đạt GMP, cập nhật 24/10/2025](https://dav.gov.vn/danh-sach-cac-cssx-trong-nuoc-dat-tieu-chuan-nguyen-tac-gmp-gmp-bao-bi-duoc-pham-cap-nhat-toi-ngay-24102025-n5075.html) | Danh mục cập nhật cùng liên kết PDF/Excel | `GMP_PUBLIC_REGISTER`; phải xem phiên bản/ngày công bố | Trang chính thức; chưa kiểm tra nội dung tệp đính kèm |
| S03 | [Cục QLD - QĐ 299/QĐ-QLD, danh mục 206 thuốc nước ngoài](https://dav.gov.vn/quyet-dinh-so-299qd-qld-ve-viec-ban-hanh-danh-muc-206-thuoc-nuoc-ngoai-duoc-cap-giay-dang-ky-luu-hanh-tai-viet-nam---dot-1251-n4890.html) | **Quyết định công bố danh mục thuốc được cấp ĐKLH**, không phải bản đăng ký riêng của NSX | `REGISTRATION_PUBLIC_DECISION`; không tự xác nhận hiệu lực SĐK từng thuốc | Trang chính thức; chưa tải tệp đính kèm |
| S04 | [Bệnh viện Bạch Mai - Thư mời báo giá và cung cấp hợp đồng 13/03/2026](https://bachmai.gov.vn/bai-viet/thu-moi-bao-gia-va-cung-cap-hop-dong?id=ae6a22a6-bda1-4c8e-98f3-83a6ed82296f) | **Thư mời** doanh nghiệp gửi báo giá, cùng yêu cầu hồ sơ sản phẩm | `QUOTE_INVITATION`: không đưa giá danh mục/mẫu thành báo giá của NSX | Trang thông báo chính thức; tệp đính kèm chưa kiểm chứng |
| S05 | [CDC Hải Phòng - Thư mời báo giá 2025, phụ lục II](https://cdchaiphong.gov.vn/wp-content/uploads/2025/07/Thu-moi-bao-gia-MMT.signed.pdf) | **Mẫu báo giá trống** kèm thư mời, có cột giá VAT và thông tin thuốc | `QUOTE_BLANK_TEMPLATE` / `QUOTE_INVITATION` không thành báo giá thương mại | Đã đọc cấu trúc qua chỉ mục PDF; chưa tải bản PDF gốc thành công |
| S06 | [EMA - EudraGMDP](https://eudragmdp.ema.europa.eu/) | CSDL GMP/GDP, giấy phép và tình trạng **không tuân thủ** GMP | Chứng cứ độc lập phải tra cứu đúng site/certificate; không coi việc không thấy bản ghi là bằng chứng không đạt | Xác nhận trang dữ liệu chính thức; chưa truy vấn hồ sơ nhà máy cụ thể |
| S07 | [EMA - Statements of GMP non-compliance](https://www.ema.europa.eu/en/news/statements-non-compliance-gmp-now-publicly-available-eudragmdp) | Giải thích tài liệu **không tuân thủ GMP**; không phải giấy chứng nhận đạt GMP | `GMP_NONCOMPLIANCE_REFERENCE` | Trang chính thức |
| S08 | [EMA - Union format for a GMP certificate](https://www.ema.europa.eu/en/documents/template-form/union-format-good-manufacturing-practice-gmp-certificate_en.pdf) | **Mẫu chứng nhận GMP chưa điền** (template để cơ quan có thẩm quyền sử dụng) | `GMP_BLANK_TEMPLATE`: không coi là giấy chứng nhận được cấp | Đã đọc cấu trúc qua chỉ mục web PDF; chưa tải bản gốc thành công |
| S09 | [EMA - Interpretation of Union format GMP certificate](https://www.ema.europa.eu/en/documents/regulatory-procedural-guideline/interpretation-union-format-good-manufacturing-practice-gmp-certificate_en.pdf) | Tài liệu **hướng dẫn cách hiểu mẫu chứng nhận**, không xác nhận GMP của một nhà máy cụ thể | `GMP_GUIDANCE_REFERENCE` | Đã đọc nội dung chỉ mục web |
| S10 | [EMA - The issue and update of GMP certificates](https://www.ema.europa.eu/en/documents/regulatory-procedural-guideline/issue-update-good-manufacturing-practice-gmp-certificates_en.pdf) | Quy trình cấp, cập nhật, thu hồi/gián đoạn chứng nhận | `GMP_GUIDANCE_REFERENCE`; dùng xác định tiêu chí đọc, không coi là GMP của một nhà máy | Đã đọc nội dung chỉ mục web |

## Cải tiến đã thực thi

- `tdv_nsx_public_guard.py`: nhận biết **những tài liệu không phải chứng cứ trực tiếp** từ nội dung, không dựa vào tên tệp.
- `tdv_nsx_auto.py`: tích hợp lớp kiểm tra **trước bộ dự đoán loại tài liệu**, không bao giờ ghép danh sách công bố, mẫu trống hay thư mời làm GMP/SĐK/báo giá NSX. Giữ hồ sơ trong danh sách kiểm toán với trạng thái `TAI_LIEU_THAM_KHAO`.
- `tests/test_tdv_nsx_public_guard.py`: mẫu Word/PDF **do bài thử tự tạo theo cấu trúc đã tra cứu**, không giả làm tệp gốc DAV/EMA/bệnh viện. Bao gồm đối chứng giấy GMP và báo giá đã điền để tránh chặn nhầm mọi hồ sơ hợp lệ.
- Không tự gửi dữ liệu ra ngoài, không lưu Drive, không động vào `main`/Preview.

## Chưa được khẳng định

1. Chưa có tải thành công và xác minh SHA256 tệp PDF gốc của S01/S05/S08 trong phiên này (môi trường tải bị lỗi kết nối). Bài thử đã có **không có nghĩa là đã xử lý chính các file PDF ấy**.
2. Chưa xác minh thật từng giấy GMP, SĐK hoặc ủy quyền còn hiệu lực của NSX.
3. Chưa có thống kê độ chính xác trên tập hồ sơ thật đa dạng, chưa chứng minh nghiệp vụ đáp ứng yêu cầu E-HSMT.
4. Việc mở rộng mẫu được thực hiện riêng, **không triển khai lên Preview** cho đến khi V cho phép và ứng dụng Preview đã ổn định.

## Bước kiểm nghiệm tiếp theo (phát triển nội bộ, không yêu cầu V phân loại)

Tiếp tục sưu tầm bản gốc được phép tải, ghi trạng thái và SHA256, chạy **thử mù** nhiều nguồn không trùng loại; kiểm tra trích dẫn theo trang/cột và phát hiện sai liên kết trước khi đề nghị đưa cập nhật vào Preview.
