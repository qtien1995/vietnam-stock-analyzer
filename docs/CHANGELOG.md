# NHẬT KÝ THAY ĐỔI KIẾN TRÚC & HỆ THỐNG (CHANGELOG)

## [Phiên bản 2.0.0] - Kiểm toán Toàn diện & Tái thiết Lõi Hệ thống (Audit & Rebuild)
**Ngày phát hành:** 12/10/2026  
**Nhánh Git:** `audit-rebuild` (Base commit: `17b76a2`)  
**Bản sao lưu Database an toàn:** `data/market_backup_20261012_174222.db` (5 bảng nguyên vẹn)  

---

### 1. Sửa lỗi Dữ liệu Tài chính & Loại bỏ Dữ liệu Bịa đặt (Financial Integrity)
- **Bóc tách mảng kinh doanh (Segment Analyzer - `core/segment_analyzer.py`):**
  - **Triệt tiêu hoàn toàn tỷ lệ bịa đặt 70%:** Loại bỏ hàm fallback tự động bịa "chiếm ~70% doanh thu" cho các mã chưa có hồ sơ BCTC kiểm chứng.
  - Thiết lập cờ minh bạch `has_detailed_segments: False`, `source: "UNVERIFIED"`, `segments: []` cho mã chưa kiểm chứng.
  - Giữ lại và xác thực hồ sơ bóc tách chi tiết cho các mã đầu ngành đã kiểm chứng BCTC thực tế: `HPG`, `GVR`, `SZC`, `PVD`.
- **Động cơ Cơ bản & Công thức Định lượng (`core/fa_engine.py`):**
  - **P/E chuẩn mực:** Loại bỏ việc gán giá trị mặc định `15.0`. Khi EPS âm hoặc chưa có dữ liệu, trả về `pe = None, pe_status = "NEGATIVE_EARNINGS" | "MISSING_DATA"`.
  - **P/B an toàn:** Khi BVPS âm hoặc thiếu, trả về `pb = None, pb_status = "NEGATIVE_EQUITY" | "MISSING_DATA"`.
  - **Mô hình Peter Lynch (PEG):** Khi EPS âm hoặc tăng trưởng EPS âm, trả về `peg = None` kèm lý giải định tính trung thực; không tự động tính số âm hay chia cho 0.
  - **Altman Z''-Score:** Miễn trừ hợp lý cho khối Ngân hàng (`VCB`, `BID`, `CTG`...) và Công ty Chứng khoán với trạng thái chuẩn hóa `z_status = "NOT_APPLICABLE"` thay vì gán nhãn vỡ nợ sai lệch.
  - **Piotroski F-Score:** Đóng gói biến thể `MODIFIED_STATIC` với giới hạn điểm chuẩn [0, 9], ghi rõ ràng số tiêu chí khả dụng.
  - **Phòng thủ NoneType:** Khắc phục lỗi `TypeError` khi tính toán `working_capital`, `current_assets`, `roa`, `roe` với các công ty thiếu dữ liệu BCTC.

---

### 2. Loại bỏ Tuyên bố Xác suất Lừa dối & Quản trị Rủi ro Nghiêm ngặt (Risk Manager & Timing Engine)
- **Cơ chế Khóa Điểm Mua (Setup Validation Gate - `core/risk_manager.py`):**
  - Cổ phiếu nằm trong xu hướng giảm (Downtrend), vi phạm tiêu chí cơ bản hoặc cờ đỏ kế toán bị gắn trạng thái `has_valid_setup = False` và `setup_status = "NO_VALID_SETUP"`.
  - Khi không có setup hợp lệ: Tỷ trọng giải ngân tối đa được ép về `0.0%`, không sinh ra các mốc mục tiêu hay cắt lỗ giả tạo.
- **Biên độ Cắt lỗ theo Sàn Giao dịch:**
  - Giới hạn mức cắt lỗ tối đa theo quy định biên độ dao động phiên: HOSE (&le; 7.0%), HNX (&le; 10.0%), UPCoM (&le; 14.0%).
- **Động cơ Dự báo Thời điểm (`core/timing_engine.py`):**
  - **Loại bỏ xác suất bịa đặt:** Xóa bỏ hoàn toàn các tuyên bố "Xác suất thắng T+1..T+3 là 88%".
  - Thay thế bằng `setup_quality_score` (0 - 100 điểm) và các giai đoạn kỹ thuật khách quan theo trường phái Wyckoff/VCP Minervini.

---

### 3. Chuẩn hóa Hợp đồng Dữ liệu (Canonical Data Contracts)
- **Mô hình Pydantic v2 Chuẩn mực (`core/models.py`):**
  - Xây dựng mô hình trung tâm `AnalysisResult` đại diện cho toàn bộ kết quả phân tích.
  - Chứa đầy đủ các schema con: `QuoteData`, `FundamentalAnalysis`, `TechnicalAnalysis`, `TradeSetup`, `CouncilResult`, `TimingResult`, `MacroData`.
  - Hỗ trợ phương thức factory `from_components()` và adapter tương thích ngược `to_legacy_dict()` giúp các module cũ hoạt động trơn tru.

---

### 4. Báo cáo HTML Hoàn toàn Độc lập & Dự phòng Offline trên Microsoft Edge
- **Đồng bộ Số liệu 100% với Engine (`core/html_report_generator.py`):**
  - Box 2 và Price Ladder hiển thị chính xác trạng thái của `has_valid_setup`. Cổ phiếu bị loại bỏ sẽ hiển thị `KHÔNG CÓ VÙNG MUA (BẢO TOÀN VỐN)` và `0% (Đứng ngoài quan sát)`, không hiển thị `0 đ (-0%)`.
  - Ma trận Vĩ mô không còn chứa câu văn hardcode 70% doanh thu.
  - Các chỉ số định lượng `Altman Z`, `ROA`, `ROE`, `P/E`, `P/B`, `Fibonacci` được xử lý phòng thủ hiển thị `N/A` nếu giá trị là `None`.
- **Bộ kết xuất Đồ họa Offline Thuần Inline SVG:**
  - Thêm `render_offline_cashflow_svg()`: Vẽ biểu đồ cột CFO vs LNST vs FCF dạng SVG nhúng trực tiếp.
  - Thêm `render_offline_candles_svg()`: Vẽ biểu đồ nến Nhật OHLCV kèm khối lượng dạng SVG nhúng trực tiếp.
  - Khi mở file HTML cục bộ trên Microsoft Edge qua giao thức `file:///` mà không có kết nối Internet (hoặc CDN bên ngoài bị chặn), trang báo cáo tự động chuyển sang hiển thị biểu đồ SVG nội tuyến không lỗi.

---

### 5. Nâng cấp Giao diện Dòng lệnh (CLI & Execution Layer)
- **`main.py` Linh hoạt:**
  - Hỗ trợ tham số vị trí: `python main.py HPG` phân tích nhanh trực tiếp mà không cần gõ dài dòng.
  - Hỗ trợ cờ `--no-alert` (tắt Telegram alert khi chạy test/nghiên cứu) và `--no-browser` (không bật popup Edge khi chạy batch).
  - Hỗ trợ đầy đủ các mode: `--mode fa`, `--mode ta`, `--mode macro`, `--mode scan`, `--mode dashboard`, `--mode track`.

---

### 6. Bộ Kiểm thử Tự động Hóa Toàn diện (Automated Test Suites)
- **19 bài test tự động chạy qua Pytest 9.1.1 (100% Passed):**
  1. `tests/contracts/test_analysis_result_schema.py`: Kiểm tra serialization/deserialization schema chuẩn.
  2. `tests/report_parity/test_html_parity.py`: 3 bài test kiểm định tính đồng nhất giữa Engine và Báo cáo HTML (cổ phiếu đạt chuẩn, cổ phiếu bị loại, miễn trừ ngân hàng).
  3. `tests/unit/test_fa_engine.py`: 5 bài test kiểm định F-Score, Altman Z, P/E âm, thiếu BCTC, miễn trừ ngân hàng.
  4. `tests/unit/test_risk_manager.py`: 3 bài test kiểm định Setup Validation Gate, downtrend disqualification, biên sàn HOSE/HNX/UPCoM.
  5. `tests/unit/test_segment_analyzer.py`: 2 bài test kiểm định hồ sơ BCTC kiểm chứng vs mã chưa kiểm chứng.
  6. `tests/unit/test_ta_engine.py`: 5 bài test kiểm định miền giá trị các chỉ báo, O'Neil, VSA, Fibonacci, chuỗi nến rỗng/ngắn.

---

### 7. Tinh giản Telegram Alert 1 Chiều & Loại bỏ Bot 2 Chiều (1-Way Notification Streamlining)
- **Bắn file HTML & Cảnh báo 1 chiều trực tiếp (`alerts/telegram_bot.py`):**
  - Chuyển đổi toàn bộ luồng Telegram sang cơ chế **bắn thông báo 1 chiều** thẳng về tài khoản cá nhân của người dùng (`TELEGRAM_CHAT_ID`).
  - Tự động đính kèm file báo cáo HTML (`send_telegram_document`) sau mỗi lần phân tích cổ phiếu, cho phép chạm vào mở xem offline trên điện thoại/máy tính mà không phụ thuộc Internet.
  - Bổ sung hàm `send_telegram_radar()` gửi kết quả quét Top cổ phiếu nổ Vol 1 chiều thẳng vào Telegram mà không có bất kỳ nút bấm khảo sát hay inline callback nào.
- **Loại bỏ triệt để Bot 2 chiều:**
  - Gỡ bỏ `alerts/telegram_interactive_bot.py` và tập lệnh `run_bot.bat`.
  - Loại bỏ menu chọn chat, inline button callbacks, và lệnh `--mode bot` khỏi `main.py`.
  - Cập nhật `run_daily_radar.bat` sang sử dụng trực tiếp cơ chế bắn 1 chiều `send_telegram_radar`.

