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

| 026 | `TDV_BACKUP_026_BEFORE_NSX_VISIBILITY_20261022` | `457a9039c35667c1005cb3d4b63a66d1ffa92deb` | Trước sửa lỗi bảng hai nguồn không hiển thị trên bản Streamlit thực tế dù mã có và GitHub CI đã thành công; hình V chụp chứng minh bản chạy chỉ có bảng 29 ứng viên và không có giá trị nguồn hai bên |
| 027 | `TDV_BACKUP_027_NSX_VISIBILITY_20261022` | `a3f46f23b30703b2b00069d32fbf4170ccee0906` | Sau sửa: bảng hai nguồn được mở mặc định và đứng trước danh sách 29 ứng viên; thêm dấu nhận diện bản chạy 2026-10-22B, lỗi thiếu cặp nguồn phải thông báo; test renderer trực tiếp; 220/220 unit tests và OIDC fail-closed |

| 028 | `TDV_BACKUP_028_BEFORE_VISIBLE_BUILD_20261022` | `9e55c47c25b1f72aab73bee54ac18b53d40f7581` | Sao lưu trước bổ sung mã bản nghiệp vụ ở ĐẦU trang NSX, giúp kiểm tra liệu Streamlit Cloud đã đồng bộ bản code mà không cần nạp lại 14 file |
| 029 | `TDV_BACKUP_029_NSX_VISIBLE_BUILD_20261022` | `c28d1b695c533d7375e6f2ca7c27deb58b92d31d` | Trang NSX hiện `PHIÊN BẢN NGHIỆP VỤ NSX: 2026-10-22B` trước uploader, kiểm tra trực tiếp renderer ngay cả khi chưa nạp hồ sơ; 221/221 unit + bảo vệ OAuth fail-closed |

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


## Lỗi vận hành quan sát trong ứng dụng NSX (22/10/2026)
- Ảnh người dùng chỉ hiển thị expander “Các dòng có trường mâu thuẫn — cần đối chiếu” gồm 29 mã; không có khối “Giá trị gốc cần đối chiếu — nguồn 1 so với nguồn 2” bên dưới hay bên ngoài. Không được tiếp tục hướng dẫn tìm kiếm một phần không hiển thị.
- GitHub Preview branch đã chứa renderer, nhưng điều đó và CI không khẳng định Streamlit Community Cloud đang chạy đúng commit; không có quyền truy cập Cloud log/deployment để xác minh. Cần phân biệt code availability vs deployed runtime.
- Bản sửa tăng khả năng quan sát: render expander “ĐỐI CHIẾU 2 NGUỒN GỐC” expanded=True trước bảng tổng hợp; hai giá trị và ô nguồn xuất hiện ở bảng đầu tiên; bảng SHA/file gốc riêng. Caption `NSX · PHIÊN BẢN ĐỐI CHIẾU NGUỒN 2026-10-22B` cho biết live app đã tải mã mới; thiếu nguồn sẽ báo rõ.
- Bổ sung test giả lập trực tiếp `render_nsx_conflict_review` với 2 nguồn có 50 mg và 100 mg, kiểm soát vị trí/độ ưu tiên/mã build, tính fail-closed nếu không tạo được bảng; 220/220 tổng thể pass. Chưa có xác nhận trực quan từ Cloud; admin có thể phải reboot đúng app nếu mã không đồng bộ. Bảo toàn dữ liệu file gốc, không chỉnh SĐK/GMP, không làm thay đổi số ứng viên.


### Giới hạn phiên bản thực tế
- GitHub Actions trên nhánh Preview là KIỂM THỬ MÃ NGUỒN, không phải kiểm chứng runtime Streamlit Cloud. Một khi người dùng vẫn nhìn thấy giao diện cũ, cần xem app deployment, GitHub branch liên kết, Cloud log hoặc thực hiện Reboot app sau khi lưu dữ liệu phiên.
- Nhằm tránh bắt người dùng nạp lại 14 tài liệu để tìm bản cập nhật, mã phiên bản NSX được hiển thị ngay khi mở trang, kể cả không có uploads. Phiên bản đúng phải có `2026-10-22B` gần tiêu đề SEE PRO.


## Tích hợp kiểm tra chứng cứ NSX vào phân hệ thật — 22/10/2026
- BACKUP_030 trước khi sửa: `TDV_BACKUP_030_BEFORE_NSX_EVIDENCE_INTEGRATION_20261022`. BACKUP_031 sau thay đổi mã: `TDV_BACKUP_031_NSX_EVIDENCE_INTEGRATED_20261022`. Chỉ sửa `tdv-qc7-online-preview-20261020`, không sửa `main`; dùng một ứng dụng hiện tại.
- Trang “🛡️ Chứng cứ nhà sản xuất” trước đây là kiểm tra theo lựa chọn ví dụ Mỹ Thới/Bình Hòa, không đọc thực tế bộ hồ sơ NSX. Đã bỏ lối vào DEMO riêng, đưa việc rà soát trực tiếp vào phần **3B. Kiểm tra chứng cứ nhà sản xuất** của `💊 Báo giá & hồ sơ NSX`, chạy khi có `tdv_nsx_auto_report` sau đọc tệp.
- Bộ rà soát `tdv_manufacturer_evidence.audit_manufacturer_evidence` chỉ dùng `report.sources`, `report.products` và liên kết sơ bộ `report.links`; đọc SĐK, giấy GMP, giải trình, ủy quyền, báo giá. Nêu thiếu trích dẫn/định danh, sai khác nhà máy/SĐK/NSX ở liên kết sơ bộ; ghi vị trí nguồn, SHA256 được trích từ hồ sơ; **không tự kiểm tra tính xác thực pháp lý hay tính đúng SHA so với bytes gốc tại bước này**.
- Không phê duyệt GMP, SĐK, ủy quyền, giá, thầu. Giải trình GMP không thay thế chứng nhận. Chỉ hiện **CHƯA XÁC MINH**. Không gộp hoặc sửa 47 ứng viên/29 trường hợp nguồn mâu thuẫn/0 liên kết đã được báo cáo.
- Bổ sung sheet Excel `KIEM_TRA_CHUNG_CU_NSX`, dùng bộ định dạng và `safe_cell` sẵn có; không ghi Drive/Sheets và không tạo tài liệu hồ sơ thật trong GitHub.
- Bộ test mới `test_tdv_manufacturer_evidence.py`: 6/6 tình huống đạt trên máy kiểm thử (GMP sai nhà máy, giải trình, SĐK thiếu, SHA nguồn không nhất quán, chứng cứ chưa liên kết, tài liệu OTHER không bị gán nhầm). Bài thử bổ sung bằng report nhân tạo 47/29/0 xác nhận không thay đổi dữ liệu và luôn giữ chưa xác minh.
- Giới hạn: chưa có kiểm thử với 14 tệp NSX gốc, chưa có xác minh Streamlit Cloud triển khai mã mới. GitHub commit hiện không báo status CI; **không được coi nhánh có mã hoặc bài thử nhân tạo là nghiệm thu runtime**. IDP 3.0 ở mục riêng vẫn là bài kiểm tra DEMO, chưa được coi là bộ đọc đa tầng đã triển khai đầy đủ cho dữ liệu thật.


## Sửa lớp phân loại GMP trong luồng NSX — 22/10/2026
- BACKUP_035 trước sửa: `TDV_BACKUP_035_BEFORE_GMP_CORE_GUARD_20261022`. Mã chính vẫn chạy trên **cùng app Streamlit Preview**, nhánh `tdv-qc7-online-preview-20261020`; `main` không đổi.
- Tích hợp `tdv_nsx_gmp_guarded_auto.analyze_auto` vào lệnh đọc NSX hiện hữu. Sau khi đọc, đối chiếu loại `GMP_CERT` nghi vấn bằng nội dung chữ sẵn có ở tối đa hai trang đầu và dấu hiệu hạn chế từ tên tệp. Không dùng tên tệp để xác nhận loại hợp lệ; PDF quét không đủ chữ -> xếp `OTHER` để kiểm tra, không tự suy đoán.
- Nếu văn bản thể hiện rõ giải trình/xác nhận duy trì GMP, phân loại sơ bộ `GMP_EXPLANATION`; nếu thiếu rõ ràng hoặc chữ chứng nhận mâu thuẫn, chuyển `OTHER`. Xóa mọi liên kết GMP sơ bộ đã tạo từ tệp được đổi loại; đưa vào hàng đợi `CAN_XAC_DINH_LOAI_GMP`, tính lại số liên kết, gợi ý GMP, thống kê và truy xuất ngược.
- Báo cáo mục 3B vẫn giữ các tệp `OTHER` do kiểm soát GMP chuyển vào, đánh dấu **CẦN XÁC ĐỊNH LẠI LOẠI VĂN BẢN GMP**. Excel `KIEM_TRA_CHUNG_CU_NSX` dùng cùng audit; không sửa số thuốc, trường nguồn hoặc tự phê duyệt.
- Phiên bản quan sát trực tiếp sau triển khai dự kiến là `2026-10-22C`. Đã có 8/8 bài thử cục bộ trên báo cáo giả lập, bao gồm tình huống SHA tệp không khớp và giữ 47 ứng viên, 29 nhóm mâu thuẫn, 51 cặp so nguồn. `test_tdv_nsx_gmp_guarded_auto.py` được đưa vào repo, **chưa có xác nhận GitHub CI**.
- Giới hạn chưa nghiệm thu: chưa kiểm thử với đủ 14 tệp gốc, chưa xác nhận Streamlit Cloud nạp mã C, văn bản scan không đọc được chữ phải kiểm tra thủ công; chưa giải quyết triệt để trích trường SĐK/GMP qua OCR và đối chiếu E-HSMT.


## NSX bản D — tìm giá trị SĐK/GMP có nhãn chưa được trích chắc chắn (22/10/2026)
- Sao lưu **trước sửa**: `TDV_BACKUP_037_BEFORE_SDK_GMP_EXTRACTION_20261022`; thao tác chỉ trên nhánh Preview hiện tại, `main` và OAuth/Secrets không thay đổi. Chỉ một ứng dụng TDV QC7 ONLINE.
- Bộ quét mới `tdv_nsx_proof_hints.py` chỉ tìm theo nhãn rõ trong chữ PDF/OCR đã được đọc, cùng trang hoặc ngay cùng dòng, không đoán từ tên tệp hay suy thuốc tương đương. Với giấy SĐK kiểm tra tên thuốc có nhãn và SĐK; với GMP kiểm tra số GMP, phạm vi, ngày hết hạn **ghi trong văn bản**.
- Gợi ý được lưu `source.proof_hints` **tách khỏi** `fields`/`evidence`. Không thêm sản phẩm, không thay SĐK/GMP chính, không tự tạo liên kết, không phê duyệt. Nhiều giá trị cùng trường giữ cả hai và cảnh báo. Giới hạn 18 gợi ý/tệp được thông báo, không tuyên bố đầy đủ.
- Mục 3B trong hồ sơ NSX có bảng nguồn gốc cho gợi ý trích nhãn. Excel NSX bổ sung sheet `GOI_Y_NHAN_SDK_GMP` (tệp, loại tài liệu, trường, giá trị, vị trí, trích gốc, phương pháp, SHA256, trạng thái).
- Caption phiên bản `2026-10-22D` xác định Streamlit Cloud đã nhận cập nhật khi quan sát được trên app. Cảnh báo bảo mật sửa từ `chưa đăng nhập` thành `đã có Google OIDC cơ bản nhưng chưa có phân quyền dự án và kho hồ sơ đạt chuẩn doanh nghiệp`.
- **14/14 bài kiểm thử đơn vị cục bộ đạt** với mã helper và file tests có Git blob SHA khớp chính xác GitHub; 3 bài kiểm thử luồng `test_tdv_nsx_proof_hints_flow.py` đã thêm nhưng **chưa chạy tích hợp**. GitHub CI và triển khai trực tiếp trên Streamlit chưa được xác nhận; chưa có dữ liệu gốc 14 tệp để nghiệm thu.
- Các mốc 14 tệp, 87 dòng nguồn, 47 ứng viên, 29 trường hợp mâu thuẫn, 51 cặp gốc, 0 liên kết là **kết quả test trước**, không phải kết quả sau sửa D. Giữ trạng thái pháp lý chưa xác minh và cảnh báo nghiệp vụ.


## NSX E — Khắc phục nhãn SĐK/GMP bị bỏ sót khi PDF xuống dòng (22/10/2026)
- Sao lưu trước sửa `TDV_BACKUP_039_BEFORE_SDK_GMP_HINT_REPAIR_20261022`; chỉ cập nhật nhánh `tdv-qc7-online-preview-20261020`, không thay đổi `main` hoặc cấu hình OAuth/Secrets, không tạo ứng dụng thứ hai.
- Phát hiện lỗi thực tế trong helper: dấu hai chấm kết thúc nhãn `Số đăng ký:`, `Số đăng ký lưu hành (SĐK):`, `Tên thuốc (biệt dược):` ngăn so khớp nhãn với giá trị ở dòng sau. Đã chuẩn hóa nhãn trước khi đối chiếu, thêm biệt danh có nhãn, bảo toàn giá trị và vị trí gốc.
- Hạn chế nhiễu: từ chối ngày dạng 20/10/2026 nếu bị nhận là SĐK/số GMP; không suy ra mã từ chuỗi không nhãn; không ghép hai trang; cho phép dấu cách quanh dấu gạch trong gợi ý nhưng không sửa giá trị nguyên văn; giữ nhiều giá trị nghi vấn.
- `tdv_nsx_intake._read_one` ghi `proof_diagnostic` cùng `proof_hints`, **không** tự điền vào trường thuốc/SĐK/GMP, không tăng liên kết hoặc phê duyệt. Excel bổ sung `CHAN_DOAN_DOC_SDK_GMP` với số trang, dòng đọc được, dòng OCR, trường chưa trích được, số gợi ý và trạng thái `CHUA_XAC_MINH`; giữ sheet `GOI_Y_NHAN_SDK_GMP`.
- Caption nghiệp vụ NSX `2026-10-22E`. Không sửa cấu trúc giao diện hay tự gán chứng cứ. Giữ 47 ứng viên và 29 nhóm mâu thuẫn để kiểm tra thực tế, không tuyên bố đã kiểm chứng lại chúng.
- 21/21 bài thử cục bộ đã chạy và đạt (17 đơn vị + 4 đọc PDF giả lập qua PyMuPDF). Sáu test bổ sung trong `test_tdv_nsx_proof_hints.py` và hai test nối luồng trong `test_tdv_nsx_proof_hints_flow.py` đã được đưa vào repo, nhưng chưa có xác nhận GitHub CI.
- Chưa nghiệm thu với chính 14 tệp NSX gốc, chưa xác nhận Cloud đã nạp E. Chưa xác minh số SĐK, nhà máy, số/phạm vi/hiệu lực GMP hay điều kiện dự thầu. Không tự kết luận các hồ sơ AGICARVIR, AGIMOL 150 hoặc GCN GMP đủ hay thiếu pháp lý khi chưa đọc bản gốc.


## NSX F — chẩn đoán OCR dựa trên Excel thực tế (22/10/2026)
- Nguồn đầu vào đối soát: `TDV_NSX_SEE_PRO_KIEM_TOAN(1).xlsx` do người vận hành tải về từ TDV QC7 bản E. **Không tải workbook hoặc tài liệu pháp lý gốc lên GitHub.**
- Số liệu xác nhận trong Excel: 14/14 tệp, 87 dòng nguồn, 47 ứng viên, 29 ứng viên có 51 cặp giá trị nguồn mâu thuẫn (24 `DOSAGE_FORM`, 23 `STRENGTH`, 4 `ROUTE`), 0 liên kết; 46 dòng cần xem, trong đó có 29 dòng mâu thuẫn và 2 dòng loại GMP cảnh báo mới.
- `GOI_Y_NHAN_SDK_GMP` chỉ có hàng tiêu đề, số gợi ý là 0 cho cả 5 tài liệu trong `CHAN_DOAN_DOC_SDK_GMP`. AGICARVIR đọc 1.007 dòng (554 OCR), AGIMOL 150 đọc 852 dòng (527 OCR), GCN GMP 2023 đọc 141 dòng; **không được suy rằng bản gốc không có SĐK/GMP**.
- Hai văn bản bổ sung GMP đã mang nhãn `OTHER` trong `TU_DONG_NHAN_DIEN` nhưng cảnh báo cũ trong `CAN_XAC_MINH` còn gán nhãn `GMP_CERT`. NSX F đồng bộ nhãn dòng cảnh báo cũ sang loại sau rà soát (chỉ khi tên tệp duy nhất) và giữ lại lý do gốc, trạng thái, lịch sử nguồn. Không đụng đến 29 mâu thuẫn.
- Đã bổ sung `proof_contexts` chỉ đọc, trích tối đa 24 dòng có từ khóa trên mỗi PDF (giới hạn 5 dòng mỗi nguồn/trang), kèm dòng trước/sau **cùng trang**, SHA-256 từ tệp. Xuất Excel `DOAN_OCR_CAN_SO` để đối chiếu nguyên văn khi chưa tìm được nhãn SĐK/GMP. Không gán các đoạn này thành giá trị SĐK/GMP, không tự liên kết hoặc duyệt giấy.
- Bản nhận biết `2026-10-22F`, sao lưu trước sửa `TDV_BACKUP_043_BEFORE_OCR_REVIEW_20261022`. Pipeline GitHub Actions `tdv-nsx-preview-quality.yml` chỉ kiểm thử bằng dữ liệu tổng hợp, không dùng Secrets, không gửi dữ liệu pháp lý.
- **Chưa nghiệm thu**: cần xem GitHub Actions, Streamlit Cloud nhận bản F, lần test 14 tệp NSX và các dòng OCR thực tế trong Excel. SĐK, hiệu lực GMP, nhà máy và đáp ứng E-HSMT vẫn CHƯA XÁC MINH. `main` và OAuth/Secrets không chỉnh sửa.


## NSX G — chặn nhận nhầm tiêu đề bảng OCR thành tên thuốc/hàm lượng (22/10/2026)
- Bằng chứng trực tiếp từ workbook kết xuất E: `TRUY_XUAT_TUNG_TRUONG` ghi `PRODUCT_NAME` của AGICARVIR và AGIMOL 150 bằng phần tiêu đề bảng OCR `Hoạt chất chính- | Dạng bào ... | Sốđăngký`; `STRENGTH` AGIMOL có `chế`/các mảnh tiêu đề. Đây là trích sai cấu trúc, KHÔNG phải thuốc hay hàm lượng đã xác minh.
- Bản G sửa `_evidence_pair` và `_consecutive_pdf_fields`: chỉ cho phép cặp nhãn–giá trị hai cột khi thực sự là hai cột, từ chối ký tự phân cách bảng `|` hoặc từ khóa tiêu đề bị coi là giá trị; giữ nguyên trích gốc/OCR để đối chiếu. Các cặp `Trường: Giá trị` có cấu trúc riêng vẫn đọc được.
- Phân hệ gợi ý OCR chỉ dùng `sodangky` như tín hiệu tìm đoạn văn cần so bản gốc, tuyệt đối không tự suy SĐK từ hàng tiêu đề hay từ tên tệp.
- Thêm hồi quy tổng hợp cho bảng OCR cắt sai và nhãn+giá trị PDF hợp lệ; không tự tăng số sản phẩm hay kết luận GMP/SĐK. Version `2026-10-22G`.
- Sao lưu trước sửa `TDV_BACKUP_046_BEFORE_OCR_HEADER_FIX_20261022`. `main` giữ nguyên. Trạng thái nghiệm thu nghiệp vụ: CHƯA XÁC MINH trên 14 tệp nguồn; CI phải chạy lại bản G trước khi yêu cầu người vận hành test.


## NSX H — bảo vệ trích xuất OCR và gợi ý mã SĐK theo ngữ cảnh (22/10/2026)
- BACKUP_050 trước sửa: `TDV_BACKUP_050_BEFORE_OCR_SDK_HINT_REPAIR_20261022`. Chỉ sửa Preview của một TDV QC7 ONLINE, `main` không đổi.
- Phân tích trên Excel kết xuất bản G (không tải tệp hồ sơ và dữ liệu pháp lý lên GitHub) phát hiện tiêu đề bảng nhiều cột bị nhận thành gợi ý `PRODUCT_NAME` và mảnh tiêu đề không có con số bị nhận thành `STRENGTH`. Cả hai phải được chặn.
- `tdv_nsx_proof_hints.extract_labeled_hints`: từ chối giá trị gợi ý tên thuốc/GMP_SCOPE có dấu ngăn bảng `|`; phát hiện mã `VD/VN` với dấu chấm/gạch qua ngữ cảnh đăng ký cùng dòng hoặc ngay dòng trước cùng trang, không đoán từ nhãn bảng hay trang khác. Nhiều cách viết của cùng mã chỉ là bản ghi nguồn khác nhau, không phải hai mã trái ngược.
- `tdv_nsx_intake`: trường `STRENGTH` bắt buộc có chữ số khi parse scalar OCR, không lấy từ một từ/mảnh tiêu đề; các giá trị thật có chữ số vẫn bảo toàn trích dẫn.
- Tất cả mã mới trong `proof_hints` là GỢI Ý, chưa xác minh, có trang/SHA256/trích nguyên văn, không tự ghi vào `fields`, không tạo liên kết chứng cứ, không kết luận pháp lý/đủ điều kiện dự thầu.
- Mã quan sát trên ứng dụng: `2026-10-22H`. Kiểm thử hồi quy bổ sung cho tiêu đề nhiều cột, SĐK OCR cùng dòng/sát dòng và cùng trang, mã khác nhau, bản viết khác dấu, hàm lượng mảnh tiêu đề, hàm lượng hợp lệ. Chỉ đưa bản này lên Preview sau khi so sánh với backup và chờ CI kiểm thử lại; không tuyên bố nghiệm thu với tệp pháp lý gốc.


## NSX I — Tách câu thành phần OCR khỏi trường hoạt chất (22/10/2026)
- Nguồn chứng cứ: Excel bản H tải từ Streamlit, 5 PDF có cùng SHA với các lượt G. Kết quả H: 4 gợi ý SĐK cho **2 mã** (`VD-25114-16`, `VD-22790-15`), không còn gợi ý tên thuốc giả/từ "chế", 0 liên kết chứng cứ, cả hai văn bản bổ sung GMP vẫn bị chặn tự coi là chứng nhận.
- Vấn đề mới: `TRUY_XUAT_TUNG_TRUONG` chứa `INGREDIENT` của AGICARVIR là toàn câu OCR `M6i vien AGICARVIR chira 0,5 mg Entecavir...` — không phải tên hoạt chất đơn lẻ. Bản I chặn riêng dạng câu mô tả thành phần này khỏi trường `INGREDIENT` trong PDF, **không suy thành Entecavir**; giữ nguyên trích đoạn/vị trí nguồn ở `rejected_scalar_candidates` và Excel `CAU_THANH_PHAN_CAN_SO`.
- Chẩn đoán `CHAN_DOAN_DOC_SDK_GMP` đổi từ thông báo "không có gợi ý" sang "đã có một phần gợi ý" khi mã SĐK đã tìm được nhưng tên thuốc có nhãn chưa đủ. Không sửa thông tin công ty hoặc GMP đã trích có mâu thuẫn.
- Cảnh báo pháp lý: Công văn giải trình GMP trong chính đoạn OCR có nhắc số chứng nhận và ngày hạn vào 01/2026. Đây là **nội dung do công văn nêu**, không thay kết quả xác minh bản gốc hoặc cơ quan cấp. Không tự quyết giấy hiện còn hiệu lực hoặc thuốc đáp ứng thầu.
- BACKUP_052 trước sửa: `TDV_BACKUP_052_BEFORE_PDF_INGREDIENT_SCALAR_REPAIR_20261022`. Một ứng dụng TDV QC7 ONLINE, chỉ cập nhật Preview sau soát mã/CI, `main` và OAuth/Secrets không thay đổi. Phiên bản dự kiến `2026-10-22I`.


## NSX J — chống tái sử dụng báo cáo từ phiên bản phân tích cũ (22/10/2026)
- Phát hiện trong file Excel bản I thực tế: `TRUY_XUAT_TUNG_TRUONG` vẫn ghi toàn câu OCR `M6i vien AGICARVIR chira 0,5 mg Entecavir...` vào `INGREDIENT`, `CAU_THANH_PHAN_CAN_SO` trống; `CHAN_DOAN_DOC_SDK_GMP` vẫn báo `CHUA_CO_GOI_Y_THEO_NHAN` dù có 4 dòng SĐK theo nguồn.
- Mã nguồn GitHub I của `tdv_nsx_intake` và `tdv_nsx_proof_hints` đã có cả hai thay đổi, kiểm thử tổng hợp đạt, nhưng UI lưu `tdv_nsx_auto_report` vào `session_state` với khóa cache **chỉ dựa trên tên và nội dung tệp**, không dựa trên phiên bản bộ phân tích. Đó là một cơ chế có khả năng tái hiển thị/phát hành báo cáo H dưới nhãn UI I nếu người dùng chưa thực sự chạy lại. Không khẳng định cơ chế cache là nguyên nhân duy nhất khi chưa có log tiến trình Streamlit Cloud.
- Bản `2026-10-22J` đặt dấu phiên bản ở `tdv_nsx_intake.py`, `tdv_nsx_proof_hints.py`, `tdv_nsx_auto.py`; bộ giao diện kiểm tra module nạp thực tế và **khóa phân tích/xuất Excel nếu không khớp**. Khóa kết quả có cả phiên bản + SHA256 dữ liệu; cache khác phiên bản bị hủy an toàn và yêu cầu nhấn đọc lại.
- `analysis_version` được đóng dấu ngay khi chạy `analyze_auto`; `analysis_fingerprint` chỉ tạo khi chạy từ giao diện. Sheet `PHIEN_BAN_XU_LY` trong Excel phân biệt phiên bản dữ liệu với phiên bản module xuất, nêu bất đồng rõ ràng thay vì suy phiên bản từ nhãn UI. Dấu vân tay không chứa văn bản hồ sơ gốc.
- 5 bài test mới `test_tdv_nsx_runtime_cache.py` kiểm tra thay phiên bản làm đổi chữ ký, báo cáo thiếu phiên bản/dấu vân tay bị từ chối, module nạp cũ bị chặn. Workflow CI Preview bổ sung suite. `app.py` chỉ đổi chú thích đồng bộ để kích hoạt làm mới, không thay OAuth, phân quyền hoặc nghiệp vụ.
- Sao lưu trước `TDV_BACKUP_054_BEFORE_NSX_CACHE_VERSION_FIX_20261022`. Chưa nghiệm thu thực tế đối với 5 PDF cho đến khi Cloud hiện J và Excel mới có `PHIEN_BAN_XU_LY`; trường SĐK/GMP, hiệu lực giấy vẫn `CHUA_XAC_MINH`. `main` không đổi. Không tải nội dung PDF hoặc Excel của người dùng lên GitHub.
