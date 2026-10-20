# SEE PRO · Kho nguồn E-HSMT thuốc tân dược (đợt khởi động 20/10/2026)

**Nhiệm vụ:** tìm gốc E-HSMT thuốc tân dược, ưu tiên Generic, biệt dược gốc
được hỗ trợ đầy đủ; ưu tiên tài liệu chính thức và giữ phiên bản nguồn.
Đây là **kho nghiên cứu**, KHÔNG phải mã ứng dụng, KHÔNG gửi tài liệu lên AI.

## Phân biệt trạng thái

- **DA_XEM_PDF_CONG_KHAI:** Đã truy cập được PDF trực tiếp trên tên miền
  của cơ sở y tế; xác định được số trang và các trường bên trong;
  chưa có bản bytes tải về để tính SHA256.
- **DANH_SACH_DINH_KEM_CHUA_TAI:** Mới xác minh trang web liệt kê tên tệp.
  Không coi đây là đã sở hữu bộ HSMT hoặc đã đọc hết nội dung.
- **TAI_LIEU_LOAI_KHAC:** HSYC/Quyết định/Thông báo, không dùng thay E-HSMT.

## Hồ sơ E-HSMT gốc đã mở và xác minh nội dung

### E01 · Bệnh viện An Bình – Thuốc Generic

- **Nguồn trực tiếp tại bệnh viện**:
  https://benhvienanbinh.vn/wp-content/uploads/2024/01/e-HSMT-1.pdf
- **Trạng thái:** DA_XEM_PDF_CONG_KHAI
- **Định dạng:** PDF có lớp chữ, **61 trang**.
- **Mã thông báo:** IB2300384581-00.
- **Ngày phát hành in trên bản PDF:** 27/12/2023.
- **Quy trình in tại HSMT:** một giai đoạn hai túi hồ sơ (mẫu lịch sử).
- **Bảng tổng hợp:** quanh trang PDF 14 (0-index 13), nêu
  PP2300574961, mã GEN001, giá ước tính riêng, bảo đảm dự thầu riêng.
- **Mẫu số 00:** quanh trang PDF 21 (0-index 20); mã GEN001,
  hoạt chất Acetyl leucin, hàm lượng 500mg, đường tiêm, dạng bào chế,
  số lượng, giá kế hoạch, nhóm kỹ thuật và tiến độ.
- **Điểm mới cho SEE PRO:** không được giả định mã thuốc luôn là
  G1/GE/CP; phải xác định quan hệ giữa hai bảng trong cùng tài liệu,
  tên bảng, cột giá kế hoạch khác giá dự thầu; bảng nhiều dòng xuống
  hàng và có các biểu mẫu thuộc hai túi hồ sơ.
- **Không được tuyên bố bộ hồ sơ gốc đã đầy đủ:** PDF chỉ rõ còn tài liệu
  được đính kèm như PHAM VI CUNG CAP.rar và các chương hợp đồng .docx.
  Các tệp phụ này CHƯA được tải và kiểm chứng cùng với PDF.
- **Không được đưa vào tập chuẩn độ chính xác:** cần tải bytes,
  đối chiếu số trang, xác minh giá trị thủ công và tính SHA256 trước.
- **Cơ sở đối chiếu:** văn bản PDF từ domain chính thức, xem được cả
  Mẫu 00 và bảng tổng hợp. Địa chỉ in trong PDF là e-GP lịch sử.

## Nguồn nhận diện có đính kèm – cần xác minh và lấy bản gốc

### C01 · Bệnh viện Chợ Rẫy – Generic 1.282 mục (IB2600069494)

- Nguồn phát hiện: https://vietlex.vn/dau-thau/goi-thau/IB2600069494
- Trạng thái: DANH_SACH_DINH_KEM_CHUA_TAI.
- Trang liệt kê: Chuong V Gói 2 generic 1282 mục.zip,
  Chương III Tiêu chuẩn đánh giá kỹ thuật_generic.docx,
  quyết định phê duyệt, Chương VII/VIII.
- Điểm kiểm thử: ZIP, DOCX, tách yêu cầu kỹ thuật khỏi thông báo,
  liên kết nhiều loại văn bản. Không coi thông tin trang thứ ba là
  file gốc nếu chưa tải và xác minh nguồn.

### C02 · Bệnh viện Quân Y 7A – Generic (IB2600103711)

- Nguồn phát hiện: https://vietlex.vn/dau-thau/goi-thau/IB2600103711
- Trạng thái: DANH_SACH_DINH_KEM_CHUA_TAI.
- Trang liệt kê: Chuong V. PHAM VI CUNG CAP.docx,
  Chương III. Muc 3 - TIEU CHUAN DANH GIA VE KY THUAT.docx,
  Chương VII/VIII DOCX, quyết định PDF.
- Điểm kiểm thử: bố trí tài liệu kỹ thuật bằng DOCX, không phụ thuộc
  PDF dạng mẫu 00; cần lấy tệp gốc và phiên bản sửa đổi.

## Tài liệu khác, không được trộn vào kho E-HSMT đã xác minh

### X01 · Bệnh viện huyện Bình Chánh – Hồ sơ yêu cầu gói Generic

- Nguồn bệnh viện:
  https://binhchanhhospital.vn/Media/files/H%E1%BB%92%20S%C6%A0%20Y%C3%8AU%20C%E1%BA%A6U%20G%C3%93I%20GENERIC.pdf
- Định dạng: PDF công khai, 93 trang.
- Trạng thái: TAI_LIEU_LOAI_KHAC (HSYC, không phải E-HSMT).
- Sử dụng để kiểm tra việc **phân loại tài liệu đúng**, không xem
  là trường hợp gói thầu đấu thầu rộng rãi qua mạng.

## Quy trình kiểm chứng để nhập vào tập kiểm thử

1. Xác minh liên kết nguồn phát hành và ngày/phiên bản.
2. Có bản bytes nguyên gốc được phép tải, tính SHA256 từng tệp.
3. Kiểm kê tất cả các tệp và thành phần webform liên quan (nếu có).
4. Kiểm tra sửa đổi, làm rõ, thay thế phiên bản.
5. Chọn lô có bảng dữ liệu đầy đủ, gán nhãn chuẩn từng trường
   (mã, hoạt chất, hàm lượng, đường dùng, dạng bào chế,
   số lượng, giá kế hoạch, nhóm kỹ thuật) có trang hoặc ô nguồn.
6. Đo độ chính xác trên các gói chưa dùng trong phát triển.
7. Không tự động tuyên bố PASS/FAIL hoặc chấm GMP/pháp lý chỉ từ AI.

## Tình trạng thực tế

Đã kiểm tra được cấu trúc **một PDF E-HSMT Generic gốc** trên website
bệnh viện, nhưng chưa lưu được bản bytes E01, chưa đủ phụ lục;
hai ứng viên 2026 mới xác minh tên file đính kèm.
Không khẳng định đã thu thập bộ hồ sơ đầy đủ hoặc đã huấn luyện SEE PRO
trên những nguồn chưa tải thành công.
