# QA_AUDIT.md — Toàn văn Báo cáo Kiểm toán Hệ thống Vietnam Stock Analyzer

## 1. Tổng quan Dự án & Bối cảnh Kiểm toán
- **Tên dự án:** Vietnam Stock Analyzer (`vietnam-stock-analyzer`)
- **Mục tiêu:** Hệ thống nghiên cứu, phân tích chiến lược và hỗ trợ ra quyết định đầu tư cổ phiếu Việt Nam (HOSE, HNX, UPCoM) cục bộ trên Windows.
- **Môi trường vận hành:** Windows 10/11, Python 3.11+, SQLite (`data/market.db`), Microsoft Edge (Local HTML standalone).
- **Môi trường AI phát triển:** Độc lập với môi trường AI IDE (Codex hoặc Antigravity). Logic tính toán, chuẩn mực tài chính và kiểm thử tự động độc lập với AI provider.
- **Ngày kiểm toán:** 12/10/2026.
- **Điểm khôi phục Git:** Branch `audit-rebuild`, Base commit `17b76a2`.
- **Sao lưu Database:** `data/market_backup_20261012_174222.db` (Đã kiểm định `PRAGMA integrity_check; -> ok`, bảo toàn nguyên vẹn 5 bảng dữ liệu: `eod_quotes`, `recommendations`, `sqlite_sequence`, `performance_tracking`, `stock_master`).

---

## 2. Phân loại và Tóm tắt các Phát hiện Kiểm toán (Audit Findings Classification)

Mỗi phát hiện được phân loại nghiêm ngặt theo 5 nhóm:
- **CONFIRMED BUG**: Lỗi đã được tái hiện hoặc chứng minh bằng mã nguồn và test case.
- **CONFIRMED DESIGN DEFECT**: Lỗi thiết kế vi phạm chuẩn mực tài chính hoặc quy tắc kiến trúc.
- **HIGH-RISK FINDING**: Nguy cơ tiềm ẩn về dữ liệu hoặc điều kiện biên cần giải pháp phòng ngừa.
- **UNVERIFIED**: Chưa đủ bằng chứng thực nghiệm.
- **ACCEPTED LIMITATION**: Giới hạn đã biết được chấp nhận và ghi nhận rõ ràng.

---

## 3. Bảng Chi tiết các Vấn đề Phát hiện & Đề xuất Khắc phục

### ISSUE-01: Silent Arbitrary Defaults in Fundamental Valuation Engine
- **Phân loại:** CONFIRMED BUG & DESIGN DEFECT
- **Mức độ nghiêm trọng:** P0 (Release-blocking)
- **Tập tin & Hàm ảnh hưởng:** `core/fa_engine.py` (`evaluate_buffett_moat`, `evaluate_peter_lynch`, `evaluate_asset_based_valuation`)
- **Bằng chứng & Tái hiện:**
  ```python
  # core/fa_engine.py dòng 104-106 & 112-113:
  if eps_val and eps_val > 0:
      pe = round(current_price / eps_val, 2)
  elif fin.get("pe"):
      pe = fin.get("pe")
  else:
      pe = 15.0  # Lỗi: Doanh nghiệp lỗ (EPS âm) hoặc thiếu số liệu bị gán mặc định P/E = 15.0x

  # Dòng 113:
  else:
      pb = 1.5   # Lỗi: Doanh nghiệp thiếu BVPS bị gán mặc định P/B = 1.5x
  ```
- **Nguyên nhân gốc rễ (Root Cause):** Lập trình viên sử dụng giá trị fallback cứng (15.0x và 1.5x) để tránh lỗi chia cho 0 hoặc lỗi hiển thị trên UI, thay vì trả về trạng thái `None` hoặc `NOT_APPLICABLE` và kích hoạt cảnh báo thiếu dữ liệu.
- **Tác động người dùng:**
  - Cổ phiếu kinh doanh thua lỗ nghiêm trọng (EPS âm) lại được báo cáo có P/E 15.0x như một doanh nghiệp sinh lời bình thường.
  - Cổ phiếu thiếu BCTC vẫn hiển thị định giá hợp lý với P/B 1.5x, che giấu rủi ro dữ liệu tài chính rỗng.
- **Biện pháp khắc phục:**
  - Nếu `eps <= 0` hoặc thiếu số liệu: `pe = None`, trạng thái `pe_status = "NEGATIVE_EARNINGS"` hoặc `"INSUFFICIENT_DATA"`.
  - Nếu `bvps <= 0` hoặc thiếu số liệu: `pb = None`, trạng thái `pb_status = "INSUFFICIENT_DATA"` hoặc `"NEGATIVE_EQUITY"`.
  - Không tính PEG khi tăng trưởng lợi nhuận <= 0 hoặc mẫu số không xác định; gán rõ `peg = None`, `peg_status = "NOT_APPLICABLE_NEGATIVE_GROWTH"`.
- **Test case kiểm chứng:** `tests/unit/test_fa_engine.py::test_negative_eps_and_missing_bvps`

---

### ISSUE-02: Sai lệch Chuẩn mực Tính toán Piotroski F-Score (9 Tiêu chí Kế toán)
- **Phân loại:** CONFIRMED DESIGN DEFECT
- **Mức độ nghiêm trọng:** P1
- **Tập tin & Hàm ảnh hưởng:** `core/fa_engine.py` (`calculate_piotroski_score`)
- **Bằng chứng & Tái hiện:**
  - Theo chuẩn mực khoa học của GS. Joseph Piotroski (2000), F-Score đo lường **sự biến động chất lượng kế toán qua 2 kỳ (YoY change)**:
    1. ROA > 0
    2. CFO > 0
    3. $\Delta$ROA > 0 (ROA năm nay > ROA năm trước)
    4. Accrual: CFO > Net Profit
    5. $\Delta$Leverage: Đòn bẩy nợ dài hạn giảm so với năm trước
    6. $\Delta$Liquidity: Tỷ số thanh toán hiện hành (Current Ratio) tăng so với năm trước
    7. No Dilution: Không phát hành cổ phiếu mới làm pha loãng cổ phần
    8. $\Delta$Gross Margin: Biên lãi gộp tăng so với năm trước
    9. $\Delta$Asset Turnover: Vòng quay tài sản tăng so với năm trước
  - Trong mã nguồn hiện tại:
    - Tiêu chí 5 thay bằng: `debt_eq <= 1.2` (kiểm tra mức nợ tĩnh, không đo lường biến động).
    - Tiêu chí 6 thay bằng: `working_cap > 0` (kiểm tra mức tĩnh, không kiểm tra tỷ số thanh toán hiện hành tăng).
    - Tiêu chí 7 thay bằng: `profit_growth > 12.0` (lặp lại tiêu chí tăng trưởng lợi nhuận, hoàn toàn bỏ qua việc pha loãng cổ phiếu).
    - Tiêu chí 8 thay bằng: `gross_margin >= 15.0` (ngưỡng tĩnh).
    - Tiêu chí 9 thay bằng: `rev_growth > 5.0` (không đo vòng quay tài sản).
    - Đối với Bank/Securities: Tự động cộng 1 điểm cho tiêu chí 5, 6, 8 bất kể chất lượng tài sản.
- **Nguyên nhân gốc rễ:** Thay thế công thức so sánh 2 kỳ (YoY changes) bằng các ngưỡng tĩnh tùy tiện do thiếu dữ liệu BCTC lịch sử cùng kỳ năm trước.
- **Tác động người dùng:** Doanh nghiệp có biên lợi nhuận sụt giảm mạnh và đòn bẩy nợ tăng vọt vẫn có thể đạt 7-8/9 điểm F-score nếu thỏa mãn các ngưỡng tĩnh tùy biến.
- **Biện pháp khắc phục:**
  - Xây dựng mô hình chuẩn tính toán F-Score chuẩn hóa: Khi có dữ liệu so sánh 2 kỳ (quý cùng kỳ năm trước), kiểm tra đúng 9 tiêu chí biến động.
  - Khi chỉ có dữ liệu 1 kỳ: Ghi rõ nhãn `"MODIFIED_STATIC_FSCORE"` kèm ghi chú phương pháp luận minh bạch, không gọi là chuẩn Piotroski F-Score 9 tiêu chí.
  - Xây dựng bộ chỉ tiêu riêng cho Ngân hàng (CAMELS proxy: NPL, CAR, CASA, NIM, LDR) thay vì cộng điểm bừa bãi.
- **Test case kiểm chứng:** `tests/unit/test_fa_engine.py::test_piotroski_score_standard_vs_static`

---

### ISSUE-03: Chế tạo Số liệu Phân khúc Kinh doanh và Dự án Ảo (Fabricated Segments & Projects)
- **Phân loại:** CONFIRMED BUG & DESIGN DEFECT
- **Mức độ nghiêm trọng:** P0 (Release-blocking)
- **Tập tin & Hàm ảnh hưởng:** `core/segment_analyzer.py` (`analyze_company_segments`)
- **Bằng chứng & Tái hiện:**
  ```python
  # core/segment_analyzer.py dòng 65-104:
  if "RUBBER" in sec_upper:
      default_segments = [
          {"name": "Khai thác, Chế biến & Xuất khẩu Mủ Cao su", "rev_share_pct": 65.0, ...},
          {"name": "Phát triển Hạ tầng KCN & Bồi thường chuyển đổi đất", "rev_share_pct": 20.0, ...},
          {"name": "Chế biến Gỗ cao su & Hoạt động phụ trợ", "rev_share_pct": 15.0, ...}
      ]
      default_projects = [
          {"name": f"Dự án Chuyển đổi Quỹ đất Cao su sang KCN ({sym})", ...}
      ]
  ```
- **Nguyên nhân gốc rễ:** Để giao diện báo cáo không bị trống, tác giả cũ đã viết hàm tự bịa ra cơ cấu phân khúc (65%, 20%, 15%) và nối chuỗi tên mã cổ phiếu `{sym}` vào một dự án tưởng tượng cho bất kỳ công ty nào thuộc ngành đó nếu chưa có file trong `data/segments/`.
- **Tác động người dùng:** Báo cáo HTML in ra các số liệu và dự án giả mạo như một sự thật khách quan của doanh nghiệp, vi phạm trực tiếp Quy tắc tối cao tại `AGENTS.md` ("Tuyệt đối không bịa số liệu").
- **Biện pháp khắc phục:**
  - Xóa bỏ toàn bộ logic tự sinh dự án và phân khúc ảo.
  - Khi không có dữ liệu phân khúc BCTC được kiểm chứng: Trả về `has_detailed_segments = False`, `segments = []`, `projects = []`, kèm thông báo rõ: *"Chưa có dữ liệu phân rã phân khúc chi tiết từ thuyết minh BCTC; cần kiểm tra BCTC kiểm toán gần nhất."*
- **Test case kiểm chứng:** `tests/unit/test_segment_analyzer.py::test_no_fabricated_segments_for_unknown_ticker`

---

### ISSUE-04: Dữ liệu Hàng hóa Vĩ mô Mặc định được Biến thành Quan sát Thời gian Thực
- **Phân loại:** CONFIRMED DESIGN DEFECT
- **Mức độ nghiêm trọng:** P0 (Release-blocking)
- **Tập tin & Hàm ảnh hưởng:** `core/data_loader.py` (`get_global_macro_and_commodities`), `core/macro_engine.py`, `core/html_report_generator.py`
- **Bằng chứng & Tái hiện:**
  - Các hằng số như Giá dầu Brent: 78.5 USD, Giá cao su: 204.5 c/kg, Thép HRC: 545 USD, Fed rate: 4.88%, USD/VND: 25,380 được ghi tĩnh trong code.
  - Khi người dùng chạy offline hoặc API Yahoo không cập nhật, các giá trị này được gắn kèm nhãn biến động giả tạo (ví dụ: `▲ +4.2%`) và xuất ra HTML như thể đang lấy trực tiếp từ thị trường.
  - Thậm chí trong `html_report_generator.py` dòng 75: *"Mảng mủ cao su tự nhiên là nguồn thu tiền mặt cốt lõi chiếm tới ~70% doanh thu của {sym}. Giá TSR20 neo cao tại 204.5 Cents/kg... mở rộng biên lợi nhuận gộp từ 18% lên trên 24-28%..."* được in cứng cho mọi mã liên quan đến cao su.
- **Nguyên nhân gốc rễ:** Trộn lẫn văn bản phân tích tĩnh vào hàm render HTML và dùng hằng số giả lập làm quan sát thời gian thực.
- **Tác động người dùng:** Thông tin thị trường bị sai lệch, suy luận tài chính dựa trên dữ liệu giả định nhưng trình bày như sự thật.
- **Biện pháp khắc phục:**
  - Bổ sung trường `source_type: "LIVE" | "CACHED" | "REFERENCE_BENCHMARK"` và trường `as_of_date` rõ ràng cho từng chỉ số vĩ mô.
  - Khi dùng giá trị tham chiếu tĩnh, phải ghi rõ: *"Mức tham chiếu chu kỳ (Dữ liệu cố định)"*, không tạo % biến động giả.
  - Loại bỏ hoàn toàn các câu khẳng định định lượng cứng (như "chiếm ~70%", "tăng từ 18% lên 24-28%") trong hàm render HTML nếu không xuất phát từ phân tích của doanh nghiệp đó.
- **Test case kiểm chứng:** `tests/unit/test_macro_engine.py::test_macro_provenance_and_labels`

---

### ISSUE-05: Mô hình Dự báo Thời điểm (Timing Engine) Gán Xác suất và Khung Thời gian Giả Định
- **Phân loại:** CONFIRMED DESIGN DEFECT
- **Mức độ nghiêm trọng:** P1
- **Tập tin & Hàm ảnh hưởng:** `core/timing_engine.py` (`analyze_timing_prediction`)
- **Bằng chứng & Tái hiện:**
  - Công thức: `surge_prob = min(88, max(35, surge_points))` (điểm cộng ngẫu nhiên).
  - Khung thời gian: Gán nhãn `1 - 3 phiên tới (Cận kề điểm nổ Pocket Pivot)` hoặc `Xác suất 88%`.
  - Khối lượng mua chủ động: `active_buy_pct = min(85.0, 58.0 + change_pct * 3.5)` (dùng công thức hồi quy giả từ % thay đổi giá để bịa ra tỷ lệ mua chủ động thay vì đọc sổ lệnh khớp lệnh).
- **Nguyên nhân gốc rễ:** Lạm dụng nhãn xác suất và khung thời gian T+ mà không có kiểm định thống kê hoặc mô hình backtest hỗ trợ.
- **Tác động người dùng:** Gây ấn tượng sai lệch rằng hệ thống có khả năng dự đoán tương lai ngắn hạn với độ chính xác 88%, dẫn đến tâm lý mua đuổi sai lầm.
- **Biện pháp khắc phục:**
  - Đổi tên trường từ `surge_prob` thành `setup_quality_score` (Điểm điều kiện kỹ thuật: 0-100).
  - Xóa bỏ các tuyên bố dự báo chính xác "T+1..T+3", thay bằng: *"Trạng thái kỹ thuật: Đang tích lũy siết chặt / Chờ điểm xác nhận vượt kháng cự"*.
  - Ghi chú minh bạch nguồn gốc của tỷ lệ lệnh mua chủ động là ước tính theo đà nến, không phải dữ liệu sổ lệnh tick-by-tick.
- **Test case kiểm chứng:** `tests/unit/test_timing_engine.py::test_timing_metrics_and_transparency`

---

### ISSUE-06: Quy kết Tội danh Thao túng Giá từ Tỷ số P/B Đơn thuần
- **Phân loại:** CONFIRMED DESIGN DEFECT
- **Mức độ nghiêm trọng:** P1
- **Tập tin & Hàm ảnh hưởng:** `core/fa_engine.py` (`evaluate_asset_based_valuation`)
- **Bằng chứng & Tái hiện:**
  - Khi P/B > 6.0: Gán nhãn *"BÁO ĐỘNG ĐỎ - NGUY CƠ THAO TÚNG / THỔI GIÁ... Dấu hiệu điển hình của việc thao túng giá, đội lái bơm thổi tạo thanh khoản ảo. Tuyệt đối không giải ngân theo đám đông."*
  - Khi P/B < 1.0: Tuyên bố *"Rủi ro bị thổi giá ảo: RẤT THẤP. Mua 1 đồng cổ phiếu nhận về X đồng tài sản thực."*
- **Nguyên nhân gốc rễ:** Đơn giản hóa quá mức động lực định giá tài sản; bỏ qua đặc thù của doanh nghiệp thâm dụng tài sản vô hình (công nghệ, bán lẻ, dịch vụ có ROIC cao như FPT, MWG có P/B tự nhiên cao) và cạm bẫy giá trị của các doanh nghiệp P/B thấp nhưng tài sản mục rỗng, nợ xấu ngầm.
- **Tác động người dùng:** Đưa ra cáo buộc pháp lý / hình sự không có căn cứ đối với doanh nghiệp chất lượng cao, đồng thời khuyến khích nhà đầu tư lao vào các cổ phiếu "rẻ ảo" nguy hiểm.
- **Biện pháp khắc phục:**
  - Thay đổi hệ thống đánh giá thành: Đánh giá Định giá Tài sản (Asset Valuation Multiple) với các mức: *Định giá chiết khấu sâu (Deep Value / Cần rà soát bẫy giá trị), Định giá cân bằng, Định giá thặng dư cao (High Growth Premium / Rủi ro điều chỉnh bội số Multiple Contraction)*.
  - Phân loại rõ theo nhóm ngành: Doanh nghiệp thâm dụng vốn/tài sản (Ngân hàng, BĐS, Sản xuất) áp dụng thang P/B khác với Doanh nghiệp công nghệ/dịch vụ/tiêu dùng.
- **Test case kiểm chứng:** `tests/unit/test_fa_engine.py::test_asset_valuation_fair_labeling`

---

### ISSUE-07: Quản trị Rủi ro Thiết lập Mục tiêu và Cắt lỗ Cố định Thiếu Kiểm định Tính hợp lệ
- **Phân loại:** CONFIRMED BUG & DESIGN DEFECT
- **Mức độ nghiêm trọng:** P1
- **Tập tin & Hàm ảnh hưởng:** `core/risk_manager.py` (`calculate_trade_setup`)
- **Bằng chứng & Tái hiện:**
  - Dòng 149-153: Luôn tự động tính TP1 = Giá + 12%, TP2 = Giá + 20%, TP3 = Giá + 35% mà không dựa trên kháng cự thực tế hay biên an toàn.
  - Dòng 77-80: Cắt lỗ bị giới hạn cứng từ 3.8% đến 7.0%, và tuyên bố "Chặn lỗ tối đa -7% (Nguyên tắc bảo toàn vốn)", tạo ảo tưởng cho người dùng rằng mức lỗ tối đa không thể vượt quá 7% (bỏ qua rủi ro mở gap sàn, kẹp thanh khoản trắng bên mua).
  - Khi cổ phiếu ở xu hướng giảm mạnh (Downtrend) hoặc rủi ro nghiêm trọng: Hệ thống vẫn tính toán điểm mua "Quan sát quanh...", TP1, TP2 thay vì xuất trạng thái tường minh `NO_VALID_SETUP`.
- **Nguyên nhân gốc rễ:** Thiếu logic xác thực điều kiện tiên quyết của một thiết lập giao dịch hợp lệ (Valid Trade Setup Gate).
- **Tác động người dùng:** Tạo ra kế hoạch giao dịch cho các mã không đạt chuẩn, ép buộc tỷ lệ R:R danh nghĩa 2:1 giả tạo.
- **Biện pháp khắc phục:**
  - Đưa vào trạng thái rõ ràng: `has_valid_setup: bool`. Khi cổ phiếu vi phạm bộ lọc kỹ thuật hoặc cơ bản nghiêm trọng, trả về `setup_status = "NO_VALID_SETUP"`, không đưa ra vùng mua hay mục tiêu giá ảo.
  - Đưa vào cảnh báo rủi ro thực tế: Mức cắt lỗ là mức giá kích hoạt lệnh bán kỷ luật, không phải bảo hiểm đảm bảo mức lỗ thực tế không vượt quá 7% trong điều kiện thị trường rơi sàn liên tục mất thanh khoản.
- **Test case kiểm chứng:** `tests/unit/test_risk_manager.py::test_no_valid_setup_on_downtrend_and_high_risk`

---

### ISSUE-08: Thiếu Cấu trúc Dữ liệu Chuẩn Canonical AnalysisResult và Đứt gãy Parity
- **Phân loại:** CONFIRMED DESIGN DEFECT
- **Mức độ nghiêm trọng:** P0 (Release-blocking)
- **Tập tin & Hàm ảnh hưởng:** `core/stock_service.py`, `core/html_report_generator.py`, `main.py`
- **Bằng chứng & Tái hiện:**
  - Dữ liệu giữa các tầng phân tích và báo cáo HTML được truyền qua các `dict` lồng nhau không có schema cố định.
  - Tầng HTML tự tính toán lại hoặc định dạng lại nhiều trường, dẫn đến sự không nhất quán giữa kết quả trên Terminal CLI, Báo cáo Markdown và Báo cáo HTML.
- **Nguyên nhân gốc rễ:** Chưa có một Data Contract thống nhất và schema kết quả chuẩn (`Canonical AnalysisResult`).
- **Biện pháp khắc phục:**
  - Xây dựng dataclass / Pydantic schema `AnalysisResult` chuẩn hóa, chứa đầy đủ metadata, provenance, data quality status, FA metrics, TA indicators, Valuation scenarios, Risk parameters, Council opinions, và Invalidation conditions.
  - Tầng HTML và CLI chỉ đọc dữ liệu từ `AnalysisResult`, tuyệt đối không tự tính toán lại công thức tài chính.
- **Test case kiểm chứng:** `tests/contracts/test_analysis_result_schema.py`

---

### ISSUE-09: Xử lý Kỳ BCTC và Chuỗi Dòng tiền TTM Tiềm ẩn Sai số
- **Phân loại:** CONFIRMED BUG
- **Mức độ nghiêm trọng:** P1
- **Tập tin & Hàm ảnh hưởng:** `core/data_loader.py` (`get_financial_data`)
- **Bằng chứng & Tái hiện:**
  - Sắp xếp cột quý bằng `sorted(q_cols, reverse=True)` có thể sai nếu định dạng cột không theo chuẩn `YYYY-QX` (ví dụ `Q2/2024` so với `Q4/2023`).
  - Khi số quý có sẵn trong BCTC ít hơn 4 quý (ví dụ công ty mới lên sàn hoặc mới công bố 2 quý), hàm `sum(cfo_series.values())` vẫn tính tổng 2 quý và gắn nhãn là `cfo_ttm`, gây suy giảm nhân tạo 50% dòng tiền hoạt động cả năm.
- **Nguyên nhân gốc rễ:** Thiếu bộ chuẩn hóa kỳ báo cáo (Period Normalizer) và kiểm tra số quan sát tối thiểu (Minimum 4 Quarters for TTM).
- **Biện pháp khắc phục:**
  - Chuẩn hóa tên cột quý theo cấu trúc `YYYY_QX` trước khi sắp xếp theo trục thời gian.
  - Kiểm tra số lượng quý cấu thành TTM: Nếu không đủ 4 quý liên tiếp, đánh dấu `ttm_status = "INCOMPLETE_QUARTERS"` và không gán nhãn TTM giả.
- **Test case kiểm chứng:** `tests/unit/test_data_loader.py::test_quarter_sorting_and_ttm_completeness`

---

### ISSUE-10: Phụ thuộc Thư viện CDN Ngoài Làm Hỏng Báo Cáo Khi Mở Offline
- **Phân loại:** CONFIRMED BUG & USABILITY DEFECT
- **Mức độ nghiêm trọng:** P2
- **Tập tin & Hàm ảnh hưởng:** `core/html_report_generator.py`
- **Bằng chứng & Tái hiện:**
  - Báo cáo HTML gọi `https://cdn.jsdelivr.net/npm/chart.js` và `https://unpkg.com/lightweight-charts@4.1.3/...`.
  - Khi ngắt kết nối mạng Internet hoặc mở file HTML trên máy nội bộ không có mạng, các khung biểu đồ trở nên trống rỗng, kèm lỗi JavaScript trong console.
- **Nguyên nhân gốc rễ:** Không có cơ chế Graceful Offline Fallback (hiển thị biểu đồ SVG thuần hoặc bảng số liệu thay thế khi thư viện CDN không tải được).
- **Biện pháp khắc phục:**
  - Xây dựng fallback nội tuyến: Nếu script CDN không tải được (kiểm tra `window.Chart` hoặc `window.LightweightCharts`), tự động kích hoạt bảng biểu hoặc biểu đồ SVG nội tuyến được nhúng sẵn, đảm bảo người dùng luôn đọc được dữ liệu trực quan ngay cả khi offline hoàn toàn.
- **Test case kiểm chứng:** `tests/report_parity/test_offline_html_rendering.py`

---

## 4. Kế hoạch Hành động Tổng thể (Action Plan)
1. **Giai đoạn 1:** Xây dựng Data Contract & Canonical Schema (`AnalysisResult`).
2. **Giai đoạn 2:** Sửa đổi và chuẩn hóa toàn bộ công thức trong `core/fa_engine.py`, `core/ta_engine.py`, `core/risk_manager.py`, `core/timing_engine.py`, `core/segment_analyzer.py`, `core/macro_engine.py`.
3. **Giai đoạn 3:** Xây dựng bộ Test Suite hoàn chỉnh (Unit, Integration, Contract, Report Parity) bao quát tất cả các trường hợp biên.
4. **Giai đoạn 4:** Tái cấu trúc bộ sinh Báo cáo HTML chuyên nghiệp, đảm bảo nguyên tắc Một nguồn chân lý (Single Source of Truth), trung thực 100% với dữ liệu phân tích và hiển thị hoàn hảo trên Microsoft Edge offline.
