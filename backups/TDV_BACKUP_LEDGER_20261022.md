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

| 014 | `TDV_BACKUP_014_BEFORE_LEADERSHIP_TRIAGE_20261022` | `d0cba956cf069dbf2ce07b474eeca49259f70dd1` | Trạng thái Preview trước khi tích hợp thứ tự rà soát vào báo cáo Lãnh đạo, CI đã đạt 174/174 bài | 
| 015 | `TDV_BACKUP_015_LEADERSHIP_TRIAGE_20261022` | `387de6db60d9da7185ead043edcffaa5835e7f97` | Bộ triage đọc-only: chênh lệch kỹ thuật / chứng cứ SĐK-GMP / chưa có ứng viên, ưu tiên theo công việc. Bổ sung bảng trong Báo cáo Lãnh đạo, sheet Excel `UU_TIEN_XU_LY` và phần Word. Kiểm thử giả lập 181/181 và AppTest đạt; chưa thử 13 PDF NSX gốc |

| 016 | `TDV_BACKUP_016_20261022` | `f8e84cab9a7bc7153381b2accfe1395b88ea2f5d` | Sao lưu Preview trước khi nâng SEE PRO kiểm toán chất lượng trích xuất |
| 017 | `TDV_BACKUP_017_SEE_PRO_QUALITY_20261022` | `e45e0a3ce35d30c235f99e6213fd11d5c97dbcac` | Mã kiểm thử 190/190: kiểm đếm tệp Upload, lưu lỗi đọc, đo độ phủ trích dẫn riêng E-HSMT/NSX, cảnh báo kết quả xanh thiếu nguồn, thêm sheet E-HSMT `KIEM_TOAN_CHAT_LUONG`; không kiểm định độ chính xác bằng tài liệu thật |

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


## Nhật ký 22/10 — Tập hợp vấn đề xử lý cho Lãnh đạo

- Tên module mới: `tdv_review_priorities.py`. Chỉ tổng hợp trạng thái **đã trích xuất**; không sửa E-HSMT, NSX, các liên kết hoặc chứng cứ gốc.
- Mức 1: chênh lệch kỹ thuật hoặc chứng cứ SĐK có định danh mâu thuẫn (cần so gốc).
- Mức 2: nhiều ứng viên, tiêu chí có ứng viên nhưng thiếu chứng cứ, gợi ý SĐK chưa xác minh, GMP theo nhà máy chưa xác minh, tài liệu chưa ghép.
- Mức 3: chỉ có gợi ý tên hoặc chưa có ứng viên. Số mục công việc có thể lớn hơn số mã thuốc; **không** phải đếm thuốc không đạt.
- Excel `UU_TIEN_XU_LY` xuất mọi vấn đề có trích dẫn nguồn khi dưới giới hạn; Word chỉ hiện một số mục ưu tiên và hướng dẫn xem Excel.
- Chức năng dành cho người dùng hiện tại **chưa có xác thực doanh nghiệp**; không upload NSX mật vào Preview công khai. Không bật lưu Google Drive, phê duyệt pháp lý hoặc trả phí.
- CI cuối phải đạt trên đúng commit sau cập nhật nhật ký trước khi thay đổi nhánh Preview; `main` giữ nguyên.


## SEE PRO Quality Gate — 22/10/2026
- Đã thêm `see_pro_quality_gate.py` với ba phép kiểm **E-HSMT**, **NSX**, **SO SÁNH**. Tệp nạp có SHA-256 và lỗi trích xuất phải được ghi lại; các trường dữ liệu trích xuất không có trích dẫn riêng phải hiển thị khác với trường có nguồn.
- Khi một tiêu chí **XANH SƠ BỘ** thiếu dấu vết tệp/trang-dòng ở E-HSMT hoặc NSX, UI cảnh báo rõ. Phần này **không thay đổi** kết luận chuyên môn/luật hay ba màu gốc, để tránh tô xanh từ một kiểm tra chất lượng.
- Excel E-HSMT có sáu sheet, gồm thêm `KIEM_TOAN_CHAT_LUONG`. Trên giao diện NSX hiện thị bảng độ phủ có nguồn, trường mâu thuẫn và tệp chưa đọc đủ.
- `99,9999%` chỉ là **mục tiêu phát triển**, **không phải tỷ lệ chính xác đã kiểm định**. Cần tập dữ liệu gốc được chuyên gia gán nhãn, tập lỗi hiểm trọng và nghiệm thu độc lập. Bộ 190 bài kiểm thử tổng hợp chỉ xác nhận quy tắc/phần mềm hoạt động như thiết kế.
- Không tạo tài khoản Cloud, không bật thanh toán, không ghi tài liệu lên GitHub/Drive, không bật quyền duyệt hồ sơ.
