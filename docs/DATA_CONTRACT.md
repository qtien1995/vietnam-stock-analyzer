# DATA_CONTRACT.md — Hợp Đồng Dữ Liệu & Quy Chuẩn Schema Vietnam Stock Analyzer

Tài liệu này xác lập Hợp đồng Dữ liệu (Data Contract) chính thức, bất biến và có hiệu lực ràng buộc đối với tất cả các module trong hệ thống Vietnam Stock Analyzer.

---

## 1. HỆ THỐNG TRẠNG THÁI CHẤT LƯỢNG DỮ LIỆU (DATA QUALITY ENUM)

Mỗi chỉ số hoặc tập dữ liệu trong hệ thống phải mang một trong các trạng thái sau:

| Trạng thái | Ý nghĩa | Hành vi tiếp nhận ở tầng dưới |
| :--- | :--- | :--- |
| `VALID` | Dữ liệu đầy đủ, hợp lệ, đã qua kiểm tra logic kế toán | Được dùng để tính toán và đưa vào kết luận khuyến nghị |
| `VALID_WITH_WARNINGS` | Dữ liệu khả dụng nhưng có cảnh báo nhỏ (ví dụ số liệu kỳ gần nhất chưa kiểm toán) | Cho phép tính toán kèm hiển thị cờ cảnh báo trên báo cáo |
| `STALE` | Dữ liệu cũ quá thời hạn quy định (> 180 ngày chưa có BCTC mới) | Buộc hiển thị cảnh báo dữ liệu cũ; hạ độ tin cậy của khuyến nghị |
| `INSUFFICIENT_DATA` | Thiếu số liệu thiết yếu (ví dụ thiếu số lượng CP hoặc thiếu CFO) | Trả về `None`; cấm thay thế bằng số mặc định tùy tiện |
| `NOT_APPLICABLE` | Tiêu chí không áp dụng cho mô hình này (ví dụ nợ vay đối với Ngân hàng) | Đánh dấu N/A rõ ràng; không tính điểm tiêu chí này |
| `INVALID` | Dữ liệu mâu thuẫn hoặc vô lý (ví dụ giá âm, tổng tài sản âm) | Báo lỗi và từ chối xử lý |

---

## 2. QUY CHUẨN ĐƠN VỊ ĐO LƯỜNG (UNIT CONVENTIONS)

1. **Giá cổ phiếu (Stock Prices):**
   - Nội bộ hệ thống: **VNĐ** (Việt Nam Đồng). Ví dụ: `25400.0`.
   - Nếu dữ liệu thô từ sàn trả về đơn vị nghìn đồng (ví dụ `25.4`): Bộ chuẩn hóa `core/data_loader.py` **bắt buộc** nhân `1,000` ngay tại cửa ngõ vào.
2. **Khối lượng cổ phiếu (Share Quantities):**
   - Đơn vị: **Cổ phiếu nguyên chiếc** (Shares). Ví dụ: `15000000.0`.
3. **Giá trị giao dịch & Giá trị Báo cáo tài chính (Financial Values):**
   - Nội bộ hệ thống: **VNĐ**. Ví dụ: `1250000000000.0` (1,250 tỷ VNĐ).
   - Hiển thị trên Báo cáo: Định dạng thông minh qua `format_vnd_human` (ví dụ `1,250.0 tỷ đ` hoặc `450.5 triệu đ`).
4. **Tỷ lệ phần trăm (Percentages):**
   - Nội bộ hệ thống: Lưu theo giá trị phần trăm thực (ví dụ `15.5` nghĩa là $15.5\%$).
   - Hiển thị: Gắn ký hiệu `%` và làm tròn 1-2 chữ số thập phân (`15.5%`).
5. **Hệ số bội số (Multiples):**
   - Đơn vị: Lần (x). Ví dụ: `pe = 12.4`, hiển thị `12.4x`.

---

## 3. CANONICAL ANALYSIS RESULT SCHEMA SPECIFICATION

Hợp đồng dữ liệu `AnalysisResult` được định nghĩa trong `core/models.py` với cấu trúc:

```python
class DataQualityStatus(str, Enum):
    VALID = "VALID"
    VALID_WITH_WARNINGS = "VALID_WITH_WARNINGS"
    STALE = "STALE"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    NOT_APPLICABLE = "NOT_APPLICABLE"
    INVALID = "INVALID"

class RecommendationAction(str, Enum):
    STRONG_BUY = "MUA MẠNH (STRONG BUY)"
    TEST_BUY = "MUA THĂM DÒ (TEST BUY)"
    WATCHLIST = "THEO DÕI (WATCHLIST)"
    AVOID = "BÁN / TRÁNH XA (AVOID)"
    NO_VALID_SETUP = "CHƯA CÓ ĐIỂM MUA HỢP LỆ (NO SETUP)"

class ConfidenceLevel(str, Enum):
    HIGH = "CAO"
    MEDIUM = "VỪA"
    LOW = "THẤP"
```

### Các Khối Thuộc Tính Chính của `AnalysisResult`:
1. **Metadata:**
   - `symbol: str` (ví dụ: "HPG")
   - `company_name: str`
   - `exchange: str` ("HOSE", "HNX", "UPCOM")
   - `price_limit_pct: float` (7.0, 10.0, 15.0)
   - `analysis_timestamp: datetime`
   - `market_data_as_of: datetime`
   - `latest_financial_quarter: str` (ví dụ: "2024-Q3")
   - `data_quality_status: DataQualityStatus`
   - `data_warnings: List[str]`

2. **Market & Quote Data:**
   - `current_price: float` (VNĐ)
   - `ref_price: float`
   - `change: float`
   - `change_pct: float`
   - `volume: float`
   - `trading_value: float`
   - `foreign_net_vol: float`

3. **Fundamental Analysis (`fa`):**
   - `ratios`: `pe`, `pb`, `roe`, `roa`, `roic`, `gross_margin`, `net_margin`, `debt_to_equity`
   - `cash_flow`: `cfo_ttm`, `capex_ttm`, `fcf_ttm`, `quality_grade`, `altman_z`, `z_zone`, `earnings_quality_ratio`
   - `f_score`: `piotroski_score` (0-9), `f_score_variant` ("STANDARD" / "MODIFIED_STATIC")
   - `valuation`: `fair_price`, `margin_of_safety_pct`, `bvps`, `tbvps`, `ncavps`, `valuation_scenario`
   - `segments`: Danh sách phân khúc thực tế từ BCTC (hoặc rỗng nếu chưa kiểm chứng)

4. **Technical Analysis (`ta`):**
   - `indicators`: `ema20`, `ema50`, `sma200`, `rsi14`, `macd`, `macd_signal`, `atr14`, `sup_20d`, `res_20d`, `vol_ratio`
   - `patterns`: `pattern_name`, `vcp_stage`, `vsa_signal`, `fibo_levels`

5. **Risk Management & Trade Setup (`trade_setup`):**
   - `has_valid_setup: bool`
   - `action: RecommendationAction`
   - `confidence: ConfidenceLevel`
   - `consensus_score: int` (0-100)
   - `buy_zone: str`
   - `stop_loss: float`
   - `stop_loss_pct: float`
   - `take_profit_1: float`
   - `take_profit_2: float`
   - `risk_reward_ratio: float`
   - `max_position_size_pct: float`
   - `invalidation_conditions: List[str]`

6. **Council Synthesis (`council`):**
   - `members`: Danh sách 5 chuyên gia với luận điểm, điểm số, và điều kiện vô hiệu hóa.
   - `clash_of_perspectives`: Điểm mâu thuẫn chính giữa các trường phái.
   - `cro_verdict`: Phán quyết của Giám đốc Quản trị rủi ro.

---

## 4. QUY TẮC BẤT DI BẤT DỊCH CHO CONSUMERS
- Mọi giao diện (Terminal, HTML, Markdown, Telegram, Dashboard) **PHẢI** đọc dữ liệu từ `AnalysisResult`.
- Tuyệt đối không có module hiển thị nào được phép ghi đè (overwrite) hoặc tính toán lại bất kỳ trường số liệu nào.
