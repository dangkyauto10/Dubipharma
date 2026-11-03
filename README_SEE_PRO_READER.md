# SEE PRO READER — Bộ mã nguồn gốc đọc và trích xuất tài liệu

**Nguồn:** [dangkyauto10/Dubipharma](https://github.com/dangkyauto10/Dubipharma), nhánh `tdv-qc7-online-preview-20261020` tại commit `d680f4addb740bba043c7a15d57000beaa1d298b` (bản SEE PRO Preview J).

**Tình trạng:** Bộ mã gốc được bóc tách để nghiên cứu và tái sử dụng trong SEE PRO READER. Toàn bộ `39` tệp Python nghiệp vụ và `30` tệp kiểm thử được sao chép **nguyên nội dung**, giữ SHA Git tương ứng trong `SOURCE_MANIFEST.json`. Không chỉnh sửa thuật toán, parser hoặc bảng đối chiếu.

## Bộ đọc tài liệu (Python, phía máy chủ)

| Nhóm | Mã nguồn gốc |
| --- | --- |
| Đọc PDF/Word/Excel/CSV/ảnh và OCR | `see_pro_multiformat.py`, `tdv_real_intake.py`, `see_pro_adapters.py` |
| Đọc PDF và bảng kỹ thuật E-HSMT | `tdv_ehsmt_intake.py`, `tdv_ehsmt_xlsx.py`, `see_pro_pdf_geometry.py` |
| Nhận diện hồ sơ, bảng và trường dữ liệu | `see_pro_structured.py`, `see_pro_notice.py`, `see_pro_workbench.py` |
| Đọc nhà sản xuất (NSX), thuốc, GMP, báo giá | `tdv_nsx_auto.py`, `tdv_nsx_intake.py`, `tdv_nsx_adaptive.py`, `tdv_nsx_multisheet.py`, `tdv_nsx_workbench.py` cùng các bộ kiểm tra chứng cứ NSX |
| Truy xuất chứng cứ, số trang/ô nguồn | `see_pro_traceability.py`, `see_pro_quality_gate.py`, `tdv_tender_trace.py`, `tdv_tender_context.py` |
| Đối chiếu E-HSMT và NSX | `tdv_leadership_report.py`, `tdv_comparison_ui.py`, `tdv_see_pro_leadership.py`, `tdv_see_pro_scope.py` |
| Quy tắc đọc đa tầng PDF | `tdv_idp3_rules.py`, `tdv_idp3_workflow.py` |
| Bộ đọc/duyệt chứng cứ có tùy chọn AI | `see_pro_ai_review.py` (có thể gửi các đoạn trích đến dịch vụ ngoài khi được cho phép) |

Các tệp hỗ trợ khác được giữ trong gói để không mất phụ thuộc mã nguồn. Kiểm tra `SOURCE_MANIFEST.json` để thấy danh sách đầy đủ và SHA chính xác từng tệp.

## Quy tắc tách dùng cho SEE PRO READER

1. **Giữ nguyên các bộ đọc gốc.** Tạo thêm một lớp API phía máy chủ để nhận tệp, trả nội dung dạng văn bản có cấu trúc và thông tin nguồn.
2. **Tích hợp đọc thành tiếng (Text-to-Speech) là bước mới**, không sẵn trong bộ mã gốc này. Muốn đọc trên Boox hoặc TV Samsung nên dùng frontend web, server Python đảm nhiệm đọc và trích xuất tài liệu; thiết bị khách nhận văn bản/âm thanh qua mạng.
3. **Không đưa kho hồ sơ mật hay API key vào web công khai.** Các chức năng tự phân tích bằng AI bên ngoài phải có bước đồng ý riêng.
4. `requirements.txt` và `packages.txt` là tệp phụ thuộc gốc; `requirements-reader.txt` là danh sách tham khảo rút gọn, không thay thế việc kiểm thử tương thích khi triển khai.

## Giới hạn của gói

- Đây là **mã nguồn gốc bộ đọc**, chưa phải ứng dụng SEE PRO READER đã có thể cài trực tiếp trên TV hoặc Boox.
- Giao diện cũ dùng Streamlit và phụ thuộc bộ nhớ phiên; khi tích hợp ứng dụng mới cần tạo API, phiên làm việc, xác thực và lưu trữ phù hợp.
- Một số bài kiểm thử gốc tham chiếu tới giao diện SEE PRO cũ, nên không nhất thiết chạy độc lập chỉ với gói này.
- Không đóng gói mật khẩu, thông tin đăng nhập, `.streamlit/secrets.toml`, tệp E-HSMT/NSX tải lên hoặc dữ liệu khách hàng.
- Nhánh `main` và Preview J ban đầu không bị sửa khi tạo gói trích xuất.
