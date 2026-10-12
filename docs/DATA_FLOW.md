# DATA_FLOW.md — Luồng Dữ Liệu Chi Tiết Của Hệ Thống Vietnam Stock Analyzer

## 1. Bản Đồ Luồng Dữ Liệu Tổng Thể (End-to-End Data Pipeline)

```
[1. Data Sources]
  ├── SSI iBoard (Realtime Prices, Order Book, Foreign Flow)
  ├── DNSE / Entrade (Historical OHLCV Candles)
  ├── vnstock / VCI (Quarterly Financial Statements, Overview, Shareholders, Officers, Subsidiaries)
  ├── Yahoo Finance (Crude Oil Brent, Gold Spot, DXY Index)
  └── Local Storage / User Overrides (data/segments/{symbol}.json, config.py)
         │
         ▼
[2. Raw Data Ingestion]
  ├── Dict: raw_quote (price, ref, vol, val, high, low, foreign)
  ├── DataFrame: raw_ohlcv (time, open, high, low, close, volume)
  ├── Dict: raw_financials (balance_sheet, income_statement, cash_flow)
  ├── Dict: raw_governance (shareholders, officers, subsidiaries, overview)
  └── Dict: raw_macro (global_commodities, vietnam_macro)
         │
         ▼
[3. Data Normalization & Quality Gate]
  ├── Unit Harmonization: Chuyển toàn bộ giá sang VNĐ, chia cổ phiếu nguyên chiếc
  ├── Period Alignment: Sắp xếp các cột quý theo chuỗi thời gian chuẩn YYYY_QX
  ├── Outlier & Sanity Check: Giá > 0, Volume >= 0, Cân đối kế toán (Tài sản ≈ Nợ + Vốn CSH)
  └── Status Assignment: VALID / VALID_WITH_WARNINGS / STALE / INSUFFICIENT / NOT_APPLICABLE
         │
         ▼
[4. Historical Persistence]
  └── SQLite (data/market.db)
        ├── stock_master (symbol, exchange, company_name, sector, price_limit_pct)
        └── eod_quotes (symbol, trading_date, OHLCV, foreign_net_vol)
         │
         ▼
[5. Quantitative Analytical Engines]
  ├── Financial Engine (core/fa_engine.py):
  │     ├── Growth & Margins (Revenue, Profit, Gross, Operating, Net)
  │     ├── Returns (ROE, ROA, ROIC, DuPont proxy)
  │     ├── Cash Flow Forensic (CFO TTM, CapEx TTM, FCF TTM, CFO/Net Profit)
  │     ├── Balance Sheet Health (Debt/Equity, Working Capital, Altman Z''-Score)
  │     └── Accounting Signals (Piotroski F-Score standard / modified)
  │
  ├── Technical Engine (core/ta_engine.py):
  │     ├── Moving Averages (EMA20, EMA50, SMA200)
  │     ├── Momentum & Volatility (RSI14, MACD, ATR14)
  │     ├── Volume Dynamics (vol_ma20, vol_ratio, Pocket Pivot)
  │     ├── Support / Resistance & Breakout detection
  │     └── Pattern Recognition (VCP Minervini, VSA Price Action, Fibonacci)
  │
  ├── Macro & Sector Engine (core/macro_engine.py):
  │     ├── Sector Classification (100% 1,500+ tickers via dynamic rules)
  │     ├── Commodity Sensitivity & Transmission Lag
  │     └── Macro Tailwind Score (0 - 100)
  │
  ├── Governance Analyzer (core/governance_analyzer.py):
  │     ├── Free float, State ownership, Foreign ownership
  │     ├── Leadership alignment (Skin in the game)
  │     └── Related-party & Shell network risk (G-Score 0 - 100)
  │
  └── Segment Analyzer (core/segment_analyzer.py):
        └── Core business segments & real project tracking (No fabrication)
         │
         ▼
[6. Valuation & Risk Integration]
  ├── Valuation Engine (core/fa_engine.py):
  │     ├── Asset-Based (BVPS, TBVPS, NCAVPS, Net Cash Per Share)
  │     ├── Multiples (P/E, P/B, PEG with strict domain validity)
  │     └── Fair Price & Margin of Safety calculation
  │
  └── Risk Manager (core/risk_manager.py):
        ├── Setup Validation Gate (has_valid_setup: True/False)
        ├── Dynamic Stop Loss (placed below support/ATR, bounded by exchange limit)
        ├── Take Profit Scenarios (TP1, TP2, TP3 based on resistance & fair price)
        ├── Risk/Reward ratio calculation
        └── Position sizing (% NAV based on 1.5% max portfolio risk)
         │
         ▼
[7. Council Deliberation & Synthesis]
  ├── Multi-Agent Council (ai/council.py):
  │     ├── 5 Perspectives (Value, Growth, Technical, Macro, Risk)
  │     ├── Voting summary & Consensus score (0 - 100)
  │     ├── Clash of perspectives & CRO synthesis
  │     └── Invalidation conditions
  │
  └── Canonical AnalysisResult (core/models.py):
        └── Hợp đồng dữ liệu duy nhất chứa toàn bộ kết quả phân tích
         │
         ▼
[8. Presentation & Delivery]
  ├── HTML Report Generator (reports/YYYY-MM-DD_{symbol}.html)
  ├── Markdown Report (reports/YYYY-MM-DD_{symbol}.md)
  ├── Terminal CLI Dashboard (Rich formatted tables & panels)
  ├── Offline Dashboard (DASHBOARD.html)
  ├── Telegram Alerts & Interactive Bot (alerts/)
  └── Performance Tracking (market.db -> recommendations & performance_tracking)
```

---

## 2. Truy Vết Dữ Liệu Từng Thành Phần (Data Lineage & Dependencies)

### 2.1 Từ Báo Cáo Tài Chính tới Báo Cáo HTML
1. **Nguồn:** `stock.finance.balance_sheet`, `income_statement`, `cash_flow`.
2. **Chuẩn hóa:** `clean_val` bóc tách số thực; lọc và sắp xếp chính xác 4 quý gần nhất; kiểm tra có đủ 4 quý để tính TTM hay không.
3. **Tính toán:**
   - `cfo_ttm`: Tổng CFO của 4 quý gần nhất (nếu đủ 4 quý).
   - `fcf_ttm = cfo_ttm - capex_ttm`.
   - `earnings_quality_ratio = cfo_ttm / ttm_profit`.
4. **Canonical Schema:** Lưu vào `AnalysisResult.fa.cash_flow` và `AnalysisResult.fa.ratios`.
5. **Render HTML:** Tầng HTML chỉ đọc `result.fa.cash_flow.cfo_ttm` và chuỗi `quarterly_cash_flows` để vẽ bảng và biểu đồ Chart.js.

### 2.2 Từ Dữ Liệu Giá tới Kế Hoạch Giao Dịch
1. **Nguồn:** Khớp lệnh SSI iBoard hoặc nến DNSE.
2. **Chuẩn hóa:** Giá chuẩn VNĐ; xác định chính xác Sàn giao dịch (HOSE: biên độ 7%, HNX: 10%, UPCoM: 15%).
3. **Tính toán TA:** Tính các đường trung bình EMA20, EMA50, Hỗ trợ 20 phiên (`sup_20d`), Kháng cự 20 phiên (`res_20d`), biến động ATR14.
4. **Thiết lập Giao dịch (Risk Manager):**
   - Xác định xu hướng: nếu `price < ema20 and price < ema50` $\to$ Cảnh báo Downtrend.
   - Nếu vi phạm nghiêm trọng: `has_valid_setup = False`, `action = "BÁN / TRÁNH XA"`, không sinh điểm mua giả tạo.
   - Nếu đạt chuẩn: Đặt cắt lỗ `stop_loss = min(sup_20d * 0.98, price - 2*atr)`, giới hạn theo biên độ sàn.
5. **Canonical Schema:** Lưu vào `AnalysisResult.trade_setup`.
6. **Render HTML:** Hiển thị trực quan trên thước đo Price Ladder và đồ thị nến TradingView.

---

## 3. Các Điểm Nghẽn và Lỗ Hổng Đã Được Loại Bỏ (Eliminated Deficiencies)
1. **Loại bỏ tính toán lặp:** Trước đây cả `fa_engine`, `risk_manager`, `stock_service` và `html_report_generator` đều tự tính lại `fair_price` hoặc `pe/pb`. Nay toàn bộ được tính một lần duy nhất tại Engine và truyền qua `AnalysisResult`.
2. **Loại bỏ Fallback thầm lặng:** Không còn hiện tượng số liệu thiếu tự động biến thành 15.0x hoặc 1.5x.
3. **Loại bỏ Tự sinh Phân khúc ảo:** Dữ liệu phân khúc rỗng sẽ được đánh dấu rõ ràng `INSUFFICIENT_DATA`.
4. **Loại bỏ Phụ thuộc CDN cứng:** Tích hợp bộ vẽ biểu đồ bảng số liệu nội tuyến khi máy tính không kết nối mạng.
