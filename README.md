# 🏛️ VIETNAM STOCK ANALYZER (AI-AGNOSTIC LOCAL TERMINAL)

> **Hệ thống Phân tích Chứng khoán Cục bộ Đa AI**  
> Kết hợp Phân tích Cơ bản (FA), Phân tích Kỹ thuật (TA) và Hội đồng Phản biện Đa góc nhìn (Warren Buffett, Peter Lynch, William O'Neil, Price Action VSA & Chief Risk Officer).  
> *Được thiết kế theo tiêu chuẩn mở, sẵn sàng để bất kỳ trợ lý AI nào (Gemini, ChatGPT, Claude) hoặc lập trình viên mở thư mục này ra là có thể trực tiếp nghiên cứu, phát triển tiếp.*

---

## 🎯 1. TỔNG QUAN DỰ ÁN

Dự án này là một công cụ phân tích chứng khoán Việt Nam (HOSE, HNX, UPCoM) chạy trực tiếp trên máy tính cá nhân. Dự án giải quyết các bài toán then chốt:
1. **Dữ liệu khớp lệnh Realtime trong phiên & BCTC nhiều năm:** Lấy tự động, hoàn toàn miễn phí từ các cổng dữ liệu mở của các CTCK lớn (SSI / TCBS qua `vnstock`), hỗ trợ cầu nối token FireAnt khi cần.
2. **Không phụ thuộc vào một AI cố định (AI-Agnostic):** Có thể cắm trực tiếp API Key của **Google Gemini**, **OpenAI ChatGPT**, **Anthropic Claude**, hoặc chạy offline với **Ollama** hoặc chế độ **Rule-Based độc lập** (không cần internet hay API key vẫn tính toán điểm mua/bán chuẩn xác).
3. **Đề xuất Điểm Mua & Điểm Bán chuẩn xác:** Kèm Vùng mua tối ưu, Mức cắt lỗ cứng $\le 7\%$, Mục tiêu chốt lời 1 & 2 theo tỷ lệ $Risk/Reward \ge 2:1$.
4. **Giải thích cặn kẽ tại sao (Why):** Mỗi mã cổ phiếu đều được "chất vấn" qua 4 lăng kính của các huyền thoại đầu tư trước khi Giám đốc Quản trị rủi ro ra phán quyết cuối cùng.
5. **Kênh xuất kết quả phong phú:** Bảng Terminal màu trực quan (Rich UI), file báo cáo Markdown chi tiết lưu tại `reports/`, và cảnh báo tức thì về điện thoại qua Telegram Bot.

---

## 📂 2. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
vietnam-stock-analyzer/
│
├── README.md                  # Tài liệu hướng dẫn tổng quan và vận hành cho Người & AI
├── ARCHITECTURE.md            # Tài liệu kiến trúc chuyên sâu, công thức định lượng
├── requirements.txt           # Thư viện phụ thuộc Python
├── .env                       # File cấu hình bí mật cục bộ (API keys, Telegram, Watchlist)
├── .env.example               # File cấu hình mẫu
│
├── main.py                    # Entry point chính chạy CLI (--mode scan hoặc --mode analyze)
├── config.py                  # Load biến môi trường và thiết lập ngưỡng giao dịch
│
├── core/                      # Bộ máy tính toán định lượng cốt lõi
│   ├── __init__.py
│   ├── data_loader.py         # Lấy giá realtime SSI/DNSE, nến OHLCV và BCTC
│   ├── fa_engine.py           # Tính Piotroski F-Score (0-9), Buffett Moat, Lynch PEG
│   ├── ta_engine.py           # Tính EMA, RSI, MACD, Volume Spike, O'Neil Breakout, VSA
│   └── risk_manager.py        # Tính Buy Zone, Stop Loss (<= 7%), Take Profit 1 & 2, R:R
│
├── ai/                        # Tầng kết nối AI linh hoạt
│   ├── __init__.py
│   ├── llm_router.py          # Unified AI Client: Hỗ trợ Gemini, OpenAI, Claude, Ollama, Offline
│   ├── council.py             # Điều phối 4 góc nhìn huyền thoại + 1 Trọng tài rủi ro
│   └── prompts/               # Bộ Prompt chuẩn hóa dưới dạng Markdown độc lập
│       ├── buffett.md         # Prompt góc nhìn Warren Buffett
│       ├── lynch.md           # Prompt góc nhìn Peter Lynch
│       ├── oneil.md           # Prompt góc nhìn William O'Neil (CANSLIM)
│       ├── vsa.md             # Prompt góc nhìn Price Action & Wyckoff VSA
│       └── cro_arbiter.md     # Prompt Giám đốc Quản trị rủi ro (CRO)
│
├── alerts/                    # Kênh gửi cảnh báo
│   ├── __init__.py
│   └── telegram_bot.py        # Module gửi tín hiệu tức thì về Telegram khi có điểm mua/bán
│
└── reports/                   # Nơi tự động lưu trữ các file báo cáo phân tích (.md)
```

---

## 🚀 3. HƯỚNG DẪN CÀI ĐẶT & SỬ DỤNG

### Bước 1: Kích hoạt môi trường và cài đặt thư viện
```bash
# Cài đặt các thư viện cần thiết
pip install rich pandas requests python-dotenv

# (Tùy chọn) Cài đặt thư viện vnstock bản mới nhất:
pip install -U --extra-index-url https://vnstocks.com/api/simple vnstock
```

### Bước 2: Thiết lập file cấu hình `.env`
Mở file `.env` và điều chỉnh cấu hình theo nhu cầu:
```env
# Chọn nhà cung cấp AI: 'gemini', 'openai', 'claude', 'ollama', hoặc 'offline'
LLM_PROVIDER=offline

# Điền API Key nếu bạn muốn AI viết bài luận giải chuyên sâu:
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Cảnh báo Telegram (Tùy chọn):
TELEGRAM_ENABLED=false
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
```

### Bước 3: Chạy ứng dụng

#### 👉 Chế độ 1: Soi sâu 1 mã cổ phiếu bất kỳ (`analyze`)
```bash
# Phân tích mã HPG (mặc định)
python main.py --mode analyze --ticker HPG

# Phân tích mã FPT, VCB, MWG...
python main.py --mode analyze --ticker FPT
python main.py --mode analyze --ticker VCB
```
*Kết quả:* Hệ thống lấy giá realtime trong phiên, tính toán BCTC, in bảng tổng kết sắc nét trên Terminal và tự động tạo file báo cáo `reports/YYYY-MM-DD_MÃ.md`.

#### 👉 Chế độ 2: Quét toàn sàn tìm cổ phiếu tăng trưởng đột biến (`scan`)
```bash
# Quét danh sách các mã trọng điểm và xuất top 5 mã tiềm năng nhất hôm nay
python main.py --mode scan --top 5
```
*Kết quả:* Bảng xếp hạng Top các mã bùng nổ thanh khoản (Nổ Vol $> 1.3x$ MA20) và bứt phá nền giá kèm khuyến nghị mua, cắt lỗ và chốt lời.

#### 👉 Chế độ 3: Trợ lý Telegram Bot tương tác 2 chiều (`bot`)
```bash
# Khởi động Bot lắng nghe lệnh trực tiếp từ điện thoại / Telegram cá nhân
python main.py --mode bot
# hoặc chạy trực tiếp file module:
python alerts/telegram_interactive_bot.py
```
*Tính năng:* Bạn có thể mở ứng dụng Telegram trên điện thoại và chat ra lệnh trực tiếp cho Bot:
* `/soi <MÃ>` hoặc chỉ cần gõ tên mã (ví dụ: `FPT`, `HPG`, `IDC`): Bot tính toán tức thì và trả về báo cáo phân tích, vùng mua, cắt lỗ 7%, chốt lời TP1/TP2 và phản biện từ 4 nhà đầu tư AI.
* `/scan` hoặc `/scan 5`: Quét nhanh top cổ phiếu nổ vol đẹp nhất trong phiên.
* `/gia <MÃ>`: Xem nhanh giá khớp lệnh realtime, % thay đổi và khối lượng.
* `/watchlist`: Xem danh sách cổ phiếu đang theo dõi.
* *Bảo mật:* Hệ thống tích hợp Whitelist bảo mật cao, chỉ duy nhất `TELEGRAM_CHAT_ID` của bạn mới có quyền ra lệnh.

---

## 🤖 4. HƯỚNG DẪN DÀNH CHO CÁC MÔ HÌNH AI (GEMINI / CLAUDE / CHATGPT)

Khi bạn (AI) được người dùng mở thư mục này để yêu cầu nghiên cứu hoặc mở rộng tính năng:
1. **Thêm tiêu chí lọc mới:** Chỉnh sửa file `config.py` để bổ sung các ngưỡng giao dịch.
2. **Nâng cấp công thức FA:** Đọc và tinh chỉnh trong `core/fa_engine.py` (ví dụ: bổ sung chỉ số Altman Z-Score hoặc dòng tiền tự do FCF).
3. **Nâng cấp công thức TA:** Đọc và tinh chỉnh trong `core/ta_engine.py` (ví dụ: bổ sung mẫu hình VCP của Mark Minervini hoặc phân kỳ MACD).
4. **Tùy biến phong cách phản biện:** Mở trực tiếp các file trong `ai/prompts/*.md` để cập nhật tư duy phân tích theo sở thích của người dùng.
