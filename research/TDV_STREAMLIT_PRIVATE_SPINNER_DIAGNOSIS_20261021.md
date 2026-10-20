# TDV QC7 ONLINE — Kết quả chẩn đoán màn hình quay Streamlit (21/10/2026)

## Nguyên tắc bảo vệ dự án

- Preview **PRIVATE** là cấu hình có chủ đích; không được chuyển Public.
- Không đụng `main`, Preview, SEE PRO hay Google Drive để thử sửa mò.
- Lần thử browser ẩn danh **không đủ để xác nhận** một ứng dụng PRIVATE bị hỏng.

## Các phép thử đã hoàn thành

1. **GitHub code regression, Preview SHA `87e8e8947d6aad62969160d877ad9c69bb04f3cb`:** 148/148 unittest PASS. Run: https://github.com/dangkyauto10/Dubipharma/actions/runs/39499326404. Điều này **không** chứng minh môi trường Streamlit Cloud chạy.
2. **Khởi động máy chủ thực**: GitHub Actions đã checkout **đúng Preview SHA**, cài đầy đủ `requirements.txt`, chạy `python -m streamlit run app.py`. `/_stcore/health` trả `200 'ok'`.
3. **Dùng Chromium thật trên máy chạy độc lập**: mở trang chủ TDV QC7, nhìn thấy nội dung; click mục Báo giá & hồ sơ NSX thành công. Browser test `LOCAL_BROWSER_SMOKE_PASS`; không phát hiện JavaScript `pageerror` hoặc console.error. Run: https://github.com/dangkyauto10/Dubipharma/actions/runs/39502440005.
4. **Trình duyệt không có phiên đăng nhập truy cập Preview đang PRIVATE**: bị đưa sang `share.streamlit.io` và được yêu cầu đăng nhập (đúng với mô hình Private). Không được dùng hiện tượng này làm lỗi phân quyền.
5. **Ảnh do V cung cấp, Chrome đăng nhập nhưng spinner vô hạn**: **chưa** có browser Cloud logs khi đã xác thực để phân biệt lỗi provisioning, backend, runtime hoặc websocket.
6. **Tài liệu hiện hành của Streamlit**: `https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app` ghi Cloud logs là kênh chính để xử lý lỗi vận hành. Các topic tháng 10/2026 báo app Private spinner vô hạn, manager provisioning/lỗi proxy và logs trống, ví dụ `https://discuss.streamlit.io/t/private-community-cloud-app-stuck-at-spinning-up-manager-process/122748`, `https://discuss.streamlit.io/t/private-app-stuck-loading-http-500-on-running-status-and-empty-logs/122730`; đây là bằng chứng bối cảnh, **không xác định** trạng thái app TDV.

## Kết luận có thể kiểm chứng

**Mã Preview hoạt động độc lập; sự cố Cloud chưa được xác định và không đủ cơ sở thay đổi code/quyền chia sẻ.** Bước cần thông tin riêng của tài khoản quản trị: **Cloud logs đúng ứng dụng** `dubipharma · tdv-qc7-online-preview-20261020 · app.py` khi spinner. Chụp phần đuôi log, không cần tiết lộ password/token.

Nếu log **không có sự kiện Clone/Install/Starting** → nghi provisioning/Cloud trước khi Python chạy.
Nếu log có **Python Traceback hoặc ModuleNotFoundError** → sửa lỗi phụ thuộc/runtime có kiểm thử trước, không phá SEE PRO.
Nếu log nói **Listening/Running nhưng browser spinner** → xem WebSocket/browser console và proxy Cloud.
Chỉ cân nhắc **Reboot chính Preview** sau khi xác định trạng thái, biết rằng reboot tạm ngắt người đang sử dụng; **không** đổi thành Public, **không** xóa/redeploy mù.

## Trạng thái repo

- Nhánh chẩn đoán: `tdv-see-pro-nsx-public-corpus-20261021`.
- Preview vẫn `87e8e8947d6aad62969160d877ad9c69bb04f3cb` lúc kiểm tra.
- Main vẫn `d811cf4e33c567bae3fd5bfa8e712313c294cee5`.
- Không có thao tác ghi Google Drive/Sheets.
