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

### Giai Đoạn 2: Test Foundation (Nền tảng Kiểm Thử & Fixtures - Đã hoàn thành)
- [x] Xây dựng thư mục `tests/` với các phân nhóm:
  - `tests/fixtures/`: Tạo fixtures dữ liệu đóng băng (frozen fixtures) cho các trường hợp:
    1. Doanh nghiệp sản xuất thông thường (HPG).
    2. Ngân hàng thương mại (VCB/MBB - mô hình tài chính đặc thù).
    3. Công ty chứng khoán (SSI).
    4. Doanh nghiệp BĐS (VHM/KDH).
    5. Doanh nghiệp kinh doanh thua lỗ, EPS âm (lỗ lũy kế).
    6. Doanh nghiệp thiếu BCTC / thiếu CFO.
    7. Cổ phiếu thanh khoản thấp / kẹp thanh khoản sàn.
- [x] Viết bộ Unit tests cho các công thức tài chính và kỹ thuật (`tests/unit/`).
- [x] Viết bộ Contract tests kiểm định schema `AnalysisResult` (`tests/contracts/`).
- [x] Viết bộ Report Parity tests parse và đối chiếu số liệu HTML (`tests/report_parity/`).

### Giai Đoạn 3: Correctness (Sửa Lỗi Dữ Liệu & Công Thức - Đã hoàn thành)
- [x] Loại bỏ hoàn toàn các giá trị mặc định tùy tiện (P/E = 15.0, P/B = 1.5, PEG = 99.9) trong `core/fa_engine.py`.
- [x] Chuẩn hóa công thức Piotroski F-Score (9 tiêu chí kế toán chuẩn và phân biệt rõ với biến thể tĩnh).
- [x] Xóa bỏ toàn bộ logic tự bịa đặt phân khúc kinh doanh và dự án ảo trong `core/segment_analyzer.py`.
- [x] Gắn nhãn nguồn gốc và độ tươi cho các chỉ số vĩ mô/hàng hóa trong `core/data_loader.py` và `core/macro_engine.py`.
- [x] Sửa đổi nhãn dự báo thời điểm trong `core/timing_engine.py` (loại bỏ tuyên bố xác suất 88% và T+1..T+3 vô căn cứ).
- [x] Sửa đổi thang đánh giá định giá tài sản trong `core/fa_engine.py` (loại bỏ quy kết tội danh thao túng từ P/B).
- [x] Nâng cấp `core/risk_manager.py` với cổng kiểm định thiết lập giao dịch (`has_valid_setup`) và trạng thái `NO_VALID_SETUP`.
- [x] Bổ sung mô hình phân rã DuPont 3 nhân tố và tỷ suất sinh lời ROIC trong `core/fa_engine.py`.
- [x] Bổ sung khung giá 52 tuần trượt và O'Neil RS Rating (thang điểm 1-99) trong `core/ta_engine.py`.

### Giai Đoạn 4: Core Architecture & Canonical AnalysisResult (Đã hoàn thành)
- [x] Tạo module `core/models.py` định nghĩa Canonical `AnalysisResult` và các Data Quality Enums.
- [x] Cập nhật `core/stock_service.py` đóng gói toàn bộ kết quả phân tích vào `AnalysisResult`.
- [x] Duy trì các adapter tương thích ngược cho `main.py`, Telegram bot và `app.py`.
- [x] Bổ sung hàm dùng chung `generate_eli5_summary()` cung cấp góc nhìn đứa trẻ lên 5.

### Giai Đoạn 5: HTML Report Rebuild & Parity (Đã hoàn thành)
- [x] Tái thiết kế `core/html_report_generator.py` theo cấu trúc 13 khối chuẩn mực.
- [x] Đảm bảo 100% số liệu lấy trực tiếp từ `AnalysisResult`, không tự tính toán lại.
- [x] Bổ sung cơ chế Graceful Offline Fallback (hiển thị biểu đồ SVG nội tuyến và bảng dữ liệu khi không có internet).
- [x] Tối ưu hóa hiển thị trên Microsoft Edge cho cả giao diện máy tính, điện thoại di động và Print CSS.
- [x] Bổ sung hiển thị đầy đủ DuPont 3 nhân tố, ROIC, 52W High/Low và O'Neil RS Rating.

### Giai Đoạn 6: Full Integration & CLI Verification (Đã hoàn thành)
- [x] Kiểm thử toàn diện các chế độ CLI trong `main.py` (`full`, `fa`, `ta`, `scan`, `macro`, `track`, `ask`, `dashboard`).
- [x] Tái cấu trúc Terminal Dashboard và Markdown Report chuẩn 7 Phân hệ 360° theo `AGENTS.md`.
- [x] Kiểm thử lưu vết SQLite database và kiểm tra không rò rỉ khóa bảo mật `.env`.

### Giai Đoạn 7 & 8: Final QA & Acceptance Deliverables (Đã hoàn thành)
- [x] Chạy toàn bộ test suite (35 bài test) và đạt 100% pass.
- [x] Hoàn thiện tài liệu nghiệm thu `docs/CHANGELOG.md` (v2.1.0) và `docs/QA_AUDIT.md`.
