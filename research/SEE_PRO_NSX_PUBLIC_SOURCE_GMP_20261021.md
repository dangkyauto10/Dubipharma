# SEE PRO · NSX · Nguồn học dữ liệu công khai GMP (21/10/2026)

**Mục đích:** nâng nhận diện loại tài liệu NSX, không tự thay đổi Preview, main hoặc nghiệp vụ đã được V xác lập. Không tự suy ra GMP đáp ứng hay thuốc đủ điều kiện dự thầu.

## Nguồn chính thức được phát hiện và kiểm tra trang công khai

1. **Cục Quản lý Dược — tra cứu cơ sở sản xuất nước ngoài đáp ứng GMP**
   - URL: https://dichvucong.dav.gov.vn/DanhSachCoSoSanXuatNuocNgoaiDapUngGMP/
   - Loại: **cơ sở dữ liệu tra cứu / danh sách công bố**, KHÔNG phải bản scan giấy chứng nhận cho một nhà máy cụ thể.
   - Trường quan sát được từ trang: IDCC, ID công ty, tên cơ sở, địa chỉ, phạm vi chứng nhận, nguyên tắc GMP, mã số chứng nhận, ngày cấp, ngày hết hạn, cơ quan cấp, đợt công bố.
   - **Điểm kiểm thử**: cùng công ty có thể có nhiều cơ sở; phải đối chiếu đúng **tên + địa chỉ cơ sở + phạm vi sản xuất + thời điểm**; ngày hết hạn cũ trong bản ghi lịch sử không chứng minh tình trạng hiện hành.

2. **Cục Quản lý Dược — công văn công bố PIC/S-GMP/EU-GMP đợt 70**
   - URL: https://dav.gov.vn/cong-van-so-21355qld-cl-gui-cac-syt-ve-viec-cong-bo-co-so-san-xuat-thuoc-dat-tieu-chuan-pics-gmp-va-eu-gmp-dot-70-n2711.html
   - Loại: **công văn và danh sách cơ sở được công bố theo đợt**, không phải chứng nhận GMP gốc.
   - Trang có liên kết danh sách công bố PDF và Excel; **chưa tải và kiểm chứng từng file đính kèm**.
   - Điểm kiểm thử: phát hiện **đợt công bố**, ngày công bố và phân biệt danh sách với chứng nhận.

3. **EMA EudraGMDP**
   - URL: https://eudragmdp.ema.europa.eu/
   - Loại: **cơ sở dữ liệu chính thức về MIA/GMP, báo cáo không tuân thủ, GDP**; dữ liệu do cơ quan có thẩm quyền trong EEA nhập.
   - Trang cơ quan mô tả rõ **không có chứng nhận GMP tìm thấy không tự chứng minh cơ sở không tuân thủ**, nên SEE PRO tuyệt đối không tự kết luận FAIL chỉ vì tra cứu không thấy.
   - Kiểm thử: GMP certificate khác manufacturing/importation authorisation (MIA), khác GDP, khác non-compliance report. Mã số chứng nhận không phải mã số đăng ký lưu hành thuốc.

4. **EMA EudraGMDP — màn hình tìm chứng nhận GMP**
   - URL: https://eudragmdp.ema.europa.eu/inspections/gmpc/searchGMPCompliance.do
   - Màn hình có certificate number, date, site name, country, DUNS, OMS identifiers, site reference, manufacturing operations và lựa chọn tra cứu non-compliance.
   - Điểm kiểm thử: pháp nhân, địa chỉ xưởng, phạm vi thao tác/đóng gói, hiệu lực và chứng nhận nhiều phiên bản phải được liên kết theo nguồn.

5. **EMA — hướng dẫn EudraGMDP và phạm vi GMP**
   - URL: https://www.ema.europa.eu/en/human-regulatory-overview/research-development/compliance-research-development/good-manufacturing-practice/eudragmdp-database
   - Phân biệt số nhận diện tổ chức (OMS) với nhà máy cụ thể, và chứng nhận với cơ quan cấp.

## Các bài học parser (chưa đồng nghĩa với việc đã huấn luyện mô hình)

- **GMP_CERT**: chỉ khi thực sự là chứng nhận cơ sở, không phải bài thông báo công bố.
- **GMP_PUBLIC_REGISTER**: danh sách cơ sở đáp ứng GMP / dữ liệu tra cứu của cơ quan quản lý.
- **GMP_PUBLICATION_NOTICE**: công văn công bố danh sách/đợt công bố.
- **MIA**: giấy phép sản xuất/nhập khẩu, không đồng nhất với GMP.
- **GDP**: thực hành phân phối tốt, không đồng nhất GMP sản xuất.
- **GMP_NON_COMPLIANCE**: báo cáo không đáp ứng, không phải chứng chỉ tích cực.
- **GMP_UNKNOWN**: tài liệu không đủ chứng cứ để phân loại; không tự động đánh giá.

Ưu tiên các đối sánh: **exact manufacturer site** (tên + địa chỉ), certificate number + issuer, GMP scope, manufacturing operations, certificate dates. Đánh dấu văn bản OCR/scan và giá trị cần kiểm chứng nguyên bản. Xác định sản phẩm và loại tài liệu trong hệ thống là công việc TOOL, không đặt gánh nặng phân loại cho người dùng.

## Hạn chế và trạng thái

- Đây là **5 đầu mối trang/dữ liệu chính thức được rà soát**, không phải 5 file GMP nguyên gốc đã tải.
- **0 tài liệu gốc mới được thu vào kho kiểm thử trong lượt này**.
- Chưa đưa dữ liệu vào tập huấn luyện AI, chưa gọi Gemini, chưa đánh giá hồ sơ của NSX thực tế.
- Tệp này là **ghi nhận nguồn và quy tắc kiểm thử đề xuất** trên nhánh nghiên cứu. Không thay đổi thiết kế hiện hành, không cập nhật Preview hoặc main, không ghi Drive.

## Liên hệ SEE PRO

Khi có bản sao hợp pháp của chứng nhận/listing/đơn giá thật, kiểm thử parser trên nhánh riêng; chỉ đề xuất thay đổi sau khi đảm bảo các chứng cứ thuộc đúng cơ sở, đúng sản phẩm, đúng phiên bản và không ảnh hưởng bài kiểm thử E-HSMT đã qua.
