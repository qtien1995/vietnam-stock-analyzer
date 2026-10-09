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
from core.data_loader import get_realtime_quote, get_historical_ohlcv, get_financial_data, get_all_tickers_realtime
from core.fa_engine import analyze_fundamentals
from core.ta_engine import analyze_technicals
from core.risk_manager import calculate_trade_setup
from core.db_manager import save_eod_quote, save_recommendation
from ai.council import InvestmentCouncil
from ai.llm_router import LLMRouter

# Bộ nhớ hội thoại ngắn hạn (Context Memory)
chat_memory: List[Dict[str, str]] = []


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
            [{"text": "📊 Danh Mục Watchlist"}, {"text": "❓ Hướng Dẫn"}]
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
                {"text": "📊 Danh Mục Watchlist (20 mã)", "callback_data": "cmd:watchlist"},
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
    if action == 'soi':
        rows.append([{"text": "🏛️ Soi FA", "callback_data": "cmd:pick_fa"}, {"text": "📈 Soi TA", "callback_data": "cmd:pick_ta"}])
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


def handle_scan(chat_id: str | int, top_n: int = 10):
    send_message(chat_id, "⏳ *HỆ THỐNG RADAR TÀN CẦU ĐANG KHỞI ĐỘNG*...\n\nĐang quét Realtime toàn bộ 1500+ mã trên HOSE, HNX, UPCoM...")
    
    try:
        from core.data_loader import get_all_tickers_realtime
        all_tickers = get_all_tickers_realtime()
        
        if not all_tickers:
            send_message(chat_id, "❌ Lỗi kết nối dữ liệu. Vui lòng thử lại sau.")
            return
            
        liquid_tickers = [t for t in all_tickers if t.get('value', 0) >= 300_000_000]
        liquid_tickers.sort(key=lambda x: (x.get('change_pct', 0), x.get('value', 0)), reverse=True)
        eval_pool = liquid_tickers[:40]
        
        send_message(chat_id, f"✅ Đã lọc ra {len(liquid_tickers)} mã đạt chuẩn Thanh khoản (>300tr/phiên).\nĐang nạp OHLCV để quét tín hiệu TA...")
        
        ta_candidates = []
        for t in eval_pool:
            sym = t['symbol']
            try:
                df_ohlcv = get_historical_ohlcv(sym, days=150)
                if df_ohlcv.empty:
                    continue
                ta_result = analyze_technicals(df_ohlcv)
                t['ta_score'] = ta_result.get('ta_total_score', 50)
                t['vol_ratio'] = ta_result.get('indicators', {}).get('vol_ratio', 1.0)
                t['ta_result'] = ta_result
                ta_candidates.append(t)
            except Exception:
                pass
                
        ta_candidates.sort(key=lambda x: (x['vol_ratio'] >= 1.2, x['ta_score'], x['vol_ratio']), reverse=True)
        final_candidates = ta_candidates[:min(top_n, 8)]
        
        send_message(chat_id, f"✅ Đã quét xong Kỹ thuật. Đang đi sâu soi BCTC (FA) Top {len(final_candidates)} siêu cổ...")
        
        results = []
        for c in final_candidates:
            sym = c['symbol']
            fin = get_financial_data(sym)
            fa = analyze_fundamentals(fin, c['price'])
            trade = calculate_trade_setup(c['price'], fa, c['ta_result'], c)
            results.append({
                'symbol': sym,
                'price': c['price'],
                'change_pct': c['change_pct'],
                'action': trade.get('action', 'QUAN SÁT'),
                'score': trade.get('consensus_score', 0),
                'f_score': fa.get('f_score', 0),
                'pe': fa.get('ratios', {}).get('pe', 'N/A')
            })
            
        results.sort(key=lambda x: x['score'], reverse=True)
        
        msg = f"🏆 *TOP {len(results)} SIÊU CỔ PHIẾU HÔM NAY*\n\n"
        for idx, r in enumerate(results, 1):
            act_icon = "🟢" if "MUA" in r['action'] else ("🟡" if "THEO DÕI" in r['action'] else "🔴")
            msg += f"{idx}. *{r['symbol']}* - {r['price']:,.0f} ({r['change_pct']:+.1f}%)\n"
            msg += f"   {act_icon} Khuyến nghị: *{r['action']}*\n"
            msg += f"   🎯 Điểm Đ.Thuận: {r['score']}/100 | FA: {r['f_score']}/9 | P/E: {r['pe']}\n\n"
            
        msg += "💡 _Dùng /fa <Mã> hoặc /ta <Mã> để xem chi tiết._"
        
        send_message(chat_id, msg)
        
    except Exception as e:
        send_message(chat_id, f"❌ Lỗi khi quét thị trường: {str(e)}")

def handle_analyze(chat_id: str | int, symbol: str):
    """Phân tích chuyên sâu 1 mã với 5 góc nhìn Hội đồng AI."""
    symbol = symbol.upper().strip()
    send_message(chat_id, f"⏳ Đang lấy dữ liệu BCTC & Kỹ thuật mới nhất cho mã *{symbol}*...")

    quote = get_realtime_quote(symbol)
    df_ohlcv = get_historical_ohlcv(symbol, days=250)
    fin_data = get_financial_data(symbol)

    current_price = quote.get("price") or (float(df_ohlcv["close"].iloc[-1]) if not df_ohlcv.empty else 0.0)
    if current_price <= 0:
        send_message(
            chat_id,
            f"❌ Không tìm thấy dữ liệu giá cho `{symbol}`. Vui lòng kiểm tra lại mã cổ phiếu.",
            reply_markup={"inline_keyboard": [[{"text": "🔙 Quay lại Menu", "callback_data": "cmd:menu"}]]}
        )
        return

    save_eod_quote(quote)

    fa_result = analyze_fundamentals(fin_data, current_price)
    ta_result = analyze_technicals(df_ohlcv)
    trade_setup = calculate_trade_setup(current_price, fa_result, ta_result, quote)

    # Lưu recommendation vào Database
    save_recommendation(trade_setup, quote)

    council = InvestmentCouncil()
    council_result = council.deliberate(symbol, quote, fa_result, ta_result, trade_setup)

    # Các thông số cơ bản cốt lõi
    fin = fa_result.get("ratios", {})
    pe_val = fin.get("pe")
    pb_val = fin.get("pb")
    roe_val = fin.get("roe")
    gr_val = fin.get("profit_growth")
    pe_str = f"{pe_val:.1f}x" if pe_val is not None else "N/A"
    pb_str = f"{pb_val:.2f}x" if pb_val is not None else "N/A"
    roe_str = f"{roe_val:.1f}%" if roe_val is not None else "N/A"
    gr_str = f"{gr_val:+.1f}%" if gr_val is not None else "N/A"

    report_text = (
        f"📊 *BÁO CÁO: {symbol} - {quote.get('company_name', symbol)}*\n"
        f"📅 _Dữ liệu: Chốt phiên ngày {quote.get('trading_date') or datetime.now().strftime('%d/%m/%Y')}_\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Khuyến nghị:* *{trade_setup.get('action')}* ({trade_setup.get('consensus_score', 0)}/100 điểm)\n"
        f"💵 *Giá hiện tại:* `{current_price:,.0f} VND` ({quote.get('change_pct', 0):+.2f}%)\n"
        f"📈 *Chỉ số cốt lõi:* P/E: `{pe_str}` | P/B: `{pb_str}` | ROE: `{roe_str}` | Tăng trưởng LN: `{gr_str}`\n"
        f"🛒 *Vùng mua:* `{trade_setup.get('buy_zone')}`\n"
        f"🛑 *Cắt lỗ:* `{trade_setup.get('stop_loss', 0):,.0f}` (-{trade_setup.get('stop_loss_pct', 0)}%)\n"
        f"🚀 *Ngắn hạn (TP1):* `{trade_setup.get('take_profit_1', 0):,.0f}` (+{trade_setup.get('take_profit_1_pct', 0)}%)\n"
        f"🎯 *Trung hạn (TP2):* `{trade_setup.get('take_profit_2', 0):,.0f}` (+{trade_setup.get('take_profit_2_pct', 0)}%)\n"
        f"⚖️ *Tỷ lệ R:R:* `{trade_setup.get('risk_reward_ratio')}:1` | Tỷ trọng tối đa: `{trade_setup.get('max_position_size_pct', 10):.1f}% NAV`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Chiến lược:* {trade_setup.get('action_summary')}\n"
    )

    # Cảnh báo rủi ro nếu có
    val_warn = fa_result.get("valuation_warning")
    if val_warn or trade_setup.get("in_downtrend") or trade_setup.get("heavy_foreign_sell"):
        report_text += "\n⚠️ *CẢNH BÁO RỦI RO:*\n"
        if val_warn:
            report_text += f"• Định giá: _{val_warn}_\n"
        if trade_setup.get("in_downtrend"):
            report_text += "• Kỹ thuật: _Giá đang nằm dưới các đường xu hướng EMA20/EMA50 (ngắn & trung hạn)._\n"
        if trade_setup.get("heavy_foreign_sell"):
            report_text += f"• Dòng tiền: _Khối ngoại đang bán ròng mạnh ({quote.get('foreign_net_vol', 0):,.0f} CP)._\n"

    report_text += "\n🎭 *HỘI ĐỒNG PHÁN QUYẾT:*\n"

    # Trích xuất lý do từ các trường phái
    for role, key in [("Giá trị (Buffett)", "buffett"), ("Tăng trưởng (Lynch)", "lynch"), ("Kỹ thuật (O'Neil)", "oneil"), ("Dòng tiền (VSA)", "vsa")]:
        reason = (fa_result.get(key) or ta_result.get(key) or {}).get("reasons", [""])[0]
        report_text += f"• *{role}:* _{reason}_\n"

    action_buttons = {
        "inline_keyboard": [
            [
                {"text": f"💵 Giá Realtime ({symbol})", "callback_data": f"gia:{symbol}"},
                {"text": "🏆 Top 10 Hôm Nay", "callback_data": "cmd:top10"}
            ],
            [
                {"text": "🔍 Soi Mã Khác", "callback_data": "cmd:pick_soi"},
                {"text": "📋 Menu Chính", "callback_data": "cmd:menu"}
            ]
        ]
    }

    send_message(chat_id, report_text, reply_markup=action_buttons)


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

    print(f"🔘 [Callback từ User {chat_id}]: {data}")

    if data == "cmd:menu":
        handle_menu(chat_id)
    elif data == "cmd:top10":
        handle_scan(chat_id, top_n=10)
    elif data == "cmd:pick_soi":
        handle_quick_soi_picker(chat_id)
    elif data == "cmd:pick_gia":
        handle_quick_gia_picker(chat_id)
    elif data == "cmd:watchlist":
        handle_watchlist_view(chat_id)
    elif data == "cmd:help":
        handle_help(chat_id)
    elif data.startswith("soi:"):
        symbol = data.split(":", 1)[1]
        handle_analyze(chat_id, symbol)
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
                    offset = item["update_id"] + 1

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
                    elif text in ["/watchlist", "📊 Danh Mục Watchlist", "Watchlist"]:
                        handle_watchlist_view(chat_id)
                    elif text in ["🔍 Soi Cổ Phiếu", "Soi"]:
                        handle_quick_soi_picker(chat_id)
                    elif text in ["💵 Tra Giá Realtime", "Giá"]:
                        handle_quick_gia_picker(chat_id)
                    elif text in ["/help", "❓ Hướng Dẫn", "Hướng dẫn", "Help"]:
                        handle_help(chat_id)
                    elif text.startswith("/soi"):
                parts = text.split(" ")
                if len(parts) > 1:
                    handle_analyze(chat_id, parts[1])
            elif text.startswith("/fa"):
                parts = text.split(" ")
                if len(parts) > 1:
                    from main import analyze_single_ticker
                    analyze_single_ticker(parts[1], mode="fa", save_report=False, send_alert=False)
                    send_message(chat_id, f"✅ Đã chạy phân tích Cơ Bản cho {parts[1]}. Vui lòng xem Terminal.")
            elif text.startswith("/ta"):
                parts = text.split(" ")
                if len(parts) > 1:
                    from main import analyze_single_ticker
                    analyze_single_ticker(parts[1], mode="ta", save_report=False, send_alert=False)
                    send_message(chat_id, f"✅ Đã chạy phân tích Kỹ Thuật cho {parts[1]}. Vui lòng xem Terminal.")
            elif text == "/soi": # Block cũ để ignore
                        parts = text.split(maxsplit=1)
                        if len(parts) > 1:
                            handle_analyze(chat_id, parts[1])
                        else:
                            handle_quick_soi_picker(chat_id)
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
