import requests
from typing import Dict, Any
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_ENABLED


def send_telegram_alert(symbol: str, trade_setup: Dict[str, Any], company_name: str = "") -> bool:
    """
    Gửi cảnh báo tín hiệu giao dịch trực tiếp về Telegram cá nhân / nhóm.
    """
    if not TELEGRAM_ENABLED or not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    action = trade_setup.get("action", "THEO DÕI")
    emoji = "🔥" if "MUA MẠNH" in action else ("⚡" if "MUA" in action else "⚠️")
    
    message = (
        f"{emoji} *TÍN HIỆU GIAO DỊCH CHỨNG KHOÁN VN*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📌 *Mã CP:* `{symbol}` - {company_name}\n"
        f"🎯 *Khuyến nghị:* *{action}*\n"
        f"⭐ *Độ đồng thuận:* `{trade_setup.get('consensus_score', 0)}/100 điểm`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💵 *Giá hiện tại:* `{trade_setup.get('current_price', 0):,.0f} VND`\n"
        f"🛒 *Vùng mua (Buy Zone):* `{trade_setup.get('buy_zone')}`\n"
        f"🛑 *Cắt lỗ (Stop Loss):* `{trade_setup.get('stop_loss', 0):,.0f} VND` (-{trade_setup.get('stop_loss_pct', 0)}%)\n"
        f"🎯 *Mục tiêu 1 (TP1):* `{trade_setup.get('take_profit_1', 0):,.0f} VND` (+{trade_setup.get('take_profit_1_pct', 0)}%)\n"
        f"🚀 *Mục tiêu 2 (TP2):* `{trade_setup.get('take_profit_2', 0):,.0f} VND` (+{trade_setup.get('take_profit_2_pct', 0)}%)\n"
        f"⚖️ *Tỷ lệ Risk / Reward:* `{trade_setup.get('risk_reward_ratio')}:1`\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"💡 *Chiến lược:* {trade_setup.get('action_summary')}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            payload.pop("parse_mode", None)
            r = requests.post(url, json=payload, timeout=10)
        if r.status_code == 200:
            print("📲 Đã gửi cảnh báo tín hiệu giao dịch về Telegram cá nhân!")
            return True
        else:
            print(f"⚠️ Telegram API response: {r.status_code} - {r.text}")
            return False
    except Exception as e:
        print(f"❌ Lỗi gửi cảnh báo Telegram: {e}")
        return False

