# REPORT_AUDIT.md — Kiểm Toán Toàn Diện Báo Cáo HTML & Nguyên Nhân Đứt Gãy Parity

Tài liệu này truy vết và phân tích tường tận nguyên nhân gốc rễ của hiện tượng người dùng phản ánh: *"Phân tích trong môi trường lập trình thì ổn, nhưng báo cáo HTML xuất ra lại chứa nhiều điểm sai lệch."*

---

## 1. NGUYÊN NHÂN GỐC RỄ CỦA SỰ SAI LỆCH (ROOT CAUSES OF HTML INACCURACIES)

### 1.1 Khởi Tạo Lại Tính Toán Tùy Tiện Bên Trong Renderer (Renderer Recalculation)
- **Thực trạng cũ:** Hàm `generate_html_report` trong `core/html_report_generator.py` thay vì đóng vai trò là một tầng biểu diễn thuần túy (pure presentation layer), đã tự ý tính toán lại các biến số tài chính.
- **Ví dụ điển hình:**
  - Dòng 784-790: Tự gọi lại `timing_result = analyze_timing_prediction(...)` nếu thiếu, sử dụng tham số mặc định khác với tham số đã tính ở `stock_service.py`.
  - Tự động gán lại màu sắc hành động và phán quyết dựa trên chuỗi text thay vì đọc trường enum chuẩn.
  - Tự suy luận tỷ lệ đòn bẩy nợ và biên an toàn bằng logic riêng lẻ trong hàm `build_comprehensive_macro_impact_matrix`.

### 1.2 Chèn Ép Số Liệu và Nhận Định Giả Mạo Cố Định (Hardcoded Fabricated Statements)
- **Thực trạng cũ:** Báo cáo HTML chứa các câu khẳng định cứng được in sẵn:
  - Cho mọi mã cao su: *"Mảng mủ cao su tự nhiên là nguồn thu tiền mặt cốt lõi chiếm tới ~70% doanh thu của {sym}... mở rộng biên lợi nhuận gộp từ 18% lên trên 24-28%..."*
  - Cho mọi mã xuất khẩu: *"{sym} là nhà xuất khẩu lớn thu về ngoại tệ USD... duy trì tỷ lệ đòn bẩy vay nợ ngoại tệ rất thấp nên không chịu rủi ro lỗ tỷ giá..."* (thực tế có những công ty xuất khẩu vay nợ USD hàng nghìn tỷ).
  - Tự sinh các dự án ảo cho các công ty chưa có file segment JSON.
- **Tác động:** Báo cáo HTML đưa ra các kết luận hoàn toàn sai lệch so với dữ liệu tài chính thực tế của doanh nghiệp đang phân tích.

### 1.3 Bất Đồng Bộ Giữa Thẻ Tóm Tắt (Cards), Bảng Biểu (Tables) và Đồ Thị (Charts)
- **Thực trạng cũ:**
  - Trên Thẻ Tóm Tắt: Hiển thị P/E = 15.0x (do fallback mặc định khi EPS âm).
  - Trong Bảng Chỉ Số: Hiển thị LNST âm.
  - Trên Đồ Thị Dòng Tiền: Cột LNST âm nhưng trên thẻ tóm tắt lại ghi là "Cổ phiếu định giá hợp lý P/E 15x".
  - Đây chính là nguyên nhân trực tiếp khiến người dùng thấy báo cáo "tự mâu thuẫn và thiếu tin cậy".

### 1.4 Sai Lệch Kỳ Báo Cáo và Đơn Vị Đo Lường (Units & Periods Mismatch)
- **Thực trạng cũ:**
  - Một số chỗ dùng VNĐ, một số chỗ dùng Nghìn VNĐ hoặc Tỷ VNĐ mà không có nhãn đơn vị rõ ràng.
  - Chuỗi 4 quý trên biểu đồ `cashFlowChart` được gán nhãn tĩnh `["Q3", "Q4", "Q1", "Q2"]` nếu dữ liệu quý rỗng, khiến người dùng lầm tưởng đó là 4 quý thực tế.
  - Trộn lẫn số liệu luỹ kế năm với số liệu TTM hoặc số liệu quý đơn lẻ.

### 1.5 Phụ Thuộc CDN Bên Ngoài Khiến Báo Cáo Trắng Biểu Đồ Khi Mở Offline
- **Thực trạng cũ:** Báo cáo gọi thư viện qua CDN:
  - `https://cdn.jsdelivr.net/npm/chart.js`
  - `https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js`
- **Hậu quả:** Khi người dùng mở file HTML trên Microsoft Edge ở chế độ không có kết nối internet, mã JavaScript ném lỗi `Chart is not defined`, toàn bộ khu vực biểu đồ bị treo trắng, mất khả năng tương tác.

---

## 2. QUY CHUẨN THIẾT KẾ BÁO CÁO MỚI (REPORT SPECIFICATION & PARITY ENFORCEMENT)

### 2.1 Cấu Trúc 13 Khối Báo Cáo Chuẩn Mực (Institutional Structure)
1. **Executive Investment Snapshot (Tóm tắt chiến lược điều hành):**
   - Mã cổ phiếu, Sàn, Tên công ty, Ngành nghề, Giá hiện tại, Biến động phiên.
   - Phán quyết: `Mua dần / Chờ / Theo dõi / Tránh` + Độ tin cậy + Lý do trọng tâm.
   - Trạng thái thiết lập: `VALID_SETUP` hoặc `NO_VALID_SETUP`.
2. **Data Freshness & Provenance (Chất lượng và độ tươi dữ liệu):**
   - Ngày giờ dữ liệu thị trường, Kỳ BCTC mới nhất (`latest_quarter`).
   - Nguồn gốc số liệu (Realtime / EOD / Cache) và Trạng thái (`VALID`, `STALE`, `INSUFFICIENT`).
3. **Core Investment Thesis & Invalidation (Luận điểm trung tâm & Điều kiện mất hiệu lực):**
   - Bằng chứng ủng hộ, Bằng chứng phản đối, Ngưỡng vô hiệu hóa luận điểm.
4. **Fundamental Analysis & Financial Health (Sức khỏe tài chính & Khả năng sinh lời):**
   - Tăng trưởng, Biên lợi nhuận, ROE/ROA/ROIC, DuPont proxy, F-Score.
5. **Cash Flow Forensic & Earnings Quality (Kiểm toán dòng tiền & Chất lượng lợi nhuận):**
   - CFO TTM, CapEx TTM, FCF TTM, Tỷ lệ CFO/Net Profit, Altman Z''-Score.
6. **Quarterly Trend Chart & Tables (Biểu đồ & Bảng xu hướng quý):**
   - So sánh Dòng tiền thật CFO vs LNST kế toán kèm bảng số liệu chi tiết.
7. **Valuation Scenarios & Margin of Safety (Định giá kịch bản & Biên an toàn):**
   - BVPS, TBVPS, NCAVPS, P/E, P/B, PEG (kèm trạng thái hợp lệ).
   - Giá trị hợp lý ước tính và Biên an toàn (% Margin of Safety).
8. **Technical Analysis & Momentum (Phân tích kỹ thuật & Xu hướng):**
   - EMA20, EMA50, SMA200, RSI, MACD, Volume MA20.
   - Nhận diện mẫu hình nén biên độ (VCP) và hành vi VSA.
9. **Interactive Candlestick Chart (Biểu đồ nến Nhật tương tác):**
   - Nến OHLCV, đường EMA, mốc Pivot và Stop Loss trực quan.
10. **Risk Management & Execution Plan (Kế hoạch quản trị rủi ro & Thực thi):**
    - Vùng giải ngân, Mức kích hoạt cắt lỗ kỷ luật, Mục tiêu giá, Tỷ trọng tối đa % NAV.
11. **Business Model & Core Segments (Mô hình kinh doanh & Phân khúc thật):**
    - Cơ cấu phân khúc từ BCTC thật (chỉ hiển thị khi có dữ liệu kiểm chứng, không bịa số liệu).
12. **Corporate Governance & Ownership (Quản trị doanh nghiệp & Cổ đông):**
    - Cơ cấu cổ đông lớn, Cam kết vốn ban lãnh đạo (Skin in the game), Rủi ro giao dịch liên quan.
13. **Multi-Perspective Council Synthesis (Bàn tròn Hội đồng Tham mưu 5 Góc nhìn):**
    - Ý kiến chi tiết của từng trường phái tư duy và điểm va chạm tranh biện.

---

## 3. NGUYÊN TẮC PARITY TUYỆT ĐỐI (ZERO DISCREPANCY RULE)

Mọi giá trị số hiển thị trên HTML **PHẢI** thỏa mãn:
$$V_{\text{HTML}} \equiv V_{\text{AnalysisResult}}$$
- Chỉ cho phép phép biến đổi hiển thị được tài liệu hóa (làm tròn số thập phân, phân cách hàng nghìn bằng dấu phẩy, chuyển đổi tỷ VNĐ).
- Tuyệt đối không có bất kỳ logic `if/else` nào trong file HTML làm thay đổi giá trị của chỉ số hoặc khuyến nghị.
- Tích hợp bộ kiểm thử tự động `tests/report_parity/test_html_parity.py` parse trực tiếp HTML đã render để so khớp từng con số với `AnalysisResult`.
