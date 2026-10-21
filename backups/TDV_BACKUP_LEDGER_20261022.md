# TDV QC7 · Nhật ký sao lưu và thay đổi 22/10/2026

## Nguyên tắc
- Một ứng dụng Streamlit Preview TDV QC7 ONLINE hiện có. Không tạo ứng dụng, repository hoặc tài khoản mới.
- `main` giữ nguyên. Trước cập nhật: tạo nhánh BACKUP_### từ SHA Preview và thử nghiệm trên nhánh riêng.
- Không đưa 13 tài liệu NSX gốc, khóa, token, hợp đồng hoặc nội dung riêng tư lên GitHub công khai.
- Kiểm thử bằng dữ liệu tổng hợp KHÔNG phải nghiệm thu tính đúng trên PDF NSX gốc.
- Không ghi Drive/Sheets, không tự duyệt SĐK/GMP/ủy quyền/báo giá hoặc điều kiện dự thầu.

## BACKUP theo số thứ tự

| Số | Nhánh backup | Mã commit | Nội dung |
|---|---|---|---|
| 012 | `TDV_BACKUP_012_BEFORE_NSX_EVIDENCE_LINKS_20261022` | `243e514801b31e1d573a33ced3ec85dd458729a9` | Bản trước khi xây gợi ý truy xuất SĐK/GMP, đã có sửa đa sheet và kiểm thử 158/158 |
| 013 | `TDV_BACKUP_013_NSX_EVIDENCE_CANDIDATES_20261022` | `28ac3a6fc69a15a97880f234e837f4a99780bff1` | Bản kiểm thử 174/174 trên nhánh riêng: đọc nhãn SĐK, gợi ý theo tên thuốc có nguồn và tiêu chí phụ; GMP theo nhà máy; ngày ghi trên giấy; chứng cứ trong OTHER; Excel 3 sheet chẩn đoán |

## Ghi nhận và giới hạn

1. Ảnh và Excel NSX người dùng cung cấp: 13 tài liệu đã đọc, 87 dòng trích xuất ban đầu, 0 liên kết sơ bộ. File Excel có các trường đăng ký pháp lý chủ yếu chưa gắn vào từng dòng sản phẩm. **Không** thể suy 0 liên kết thành kết luận không có chứng cứ hay không đủ điều kiện.
2. Sau sửa đa sheet ở BACKUP_011: các dòng lặp trong CÙNG TỆP chỉ được hợp nhất khi có định danh phụ trùng; các thông số mâu thuẫn giữ vàng. Chưa kiểm chứng lại trên 13 tệp gốc.
3. Đợt này thêm `tdv_nsx_evidence_candidates.py`, tích hợp `tdv_nsx_auto.py` và `tdv_nsx_workbench.py`. Chỉ tìm gợi ý chính xác có trích dẫn trang/dòng và SHA-256. Tên gần giống không được tự gộp.
4. Giấy GMP được ánh xạ **cấp nhà máy**, không tự xác nhận cho tất cả thuốc ở nhà máy. Thời hạn ghi trong giấy chỉ là cảnh báo lịch; còn phải kiểm tra số chứng nhận, phạm vi, gia hạn, thu hồi, yêu cầu dự án và hiệu lực pháp lý.
5. Có thêm các sheet Excel `GOI_Y_SDK_CHUA_XAC_MINH`, `GMP_THEO_NHA_MAY`, `CHUNG_CU_CHUA_GHEP`. Bảng `LIEN_KET_CHUNG_CU` và số lượng liên kết chứng cứ gốc vẫn giữ quy tắc cũ; gợi ý không được cộng vào % đạt.
6. GitHub Actions trên commit `28ac3a6fc69a15a97880f234e837f4a99780bff1`: **174/174 synthetic unit/integration tests PASS**, compile và khởi động AppTest thành công. 13 PDF NSX gốc không có sẵn trong môi trường phát triển; không được tuyên bố kiểm chứng chúng.
7. Quyền Lãnh đạo hiệu chỉnh/phê duyệt và lưu Drive vẫn khóa cho đến khi có xác thực/phân quyền/nhật ký phù hợp.

## Quy trình khôi phục
Nếu bản Preview mới lỗi: đối chiếu mã commit và hiệu lực trạng thái trước khi khôi phục mã trên branch `TDV_BACKUP_012_BEFORE_NSX_EVIDENCE_LINKS_20261022`. Không đưa `main` vào quy trình. Backup code **không** phải bản sao dữ liệu dự án.
