"""
Lớp Dịch vụ Hợp nhất (Unified Stock Service Layer)
Chịu trách nhiệm toàn bộ logic nghiệp vụ cốt lõi:
- Quét và sàng lọc toàn thị trường (Market Screener)
- Phân tích chuyên sâu 1 mã (Full, FA-only, TA-only)
- Điều phối lưu trữ Database và sinh báo cáo HTML/Alerts
Được dùng chung bởi CLI (main.py) và Telegram Bot (telegram_interactive_bot.py).
"""

import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import REPORTS_DIR, MIN_LIQUIDITY_VALUE
from core.data_loader import (
    get_realtime_quote,
    get_historical_ohlcv,
    get_financial_data,
    get_all_tickers_realtime
)
from core.fa_engine import analyze_fundamentals
from core.ta_engine import analyze_technicals
from core.risk_manager import calculate_trade_setup
from core.db_manager import save_eod_quote, save_recommendation
from core.html_report_generator import generate_html_report
from core.macro_engine import classify_sector, SECTOR_PROFILES
from ai.council import InvestmentCouncil
from alerts.telegram_bot import send_telegram_alert


def get_liquidity_rating(value_vnd: float) -> str:
    """Đánh giá chất lượng thanh khoản phiên"""
    if value_vnd >= 10_000_000_000:
        return "A (Cao)"
    elif value_vnd >= 2_000_000_000:
        return "B (Trung bình)"
    elif value_vnd >= 300_000_000:
        return "C (Thấp - Hidden Gem)"
    return "D (Chết thanh khoản)"


def matches_sector_filter(symbol: str, company_name: str, sector_filter: str) -> bool:
    """Kiểm tra mã cổ phiếu có khớp với từ khóa lọc ngành hay không"""
    if not sector_filter:
        return True

    sf = sector_filter.lower().strip()
    sec_key = classify_sector(symbol, {"organ_name": company_name})
    sec_conf = SECTOR_PROFILES.get(sec_key, {})
    sec_name = sec_conf.get("sector_name", "").lower()

    aliases = {
        "kcn": ["industrial_real_estate", "khu công nghiệp", "kcn"],
        "bds kcn": ["industrial_real_estate", "khu công nghiệp", "kcn"],
        "ban le": ["retail_consumer", "bán lẻ", "tiêu dùng"],
        "bán lẻ": ["retail_consumer", "bán lẻ", "tiêu dùng"],
        "retail": ["retail_consumer", "bán lẻ", "tiêu dùng"],
        "ngan hang": ["bank", "ngân hàng"],
        "ngân hàng": ["bank", "ngân hàng"],
        "bank": ["bank", "ngân hàng"],
        "thep": ["steel_materials", "thép", "vật liệu"],
        "thép": ["steel_materials", "thép", "vật liệu"],
        "steel": ["steel_materials", "thép", "vật liệu"],
        "chung khoan": ["securities", "chứng khoán"],
        "chứng khoán": ["securities", "chứng khoán"],
        "dau khi": ["oil_gas_energy", "dầu khí", "năng lượng"],
        "dầu khí": ["oil_gas_energy", "dầu khí", "năng lượng"],
        "dau tu cong": ["public_invest_infra", "đầu tư công", "hạ tầng"],
        "đầu tư công": ["public_invest_infra", "đầu tư công", "hạ tầng"],
        "xuat khau": ["export_seafood_textile", "xuất khẩu", "thủy sản", "dệt may"],
        "xuất khẩu": ["export_seafood_textile", "xuất khẩu", "thủy sản", "dệt may"],
        "cang bien": ["logistics_port", "cảng biển", "logistics"],
        "cảng biển": ["logistics_port", "cảng biển", "logistics"],
        "bds": ["residential_real_estate", "industrial_real_estate", "bất động sản", "địa ốc"],
    }

    for alias_key, target_terms in aliases.items():
        if alias_key in sf or sf in alias_key:
            if any(t in sec_key.lower() or t in sec_name or t in company_name.lower() for t in target_terms):
                return True

    return sf in sec_key.lower() or sf in sec_name or sf in company_name.lower() or sf in symbol.lower()


def run_screener(
    top_n: int = 10,
    sector_filter: Optional[str] = None,
    min_value: float = MIN_LIQUIDITY_VALUE,
    on_progress: Optional[Any] = None,
    progress_callback: Optional[Any] = None
) -> List[Dict[str, Any]]:
    """
    Quy trình sàng lọc toàn diện toàn bộ thị trường:
    1. Quét realtime toàn bộ cổ phiếu trên 3 sàn
    2. Lọc thanh khoản và lọc nhóm ngành
    3. Phân tích TA chọn top ứng viên nổ vol
    4. Phân tích BCTC & Vĩ mô chuyên sâu
    5. Xếp hạng tổng thể
    """
    callback = progress_callback or on_progress
    if callback:
        callback("Tải dữ liệu bảng giá Realtime 3 sàn...")

    all_tickers = get_all_tickers_realtime()
    if not all_tickers:
        return []

    # Lọc thanh khoản
    liquid_tickers = [t for t in all_tickers if t.get("value", 0) >= min_value]

    if sector_filter:
        liquid_tickers = [
            t for t in liquid_tickers
            if matches_sector_filter(t.get("symbol", ""), t.get("company_name", ""), sector_filter)
        ]

    liquid_tickers.sort(key=lambda x: (x.get("change_pct", 0), x.get("value", 0)), reverse=True)
    eval_pool = liquid_tickers[:80]

    if callback:
        callback(f"Đã lọc {len(liquid_tickers)} mã đạt thanh khoản. Đang phân tích kỹ thuật...")

    ta_candidates = []
    for idx, t in enumerate(eval_pool, start=1):
        sym = t["symbol"]
        try:
            df_ohlcv = get_historical_ohlcv(sym, days=250)
            if df_ohlcv.empty:
                continue
            ta_result = analyze_technicals(df_ohlcv)
            t["ta_score"] = ta_result.get("ta_total_score", 50)
            t["vol_ratio"] = ta_result.get("indicators", {}).get("vol_ratio", 1.0)
            t["ta_result"] = ta_result
            ta_candidates.append(t)
        except Exception:
            pass

    # Sort theo nổ vol và điểm TA
    ta_candidates.sort(key=lambda x: (x["vol_ratio"] >= 1.2, x["ta_score"], x["vol_ratio"]), reverse=True)
    final_candidates = ta_candidates[:min(len(ta_candidates), max(top_n, 8))]

    if callback:
        callback(f"Đang bóc tách BCTC chuyên sâu cho Top {len(final_candidates)} mã...")

    results = []
    for c in final_candidates:
        sym = c["symbol"]
        price = c["price"]
        ta_result = c["ta_result"]

        try:
            fin_data = get_financial_data(sym)
            fa_result = analyze_fundamentals(fin_data, price, c)
            trade = calculate_trade_setup(price, fa_result, ta_result, c)

            sector_name = fa_result.get("macro", {}).get("sector_name", "Doanh nghiệp")
            cfo_grade = fa_result.get("cash_flow", {}).get("quality_grade", "B")

            results.append({
                "symbol": sym,
                "exchange": c.get("exchange", ""),
                "sector_name": sector_name,
                "price": price,
                "change_pct": c.get("change_pct", 0),
                "value": c.get("value", 0),
                "vol_ratio": c.get("vol_ratio", 1.0),
                "consensus_score": trade.get("consensus_score", 0),
                "action": trade.get("action", "QUAN SÁT"),
                "buy_zone": trade.get("buy_zone", ""),
                "stop_loss": trade.get("stop_loss", 0),
                "tp1": trade.get("take_profit_1", 0),
                "f_score": fa_result.get("f_score", 0),
                "cfo_grade": cfo_grade,
                "pe": fa_result.get("ratios", {}).get("pe", "N/A"),
                "liquidity": get_liquidity_rating(c.get("value", 0))
            })
            time.sleep(0.15)
        except Exception:
            pass

    results.sort(key=lambda x: (x["consensus_score"], x["vol_ratio"]), reverse=True)

    return results[:top_n]


def analyze_ticker_full(
    symbol: str,
    save_report: bool = True,
    send_alert: bool = True
) -> Dict[str, Any]:
    """
    Quy trình phân tích chuyên sâu toàn diện 1 mã cổ phiếu (Top-down FA & TA).
    Tự động ghi Database EOD quote, Recommendation và sinh Báo cáo HTML.
    """
    symbol = symbol.upper().strip()

    # 1. Thu thập dữ liệu giá
    quote = get_realtime_quote(symbol)
    current_price = quote.get("price", 0)

    # Fallback giá nếu bảng giá chưa có
    if current_price <= 0:
        df_tmp = get_historical_ohlcv(symbol, days=30)
        if not df_tmp.empty:
            current_price = float(df_tmp["close"].iloc[-1])
            quote["price"] = current_price

    if current_price <= 0:
        return {"error": f"Không tìm thấy dữ liệu giá cho mã {symbol}."}

    # 2. Thu thập dữ liệu kỹ thuật & cơ bản
    df_ohlcv = get_historical_ohlcv(symbol, days=250)
    ta_result = analyze_technicals(df_ohlcv)

    fin_data = get_financial_data(symbol)
    if fin_data.get("eps") and fin_data["eps"] > 0 and current_price > 0:
        fin_data["pe"] = round(current_price / fin_data["eps"], 2)
    if fin_data.get("bvps") and fin_data["bvps"] > 0 and current_price > 0:
        fin_data["pb"] = round(current_price / fin_data["bvps"], 2)

    fa_result = analyze_fundamentals(fin_data, current_price, quote)
    trade_setup = calculate_trade_setup(current_price, fa_result, ta_result, quote)

    # 3. Lưu trữ SQLite Database
    save_eod_quote(quote)
    save_recommendation(trade_setup, quote)

    # 4. Phản biện Hội đồng AI
    council = InvestmentCouncil()
    council_result = council.deliberate(symbol, quote, fa_result, ta_result, trade_setup)

    # 5. Xuất bản Báo cáo HTML
    html_path = None
    if save_report:
        html_path = generate_html_report(symbol, quote, fa_result, ta_result, trade_setup, council_result)

    # 6. Gửi Telegram nếu bật
    if send_alert:
        send_telegram_alert(
            symbol=symbol,
            trade_setup=trade_setup,
            company_name=quote.get("company_name", ""),
            fa_result=fa_result,
            html_report_path=html_path
        )

    return {
        "symbol": symbol,
        "quote": quote,
        "current_price": current_price,
        "fa_result": fa_result,
        "ta_result": ta_result,
        "trade_setup": trade_setup,
        "council_result": council_result,
        "html_path": html_path
    }


def analyze_ticker_fa(symbol: str) -> Dict[str, Any]:
    """Phân tích chuyên sâu mảng Cơ bản (FA)"""
    symbol = symbol.upper().strip()
    quote = get_realtime_quote(symbol)
    current_price = quote.get("price", 0)

    if current_price <= 0:
        df_tmp = get_historical_ohlcv(symbol, days=30)
        if not df_tmp.empty:
            current_price = float(df_tmp["close"].iloc[-1])
            quote["price"] = current_price

    fin_data = get_financial_data(symbol)
    fa_result = analyze_fundamentals(fin_data, current_price, quote)

    return {
        "symbol": symbol,
        "quote": quote,
        "current_price": current_price,
        "fa_result": fa_result
    }


def analyze_ticker_ta(symbol: str) -> Dict[str, Any]:
    """Phân tích chuyên sâu mảng Kỹ thuật (TA) & Kế hoạch ngắn hạn"""
    symbol = symbol.upper().strip()
    quote = get_realtime_quote(symbol)
    current_price = quote.get("price", 0)

    df_ohlcv = get_historical_ohlcv(symbol, days=250)
    if current_price <= 0 and not df_ohlcv.empty:
        current_price = float(df_ohlcv["close"].iloc[-1])
        quote["price"] = current_price

    ta_result = analyze_technicals(df_ohlcv)
    trade_setup = calculate_trade_setup(current_price, {"fa_total_score": 50}, ta_result, quote)

    return {
        "symbol": symbol,
        "quote": quote,
        "current_price": current_price,
        "ta_result": ta_result,
        "trade_setup": trade_setup
    }
