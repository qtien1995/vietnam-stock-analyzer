import time
import requests
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Đảm bảo console Windows in đúng UTF-8 không bị UnicodeEncodeError
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

import json

from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED

# Cache chống gửi đúp cảnh báo lưu file (Persistent De-duplication guard liên tiến trình)
CACHE_FILE = Path("data") / "alerts_cache.json"


def _load_alert_cache() -> Dict[str, float]:
    try:
        if CACHE_FILE.exists():
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_alert_cache(cache: Dict[str, float]):
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        now = time.time()
        # Dọn dẹp các mục cũ hơn 24 giờ
        cleaned = {k: v for k, v in cache.items() if (now - v) < 86400}
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cleaned, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def is_duplicate_alert(target_chat_id: str | int, symbol: str, cooldown_seconds: float = 90.0) -> bool:
    """Kiểm tra xem cảnh báo cho mã này vừa được gửi tới chat_id chưa (trên toàn hệ thống)."""
    cache = _load_alert_cache()
    key = f"{target_chat_id}_{symbol.upper()}"
    last_sent = cache.get(key, 0.0)
    now = time.time()
    return (now - last_sent) < cooldown_seconds


def record_sent_alert(target_chat_id: str | int, symbol: str):
    """Ghi nhận thời điểm vừa gửi cảnh báo thành công vào ổ cứng."""
    cache = _load_alert_cache()
    key = f"{target_chat_id}_{symbol.upper()}"
    cache[key] = time.time()
    _save_alert_cache(cache)



def send_telegram_document(
    file_path: str | Path,
    caption: str = "",
    chat_id: Optional[str | int] = None
) -> bool:
    """
    Gửi file tài liệu (HTML report, PDF, log...) trực tiếp qua Telegram Bot bằng API sendDocument.
    Cho phép người dùng bấm vào mở trực tiếp trên di động hoặc máy tính.
    """
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_BOT_TOKEN or not target_chat_id:
        return False

    path = Path(file_path)
    if not path.exists():
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument"
    try:
        with open(path, "rb") as f:
            files = {"document": (path.name, f, "text/html")}
            data = {"chat_id": str(target_chat_id), "caption": caption}
            r = requests.post(url, data=data, files=files, timeout=25)
            if r.status_code == 200:
                print(f"📄 Đã gửi file báo cáo HTML ({path.name}) trực tiếp về Telegram!")
                return True
            else:
                print(f"⚠️ Telegram sendDocument error: {r.status_code} - {r.text}")
                return False
    except Exception as e:
        print(f"❌ Lỗi gửi file HTML qua Telegram: {e}")
        return False


def send_telegram_alert(
    symbol: str,
    trade_setup: Dict[str, Any],
    company_name: str = "",
    fa_result: Optional[Dict[str, Any]] = None,
    html_report_path: Optional[str | Path] = None,
    chat_id: Optional[str | int] = None
) -> bool:
    """
    Gửi cảnh báo tín hiệu giao dịch phân tách bạch 2 TRƯỜNG PHÁI:
    1. VÙNG MUA ĐẦU TƯ GIÁ TRỊ (Tích sản / Biên an toàn - Warren Buffett & Graham)
       Kèm Định giá thực, lý do và cảnh báo nếu thị giá đang vượt quá giá trị thực.
    2. VÙNG MUA LƯỚT SÓNG NGẮN HẠN (Swing / Kỹ thuật - O'Neil & Wyckoff)
       Dành cho người lướt sóng theo đà dòng tiền kèm Cắt lỗ, Chốt lời, R:R và kỷ luật.
    3. ĐÍNH KÈM FILE HTML BÁO CÁO TRỰC QUAN để mở ngay trên điện thoại và máy tính.
    """
    target_chat_id = chat_id or TELEGRAM_CHAT_ID
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not target_chat_id:
        return False

    # Cơ chế kiểm tra chống gửi đúp liên tiến trình lưu file (Persistent De-duplication 90s)
    if is_duplicate_alert(target_chat_id, symbol, cooldown_seconds=90.0):
        print(f"⏱️ Đã chặn cảnh báo gửi đúp cho mã {symbol} (vừa gửi trong vòng 90 giây trước trên toàn hệ thống).")
        return True

    action = trade_setup.get("action", "THEO DÕI")
    emoji = "🔥" if "MUA MẠNH" in action else ("⚡" if "MUA" in action else "⚠️")
    
    current_price = trade_setup.get("current_price", 0.0)
    fair_price = trade_setup.get("fair_price", 0.0)
    value_status = trade_setup.get("value_status", "ĐỊNH GIÁ HỢP LÝ")
    value_buy_zone = trade_setup.get("value_buy_zone", f"≤ {fair_price:,.0f} VND")
    value_rationale = trade_setup.get("value_rationale", "Dựa trên định giá P/E, P/B và sức mạnh dòng tiền cốt lõi.")
    value_warning = trade_setup.get("value_warning", "")
    val_gap_expl = trade_setup.get("valuation_gap_explanation", "")
    
    swing_buy_zone = trade_setup.get("swing_buy_zone") or trade_setup.get("buy_zone", "")
    stop_loss = trade_setup.get("stop_loss", 0.0)
    stop_loss_pct = trade_setup.get("stop_loss_pct", 7.0)
    tp1 = trade_setup.get("take_profit_1", 0.0)
    tp1_pct = trade_setup.get("take_profit_1_pct", 9.0)
    tp2 = trade_setup.get("take_profit_2", 0.0)
    tp2_pct = trade_setup.get("take_profit_2_pct", 22.0)
    rr_ratio = trade_setup.get("risk_reward_ratio", 2.0)
    max_pos = trade_setup.get("max_position_size_pct", 15.0)
    swing_note = trade_setup.get("swing_strategy_note", "")

    # Thông tin Vĩ mô & FA nếu có
    macro_info = ""
    if fa_result:
        macro = fa_result.get("macro", {})
        if macro.get("sector_name"):
            macro_info = f"🏢 *Ngành:* _{macro.get('sector_name')}_ (Pha: {macro.get('cycle_phase', 'Bình thường')})\n"

    # Xây dựng nội dung tin nhắn Markdown
    message = (
        f"{emoji} *TÍN HIỆU PHÂN TÍCH CHỨNG KHOÁN VN*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Mã CP:* `{symbol}` - {company_name}\n"
        f"{macro_info}"
        f"💵 *Thị giá hiện tại:* `{current_price:,.0f} VND`\n"
        f"🎯 *Khuyến nghị:* *{action}*\n"
        f"⭐ *Độ đồng thuận:* `{trade_setup.get('consensus_score', 0)}/100 điểm`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏛️ *1. GÓC NHÌN ĐẦU TƯ GIÁ TRỊ (BUFFETT & GRAHAM):*\n"
        f"• *Trạng thái:* *{value_status}*\n"
        f"• *Giá trị thực ước tính (Fair Value):* `{fair_price:,.0f} VND`\n"
        f"• *Vùng gom an toàn (Margin of Safety ≥ 15%):* `{value_buy_zone}`\n"
        f"• *Lý do định giá:* _{value_rationale}_\n"
    )

    if val_gap_expl:
        message += f"• 💡 *Lý giải chênh lệch thị giá vs giá trị thực:* _{val_gap_expl}_\n"

    if value_warning:
        message += f"• ⚠️ *Cảnh báo giá trị:* _{value_warning}_\n"

    message += (
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🏄 *2. KẾ HOẠCH LƯỚT SÓNG NGẮN HẠN (SWING / KỸ THUẬT):*\n"
        f"• *Vùng mua lướt sóng (Buy Zone):* `{swing_buy_zone}`\n"
        f"• *Cắt lỗ nghiêm ngặt (Stop Loss):* `{stop_loss:,.0f} VND` (-{stop_loss_pct}%)\n"
        f"• *Mục tiêu ngắn hạn (TP1):* `{tp1:,.0f} VND` (+{tp1_pct}%)\n"
        f"• *Mục tiêu trung hạn (TP2):* `{tp2:,.0f} VND` (+{tp2_pct}%)\n"
        f"• *Tỷ lệ Risk / Reward:* `{rr_ratio}:1` | Tỷ trọng NAV: `Max {max_pos:.1f}%`\n"
    )

    if swing_note:
        message += f"• 💡 *Lưu ý lướt sóng:* _{swing_note}_\n"

    # Link báo cáo HTML
    if html_report_path:
        html_p = Path(html_report_path)
        message += (
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🌐 *BÁO CÁO HTML TRỰC QUAN (MOBILE & DESKTOP):*\n"
            f"• Đã đính kèm file `{html_p.name}` bên dưới!\n"
            f"• *Mẹo:* Chạm vào file đính kèm trên Telegram để mở xem ngay báo cáo tương tác Chart.js đa tầng.\n"
        )

    # 1. Gửi tin nhắn Text qua Telegram
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": str(target_chat_id),
        "text": message,
        "parse_mode": "Markdown",
    }

    send_success = False
    try:
        r = requests.post(url, json=payload, timeout=12)
        if r.status_code != 200:
            # Fallback nếu lỗi markdown entity
            payload.pop("parse_mode", None)
            r = requests.post(url, json=payload, timeout=12)
        if r.status_code == 200:
            print("📲 Đã gửi cảnh báo tín hiệu giao dịch về Telegram cá nhân!")
            send_success = True
            record_sent_alert(target_chat_id, symbol)
        else:
            print(f"⚠️ Telegram API response: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"❌ Lỗi gửi tin nhắn Telegram: {e}")

    # 2. Gửi đính kèm file HTML trực tiếp nếu có
    if html_report_path and Path(html_report_path).exists():
        send_telegram_document(
            file_path=html_report_path,
            caption=f"🌐 Báo cáo chiến lược toàn diện: {symbol} | Vietnam Stock Analyzer",
            chat_id=target_chat_id
        )

    return send_success
