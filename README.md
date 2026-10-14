# 🏛️ VIETNAM STOCK ANALYZER (ZERO-SERVER LOCAL TERMINAL)

> **Hệ thống Phân tích Chứng khoán Cục bộ Đa AI & Bảng Điều Khiển Offline**  
> Kết hợp Phân tích Cơ bản (FA), Phân tích Kỹ thuật (TA), Radar Vĩ mô & Hàng hóa thế giới, Động cơ Dự báo Thời điểm (Timing Engine: *Khi nào tăng? Khi nào sập?*) và Hội đồng Phản biện Đa góc nhìn (Warren Buffett, Peter Lynch, William O'Neil, Price Action VSA & Chief Risk Officer).  
> *Kiến trúc Zero-Server: Hoạt động offline mượt mà trên Microsoft Edge (`file:///...`), không cần server nền, bảo mật tuyệt đối dữ liệu cục bộ.*

---

## 🎯 1. TỔNG QUAN DỰ ÁN & CÁC NĂNG LỰC CỐT LÕI

Dự án là trạm phân tích chứng khoán Việt Nam (HOSE, HNX, UPCoM) chạy trực tiếp trên máy tính cá nhân (Windows), giải quyết triệt để các bài toán then chốt:

1. **Kiến trúc Zero-Server (Offline trên Microsoft Edge):**
   - Không cần khởi động server nền phức tạp, không cần giữ cửa sổ console đen treo máy.
   - Toàn bộ giao diện điều hành ([`DASHBOARD.html`](file:///d:/AI/vietnam-stock-analyzer/DASHBOARD.html)) và sơ đồ tư duy ([`PROJECT_MINDMAP.html`](file:///d:/AI/vietnam-stock-analyzer/PROJECT_MINDMAP.html)) đều là file HTML tĩnh độc lập, thiết kế chuẩn đồ họa Bloomberg Terminal Dark Theme, mở mượt mà bằng Microsoft Edge.
2. **Động cơ Dự báo Thời điểm — Timing Matrix Engine (*Khi nào tăng? Khi nào sập?*):**
   - Không chỉ khuyến nghị mua/bán chung chung, hệ thống định lượng chính xác:
     * **Kịch bản Tăng:** Điều kiện kích hoạt Pivot giá, gom hàng cạn kiệt VSA No Supply / Spring, độ trễ thẩm thấu tin tức vĩ mô (1–3 phiên), xác suất bứt phá (%) và khung thời gian dự kiến (T+1 đến T+5).
     * **Kịch bản Sập:** Bẫy phân phối ngầm Upthrust, phân kỳ âm RSI/MACD, bẫy "Tin ra là bán", mốc vi phạm rủi ro và điều kiện kịch bản mất hiệu lực.
3. **Radar Vĩ mô & Ma trận Hàng hóa Thế giới (Global Macro & Commodities):**
   - Tự động quét và cập nhật các biến số vĩ mô trọng yếu: FED Funds Rate, US Core CPI, Chỉ số Dollar DXY, Tỷ giá USD/VND, Dầu Brent & WTI, Vàng SJC & Thế giới, Cao su TSR20 & TOCOM, Thép HRC, Phân bón Urea.
   - Tự động bóc tách độ nhạy (Sensitivity) và độ trễ thẩm thấu (Macro Transmission Lag) đối với từng nhóm ngành và mã cổ phiếu cụ thể (Dầu khí PVD/PVS, Cao su GVR/PHR, Thép HPG/NKG, Phân bón DPM/DCM...).
4. **Báo cáo HTML Trực quan Chuyên sâu:**
   - Xuất file báo cáo HTML độc lập tại thư mục `reports/` với giao diện màu sắc trực quan, thẻ cảnh báo, bảng so sánh đa trường phái và khối ma trận Timing Matrix.
5. **Kênh Cảnh báo 1-Chiều qua Telegram (Zero-Polling):**
   - Không chạy bot nền 2 chiều 24/7 gây chậm máy. Thay vào đó, sau mỗi lệnh phân tích hoặc quét thị trường, hệ thống tự động bắn bản tin tóm tắt và đính kèm file báo cáo HTML trực tiếp về điện thoại.
6. **Hội đồng Phản biện Đa góc nhìn (Council of AI Experts):**
   - Mỗi mã cổ phiếu đều được thẩm định độc lập qua 5 góc nhìn: Giá trị (Buffett/Munger), Tăng trưởng (Lynch/O'Neil), Kỹ thuật & Dòng tiền (Wyckoff/VSA), Vĩ mô & Chu kỳ (Dalio/Marks) và Trọng tài Quản trị Rủi ro (CRO Arbiter) bảo đảm kỷ luật cắt lỗ $\le 7\%$ và Risk/Reward $\ge 2:1$.

---

## 📂 2. CẤU TRÚC 7 PHÂN HỆ DỰ ÁN

```text
vietnam-stock-analyzer/
│
├── README.md                  # Hướng dẫn tổng quan & vận hành
├── ARCHITECTURE.md            # Tài liệu kiến trúc chuyên sâu & công thức định lượng
├── AGENTS.md                  # Quy chế hoạt động & chuẩn mực tham mưu
├── requirements.txt           # Thư viện phụ thuộc Python
├── .env                       # Cấu hình API keys, Telegram, Watchlist
├── .env.example               # File cấu hình mẫu
│
├── DASHBOARD.html             # [MỚI] Bảng điều khiển Bloomberg Terminal Offline mở trên Edge
├── PROJECT_MINDMAP.html       # [MỚI] Sơ đồ tư duy tương tác D3.js + Bento Grid 7 phân hệ
├── main.py                    # Entry point chính (--mode dashboard, analyze, scan, macro)
├── config.py                  # Ngưỡng giao dịch, Watchlist và tham số hệ thống
│
├── core/                      # 7 Phân hệ tính toán cốt lõi
│   ├── __init__.py
│   ├── data_loader.py         # Nạp giá realtime, nến OHLCV, BCTC, Vĩ mô & Hàng hóa thế giới
│   ├── fa_engine.py           # Piotroski F-Score, DuPont, CAMELS, Moat, PEG, P/B Asset Bargain
│   ├── ta_engine.py           # EMA Trend, RSI, MACD, Volume Spike, O'Neil Pivot, Wyckoff VSA
│   ├── macro_engine.py        # Phân tích FED, CPI, DXY, Tỷ giá, Dầu, Vàng, Cao su, Thép, Phân bón
│   ├── timing_engine.py       # [MỚI] Động cơ dự báo thời điểm (Khi nào tăng? Khi nào sập?)
│   ├── risk_manager.py        # Buy Zone, Stop Loss (<= 7%), Target R:R >= 2:1, Kelly Sizing
│   ├── governance_analyzer.py # Radar phát hiện tăng vốn ảo, sở hữu chéo, Skin in the game
│   ├── segment_analyzer.py    # Bóc tách cơ cấu mảng kinh doanh cốt lõi (Core Business Segments)
│   ├── html_report_generator.py # Sinh báo cáo HTML đồ họa trực quan chuyên sâu
│   ├── dashboard_generator.py # [MỚI] Biên dịch DASHBOARD.html tổng hợp thị trường
│   ├── stock_service.py       # Facade Service thống nhất xử lý dữ liệu
│   └── db_manager.py          # SQLite Market Database lưu trữ cục bộ
│
├── ai/                        # Tầng kết nối AI linh hoạt (AI-Agnostic)
│   ├── __init__.py
│   ├── llm_router.py          # Router đa nền tảng: Gemini, OpenAI, Claude, Ollama, Offline
│   ├── council.py             # Hội đồng 5 góc nhìn phản biện độc lập
│   └── prompts/               # Bộ Prompt chuẩn hóa chuyên gia (.md)
│
├── alerts/                    # Kênh xuất cảnh báo
│   ├── __init__.py
│   └── telegram_bot.py        # Push 1-chiều: Bắn tóm tắt & gửi kèm file HTML về Telegram
│
├── data/                      # Dữ liệu cục bộ
│   ├── market.db              # SQLite Database
│   └── segments/              # Hồ sơ phân khúc doanh nghiệp (.json)
│
├── cache/                     # Bộ đệm dữ liệu vĩ mô & hàng hóa
│   └── macro_commodities_cache.json
│
└── reports/                   # Thư mục lưu trữ tự động các file báo cáo (.html & .md)
```

---

## 🚀 3. HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG

### Bước 1: Kích hoạt môi trường và cài đặt thư viện
```bash
# Cài đặt các thư viện phụ thuộc
pip install rich pandas requests python-dotenv

# (Tùy chọn) Cài đặt thư viện vnstock:
pip install -U --extra-index-url https://vnstocks.com/api/simple vnstock
```

### Bước 2: Thiết lập file cấu hình `.env`
Mở file `.env` và thiết lập cấu hình:
```env
# Chọn nhà cung cấp AI: 'gemini', 'openai', 'claude', 'ollama', hoặc 'offline'
LLM_PROVIDER=offline

# API Keys (tùy chọn nếu muốn AI mở rộng luận giải):
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Cảnh báo Telegram (Tùy chọn - Push 1 chiều file HTML về máy):
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

---

### Bước 3: Vận hành ứng dụng

#### 🚀 Cách 1 (Khuyên dùng): Phân Tích 360 Độ Trực Tiếp Trên Đoạn Chat Antigravity
Chỉ cần mở một đoạn chat trong Antigravity IDE và yêu cầu phân tích mã cổ phiếu (ví dụ: *"Phân tích cổ phiếu HPG/IDJ/FPT"*).
> **Trải nghiệm:** Hội đồng Tham mưu AI sẽ cung cấp:
> - **Phân tích 360 độ chuẩn nhà đầu tư chuyên nghiệp:** Bóc tách BCTC 4 quý, dòng tiền thực (CFO/FCF), kiểm toán tài sản, định giá P/E & P/B, chỉ báo kỹ thuật, Wyckoff VSA, mô hình VCP, động cơ thời điểm (khi nào tăng, khi nào sập), 3 kịch bản giá & điều kiện mất hiệu lực.
> - **Giải thích như đứa trẻ lên 5 (ELI5):** Dùng các hình ảnh ẩn dụ đời thường dễ hiểu nhất để bóc trần bản chất cốt lõi của doanh nghiệp và thương vụ đầu tư.
> - **Tự động xuất bản Báo cáo HTML cao cấp:** Lưu vào thư mục `reports/` và tự động bắn trực tiếp file HTML về Telegram cá nhân.

---

#### 🌟 Cách 2: Mở Bảng Điều Khiển Offline trên Microsoft Edge (`DASHBOARD.html`)
Bạn có thể mở trực tiếp không cần dòng lệnh:
1. **1-Click khởi chạy siêu tốc:** Nhấp đúp chuột vào file [`Mo_Dashboard.bat`](file:///d:/AI/vietnam-stock-analyzer/Mo_Dashboard.bat) hoặc [`Mo_Web_App.vbs`](file:///d:/AI/vietnam-stock-analyzer/Mo_Web_App.vbs).
2. Hoặc chạy lệnh để cập nhật dữ liệu mới nhất và tự động kích hoạt Edge:
```bash
python main.py --mode dashboard
```
*Giao diện cung cấp:*
* **Chỉ số Vĩ mô & Hàng hóa thế giới:** Dầu Brent, Vàng, Cao su, Thép, DXY, Tỷ giá, Lãi suất FED.
* **Top Tín hiệu Dòng tiền & Bứt phá:** Danh sách cổ phiếu nổ Vol, điểm Pivot, xu hướng VSA.
* **Động cơ Thời điểm Tóm tắt:** Tín hiệu tăng/sập sắp tới của các mã trọng điểm.
* **Thư viện Báo cáo Phân tích:** Danh sách các file báo cáo HTML đã xuất, nhấp là mở ngay.

---

#### 🧠 Cách 3: Xem Sơ đồ Tư duy Dự án trên Microsoft Edge (`PROJECT_MINDMAP.html`)
Nhấp đúp chuột vào file [`PROJECT_MINDMAP.html`](file:///d:/AI/vietnam-stock-analyzer/PROJECT_MINDMAP.html) để khám phá:
* Cây sơ đồ tư duy tương tác D3.js (phóng to, thu nhỏ, đóng/mở nhánh phân hệ).
* Bảng điều khiển Bento Grid trực quan trình bày chi tiết năng lực của **7 Phân hệ hoàn chỉnh**.

---

#### 🔍 Cách 4: Soi sâu 1 mã cổ phiếu bất kỳ (`analyze`)
```bash
# Phân tích mã PVD (Dầu khí)
python main.py --mode analyze --ticker PVD

# Phân tích mã GVR (Cao su)
python main.py --mode analyze --ticker GVR

# Phân tích mã HPG (Thép), FPT (Công nghệ)...
python main.py --mode analyze --ticker HPG
```
*Kết quả:*
1. In bảng tổng kết đa sắc nét trên Terminal.
2. Tự động biên dịch file báo cáo HTML chuyên sâu tại `reports/YYYY-MM-DD_MÃ.html` (bao gồm Radar Hàng hóa & Khối Động cơ Thời điểm).
3. Nếu bật Telegram, hệ thống tự động **bắn tóm tắt khuyến nghị + Timing Matrix + đính kèm file HTML** về điện thoại.

---

#### 💬 Cách 5: Bàn Tròn Hỏi-Đáp Trực Tiếp với 11 Chuyên Gia Hội Đồng (`ask`)
Tương tác trực tiếp với bất kỳ ai trong 11 trường phái đầu tư đỉnh cao:
```bash
# Xem danh mục 11 chuyên gia và mã viết tắt
python main.py --list-experts

# Hỏi Warren Buffett về con hào kinh tế của HPG
python main.py --mode ask --ticker HPG --expert buffett --question "Con hào kinh tế của Hòa Phát có bền vững không?"

# Hỏi Nassim Taleb & CRO Arbiter về kịch bản rủi ro xấu nhất
python main.py --mode ask --ticker IDJ --expert cro --question "Kịch bản xấu nhất (Pre-Mortem) của cổ phiếu này là gì?"

# Hỏi Chuyên gia Thẩm định Quỹ PE (Private Equity)
python main.py --mode ask --ticker GVR --expert pe --question "Chất lượng tài sản và triển vọng thoái vốn KCN thế nào?"
```

---

#### 🌐 Cách 6: Quét Ma trận Vĩ mô & Hàng hóa Thế giới (`macro`)
```bash
python main.py --mode macro
```
*Kết quả:* Bảng Terminal trực quan tổng hợp chi tiết mức giá hiện tại, biến động % ngày của Dầu Brent, WTI, Vàng thế giới, Vàng SJC, Cao su TSR20, Thép HRC, Phân bón Urea, Chỉ số DXY, Tỷ giá USD/VND và Lãi suất FED.

---

#### 🚀 Cách 7: Quét toàn sàn tìm điểm nổ Vol (`scan`)
```bash
# Quét tìm top 5 mã bùng nổ thanh khoản và bứt phá nền giá
python main.py --mode scan --top 5
```
*Kết quả:* Bảng xếp hạng các mã nổ Vol ($> 1.3x$ MA20) đạt tiêu chí CANSLIM và VSA kèm vùng mua, cắt lỗ và chốt lời.


---

## 🛡️ 4. QUY TẮC QUẢN TRỊ RỦI RO BẤT DI BẤT DỊCH
1. **Cắt lỗ cứng $\le 7\%$:** Mọi khuyến nghị mua bắt buộc phải có mức cắt lỗ vi phạm tối đa không quá 7% từ giá vào lệnh.
2. **Tỷ lệ Lãi / Lỗ $R:R \ge 2:1$:** Không mở vị thế nếu tiềm năng lợi nhuận ngắn hạn không đạt gấp đôi rủi ro.
3. **Phạt nặng Bẫy Giá trị & Tăng vốn ảo:** Cổ phiếu dù $P/B$ rẻ nhưng có dấu hiệu sở hữu chéo, nợ vay gấp nhiều lần tiền mặt hoặc tài sản đọng vốn lớn sẽ bị gắn cờ đỏ cảnh báo và hạ tỷ trọng về 0%.
4. **Điều kiện mất hiệu lực rõ ràng:** Mọi kịch bản dự báo tăng đều đi kèm mức giá vi phạm (Failure Level) — nếu thủng mốc này, kịch bản lập tức mất hiệu lực.
