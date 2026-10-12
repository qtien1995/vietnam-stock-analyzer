# FORMULA_AUDIT.md — Toàn Văn Kiểm Toán Công Thức Tài Chính & Định Lượng

Tài liệu này kiểm toán chi tiết từng công thức toán học và tài chính được áp dụng trong hệ thống Vietnam Stock Analyzer, đối chiếu với các nguồn học thuật và thực tiễn chuẩn mực quốc tế.

---

## 1. CÔNG THỨC PHÂN TÍCH CƠ BẢN (FUNDAMENTAL ANALYSIS)

### 1.1 Tăng Trưởng Doanh Thu & Lợi Nhuận Cùng Kỳ (YoY Growth)
- **Định nghĩa:** Tỷ lệ phần trăm tăng/giảm của Doanh thu thuần hoặc Lợi nhuận sau thuế của một quý so với cùng kỳ năm trước.
- **Biểu thức toán học:**
  $$\text{Growth}_{\text{YoY}} = \frac{V_t - V_{t-4}}{|V_{t-4}|} \times 100\%$$
- **Đầu vào:** $V_t$ (giá trị quý hiện tại), $V_{t-4}$ (giá trị quý cùng kỳ năm trước).
- **Đơn vị & Kỳ:** Triệu VNĐ hoặc Tỷ VNĐ; định kỳ theo Quý (Quarterly).
- **Điều kiện hợp lệ:** $V_{t-4} \neq 0$ và cả hai kỳ cùng tuân theo một chuẩn mực kế toán (VAS hợp nhất).
- **Trường hợp không xác định (Undefined):** Khi $V_{t-4} = 0$ hoặc thiếu dữ liệu quý $t-4$.
- **Xử lý đặc biệt khi lợi nhuận kỳ trước âm:** Dùng mẫu số $|V_{t-4}|$ để chiều biến động phản ánh đúng thực chất (chuyển từ lỗ sang lãi là tăng trưởng dương).
- **Vị trí cài đặt:** `core/fa_engine.py` / `core/data_loader.py`.

---

### 1.2 Biên Lợi Nhuận (Profit Margins: Gross, Operating, Net)
- **Biểu thức toán học:**
  $$\text{Gross Margin} = \frac{\text{Gross Profit}}{\text{Net Revenue}} \times 100\%$$
  $$\text{Net Margin} = \frac{\text{Net Profit After Tax}}{\text{Net Revenue}} \times 100\%$$
- **Đầu vào:** Lợi nhuận gộp, Lợi nhuận sau thuế TTM, Doanh thu thuần TTM.
- **Điều kiện hợp lệ:** $\text{Net Revenue} > 0$.
- **Trường hợp không xác định:** $\text{Net Revenue} \leq 0 \implies \text{Margin} = \text{None}$ (trạng thái `UNDEFINED_ZERO_REVENUE`). Không áp dụng cho Ngân hàng (dùng NIM thay thế).

---

### 1.3 Tỷ Suất Sinh Lời: ROE, ROA, ROIC & DuPont Decomposition
- **Biểu thức toán học:**
  $$\text{ROE} = \frac{\text{Net Profit (TTM)}}{\text{Average Owners' Equity}} \times 100\%$$
  $$\text{ROA} = \frac{\text{Net Profit (TTM)}}{\text{Average Total Assets}} \times 100\%$$
  $$\text{ROIC} = \frac{\text{NOPAT}}{\text{Invested Capital}} = \frac{\text{EBIT} \times (1 - t)}{\text{Total Debt} + \text{Owners' Equity} - \text{Cash}}$$
- **Phân rã DuPont 3 nhân tố:**
  $$\text{ROE} = \left(\frac{\text{Net Profit}}{\text{Revenue}}\right) \times \left(\frac{\text{Revenue}}{\text{Assets}}\right) \times \left(\frac{\text{Assets}}{\text{Equity}}\right) = \text{Net Margin} \times \text{Asset Turnover} \times \text{Equity Multiplier}$$
- **Điều kiện hợp lệ:** Vốn chủ sở hữu $> 0$, Tổng tài sản $> 0$.
- **Xử lý biên:** Nếu Vốn chủ sở hữu $\leq 0$ (âm vốn chủ do lỗ lũy kế), ROE không được tính vì sẽ tạo ra số dương sai lệch (lỗ / vốn âm ra dương). Hệ thống gán `roe = None`, trạng thái `NEGATIVE_EQUITY`.

---

### 1.4 Dòng Tiền Tự Do (Free Cash Flow - FCF) & Chất Lượng Lợi Nhuận
- **Biểu thức toán học:**
  $$\text{FCF} = \text{CFO} - \text{CapEx}$$
  $$\text{Earnings Quality Ratio} = \frac{\text{CFO (TTM)}}{\text{Net Profit (TTM)}}$$
- **Ý nghĩa:**
  - $\text{CFO} > \text{Net Profit}$: Lợi nhuận có chất lượng cao, thu được tiền mặt thực chất.
  - $\text{CFO} < 0$ trong khi $\text{Net Profit} > 0$: Cảnh báo nghiêm trọng về lợi nhuận trên giấy tờ (Accrual Trap), nguy cơ doanh thu ảo hoặc ứ đọng phải thu.
- **Vị trí cài đặt:** `core/fa_engine.py` (`evaluate_cash_flow_forensic`).

---

### 1.5 Điểm Số Piotroski F-Score (Chuẩn 9 Tiêu Chí Kế Toán)
- **Nguồn:** GS. Joseph Piotroski (Đại học Chicago, 2000).
- **9 Tín hiệu nhị phân (0 hoặc 1 điểm, Tổng: 0 - 9 điểm):**
  1. **ROA dương:** $\text{ROA}_t > 0$ (+1)
  2. **Dòng tiền CFO dương:** $\text{CFO}_t > 0$ (+1)
  3. **Biến động sinh lời tích cực:** $\Delta\text{ROA} = \text{ROA}_t - \text{ROA}_{t-1} > 0$ (+1)
  4. **Chất lượng dòng tiền:** $\text{CFO}_t > \text{Net Profit}_t$ (+1)
  5. **Giảm đòn bẩy nợ:** $\text{LongTermDebt}_t / \text{Assets}_t \leq \text{LongTermDebt}_{t-1} / \text{Assets}_{t-1}$ (+1)
  6. **Cải thiện thanh khoản:** $\text{CurrentRatio}_t > \text{CurrentRatio}_{t-1}$ (+1)
  7. **Không pha loãng cổ phiếu:** $\text{Shares}_t \leq \text{Shares}_{t-1}$ (+1)
  8. **Cải thiện biên lãi gộp:** $\text{GrossMargin}_t > \text{GrossMargin}_{t-1}$ (+1)
  9. **Cải thiện vòng quay tài sản:** $\text{AssetTurnover}_t > \text{AssetTurnover}_{t-1}$ (+1)
- **Quy tắc hệ thống:**
  - Khi có đủ số liệu so sánh 2 kỳ: Tính chuẩn 9 tiêu chí Piotroski.
  - Khi chỉ có số liệu 1 kỳ: Tính phiên bản rút gọn có nhãn `MODIFIED_STATIC_FSCORE`, minh bạch rõ ràng từng tiêu chí thành phần.
  - Đối với Ngân hàng: Loại trừ tiêu chí đòn bẩy phi tài chính, thay bằng CAMELS Proxy.

---

### 1.6 Chỉ Số Kiệt Quệ Tài Chính Altman Z''-Score (Thị Trường Mới Nổi)
- **Nguồn:** Edward I. Altman (Mô hình 4 biến số cho Doanh nghiệp Phi sản xuất & Thị trường mới nổi):
  $$Z'' = 6.56 X_1 + 3.26 X_2 + 6.72 X_3 + 1.05 X_4$$
  - $X_1 = \frac{\text{Working Capital}}{\text{Total Assets}}$
  - $X_2 = \frac{\text{Retained Earnings}}{\text{Total Assets}}$
  - $X_3 = \frac{\text{EBIT}}{\text{Total Assets}}$
  - $X_4 = \frac{\text{Book Value of Equity}}{\text{Total Liabilities}}$
- **Ngưỡng đánh giá:**
  - $Z'' > 2.60$: Vùng An toàn (Safe Zone).
  - $1.10 \leq Z'' \leq 2.60$: Vùng Xám (Grey Zone - Cần theo dõi).
  - $Z'' < 1.10$: Vùng Nguy hiểm (Distress Zone - Rủi ro kiệt quệ tài chính cao).
- **Phạm vi áp dụng:** Doanh nghiệp sản xuất, xây dựng, bán lẻ; KHÔNG áp dụng cho Ngân hàng và Chứng khoán.

---

## 2. CÔNG THỨC ĐỊNH GIÁ (VALUATION MODELS)

### 2.1 Định Giá Theo Khối Tài Sản Ròng (Asset-Based Valuation)
- **Giá trị sổ sách trên mỗi cổ phiếu (BVPS):**
  $$\text{BVPS} = \frac{\text{Owners' Equity}}{\text{Total Outstanding Shares}}$$
- **Giá trị tài sản hữu hình trên mỗi cổ phiếu (TBVPS):**
  $$\text{TBVPS} = \frac{\text{Owners' Equity} - \text{Intangible Assets}}{\text{Total Outstanding Shares}}$$
- **Giá trị tài sản lưu động ròng theo Graham (NCAVPS / Net-Net):**
  $$\text{NCAVPS} = \frac{\text{Current Assets} - \text{Total Liabilities}}{\text{Total Outstanding Shares}}$$
- **Tiền mặt ròng trên mỗi cổ phiếu (Net Cash Per Share):**
  $$\text{Net Cash/Share} = \frac{\text{Cash \& Short-term Investments} - \text{Total Debt}}{\text{Total Outstanding Shares}}$$
- **Biên an toàn tài sản (% Asset Discount):**
  $$\text{Asset Discount} = \frac{\text{BVPS} - \text{Price}}{\text{BVPS}} \times 100\%$$
- **Điều kiện hợp lệ:** $\text{Shares} > 0$, $\text{Owners' Equity} > 0$. Nếu BVPS $\leq 0 \implies \text{P/B} = \text{None}$.

---

### 2.2 Định Giá Bội Số P/E, P/B & Bội Số Tăng Trưởng PEG
- **Hệ số P/E:**
  $$\text{P/E} = \frac{\text{Current Price}}{\text{EPS (TTM)}}$$
  *Điều kiện hợp lệ:* $\text{EPS} > 0$. Khi $\text{EPS} \leq 0 \implies \text{P/E} = \text{None}$ (ghi rõ "LỖ / KHÔNG TÍNH ĐƯỢC"). Tuyệt đối không gán mặc định 15.0x.
- **Hệ số P/B:**
  $$\text{P/B} = \frac{\text{Current Price}}{\text{BVPS}}$$
  *Điều kiện hợp lệ:* $\text{BVPS} > 0$. Khi $\text{BVPS} \leq 0 \implies \text{P/B} = \text{None}$. Tuyệt đối không gán mặc định 1.5x.
- **Hệ số PEG (Peter Lynch):**
  $$\text{PEG} = \frac{\text{P/E}}{\text{Profit Growth Rate (YoY)}}$$
  *Điều kiện hợp lệ:* $\text{P/E}$ xác định và $\text{Growth Rate} > 0$. Khi $\text{Growth} \leq 0 \implies \text{PEG} = \text{None}$ (ghi rõ "TĂNG TRƯỞNG ÂM / KHÔNG ÁP DỤNG").

---

## 3. CÔNG THỨC PHÂN TÍCH KỸ THUẬT (TECHNICAL ANALYSIS)

### 3.1 Đường Trung Bình Động EMA & SMA
- **SMA $N$ phiên:**
  $$\text{SMA}_t(N) = \frac{1}{N} \sum_{i=0}^{N-1} \text{Close}_{t-i}$$
- **EMA $N$ phiên:**
  $$\alpha = \frac{2}{N + 1}, \quad \text{EMA}_t(N) = \text{Close}_t \times \alpha + \text{EMA}_{t-1}(N) \times (1 - \alpha)$$

### 3.2 Chỉ Số Sức Mạnh Tương Đối RSI 14 (Wilder's Smoothing)
- $$\text{RS} = \frac{\text{Average Gain}_{14}}{\text{Average Loss}_{14}}, \quad \text{RSI} = 100 - \frac{100}{1 + \text{RS}}$$

### 3.3 Độ Biến Động Thực Tế ATR 14 (Average True Range)
- $$\text{TR}_t = \max(\text{High}_t - \text{Low}_t, |\text{High}_t - \text{Close}_{t-1}|, |\text{Low}_t - \text{Close}_{t-1}|)$$
- $$\text{ATR}_t(14) = \frac{\text{ATR}_{t-1}(14) \times 13 + \text{TR}_t}{14}$$

### 3.4 Fibonacci Retracement & Overhead Supply
- Dải dao động: $\text{Diff} = \text{High}_{\text{lookback}} - \text{Low}_{\text{lookback}}$
- $\text{Fibo 38.2\%} = \text{High} - 0.382 \times \text{Diff}$
- $\text{Fibo 50.0\%} = \text{High} - 0.500 \times \text{Diff}$
- $\text{Fibo 61.8\%} = \text{High} - 0.618 \times \text{Diff}$

---

## 4. CÔNG THỨC QUẢN TRỊ RỦI RO & PHÂN BỔ VỐN (RISK MANAGEMENT)

### 4.1 Điểm Cắt Lỗ Kỷ Luật (Stop Loss)
- Đặt dưới hỗ trợ gần nhất có biên đệm hoặc theo ATR:
  $$\text{SL}_{\text{candidate}} = \min(\text{Support}_{20d} \times 0.98, \text{Price} - 2.0 \times \text{ATR}_{14})$$
- Ràng buộc theo quy định biên độ sàn giao dịch:
  $$\text{SL} = \min(\max(\text{SL}_{\text{candidate}}, \text{Price} \times (1 - \text{Limit}_{\max})), \text{Price} \times (1 - \text{Limit}_{\min}))$$
- **Cảnh báo bắt buộc:** Mức cắt lỗ là điều kiện kích hoạt lệnh kỷ luật, không phải bảo đảm tài chính trong kịch bản mở gap giảm sàn trắng bên mua.

### 4.2 Tỷ Trọng Danh Mục Tối Đa (% NAV Allocation)
- Rủi ro tối đa cho phép trên 1 cổ phiếu: 1.5% tổng giá trị tài sản ròng danh mục (NAV).
- Tỷ trọng vị thế lý thuyết:
  $$\text{Position Size} = \min\left(\frac{1.5\%}{\text{Stop Loss \%}}, 25.0\%\right)$$
  - Khuyến nghị Mua mạnh: Tối đa 25% NAV.
  - Khuyến nghị Mua thăm dò: Tối đa 15% NAV.
  - Khuyến nghị Theo dõi: Tối đa 5% NAV.
  - Khuyến nghị Tránh xa / Bán: 0% NAV (`NO_VALID_SETUP`).
