import time
import requests
import re
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime

# Đảm bảo console Windows hiển thị đúng UTF-8 và flush tức thì
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

from config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
    TELEGRAM_ENABLED,
    DEFAULT_WATCHLIST,
    REPORTS_DIR
)
from core.data_loader import get_realtime_quote
from core.stock_service import (
    run_screener,
    analyze_ticker_full,
    analyze_ticker_fa,
    analyze_ticker_ta
)
from core.performance_tracker import (
    evaluate_all_recommendations,
    get_performance_telegram_summary
)
from alerts.telegram_bot import send_telegram_document, is_duplicate_alert, record_sent_alert
from ai.council import InvestmentCouncil
from ai.llm_router import LLMRouter

# Bộ nhớ hội thoại ngắn hạn (Context Memory)
chat_memory: List[Dict[str, str]] = []

# Cache chống spam / double-click / trùng lặp lệnh
_PROCESSING_REQUESTS: Dict[str, float] = {}
_PROCESSED_UPDATE_IDS = set()



# =====================================================================
# 1. KEYBOARD VÀ MENU TƯƠNG TÁC
# =====================================================================

def get_persistent_reply_keyboard() -> dict:
    """
    Bàn phím tương tác cố định dưới thanh nhập tin nhắn.
    Người dùng chỉ cần chạm nút trên điện thoại hoặc click chuột trên máy tính,
    hoàn toàn không cần nhớ lệnh gõ.
    """
    return {
        "keyboard": [
            [{"text": "🏆 Top 10 Hôm Nay"}, {"text": "📋 Menu Tính Năng"}],
            [{"text": "🔍 Soi Cổ Phiếu"}, {"text": "💵 Tra Giá Realtime"}],
            [{"text": "📈 Hiệu Suất PnL"}, {"text": "📊 Danh Mục Watchlist"}]
        ],
        "resize_keyboard": True,
        "is_persistent": True
    }


def get_menu_inline_keyboard() -> dict:
    """Bàn phím Inline gắn liền với tin nhắn Menu điều khiển."""
    return {
        "inline_keyboard": [
            [
                {"text": "🏆 Top 10 Cổ Phiếu Nổ Vol & Tích Lũy", "callback_data": "cmd:top10"}
            ],
            [
                {"text": "🔍 Soi Nhanh Mã Hot", "callback_data": "cmd:pick_soi"},
                {"text": "💵 Tra Cứu Giá", "callback_data": "cmd:pick_gia"}
            ],
            [
                {"text": "📈 Hiệu Suất Khuyến Nghị (PDCA)", "callback_data": "cmd:pnl"},
                {"text": "📊 Watchlist (20 mã)", "callback_data": "cmd:watchlist"}
            ],
            [
                {"text": "❓ Hướng Dẫn & Mẹo Chat", "callback_data": "cmd:help"}
            ]
        ]
    }


def get_stock_picker_inline_keyboard(action: str = "soi") -> dict:
    """Bàn phím inline chọn nhanh các cổ phiếu trọng điểm."""
    top_tickers = [
        ("HPG", "🏭 HPG"), ("FPT", "💻 FPT"), ("VCB", "🏦 VCB"),
        ("SSI", "📈 SSI"), ("MWG", "📱 MWG"), ("TCB", "🏦 TCB"),
        ("VHM", "🏢 VHM"), ("MSN", "🛒 MSN"), ("DGC", "🌿 DGC"),
        ("VND", "📊 VND"), ("STB", "🏛️ STB"), ("ACB", "💳 ACB")
    ]
    rows = []
    current_row = []
    for code, label in top_tickers:
        current_row.append({"text": label, "callback_data": f"{action}:{code}"})
        if len(current_row) == 3:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    if action == 'soi':
        rows.append([{"text": "🏛️ Soi FA", "callback_data": "cmd:pick_fa"}, {"text": "📈 Soi TA", "callback_data": "cmd:pick_ta"}])
    rows.append([{"text": "🔙 Quay Lại Menu", "callback_data": "cmd:menu"}])
    return {"inline_keyboard": rows}


def get_watchlist_inline_keyboard() -> dict:
    """Tạo bàn phím inline hiển thị tất cả các mã trong Watchlist."""
    rows = []
    current_row = []
    for symbol in DEFAULT_WATCHLIST:
        current_row.append({"text": symbol, "callback_data": f"soi:{symbol}"})
        if len(current_row) == 4:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([{"text": "🔙 Quay Lại Menu", "callback_data": "cmd:menu"}])
    return {"inline_keyboard": rows}


# =====================================================================
# 2. CÁC HÀM GIAO TIẾP VỚI TELEGRAM API
# =====================================================================

def send_message(chat_id: str | int, text: str, reply_markup: Optional[dict] = None, parse_mode: Optional[str] = "Markdown") -> bool:
    """
    Gửi tin nhắn Telegram kèm bàn phím tương tác.
    Tự động fallback an toàn nếu gặp lỗi phân tích Markdown.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: Dict[str, Any] = {
        "chat_id": chat_id,
        "text": text,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if reply_markup:
        payload["reply_markup"] = reply_markup

    try:
        r = requests.post(url, json=payload, timeout=15)
        # Fallback nếu cú pháp Markdown bị lỗi (do dấu gạch dưới trong tên cty hoặc số liệu)
        if r.status_code != 200 and parse_mode:
            payload.pop("parse_mode", None)
            r = requests.post(url, json=payload, timeout=15)
        return r.status_code == 200
    except Exception as e:
        print(f"❌ Lỗi gửi Telegram message: {e}")
        return False


def answer_callback_query(callback_query_id: str, text: Optional[str] = None) -> bool:
    """Phản hồi callback_query để tắt biểu tượng loading trên nút bấm Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/answerCallbackQuery"
    payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        r = requests.post(url, json=payload, timeout=5)
        return r.status_code == 200
    except Exception:
        return False


def setup_bot_commands() -> bool:
    """
    Đăng ký danh sách lệnh chính thức với Telegram (Bot Command Menu).
    Người dùng chỉ cần nhấn nút [/] góc trái thanh nhập chat là thấy toàn bộ menu.
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setMyCommands"
    commands = [
        {"command": "menu", "description": "📋 Bảng điều khiển Menu phím bấm tương tác"},
        {"command": "top10", "description": "🏆 Top 10 cổ phiếu tiềm năng & nổ vol hôm nay"},
        {"command": "soi", "description": "🔍 Soi toàn diện 1 mã (VD: /soi HPG)"},
        {"command": "fa", "description": "🏛️ Soi Cơ Bản Doanh nghiệp (VD: /fa HPG)"},
        {"command": "ta", "description": "📈 Soi Kỹ thuật Chart & Dòng tiền (VD: /ta HPG)"},
        {"command": "pnl", "description": "📊 Nghiệm thu hiệu suất khuyến nghị PDCA"},
        {"command": "gia", "description": "💵 Bảng giá Realtime & Dòng tiền (VD: /gia FPT)"},
        {"command": "watchlist", "description": "📊 Danh mục theo dõi trọng điểm (20 mã)"},
        {"command": "help", "description": "❓ Hướng dẫn sử dụng & Mẹo hỏi đáp"},
        {"command": "start", "description": "🚀 Khởi động lại Bot & Bật bàn phím"},
    ]
    try:
        r = requests.post(url, json={"commands": commands}, timeout=10)
        return r.status_code == 200 and r.json().get("ok", False)
    except Exception as e:
        print(f"⚠️ Không thể đăng ký lệnh Telegram: {e}")
        return False


# =====================================================================
# 3. XỬ LÝ CÁC CHỨC NĂNG CHÍNH (HANDLERS)
# =====================================================================

def handle_start(chat_id: str | int):
    """Xử lý lệnh /start: Kích hoạt bàn phím bấm và hiển thị Menu điều khiển."""
    welcome_text = (
        "🤖 *HỘI ĐỒNG THAM MƯU ĐẦU TƯ TTCK VIỆT NAM (AI)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Xin chào! Tôi là Trợ lý Cố vấn Đầu tư Đa AI.\n\n"
        "✨ *BẠN KHÔNG CẦN NHỚ LỆNH:* Hãy dùng các phím bấm tiện lợi bên dưới hoặc chạm vào Menu trên màn hình.\n\n"
        "💬 *GIAO TIẾP 2 CHIỀU TỰ NHIÊN:*\n"
        "• Gõ thẳng tên mã (VD: `HPG`, `FPT`, `VCB`)\n"
        "• Chat tự do: `HPG hôm nay có điểm mua không?`, `So sánh SSI và VND`\n"
        "• Bấm nút dưới tin nhắn để soi nhanh ngay lập tức!"
    )
    send_message(
        chat_id=chat_id,
        text=welcome_text,
        reply_markup=get_persistent_reply_keyboard()
    )
    # Gửi kèm Dashboard Menu Inline
    handle_menu(chat_id)


def handle_menu(chat_id: str | int):
    """Hiển thị Bảng điều khiển Menu chính với các nút tương tác trực tiếp."""
    menu_text = (
        "📋 *BẢNG ĐIỀU KHIỂN HỘI ĐỒNG AI*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Chọn nhanh tính năng bằng cách bấm một nút dưới đây:"
    )
    send_message(
        chat_id=chat_id,
        text=menu_text,
        reply_markup=get_menu_inline_keyboard()
    )


def handle_help(chat_id: str | int):
    """Hiển thị hướng dẫn sử dụng và mẹo trò chuyện 2 chiều."""
    help_text = (
        "📖 *HƯỚNG DẪN SỬ DỤNG & MẸO TƯƠNG TÁC*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💡 *1. Không cần gõ lệnh:*\n"
        "• Dùng bàn phím phím bấm cố định ở góc dưới màn hình.\n"
        "• Nhấn biểu tượng `[/]` cạnh ô chat để mở danh sách lệnh chính thức.\n\n"
        "⚡ *2. Xem nhanh 1 mã:* Chỉ cần gõ mã cổ phiếu viết hoa hoặc thường (VD: `HPG`, `fpt`, `vcb`).\n\n"
        "🔍 *3. Lệnh tra cứu truyền thống:*\n"
        "• `/soi <MÃ>`: Phân tích 5 góc nhìn Hội đồng (VD: `/soi HPG`)\n"
        "• `/gia <MÃ>`: Xem giá Realtime, Khối lượng & Khối ngoại (VD: `/gia FPT`)\n"
        "• `/top10`: Quét Radar 10 mã khỏe nhất hôm nay\n"
        "• `/watchlist`: Xem danh mục 20 cổ phiếu trọng điểm\n\n"
        "🤖 *4. Chat 2 chiều với Hội đồng AI:*\n"
        "Bạn có thể đặt câu hỏi tự do như một nhà phân tích thực thụ."
    )
    inline_kb = {
        "inline_keyboard": [
            [{"text": "🏆 Quét Top 10 Ngay", "callback_data": "cmd:top10"}],
            [{"text": "🔍 Soi Cổ Phiếu Hot", "callback_data": "cmd:pick_soi"}],
            [{"text": "🔙 Menu Chính", "callback_data": "cmd:menu"}]
        ]
    }
    send_message(chat_id, help_text, reply_markup=inline_kb)


def handle_quick_soi_picker(chat_id: str | int):
    """Hiển thị bảng chọn nhanh cổ phiếu để soi chuyên sâu."""
    text = (
        "🔍 *CHỌN MÃ ĐỂ HỘI ĐỒNG AI PHÂN TÍCH CHUYÊN SÂU:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Bấm vào mã bạn quan tâm bên dưới, hoặc gõ trực tiếp tên mã vào ô chat (VD: `HPG`, `FPT`):"
    )
    send_message(chat_id, text, reply_markup=get_stock_picker_inline_keyboard(action="soi"))


def handle_quick_gia_picker(chat_id: str | int):
    """Hiển thị bảng chọn nhanh cổ phiếu để xem giá realtime."""
    text = (
        "💵 *TRA CỨU GIÁ REALTIME & DÒNG TIỀN:*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "Bấm vào mã bên dưới để xem giá khớp lệnh, khối lượng và động thái khối ngoại:"
    )
    send_message(chat_id, text, reply_markup=get_stock_picker_inline_keyboard(action="gia"))


def handle_watchlist_view(chat_id: str | int):
    """Hiển thị danh sách 20 mã theo dõi kèm nút bấm trực tiếp."""
    text = (
        "📊 *DANH MỤC CỔ PHIẾU THEO DÕI TRỌNG ĐIỂM (WATCHLIST)*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Hiện có *{len(DEFAULT_WATCHLIST)} mã* được giám sát tự động.\n"
        "Bấm vào bất kỳ mã nào dưới đây để soi báo cáo chi tiết:"
    )
    send_message(chat_id, text, reply_markup=get_watchlist_inline_keyboard())


def handle_quick_price(chat_id: str | int, symbol: str):
    """Tra cứu nhanh giá Realtime, Khối lượng, Khối ngoại."""
    symbol = symbol.upper().strip()
    quote = get_realtime_quote(symbol)
    price = quote.get("price", 0)

    if price <= 0:
        send_message(
            chat_id,
            f"❌ Không tìm thấy dữ liệu giá cho mã `{symbol}`. Vui lòng kiểm tra lại mã cổ phiếu.",
            reply_markup={"inline_keyboard": [[{"text": "🔙 Quay lại Menu", "callback_data": "cmd:menu"}]]}
        )
        return

    change = quote.get("change", 0)
    change_pct = quote.get("change_pct", 0)
    vol = quote.get("volume", 0)
    foreign_net = quote.get("foreign_net_vol", 0)
    company = quote.get("company_name", symbol)

    # Biểu tượng trạng thái
    trend_emoji = "🟢" if change > 0 else ("🔴" if change < 0 else "🟡")
    foreign_status = "Mua ròng 🟢" if foreign_net > 0 else ("Bán ròng 🔴" if foreign_net < 0 else "Cân bằng ⚪")

    msg = (
        f"💵 *BẢNG GIÁ REALTIME: {symbol}*\n"
        f"🏢 _{company}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"{trend_emoji} *Giá khớp lệnh:* `{price:,.0f} VND` ({change_pct:+.2f}% | {change:+,.0f})\n"
        f"📈 *Tham chiếu:* `{quote.get('ref_price', 0):,.0f}` | *Mở cửa:* `{quote.get('open', 0):,.0f}`\n"
        f"📊 *Cao nhất:* `{quote.get('high', 0):,.0f}` | *Thấp nhất:* `{quote.get('low', 0):,.0f}`\n"
        f"📦 *Khối lượng:* `{vol:,.0f}` CP\n"
        f"🌐 *Khối ngoại ròng:* `{foreign_net:+,.0f}` CP ({foreign_status})\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📅 _Cập nhật: {quote.get('trading_date') or datetime.now().strftime('%d/%m/%Y')}_"
    )

    action_buttons = {
        "inline_keyboard": [
            [
                {"text": f"🔍 Soi Chuyên Sâu ({symbol})", "callback_data": f"soi:{symbol}"},
                {"text": "🏆 Top 10 Hôm Nay", "callback_data": "cmd:top10"}
            ],
            [
                {"text": "💵 Tra Mã Khác", "callback_data": "cmd:pick_gia"},
                {"text": "📋 Menu Chính", "callback_data": "cmd:menu"}
            ]
        ]
    }
    send_message(chat_id, msg, reply_markup=action_buttons)


def handle_scan(chat_id: str | int, top_n: int = 10, sector_filter: str = None):
    filter_label = f" (Ngành: {sector_filter})" if sector_filter else ""
    send_message(chat_id, f"⏳ *HỆ THỐNG RADAR TOÀN THỊ TRƯỜNG ĐANG KHỞI ĐỘNG*{filter_label}...\n\nĐang quét Realtime toàn bộ 1500+ mã trên HOSE, HNX, UPCoM...")
    
    try:
        results = run_screener(top_n=top_n, sector_filter=sector_filter)
        if not results:
            send_message(chat_id, "❌ Không tìm thấy mã nào thỏa mãn điều kiện hoặc lỗi kết nối dữ liệu.")
            return

        msg = f"🏆 *TOP {len(results)} SIÊU CỔ PHIẾU HÔM NAY*{filter_label}\n\n"
        for idx, r in enumerate(results, 1):
            act_icon = "🟢" if "MUA" in r['action'] else ("🟡" if "THEO DÕI" in r['action'] else "🔴")
            msg += f"{idx}. *{r['symbol']}* ({r.get('exchange', '')}) - `{r['price']:,.0f}` ({r['change_pct']:+.1f}%)\n"
            msg += f"   🏷️ Ngành: _{r.get('sector_name', 'Doanh nghiệp')}_\n"
            msg += f"   {act_icon} Khuyến nghị: *{r['action']}* (Vùng mua: `{r.get('buy_zone', '')}`)\n"
            msg += f"   🎯 Điểm Đ.Thuận: `{r.get('consensus_score', 0)}/100` | FA: `F{r.get('f_score', 0)}/9` (CFO: {r.get('cfo_grade')}) | Vol: `{r.get('vol_ratio', 1.0):.2f}x`\n\n"
            
        msg += "💡 _Bấm vào nút bên dưới hoặc gõ /soi <Mã>, /fa <Mã>, /ta <Mã> để phân tích chi tiết._"
        
        kb_rows = []
        cur_row = []
        for r in results[:6]:
            sym = r['symbol']
            cur_row.append({"text": f"🔍 {sym}", "callback_data": f"soi:{sym}"})
            if len(cur_row) == 3:
                kb_rows.append(cur_row)
                cur_row = []
        if cur_row:
            kb_rows.append(cur_row)
        kb_rows.append([{"text": "🔙 Menu Chính", "callback_data": "cmd:menu"}])

        send_message(chat_id, msg, reply_markup={"inline_keyboard": kb_rows})
    except Exception as e:
        send_message(chat_id, f"❌ Lỗi khi quét thị trường: {str(e)}")


def handle_analyze(chat_id: str | int, symbol: str):
    """Phân tích chuyên sâu 1 mã với 5 góc nhìn Hội đồng AI thông qua StockService."""
    symbol = symbol.upper().strip()
    
    # Chống spam / double-request liên tiến trình trong vòng 20 giây
    if is_duplicate_alert(chat_id, symbol, cooldown_seconds=20.0):
        print(f"⏱️ Bỏ qua yêu cầu phân tích trùng lặp cho {symbol} từ Chat ID {chat_id}.")
        send_message(chat_id, f"⚡ Báo cáo phân tích cho mã `{symbol}` vừa được thực hiện trong ít giây qua. Bạn xem tin nhắn & file đính kèm phía trên nhé!")
        return
    record_sent_alert(chat_id, symbol)

    send_message(chat_id, f"⏳ Đang lấy dữ liệu BCTC & Kỹ thuật mới nhất cho mã *{symbol}*...")

    data = analyze_ticker_full(symbol)
    if not data or data.get("current_price", 0) <= 0:
        send_message(
            chat_id,
            f"❌ Không tìm thấy dữ liệu giá cho `{symbol}`. Vui lòng kiểm tra lại mã cổ phiếu.",
            reply_markup={"inline_keyboard": [[{"text": "🔙 Quay lại Menu", "callback_data": "cmd:menu"}]]}
        )
        return

    quote = data["quote"]
    fa_result = data["fa"]
    ta_result = data["ta"]
    trade_setup = data["trade"]
    current_price = data["current_price"]
    html_path = data.get("html_path")

    # Các thông số cơ bản cốt lõi
    fin = fa_result.get("ratios", {})
    macro = fa_result.get("macro", {})
    pe_val = fin.get("pe")
    pb_val = fin.get("pb")
    roe_val = fin.get("roe")
    gr_val = fin.get("profit_growth")
    pe_str = f"{pe_val:.1f}x" if pe_val is not None else "N/A"
    pb_str = f"{pb_val:.2f}x" if pb_val is not None else "N/A"
    roe_str = f"{roe_val:.1f}%" if roe_val is not None else "N/A"
    gr_str = f"{gr_val:+.1f}%" if gr_val is not None else "N/A"

    macro_sector = macro.get("sector_name", "Doanh nghiệp")
    macro_phase = macro.get("cycle_phase", "Bình thường")
    val_gap_expl = trade_setup.get("valuation_gap_explanation", "")

    report_text = (
        f"📊 *BÁO CÁO PHÂN TÍCH: {symbol}*\n"
        f"🏢 _{quote.get('company_name', symbol)}_\n"
        f"🌐 *Ngành:* _{macro_sector}_ (Pha: {macro_phase})\n"
        f"📅 _Chốt phiên: {quote.get('trading_date') or datetime.now().strftime('%d/%m/%Y')}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 *Thị giá hiện tại:* `{current_price:,.0f} VND` ({quote.get('change_pct', 0):+.2f}%)\n"
        f"🎯 *Khuyến nghị:* *{trade_setup.get('action')}* ({trade_setup.get('consensus_score', 0)}/100 điểm)\n"
        f"📈 *Chỉ số cốt lõi:* P/E: `{pe_str}` | P/B: `{pb_str}` | ROE: `{roe_str}` | Tăng trưởng: `{gr_str}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ *1. GÓC NHÌN ĐẦU TƯ GIÁ TRỊ (BUFFETT & GRAHAM):*\n"
        f"• *Trạng thái:* *{trade_setup.get('value_status', 'ĐỊNH GIÁ HỢP LÝ')}*\n"
        f"• *Giá trị thực ước tính (Fair Value):* `{trade_setup.get('fair_price', current_price):,.0f} VND`\n"
        f"• *Vùng gom an toàn (Margin of Safety ≥ 15%):* `{trade_setup.get('value_buy_zone')}`\n"
        f"• *Lý do định giá:* _{trade_setup.get('value_rationale')}_\n"
    )

    if val_gap_expl:
        report_text += f"• 💡 *Lý giải chênh lệch định giá:* _{val_gap_expl}_\n"

    if trade_setup.get("value_warning"):
        report_text += f"• ⚠️ *Cảnh báo giá trị:* _{trade_setup.get('value_warning')}_\n"

    report_text += (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏄 *2. KẾ HOẠCH LƯỚT SÓNG NGẮN HẠN (SWING / KỸ THUẬT):*\n"
        f"• *Vùng mua lướt sóng (Buy Zone):* `{trade_setup.get('swing_buy_zone')}`\n"
        f"• *Cắt lỗ nghiêm ngặt (Stop Loss):* `{trade_setup.get('stop_loss', 0):,.0f} VND` (-{trade_setup.get('stop_loss_pct', 0)}%)\n"
        f"• *Mục tiêu ngắn hạn (TP1):* `{trade_setup.get('take_profit_1', 0):,.0f} VND` (+{trade_setup.get('take_profit_1_pct', 0)}%)\n"
        f"• *Mục tiêu trung hạn (TP2):* `{trade_setup.get('take_profit_2', 0):,.0f} VND` (+{trade_setup.get('take_profit_2_pct', 0)}%)\n"
        f"• *Tỷ lệ Risk / Reward:* `{trade_setup.get('risk_reward_ratio')}:1` | Tỷ trọng: `Max {trade_setup.get('max_position_size_pct', 10):.1f}% NAV`\n"
    )

    if trade_setup.get("swing_strategy_note"):
        report_text += f"• 💡 *Lưu ý lướt sóng:* _{trade_setup.get('swing_strategy_note')}_\n"

    # Trích xuất nhận định nổi bật của Hội đồng
    report_text += "\n🎭 *HỘI ĐỒNG PHÁN QUYẾT:*\n"
    for role, key in [("Giá trị (Buffett)", "buffett"), ("Tăng trưởng (Lynch)", "lynch"), ("Kỹ thuật (O'Neil)", "oneil"), ("Dòng tiền (VSA)", "vsa")]:
        reason = (fa_result.get(key) or ta_result.get(key) or {}).get("reasons", [""])[0]
        if reason:
            report_text += f"• *{role}:* _{reason}_\n"

    report_text += (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🌐 *BÁO CÁO HTML TRỰC QUAN (MOBILE & DESKTOP):*\n"
        f"• Đã đính kèm file báo cáo HTML tương tác Chart.js bên dưới! Chạm vào file để mở xem ngay.\n"
    )

    action_buttons = {
        "inline_keyboard": [
            [
                {"text": f"💵 Giá Realtime ({symbol})", "callback_data": f"gia:{symbol}"},
                {"text": "🏆 Top 10 Hôm Nay", "callback_data": "cmd:top10"}
            ],
            [
                {"text": f"🏛️ Soi FA ({symbol})", "callback_data": f"fa:{symbol}"},
                {"text": f"📈 Soi TA ({symbol})", "callback_data": f"ta:{symbol}"}
            ],
            [
                {"text": "🔍 Soi Mã Khác", "callback_data": "cmd:pick_soi"},
                {"text": "📋 Menu Chính", "callback_data": "cmd:menu"}
            ]
        ]
    }

    send_message(chat_id, report_text, reply_markup=action_buttons)

    # Gửi kèm file HTML trực tiếp qua Telegram document
    if html_path and Path(html_path).exists():
        send_telegram_document(
            file_path=html_path,
            caption=f"🌐 Báo cáo chiến lược toàn diện: {symbol} | Vietnam Stock Analyzer",
            chat_id=chat_id
        )


def handle_fa(chat_id: str | int, symbol: str):
    """Phân tích chuyên sâu Cơ bản (FA & Quản trị) trực tiếp trên tin nhắn Telegram."""
    symbol = symbol.upper().strip()
    send_message(chat_id, f"⏳ Đang bóc tách BCTC & Quản trị cho mã *{symbol}*...")
    data = analyze_ticker_fa(symbol)
    if not data:
        send_message(chat_id, f"❌ Không thể lấy dữ liệu tài chính cho mã `{symbol}`.")
        return

    fa = data["fa"]
    quote = data["quote"]
    fin = fa.get("ratios", {})
    asset_val = fa.get("asset_valuation", {})
    cf = fa.get("cash_flow", {})
    gov = fa.get("governance", {})
    seg = fa.get("segments", {})

    msg = (
        f"🏛️ *PHÂN TÍCH CƠ BẢN DOANH NGHIỆP: {symbol}*\n"
        f"🏢 _{quote.get('company_name', symbol)}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"⭐ *Piotroski F-Score:* `{fa.get('f_score', 0)}/9`\n"
        f"💵 *P/E:* `{fin.get('pe', 'N/A')}x` | *P/B:* `{asset_val.get('pb', fin.get('pb', 'N/A'))}x`\n"
        f"💎 *BVPS (Giá trị sổ sách):* `{asset_val.get('bvps', 0):,.0f} VND`\n"
        f"📊 *ROE:* `{fin.get('roe', 'N/A')}%` | *Biên ròng:* `{fin.get('net_margin', 'N/A')}%`\n"
        f"💳 *Nợ vay / Vốn CSH:* `{fin.get('debt_to_equity', 'N/A')}x`\n"
        f"🔬 *Chất lượng Lợi nhuận (CFO):* Hạng `{cf.get('quality_grade', 'N/A')}` ({cf.get('quality_verdict', '')})\n"
        f"🚨 *Radar Thao túng:* Cấp `{asset_val.get('manipulation_risk_level', 1)}/5` ({asset_val.get('manipulation_verdict', 'An toàn')})\n"
    )

    if gov:
        own = gov.get("ownership", {})
        lead = gov.get("leadership", {})
        msg += (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"👥 *QUẢN TRỊ & CỔ ĐÔNG (G-Score: {gov.get('g_score', 0)}/100 - {gov.get('g_rating', '')}):*\n"
            f"• Trôi nổi: `{own.get('free_float_pct', 0)}%` | Ngoại: `{own.get('foreigner_pct', 0)}%`\n"
            f"• Lãnh đạo (Skin in game): `{lead.get('insider_total_pct', 0)}%` ({lead.get('skin_in_game_verdict', '')})\n"
        )

    if seg and seg.get("segments"):
        msg += "🏢 *Cơ cấu doanh thu cốt lõi:*\n"
        for s in seg.get("segments", [])[:3]:
            msg += f"• {s.get('name')}: `{s.get('rev_share_pct')}% DT` | `{s.get('gross_profit_share_pct')}% LNG`\n"

    msg += (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🧐 *Warren Buffett:* _{fa.get('buffett', {}).get('reasons', [''])[0]}_\n"
        f"🚀 *Peter Lynch:* _{fa.get('lynch', {}).get('reasons', [''])[0]}_\n"
    )

    buttons = {
        "inline_keyboard": [
            [{"text": f"📈 Soi Kỹ Thuật ({symbol})", "callback_data": f"ta:{symbol}"}, {"text": f"🔍 Soi Đầy Đủ ({symbol})", "callback_data": f"soi:{symbol}"}],
            [{"text": "🔙 Menu Chính", "callback_data": "cmd:menu"}]
        ]
    }
    send_message(chat_id, msg, reply_markup=buttons)


def handle_ta(chat_id: str | int, symbol: str):
    """Phân tích chuyên sâu Kỹ thuật (TA & Chart) trực tiếp trên tin nhắn Telegram."""
    symbol = symbol.upper().strip()
    send_message(chat_id, f"⏳ Đang phân tích Chart & Dòng tiền cho mã *{symbol}*...")
    data = analyze_ticker_ta(symbol)
    if not data:
        send_message(chat_id, f"❌ Không thể lấy dữ liệu kỹ thuật cho mã `{symbol}`.")
        return

    ta = data["ta"]
    trade = data["trade"]
    quote = data["quote"]
    ind = ta.get("indicators", {})

    msg = (
        f"📈 *PHÂN TÍCH KỸ THUẬT & DÒNG TIỀN: {symbol}*\n"
        f"🏢 _{quote.get('company_name', symbol)}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Giá hiện tại:* `{ind.get('close', 0):,.0f} VND` ({quote.get('change_pct', 0):+.2f}%)\n"
        f"📉 *EMA 20 (Ngắn hạn):* `{ind.get('ema20', 0):,.0f}` | *EMA 50:* `{ind.get('ema50', 0):,.0f}`\n"
        f"📦 *Volume Ratio (so MA20):* `{ind.get('vol_ratio', 1.0):.2f}x`\n"
        f"⚡ *RSI 14:* `{ind.get('rsi14', 50):.1f}`\n"
        f"🛡️ *Hỗ trợ 20 phiên:* `{ind.get('sup_20d', 0):,.0f}`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *KẾ HOẠCH GIAO DỊCH KỸ THUẬT:*\n"
        f"• Vùng mua tham khảo: `{trade.get('buy_zone')}`\n"
        f"• Cắt lỗ kỷ luật: `{trade.get('stop_loss', 0):,.0f} VND` (-{trade.get('stop_loss_pct', 0)}%)\n"
        f"• Chốt lời ngắn hạn (TP1): `{trade.get('take_profit_1', 0):,.0f} VND`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🦅 *William O'Neil (CANSLIM):* _{ta.get('oneil', {}).get('reasons', [''])[0]}_\n"
        f"🌊 *Wyckoff VSA:* Pha {ta.get('vsa', {}).get('phase')} - _{ta.get('vsa', {}).get('reasons', [''])[0]}_\n"
    )

    buttons = {
        "inline_keyboard": [
            [{"text": f"🏛️ Soi Cơ Bản ({symbol})", "callback_data": f"fa:{symbol}"}, {"text": f"🔍 Soi Đầy Đủ ({symbol})", "callback_data": f"soi:{symbol}"}],
            [{"text": "🔙 Menu Chính", "callback_data": "cmd:menu"}]
        ]
    }
    send_message(chat_id, msg, reply_markup=buttons)


def handle_performance_track(chat_id: str | int):
    """Tổng hợp và gửi báo cáo nghiệm thu PDCA (Hiệu suất khuyến nghị) lên Telegram."""
    send_message(chat_id, "⏳ *HỆ THỐNG PDCA ĐANG TỔNG HỢP HIỆU SUẤT KHUYẾN NGHỊ*...\n\nĐang đối chiếu các điểm vào lệnh quá khứ với biến động nến thực tế...")
    try:
        perf_data = evaluate_all_recommendations()
        summary_text = get_performance_telegram_summary(perf_data)
        buttons = {
            "inline_keyboard": [
                [{"text": "🏆 Top 10 Hôm Nay", "callback_data": "cmd:top10"}, {"text": "🔍 Soi Cổ Phiếu", "callback_data": "cmd:pick_soi"}],
                [{"text": "🔙 Menu Chính", "callback_data": "cmd:menu"}]
            ]
        }
        send_message(chat_id, summary_text, reply_markup=buttons)
    except Exception as e:
        send_message(chat_id, f"❌ Lỗi khi tính toán hiệu suất PDCA: {str(e)}")


def handle_chat(chat_id: str | int, text: str):
    """
    Xử lý giao tiếp 2 chiều thông minh bằng ngôn ngữ tự nhiên:
    - Nhận diện trực tiếp mã cổ phiếu
    - Điều hướng phân tích hoặc tra cứu giá tức thì
    - Tích hợp mô hình AI LLM Router nếu trực tuyến
    - Phản hồi hỗ trợ định lượng nếu ngoại tuyến
    """
    text_clean = text.strip()
    upper_tokens = re.findall(r'\b[A-Za-z]{3}\b', text_clean)
    upper_tokens = [t.upper() for t in upper_tokens]

    # Trường hợp 1: Người dùng chỉ gõ đúng 3 chữ cái mã cổ phiếu (VD: "HPG", "fpt", "vcb")
    if len(text_clean) == 3 and upper_tokens:
        sym = upper_tokens[0]
        handle_single_ticker_snapshot(chat_id, sym)
        return

    # Trường hợp 2: Nhận diện ý định cụ thể trong câu
    text_lower = text_clean.lower()
    if any(k in text_lower for k in ["soi ", "phân tích ", "đánh giá ", "báo cáo ", "xem xét "]) and upper_tokens:
        handle_analyze(chat_id, upper_tokens[0])
        return

    if any(k in text_lower for k in ["giá ", "gia ", "bảng giá ", "khớp lệnh "]) and upper_tokens:
        handle_quick_price(chat_id, upper_tokens[0])
        return

    if any(k in text_lower for k in ["top 10", "top10", "quét", "lọc", "mã đẹp", "cổ phiếu tốt", "tiềm năng"]):
        handle_scan(chat_id, top_n=10)
        return

    if any(k in text_lower for k in ["menu", "bảng điều khiển", "danh sách lệnh"]):
        handle_menu(chat_id)
        return

    # Trường hợp 3: Câu hỏi hội thoại / tham vấn Hội đồng AI
    global chat_memory
    send_message(chat_id, "⏳ Hội đồng AI đang tiếp nhận và suy luận câu hỏi của bạn...")

    router = LLMRouter()

    # Nếu LLM trực tuyến (Gemini, OpenAI, Claude, Ollama)
    if router.provider != "offline":
        if len(chat_memory) > 10:
            chat_memory = chat_memory[-10:]

        chat_history = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_memory])
        system_prompt = (
            "Bạn là Trưởng ban Điều phối Hội đồng Tham mưu Đầu tư TTCK Việt Nam theo AGENTS.md. "
            "Tư vấn sắc bén, trung thực, số liệu chuẩn xác, tách bạch Fact-Inference-Assumption. "
            "Không bịa số liệu, luôn đưa ra điều kiện làm luận điểm mất hiệu lực. "
            "Lịch sử hội thoại trước đó:\n" + chat_history
        )
        try:
            ai_reply = router.generate(system_prompt, text_clean)
            if ai_reply:
                chat_memory.append({"role": "User", "content": text_clean})
                chat_memory.append({"role": "Hội đồng AI", "content": ai_reply})
                send_message(chat_id, ai_reply, reply_markup=get_menu_inline_keyboard())
                return
        except Exception as e:
            print(f"⚠️ LLM Error: {e}")

    # Fallback khi chưa cấu hình API Key hoặc ở chế độ Offline Định Lượng
    if upper_tokens:
        sym = upper_tokens[0]
        quote = get_realtime_quote(sym)
        p = quote.get("price", 0)
        chg = quote.get("change_pct", 0)
        reply = (
            f"🤖 *HỘI ĐỒNG THAM MƯU AI (Chế độ Định lượng):*\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"Bạn vừa hỏi về mã *{sym}*.\n"
            f"• Giá hiện tại: `{p:,.0f} VND` ({chg:+.2f}%)\n"
            f"• Khối lượng giao dịch: `{quote.get('volume', 0):,.0f}` CP\n"
            f"• Động thái khối ngoại: `{quote.get('foreign_net_vol', 0):+,.0f}` CP\n\n"
            f"👉 Bạn muốn xem chi tiết góc nhìn nào?"
        )
        buttons = {
            "inline_keyboard": [
                [{"text": f"🔍 Soi Chuyên Sâu Hội Đồng ({sym})", "callback_data": f"soi:{sym}"}],
                [{"text": f"💵 Xem Bảng Giá Realtime ({sym})", "callback_data": f"gia:{sym}"}],
                [{"text": "🏆 Top 10 Toàn Thị Trường", "callback_data": "cmd:top10"}]
            ]
        }
        send_message(chat_id, reply, reply_markup=buttons)
    else:
        reply = (
            "🤖 *HỘI ĐỒNG THAM MƯU ĐẦU TƯ TTCK VIỆT NAM*\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Tôi đã nhận được câu hỏi của bạn. Hệ thống phân tích định lượng (Warren Buffett, Peter Lynch, William O'Neil, VSA) đã sẵn sàng phục vụ.\n\n"
            "💡 *Bạn có thể:*\n"
            "• Gõ tên mã (VD: `HPG`, `FPT`, `VCB`) để nhận phân tích tức thì.\n"
            "• Bấm nút dưới đây để chọn tính năng bạn cần:"
        )
        send_message(chat_id, reply, reply_markup=get_menu_inline_keyboard())


def handle_single_ticker_snapshot(chat_id: str | int, symbol: str):
    """Khi người dùng chỉ gõ 3 chữ cái mã cổ phiếu, phản hồi ngay bảng thông tin tóm tắt."""
    quote = get_realtime_quote(symbol)
    price = quote.get("price", 0)
    if price <= 0:
        send_message(chat_id, f"❌ Không tìm thấy thông tin mã `{symbol}`. Bạn vui lòng kiểm tra lại.")
        return

    change_pct = quote.get("change_pct", 0)
    trend_emoji = "🟢" if change_pct > 0 else ("🔴" if change_pct < 0 else "🟡")
    
    msg = (
        f"{trend_emoji} *THÔNG TIN NHANH: {symbol}*\n"
        f"🏢 {quote.get('company_name', symbol)}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💰 *Giá:* `{price:,.0f} VND` ({change_pct:+.2f}%)\n"
        f"📦 *Khối lượng:* `{quote.get('volume', 0):,.0f}` CP\n"
        f"🌐 *Khối ngoại ròng:* `{quote.get('foreign_net_vol', 0):+,.0f}` CP\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Bạn muốn thực hiện thao tác gì tiếp theo với mã *{symbol}*?"
    )
    buttons = {
        "inline_keyboard": [
            [{"text": f"🔍 Soi Chuyên Sâu Hội Đồng ({symbol})", "callback_data": f"soi:{symbol}"}],
            [{"text": f"💵 Bảng Giá Chi Tiết ({symbol})", "callback_data": f"gia:{symbol}"}],
            [{"text": "🏆 Top 10 Hôm Nay", "callback_data": "cmd:top10"}, {"text": "📋 Menu", "callback_data": "cmd:menu"}]
        ]
    }
    send_message(chat_id, msg, reply_markup=buttons)


# =====================================================================
# 4. BỘ ĐIỀU HƯỚNG CALLBACK QUERY (KHI NGƯỜI DÙNG BẤM NÚT INLINE)
# =====================================================================

def handle_callback_query(item: dict):
    """Xử lý sự kiện khi người dùng click vào bất kỳ nút bấm Inline nào."""
    cb = item.get("callback_query", {})
    cb_id = cb.get("id")
    data = cb.get("data", "")
    chat_id = cb.get("message", {}).get("chat", {}).get("id")

    if not chat_id or not data:
        return

    # Tắt spinner loading trên nút Telegram
    answer_callback_query(cb_id)

    # Chống double-click từ người dùng chạm nhanh vào nút Inline (trong vòng 3.5 giây)
    now = time.time()
    cb_key = f"{chat_id}:cb:{data}"
    if (now - _PROCESSING_REQUESTS.get(cb_key, 0.0)) < 3.5:
        print(f"⏱️ Bỏ qua double-click nút '{data}' từ chat {chat_id}.")
        return
    _PROCESSING_REQUESTS[cb_key] = now

    print(f"🔘 [Callback từ User {chat_id}]: {data}")

    if data == "cmd:menu":
        handle_menu(chat_id)
    elif data == "cmd:top10":
        handle_scan(chat_id, top_n=10)
    elif data == "cmd:pnl":
        handle_performance_track(chat_id)
    elif data == "cmd:pick_soi":
        handle_quick_soi_picker(chat_id)
    elif data == "cmd:pick_fa":
        send_message(chat_id, "🏛️ Bấm mã để soi Cơ Bản:", reply_markup=get_stock_picker_inline_keyboard(action="fa"))
    elif data == "cmd:pick_ta":
        send_message(chat_id, "📈 Bấm mã để soi Kỹ Thuật:", reply_markup=get_stock_picker_inline_keyboard(action="ta"))
    elif data == "cmd:pick_gia":
        handle_quick_gia_picker(chat_id)
    elif data == "cmd:watchlist":
        handle_watchlist_view(chat_id)
    elif data == "cmd:help":
        handle_help(chat_id)
    elif data.startswith("soi:"):
        symbol = data.split(":", 1)[1]
        handle_analyze(chat_id, symbol)
    elif data.startswith("fa:"):
        symbol = data.split(":", 1)[1]
        handle_fa(chat_id, symbol)
    elif data.startswith("ta:"):
        symbol = data.split(":", 1)[1]
        handle_ta(chat_id, symbol)
    elif data.startswith("gia:"):
        symbol = data.split(":", 1)[1]
        handle_quick_price(chat_id, symbol)


# =====================================================================
# 5. VÒNG LẶP CHÍNH CỦA BOT (POLLING LOOP)
# =====================================================================

def start_interactive_bot():
    """Khởi động Telegram Bot ở chế độ tương tác 2 chiều liên tục (Long Polling)."""
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN:
        print("❌ Telegram chưa được kích hoạt trong file .env!")
        print("Vui lòng kiểm tra TELEGRAM_BOT_TOKEN và TELEGRAM_ENABLED=true.")
        return

    # 1. Tự động dọn dẹp Webhook cũ nếu có để tránh lỗi 409 Conflict
    try:
        del_wh = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook?drop_pending_updates=false",
            timeout=10
        )
        if del_wh.status_code == 200:
            print("✅ Đã giải phóng Webhook để sẵn sàng cho chế độ Polling 2 chiều.")
    except Exception as e:
        print(f"⚠️ Cảnh báo dọn dẹp webhook: {e}")

    # 2. Đăng ký Menu lệnh trên giao diện Telegram
    if setup_bot_commands():
        print("✅ Đã thiết lập thành công Menu lệnh tương tác [/] trên ứng dụng Telegram.")

    # 3. Gửi thông báo sẵn sàng và nạp bàn phím tương tác cho người dùng
    if TELEGRAM_CHAT_ID:
        try:
            send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=(
                    "🚀 *HỘI ĐỒNG THAM MƯU ĐẦU TƯ TTCK VIỆT NAM ĐÃ TRỰC TUYẾN!*\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                    "Menu tương tác 2 chiều và Bàn phím điều khiển đã được kích hoạt thành công.\n"
                    "Bạn chỉ cần chạm vào các nút bên dưới hoặc gõ trực tiếp tên mã cổ phiếu."
                ),
                reply_markup=get_persistent_reply_keyboard()
            )
            print(f"📲 Đã gửi tin nhắn chào mừng và bật bàn phím tới Chat ID: {TELEGRAM_CHAT_ID}")
        except Exception as e:
            print(f"⚠️ Không thể gửi tin nhắn khởi động: {e}")

    print("\n" + "=" * 60)
    print("🤖 HỘI ĐỒNG AI TELEGRAM BOT ĐANG CHẠY LIÊN TỤC...")
    print("👉 Mở Telegram và nhấn các nút trên màn hình để kiểm tra giao tiếp 2 chiều.")
    print("👉 Nhấn Ctrl + C trên terminal để dừng bot bất cứ lúc nào.")
    print("=" * 60 + "\n")

    offset = None
    while True:
        try:
            url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
            params = {"timeout": 25}
            if offset is not None:
                params["offset"] = offset

            r = requests.get(url, params=params, timeout=35)
            if r.status_code == 200:
                data = r.json()
                for item in data.get("result", []):
                    up_id = item.get("update_id")
                    if up_id:
                        offset = up_id + 1
                        if up_id in _PROCESSED_UPDATE_IDS:
                            continue
                        _PROCESSED_UPDATE_IDS.add(up_id)
                        if len(_PROCESSED_UPDATE_IDS) > 2000:
                            _PROCESSED_UPDATE_IDS.clear()

                    # Trường hợp 1: Sự kiện bấm nút Inline (callback_query)
                    if "callback_query" in item:
                        handle_callback_query(item)
                        continue

                    # Trường hợp 2: Tin nhắn văn bản thông thường (message)
                    msg = item.get("message", {})
                    text = msg.get("text", "").strip()
                    chat_id = msg.get("chat", {}).get("id")

                    if not text or not chat_id:
                        continue

                    # Bộ lọc chat_id bảo mật nếu có thiết lập
                    if TELEGRAM_CHAT_ID and str(chat_id) != str(TELEGRAM_CHAT_ID):
                        continue

                    print(f"📩 [User {chat_id}]: {text}")

                    # Điều hướng các nút bấm trên Reply Keyboard và Command
                    if text in ["/start", "Khởi động"]:
                        handle_start(chat_id)
                    elif text in ["/menu", "📋 Menu Tính Năng", "Menu"]:
                        handle_menu(chat_id)
                    elif text in ["/top10", "/scan", "🏆 Top 10 Hôm Nay", "Top 10"]:
                        handle_scan(chat_id, top_n=10)
                    elif text in ["/pnl", "/track", "📈 Hiệu Suất PnL", "Hiệu suất"]:
                        handle_performance_track(chat_id)
                    elif text in ["/watchlist", "📊 Danh Mục Watchlist", "Watchlist"]:
                        handle_watchlist_view(chat_id)
                    elif text in ["🔍 Soi Cổ Phiếu", "Soi"]:
                        handle_quick_soi_picker(chat_id)
                    elif text in ["💵 Tra Giá Realtime", "Giá"]:
                        handle_quick_gia_picker(chat_id)
                    elif text in ["/help", "❓ Hướng Dẫn", "Hướng dẫn", "Help"]:
                        handle_help(chat_id)
                    elif text.startswith("/soi"):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            handle_analyze(chat_id, parts[1])
                        else:
                            handle_quick_soi_picker(chat_id)
                    elif text.startswith("/fa"):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            handle_fa(chat_id, parts[1])
                        else:
                            send_message(chat_id, "Vui lòng nhập mã cổ phiếu. Ví dụ: /fa HPG")
                    elif text.startswith("/ta"):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            handle_ta(chat_id, parts[1])
                        else:
                            send_message(chat_id, "Vui lòng nhập mã cổ phiếu. Ví dụ: /ta HPG")
                    elif text.startswith("/gia"):
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            handle_quick_price(chat_id, parts[1])
                        else:
                            handle_quick_gia_picker(chat_id)
                    else:
                        # Giao tiếp 2 chiều thông minh bằng ngôn ngữ tự nhiên
                        handle_chat(chat_id, text)

        except requests.exceptions.RequestException:
            time.sleep(3)
        except Exception as e:
            print(f"❌ Lỗi vòng lặp bot: {e}")
            time.sleep(2)


if __name__ == "__main__":
    start_interactive_bot()
