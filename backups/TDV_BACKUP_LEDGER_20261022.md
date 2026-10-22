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

| 018 | `TDV_BACKUP_018_BEFORE_GOOGLE_AUTH_20261022` | `63c64dc227abb0843e01d327783ea8c9d384b547` | Preview trước khi thêm đăng nhập; bảo mật hồ sơ chưa tích hợp |
| 019 | `TDV_BACKUP_019_GOOGLE_AUTH_20261022` | `5c16fda1f064fdde84f482235eb938691dc761a9` | Google OIDC fail-closed; chỉ email Google được xác minh và cho phép, vai trò admin/analyst/viewer; chặn toàn bộ nếu thiếu Secrets; GitHub CI 199/199 và AppTest khóa không có Secrets đạt; cần V tự cấu hình Google OAuth và Streamlit Secrets để thực sự đăng nhập |

| 020 | `TDV_BACKUP_020_BEFORE_EHSMT_QA_20261022` | `2d2d9fbf05c6c688b9312fc6b191306024347caf` | Trạng thái trước sửa sau khi user chạy E-HSMT G1-SYT PDF thật: 1/1 tệp, 596 trang, 770 mã, 770/770 hoạt chất có giá trị nhưng 0/770 ghi trích dẫn riêng, bảng chất lượng báo 0 vấn đề dù có 1 cảnh báo; tài liệu bị phân loại KET_QUA_LCNT cần kiểm tra |
| 021 | `TDV_BACKUP_021_EHSMT_EVIDENCE_QA_20261022` | `f128228ba41e0806fbef0a7f539992c3dab99119` | Mã đã kiểm thử bằng PDF tạo tổng hợp: nguồn hoạt chất ghi tệp, trang, mã dòng, SHA256, đoạn gốc; trạng thái giữa bảng tổng hợp và kỹ thuật; cảnh báo nếu phân loại BANG_EHSMT_PDF / KET_QUA_LCNT mâu thuẫn; quality gate đếm lỗi thiếu chứng cứ & các cảnh báo chưa xử lý; Excel và so sánh truy xuất trang PDF; 206/206 bài kiểm thử + fail-closed Streamlit |

| 022 | `TDV_BACKUP_022_BEFORE_TABLE_UI_20261022` | `62b0f2b30a11b174b233b98d8c36de16646fe21c` | Sao lưu trước yêu cầu căn giữa/đậm rõ ba bảng E-HSMT và chuẩn hóa giao diện các trang nghiệp vụ |
| 023 | `TDV_BACKUP_023_READABLE_TABLES_20261022` | `964cbc52806766a5a5a075700cf68b62a0adde7e` | Bản mã UI được kiểm thử 213/213: header căn giữa, giá trị ngắn/số căn giữa, văn bản dài tự xuống dòng, giữ SHA đầy đủ, bảng 770 mã chia trang; E-HSMT/NSX/Báo cáo Lãnh đạo; không thay dữ liệu, bộ so sánh màu, đăng nhập |

| 024 | `TDV_BACKUP_024_BEFORE_NSX_SOURCE_DIFF_20261022` | `002c4b2bad05e93fc5f76e68a4e028dbf0592fd9` | Trạng thái Preview trước sửa sau kiểm thử 14 tệp NSX, 47 ứng viên từ 87 dòng, 29 ứng viên xung đột và 0 liên kết SĐK/GMP; không khẳng định dữ liệu đã xác minh |
| 025 | `TDV_BACKUP_025_NSX_SOURCE_DIFF_20261022` | `c32ed6a10b4b57d82e8f1139e1ea04e1b67946a9` | Phiên bản bổ sung bảng hai giá trị gốc theo sheet và Excel audit riêng `MAU_THUAN_GIA_TRI_GOC`, không tự hợp nhất hay kết luận thuốc hợp lệ, 218/218 unit tests và OIDC fail-closed |

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


## Cổng xác thực Google — 22/10/2026

- Chỉ dùng **một** TDV QC7 Streamlit Preview, cùng repository; `main` không thay đổi.
- Phân hệ đăng nhập: `tdv_auth.py`, Google OIDC qua Streamlit `st.login/st.user/st.logout`, phiên token Google phải đủ issuer, audience, email_verified, subject, iat, exp hợp lệ. Email phải có trong `[tdv_access.roles]` lưu tại Streamlit Cloud Secrets.
- Bảo vệ mặc định: nếu thiếu hoặc cấu hình sai Secrets, người truy cập chỉ nhìn thấy **TDV QC7 ĐÃ KHÓA**, không thấy menu E-HSMT/NSX/Upload/báo cáo.
- Người dùng `viewer` không thể mở các phân hệ nạp/đọc và Google Sheets. `admin` và `analyst` chỉ có quyền thao tác ở màn hình hiện tại; không phát sinh quyền duyệt pháp lý hoặc quyền ghi Drive.
- Khi đổi danh tính Google, xóa dữ liệu công việc `tdv_*` khỏi Streamlit session; nút Đăng xuất xóa session.
- Tài liệu cấu hình: `docs/TDV_GOOGLE_OIDC_SETUP_20261022.md`, trong đó có URI callback đúng cho **cùng app**.
- Khoá OAuth và Cookie Secret không được đưa lên GitHub; `.gitignore` đã bổ sung loại trừ `.streamlit/secrets.toml` và .env.
- Đăng nhập thực bằng 2–3 tài khoản chưa thể nghiệm thu ở môi trường GitHub Actions vì không có và **không được thu thập** OAuth Client Secret của V. V phải tạo OAuth Client trên Cloud hiện có và nhập thông số trong **Settings → Secrets** của app đang chạy.
- Không xem Google OIDC là cơ chế ủy quyền cấp dự án hoàn chỉnh; đối với hồ sơ mật, vẫn cần đánh giá rủi ro Streamlit Community Cloud, Drive, lịch sử truy cập và sao lưu.
- Khôi phục: bản cũ `TDV_BACKUP_018_BEFORE_GOOGLE_AUTH_20261022` là **mã chưa có chốt đăng nhập**; nếu rollback, sẽ làm mất bảo vệ. Ưu tiên sửa OAuth/Secrets trước, không rollback về mã công khai khi có hồ sơ mật.


## Nghiệm thu E-HSMT G1-SYT — quan sát thực tế & sửa an toàn

- Ảnh người dùng 22/10/2026: tệp E-HSMT 2,4MB, 596/596 trang, 770 G1, 770 dòng tổng hợp, 770 dòng kỹ thuật, 770 kiểm tra khớp tiền và mã phân; hoạt chất 770 giá trị nhưng 0 giá trị báo có chứng cứ riêng; 1 cảnh báo tổng thể, quality gate trước sửa lại báo 0 vấn đề.
- Sai sót xác định từ mã: `HOAT_CHAT_HSMT` PDF được đọc từ `CHUNG_CU_BANG_TONG_HOP` có trang, nhưng `see_pro_workbench` chưa gắn EVIDENCE cho trường này; `see_pro_quality_gate.audit_ehsmt` không đưa độ thiếu chứng cứ và warnings vào issues.
- Sửa: khi nguồn bảng tổng hợp có đúng chuỗi hoạt chất, gắn `EVIDENCE.HOAT_CHAT_HSMT` với tệp, trang, số dòng, giá trị gốc, SHA; không tạo nguồn từ filename hoặc dữ liệu suy đoán. Thêm giá trị hoạt chất gốc cột kỹ thuật và đối chiếu CHUỖI để phát hiện khác biệt; không kết luận tương đương hóa học.
- Phân loại `KET_QUA_LCNT` trong khi parser nhận diện `BANG_EHSMT_PDF`: chuyển sang `CAN_XAC_MINH_LOAI`, giữ nguyên hai dấu hiệu mâu thuẫn, yêu cầu kiểm tra trang bìa; không tự tuyên bố E-HSMT/LCNT hợp lệ khi chưa so bản gốc.
- Bảng quality gate giờ ghi rõ số trường thiếu nguồn, cảnh báo chưa xử lý và số mã có chuỗi hoạt chất khác/trích thiếu giữa hai bảng. Không nâng 770 câu khớp hay trích dẫn thành 770 trường được chứng nhận chính xác.
- Thêm bài kiểm thử bằng PDF G1 dựng từ dữ liệu giả (không có tài liệu thầu riêng tư): nguồn hoạt chất, Excel tra trang, Word/báo cáo lãnh đạo, cảnh báo phân loại, kiểm đếm 770 tham chiếu vs kiểm định chính xác. GitHub Actions 206/206 bài và khóa Google OIDC fail-closed.
- Chưa có tệp PDF G1-SYT gốc trong môi trường phát triển để tự nghiệm thu lại; cần V chạy lại trong phiên đã được cấp quyền và kiểm tra bảng quality gate, trích dẫn trang, cảnh báo. Không gửi nội dung tệp thật lên GitHub.


## Chuẩn giao diện dữ liệu dùng chung — 22/10/2026
- Mục tiêu theo ảnh khoanh đỏ của V: tăng tương phản chữ và tiêu đề, header căn giữa hai chiều, ô số/mã/trạng thái căn giữa, nội dung tệp/nguồn/hướng xử lý dài căn theo dòng và tự xuống dòng, hàng có padding và gạch phân cách đều; trên màn hình hẹp cho phép cuộn ngang thay vì mất dữ liệu.
- Đã bổ sung `tdv_readable_tables.py` với HTML/CSS escape toàn bộ nội dung đầu vào, không script, không gọi API; tiêu đề cột đậm 13,5 px, dữ liệu 14 px và `vertical-align:middle`.
- Các bảng nguồn, tài liệu gói thầu, kiểm kê E-HSMT, tìm 770 mã, kiểm toán chất lượng, danh mục NSX, rà soát NSX và công việc ưu tiên lãnh đạo cùng mẫu hiển thị. Bảng xanh/vàng/đỏ trong SO SÁNH giữ nguyên vì có đánh giá màu nghiệp vụ và thanh tiến độ riêng.
- Trang danh mục lớn phân trang 25 dòng; có nút mở bảng native để xem, sắp xếp, sao chép nguyên giá trị. CSV/XLSX và dữ liệu phiên không bị chỉnh sửa; không ẩn/viết lại SHA256 hoặc chứng cứ dài.
- CI kiểm thử với 770 mã nhân tạo, tràn văn bản, HTML injection, email/khóa không lộ, phân trang và quyền Google fail-closed: 213/213 pass trên mã trước khi cập nhật nhật ký. **Chưa có ảnh chụp browser của bản UI mới**; cần V kiểm tra lại trên cùng ứng dụng Preview đang chạy.
- Không tạo Streamlit thứ hai, không thêm phí Cloud, không thay nhánh `main`, không bật phê duyệt GMP/SĐK/báo giá.


## NSX nghiệp vụ — truy xuất nguyên văn hai sheet, 22/10/2026
- Người dùng gửi các bảng trích xuất 14 tài liệu / 87 dòng danh mục / 47 ứng viên / 29 có mâu thuẫn / 0 liên kết / 44 chờ rà soát. Tên thuốc lặp giữa các sheet, nhiều thuốc khác nhà sản xuất với nhóm giấy chứng nhận Agimexpharm; chưa kết luận hệ thống sai vì 0 liên kết.
- Vấn đề cần giải: `STRENGTH`, `DOSAGE_FORM`, `ROUTE` trong 29 mã chỉ hiện tên trường mâu thuẫn; không thể kết luận từ bảng này sự khác biệt là thật hay do biểu mẫu.
- Sửa hẹp, fail-closed: `tdv_nsx_source_diff.compare_conflict_sources` trích *hai giá trị gốc* từ `source_rows` và `evidence`, hiển thị tên sheet/ô nguồn, tệp và SHA cho từng trường; nhiều sheet giữ đủ các cặp, không giấu chuỗi gốc. Lưu Excel `MAU_THUAN_GIA_TRI_GOC`; giữ `GOP_DONG_NHIEU_SHEET` và `TRUY_XUAT_TUNG_TRUONG`. Không thay số thuốc/gộp dòng, nguồn, GMP/SĐK, yêu cầu gói hay phán quyết.
- Lượt kiểm thử tổng hợp 218/218 đạt, OIDC fail-closed đạt; **chưa thử trực tiếp 14 tệp nguồn user vừa nạp**, phải kiểm tra bằng bản chạy thật sau đồng bộ Preview.
- Rủi ro còn phải nghiên cứu sau khi có giá trị hai bên: phương thức gộp dòng dựa tên+NSX/nhà máy hiện có thể tạo 29 nhóm mâu thuẫn. Cần rà lại nhóm này để phân biệt dòng sản phẩm thật khác hàm lượng/dạng bào chế với lỗi biểu; không được tự sửa hoặc xóa dữ liệu nguồn.
