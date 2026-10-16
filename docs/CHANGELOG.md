# NHẬT KÝ THAY ĐỔI KIẾN TRÚC & HỆ THỐNG (CHANGELOG)

## [Phiên bản 2.2.0] - Tích Hợp Radar 10 Sóng Ngành & Động Lực Luân Chuyển Dòng Tiền (2020 - 2026+)
**Ngày phát hành:** 16/10/2026  
**Nhánh Git:** `main`  
**Bộ kiểm thử:** 40/40 test cases tự động chạy qua Pytest 9.1.1 (100% Passed)  

---

### 1. Module Radar 10 Sóng Ngành & Luân Chuyển Dòng Tiền (`core/sector_wave_engine.py`)
- **Mô hình hóa 10 Sóng Ngành Lớn của TTCK Việt Nam (2020 - 2026+):**
  1. `WAVE_OIL_GAS_GEOPOLITICS` (Căng thẳng Mỹ - Iran, Eo biển Hormuz, OPEC+, Brent > 80 USD; Leaders: PVD, PVS, BSR, GAS; Runners: PVC, PVB, PVT).
  2. `WAVE_TECH_AI_SEMICONDUCTOR` (Làn sóng AI toàn cầu, Chiến lược Bán dẫn quốc gia; Leaders: FPT, CMG, CTR; Runners: ELC, VGI).
  3. `WAVE_STEEL_INFRA_TARIFF` (Thuế Chống bán phá giá HRC, Đại công trường đầu tư công; Leaders: HPG, HSG, NKG; Runners: VGS, TLH).
  4. `WAVE_SECURITIES_LIQUIDITY` (Môi trường tiền rẻ, Thanh khoản > 20k-30k tỷ/phiên, Nâng hạng FTSE/KRX; Leaders: SSI, VCI, HCM; Runners: FTS, BSI, CTS, VIX).
  5. `WAVE_RESIDENTIAL_REAL_ESTATE` (Nới lỏng tín dụng, Tháo gỡ điểm nghẽn Luật Đất đai; Leaders: VHM, KDH, NLG; Runners: DIG, CEO, DXG).
  6. `WAVE_INDUSTRIAL_PARK_FDI` (Làn sóng dịch chuyển China+1, Chuyển đổi đất cao su; Leaders: GVR, KBC, IDC; Runners: DPR, D2D).
  7. `WAVE_CHEMICAL_FERTILIZER` (Phốt pho vàng cho chip/pin, Giá Urê thế giới; Leaders: DGC, DCM, DPM; Runners: BFC, CSV).
  8. `WAVE_PUBLIC_INFRASTRUCTURE` (Mệnh lệnh giải ngân cao tốc Bắc - Nam, Sân bay Long Thành; Leaders: VCG, HHV, LCG; Runners: FCN, KSB).
  9. `WAVE_EXPORT_SHIPPING` (Tỷ giá USD/VND neo cao, Cước vận tải biển; Leaders: VHC, ANV, TNG; Runners: MSH, FMC).
  10. `WAVE_RETAIL_DOMESTIC` (Giảm thuế VAT 2%, Tăng lương cơ sở, Chuỗi bán lẻ tạo tiền; Leaders: MWG, PNJ, FRT; Runners: DGW, PET).
- **Thuật toán Đo Nhiệt Độ Sóng (Wave Heat Score: 0 - 100):** Tự động liên kết các biến số vĩ mô quốc tế (Brent, HRC, Fed, Urea, DXY...) với xung lực dòng tiền và phân loại thành 4 Pha chu kỳ:
  - `Pha 1: Tích lũy âm thầm (Smart Money gom)` (50 - 64đ)
  - `Pha 2: Bùng nổ & Đẩy sóng (Momentum - Vùng đánh sóng tốt nhất)` (65 - 82đ)
  - `Pha 3: Quá nhiệt / Phân phối đỉnh (Overheated - Cấm FOMO)` (>= 83đ)
  - `Pha 4: Hạ nhiệt / Thoái trào (Fading)` (< 50đ)
- **Cơ chế Phân cấp Cổ phiếu:** Tự động nhận diện vai trò `👑 CỔ PHIẾU ĐẦU ĐÀN (LEADER)` vs `🚀 CỔ PHIẾU CHẠY THEO BETA CAO (RUNNER)` kèm nguyên tắc kỷ luật giao dịch đón sóng.

---

### 2. Tích hợp Hệ thống Đa Nền tảng (CLI, Báo cáo & Giao diện)
- **Chế độ CLI mới `python main.py --mode wave`:** Render bảng Rich Table hiển thị trực quan 10 sóng ngành, độ nhiệt Heat score, pha chu kỳ, mã dẫn sóng và chất xúc tác.
- **Tích hợp Báo cáo 360° Phân tích từng Cổ phiếu:**
  - **Terminal Dashboard & Markdown (`main.py`):** Hiển thị khối Radar Sóng Ngành chi tiết, vai trò cổ phiếu, các mã đồng pha và kỷ luật giải ngân.
  - **Báo cáo HTML Độc lập (`core/html_report_generator.py`):** Card kính mờ thủy tinh (Glassmorphism) sang trọng với thanh tiến trình Heat Score, nút bấm điều hướng nhanh `#sec-wave` trên thanh Quick Nav Bar.
  - **Mô hình Dữ liệu Chuẩn (`core/models.py`):** Bổ sung trường `sector_wave` vào `MacroAndSectorAssessment` trong Canonical `AnalysisResult`.

---

## [Phiên bản 2.1.0] - Chuẩn Hóa Toàn Diện 7 Phân Hệ 360°, Định Lượng DuPont/ROIC/52W/RS & Bộ Test Toàn Diện
**Ngày phát hành:** 16/10/2026  
**Nhánh Git:** `main`  
**Bộ kiểm thử:** 35/35 test cases tự động chạy qua Pytest 9.1.1 (100% Passed)  

---

### 1. Bổ sung Chỉ số Định lượng Thiếu sót trong Lõi Phân tích (Core Engines)
- **Động cơ Phân tích Kỹ thuật (`core/ta_engine.py`):**
  - **Khung giá 52 Tuần (52-Week High & Low):** Tự động tính toán mức đỉnh/đáy 52 tuần trượt (250 phiên) trực tiếp trong hàm `calculate_indicators()`, lưu vào trường `high_52w` và `low_52w`. Loại bỏ việc tầng giao diện HTML tự tính toán ad-hoc.
  - **O'Neil RS Rating (Thang điểm 1 - 99):** Bổ sung hàm định lượng `calculate_rs_rating()` tính điểm sức mạnh giá theo chuẩn CANSLIM của William O'Neil (trọng số 40% cho biến động 3 tháng gần nhất, 30% cho 6 tháng, 30% cho 12 tháng), xếp hạng cổ phiếu vào thang điểm 1-99 điểm so với mặt bằng thị trường.
- **Động cơ Phân tích Cơ bản (`core/fa_engine.py`):**
  - **Phân rã Tỷ suất Sinh lời DuPont (3 Nhân tố):** Bổ sung hàm `evaluate_dupont_decomposition()` phân tách ROE thành tích của: *Biên Lợi nhuận Ròng (Net Margin) × Vòng quay Tổng Tài sản (Asset Turnover) × Đòn bẩy Tài chính (Equity Multiplier)*, tự động xác định động lực tăng trưởng chính của doanh nghiệp.
  - **Tỷ suất Sinh lời trên Vốn Đầu tư (ROIC):** Tính toán `calculate_roic()` = $NOPAT / Invested Capital$ = $(EBIT \times (1 - t)) / (Total Debt + Equity - Cash)$ để đo lường thực chất hiệu quả sinh tiền trên vốn huy động.
- **Chuẩn hóa Mô hình Dữ liệu (`core/models.py`):**
  - Cập nhật Canonical Schema Pydantic v2 `AnalysisResult`: Thêm các trường `high_52w`, `low_52w`, `rs_rating` vào `TechnicalIndicators`; thêm `dupont` và `roic` vào `FinancialRatios` và `FundamentalAnalysis`.

---

### 2. Tái cấu trúc Báo cáo Terminal & Markdown Đồng bộ Chuẩn 7 Phân Hệ 360° & ELI5
- **Tập trung hóa Module ELI5 (`core/stock_service.py`):**
  - Tạo hàm dùng chung `generate_eli5_summary()` cung cấp góc nhìn mộc mạc cho đứa trẻ lên 5: *Bán gì kiếm tiền? Tiền thật hay tiền trên giấy? Món hời hay bẫy chuột? Đội lái cá mập đang làm gì? Lời khuyên bỏ heo đất.*
- **Đồng bộ Báo cáo Markdown & Terminal CLI (`main.py`):**
  - Nâng cấp `_render_terminal_dashboard()` và `_save_markdown_report()` phản ánh đầy đủ 7 Phân hệ 360° theo quy định tại `AGENTS.md`:
    1. 🧒 Giải thích cho đứa trẻ lên 5 (ELI5)
    2. 🎯 Phán quyết Hội đồng & 2 Kế hoạch Giao dịch (Tích sản Giá trị vs Swing Kỹ thuật)
    3. 🏛️ Bảng 5 Trường phái & Điểm Mâu thuẫn Lớn nhất (Conflict Spotlight)
    4. 🔬 FA Deep-Dive (BCTC, Dòng tiền CFO/FCF, DuPont 3 nhân tố, ROIC, Bội số Định giá Tài sản, Segments, G-Score)
    5. 📈 TA Deep-Dive (Xu hướng, SMA200, 52W Range, RS Rating, VCP, Wyckoff VSA)
    6. ⚡ Động cơ Thời điểm (Timing Matrix & Price Ladder Gauge)
    7. 🔮 Dự phóng 3 Kịch bản Giá (Base/Bull/Bear) & Điều kiện Mất hiệu lực (Invalidation Triggers)
  - Loại bỏ hoàn toàn nhãn cũ "Radar Thao túng" gây hiểu nhầm pháp lý, thay thế bằng "Định giá Bội số Tài sản & Rủi ro Pha loãng".

---

### 3. Chuẩn hóa Nguồn gốc Vĩ mô & Sắp xếp Kỳ BCTC
- **Minh bạch Dữ liệu Hàng hóa Vĩ mô (`core/macro_engine.py` & `core/data_loader.py`):**
  - Bổ sung trường định danh nguồn gốc `source_type` (`"LIVE"`, `"CACHED"`, `"REFERENCE_BENCHMARK"`) và thời điểm lấy dữ liệu `as_of_date` cho từng hàng hóa vĩ mô.
- **Chuẩn hóa Trục Thời gian Quý BCTC (`core/data_loader.py`):**
  - Bổ sung hàm `normalize_quarter_key()` và `sort_quarter_columns()` chuẩn hóa tên cột quý theo chuẩn `YYYY_QX` trước khi sắp xếp theo thời gian thực tế.
  - Thêm cờ kiểm tra tính toàn vẹn 4 quý TTM: `ttm_status = "COMPLETE" | "INCOMPLETE_QUARTERS"`.

---

### 4. Bổ sung Bộ Kiểm thử Tự động Hoàn thiện (4 Test Suites Mới)
- Bổ sung 4 bộ test tự động lấp đầy toàn bộ khoảng trống kiểm thử:
  1. `tests/unit/test_timing_engine.py`: Kiểm tra giới hạn điểm số `setup_quality_score` [0, 100], tính điểm nổ Pivot/Breakdown và lịch sự kiện trọng yếu.
  2. `tests/unit/test_macro_engine.py`: Kiểm tra tính minh bạch nguồn gốc `source_type` và `as_of_date`, phân loại ngành động và điểm gió xuôi vĩ mô.
  3. `tests/unit/test_data_loader.py`: Kiểm tra chuẩn hóa định dạng quý `YYYY_QX`, sắp xếp cột quý theo trục thời gian và cờ `ttm_status`.
  4. `tests/report_parity/test_offline_html_rendering.py`: Kiểm tra báo cáo HTML offline độc lập, fallback đồ họa nội tuyến SVG nến và SVG dòng tiền trên Microsoft Edge.
- **Tổng số test cases tự động tăng lên 35 bài (100% Passed).**

---

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

