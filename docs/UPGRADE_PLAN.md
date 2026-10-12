# UPGRADE_PLAN.md — Kế Hoạch Nâng Cấp & Tái Thiết Hệ Thống Toàn Diện

## 1. MỤC TIÊU & NGUYÊN TẮC THỰC THI
- Nâng cấp hệ thống Vietnam Stock Analyzer thành một nền tảng phân tích cổ phiếu đáng tin cậy, chính xác về số liệu, trung thực về báo cáo, minh bạch về mức độ không chắc chắn.
- Bảo vệ dữ liệu người dùng (`data/market.db`, file phân khúc `data/segments/`, báo cáo đã tạo).
- Thực thi theo từng bước có kiểm thử tự động xác nhận trước khi chuyển giao.

---

## 2. LỘ TRÌNH THỰC HIỆN TỪNG GIAI ĐOẠN

### Giai Đoạn 0: Baseline & Recovery (Đã hoàn thành)
- [x] Kiểm tra trạng thái Git (Branch `audit-rebuild`, base commit `17b76a2`).
- [x] Tạo bản sao lưu toàn vẹn SQLite: `data/market_backup_20261012_174222.db` (Kiểm định `ok`).
- [x] Cài đặt `pytest` trên môi trường Python 3.11.

### Giai Đoạn 1: Audit & Documentation (Đã hoàn thành)
- [x] Hoàn thành `docs/QA_AUDIT.md` (Phân loại 10 nhóm vấn đề từ P0 đến P2).
- [x] Hoàn thành `docs/ARCHITECTURE_TARGET.md` (Kiến trúc phân lớp 12 tầng).
- [x] Hoàn thành `docs/DATA_FLOW.md` (Bản đồ luồng dữ liệu chi tiết).
- [x] Hoàn thành `docs/DATA_CONTRACT.md` (Hợp đồng dữ liệu & chuẩn hóa schema).
- [x] Hoàn thành `docs/FORMULA_AUDIT.md` (Kiểm toán toàn bộ công thức FA, TA, Valuation, Risk).
- [x] Hoàn thành `docs/REPORT_AUDIT.md` (Truy vết nguyên nhân sai lệch báo cáo HTML).

### Giai Đoạn 2: Test Foundation (Nền tảng Kiểm Thử & Fixtures)
- [ ] Xây dựng thư mục `tests/` với các phân nhóm:
  - `tests/fixtures/`: Tạo fixtures dữ liệu đóng băng (frozen fixtures) cho các trường hợp:
    1. Doanh nghiệp sản xuất thông thường (HPG).
    2. Ngân hàng thương mại (VCB/MBB - mô hình tài chính đặc thù).
    3. Công ty chứng khoán (SSI).
    4. Doanh nghiệp BĐS (VHM/KDH).
    5. Doanh nghiệp kinh doanh thua lỗ, EPS âm (lỗ lũy kế).
    6. Doanh nghiệp thiếu BCTC / thiếu CFO.
    7. Cổ phiếu thanh khoản thấp / kẹp thanh khoản sàn.
- [ ] Viết bộ Unit tests cho các công thức tài chính và kỹ thuật (`tests/unit/`).
- [ ] Viết bộ Contract tests kiểm định schema `AnalysisResult` (`tests/contracts/`).
- [ ] Viết bộ Report Parity tests parse và đối chiếu số liệu HTML (`tests/report_parity/`).

### Giai Đoạn 3: Correctness (Sửa Lỗi Dữ Liệu & Công Thức)
- [ ] Loại bỏ hoàn toàn các giá trị mặc định tùy tiện (P/E = 15.0, P/B = 1.5, PEG = 99.9) trong `core/fa_engine.py`.
- [ ] Chuẩn hóa công thức Piotroski F-Score (9 tiêu chí kế toán chuẩn và phân biệt rõ với biến thể tĩnh).
- [ ] Xóa bỏ toàn bộ logic tự bịa đặt phân khúc kinh doanh và dự án ảo trong `core/segment_analyzer.py`.
- [ ] Gắn nhãn nguồn gốc và độ tươi cho các chỉ số vĩ mô/hàng hóa trong `core/data_loader.py` và `core/macro_engine.py`.
- [ ] Sửa đổi nhãn dự báo thời điểm trong `core/timing_engine.py` (loại bỏ tuyên bố xác suất 88% và T+1..T+3 vô căn cứ).
- [ ] Sửa đổi thang đánh giá định giá tài sản trong `core/fa_engine.py` (loại bỏ quy kết tội danh thao túng từ P/B).
- [ ] Nâng cấp `core/risk_manager.py` với cổng kiểm định thiết lập giao dịch (`has_valid_setup`) và trạng thái `NO_VALID_SETUP`.

### Giai Đoạn 4: Core Architecture & Canonical AnalysisResult
- [ ] Tạo module `core/models.py` định nghĩa Canonical `AnalysisResult` và các Data Quality Enums.
- [ ] Cập nhật `core/stock_service.py` đóng gói toàn bộ kết quả phân tích vào `AnalysisResult`.
- [ ] Duy trì các adapter tương thích ngược cho `main.py`, Telegram bot và `app.py`.

### Giai Đoạn 5: HTML Report Rebuild & Parity
- [ ] Tái thiết kế `core/html_report_generator.py` theo cấu trúc 13 khối chuẩn mực.
- [ ] Đảm bảo 100% số liệu lấy trực tiếp từ `AnalysisResult`, không tự tính toán lại.
- [ ] Bổ sung cơ chế Graceful Offline Fallback (hiển thị biểu đồ SVG nội tuyến và bảng dữ liệu khi không có internet).
- [ ] Tối ưu hóa hiển thị trên Microsoft Edge cho cả giao diện máy tính, điện thoại di động và Print CSS.

### Giai Đoạn 6: Full Integration & CLI Verification
- [ ] Kiểm thử toàn diện các chế độ CLI trong `main.py` (`full`, `fa`, `ta`, `--radar`, `--dashboard`).
- [ ] Kiểm thử tạo `DASHBOARD.html`.
- [ ] Kiểm thử lưu vết SQLite database và kiểm tra không rò rỉ khóa bảo mật `.env`.

### Giai Đoạn 7 & 8: Final QA & Acceptance Deliverables
- [ ] Chạy toàn bộ test suite và đạt 100% pass.
- [ ] Tạo báo cáo nghiệm thu cuối cùng `docs/QA_TEST_REPORT.md` và `docs/CHANGELOG.md`.
