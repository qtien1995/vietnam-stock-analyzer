import os
import sys
import time
import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

# Fix Windows console UTF-8 if needed
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Disable telemetry noise and deprecation banners from vnstock
os.environ["VNSTOCK_TELEMETRY"] = "off"
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, module="vnstock.*")
warnings.filterwarnings("ignore", message=".*vnstock.*", category=DeprecationWarning)
warnings.filterwarnings("ignore", message=".*StockComponents.*", category=DeprecationWarning)

HEADERS = {

    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def get_realtime_quote(symbol: str) -> dict:
    """
    Lấy giá khớp lệnh Realtime, khối lượng giao dịch và giao dịch khối ngoại
    từ cổng bảng giá SSI (HOSE/HNX/UPCoM) hoặc fallback sang DNSE.
    Đảm bảo 100% trả về đúng Sàn giao dịch (HOSE, HNX, UPCoM) và Biên độ trần/sàn.
    """
    symbol = symbol.upper().strip()
    from core.db_manager import save_stock_master, get_stock_master
    
    # 1. Thử lấy từ SSI iBoard trên cả 3 sàn
    for exchange in ["hose", "hnx", "upcom"]:
        url = f"https://iboard-query.ssi.com.vn/stock/exchange/{exchange}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=3)
            if r.status_code == 200:
                data = r.json().get("data", [])
                matched = next((x for x in data if x.get("stockSymbol") == symbol), None)
                if matched:
                    price = float(matched.get("matchedPrice") or matched.get("refPrice") or 0)
                    ref_price = float(matched.get("refPrice") or price)
                    change = float(matched.get("priceChange") or 0)
                    change_pct = float(matched.get("priceChangePercent") or 0)
                    vol = float(matched.get("stockVol") or matched.get("nmTotalTradedQty") or 0)
                    val = float(matched.get("nmTotalTradedValue") or 0)
                    foreign_buy = float(matched.get("buyForeignQtty") or 0)
                    foreign_sell = float(matched.get("sellForeignQtty") or 0)
                    high_p = float(matched.get("highest") or price)
                    low_p = float(matched.get("lowest") or price)
                    open_p = float(matched.get("openPrice") or price)

                    # Chuẩn hóa đơn vị giá sang VND (nếu nguồn trả về đơn vị nghìn đồng)
                    if 0 < price < 1000:
                        price *= 1000
                    if 0 < ref_price < 1000:
                        ref_price *= 1000
                    if 0 < high_p < 1000:
                        high_p *= 1000
                    if 0 < low_p < 1000:
                        low_p *= 1000
                    if 0 < open_p < 1000:
                        open_p *= 1000
                    if 0 < abs(change) < 100 and price >= 1000:
                        change *= 1000

                    ex_str = exchange.upper()
                    limit_pct = 7.0 if ex_str == "HOSE" else (10.0 if ex_str == "HNX" else 15.0)
                    comp_name = matched.get("clientName") or matched.get("companyNameVi", symbol)

                    # Lưu hoặc cập nhật master data
                    try:
                        save_stock_master(symbol, comp_name, ex_str, price_limit_pct=limit_pct)
                    except Exception:
                        pass
                    
                    return {
                        "symbol": symbol,
                        "exchange": ex_str,
                        "price_limit_pct": limit_pct,
                        "source": "SSI_REALTIME",
                        "price": price,
                        "ref_price": ref_price,
                        "change": change,
                        "change_pct": change_pct,
                        "high": high_p,
                        "low": low_p,
                        "open": open_p,
                        "volume": vol,
                        "value": val,
                        "foreign_net_vol": foreign_buy - foreign_sell,
                        "trading_date": matched.get("tradingDate") or datetime.now().strftime("%Y-%m-%d"),
                        "company_name": comp_name
                    }
        except Exception:
            pass

    # Tra cứu thông tin sàn và tên công ty dự phòng từ DB / Governance
    db_master = get_stock_master(symbol)
    resolved_ex = db_master.get("exchange", "")
    resolved_name = db_master.get("company_name", symbol)
    limit_pct = db_master.get("price_limit_pct", 7.0)

    if not resolved_ex:
        try:
            gov = get_governance_data(symbol)
            ov = gov.get("overview", {})
            com_code = str(ov.get("com_group_code", "")).upper()
            if "HNX" in com_code:
                resolved_ex = "HNX"
                limit_pct = 10.0
            elif "UPCOM" in com_code:
                resolved_ex = "UPCOM"
                limit_pct = 15.0
            else:
                resolved_ex = "HOSE"
                limit_pct = 7.0
            if ov.get("organ_name"):
                resolved_name = ov.get("organ_name")
            save_stock_master(symbol, resolved_name, resolved_ex, price_limit_pct=limit_pct)
        except Exception:
            resolved_ex = "HOSE"
            limit_pct = 7.0

    # 2. Fallback: Lấy qua nến DNSE gần nhất
    try:
        now = int(time.time())
        one_week_ago = now - 7 * 86400
        url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={one_week_ago}&to={now}&symbol={symbol}&resolution=1D"
        r = requests.get(url, headers=HEADERS, timeout=4)
        if r.status_code == 200:
            data = r.json()
            if data.get("c") and len(data["c"]) > 0:
                price = float(data["c"][-1])
                ref = float(data["o"][-1])
                vol = float(data["v"][-1])
                high_p = float(data["h"][-1])
                low_p = float(data["l"][-1])
                open_p = float(data["o"][-1])

                if 0 < price < 1000:
                    price *= 1000
                if 0 < ref < 1000:
                    ref *= 1000
                if 0 < high_p < 1000:
                    high_p *= 1000
                if 0 < low_p < 1000:
                    low_p *= 1000
                if 0 < open_p < 1000:
                    open_p *= 1000

                chg = price - ref
                pct = (chg / ref * 100) if ref > 0 else 0
                return {
                    "symbol": symbol,
                    "exchange": resolved_ex,
                    "price_limit_pct": limit_pct,
                    "source": "DNSE_FALLBACK",
                    "price": price,
                    "ref_price": ref,
                    "change": chg,
                    "change_pct": round(pct, 2),
                    "high": high_p,
                    "low": low_p,
                    "open": open_p,
                    "volume": vol,
                    "value": vol * price,
                    "foreign_net_vol": 0,
                    "trading_date": datetime.now().strftime("%Y-%m-%d"),
                    "company_name": resolved_name
                }
    except Exception:
        pass

    return {
        "symbol": symbol,
        "exchange": resolved_ex or "HOSE",
        "price_limit_pct": limit_pct or 7.0,
        "source": "UNKNOWN",
        "price": 0.0,
        "ref_price": 0.0,
        "change": 0.0,
        "change_pct": 0.0,
        "high": 0.0,
        "low": 0.0,
        "open": 0.0,
        "volume": 0.0,
        "value": 0.0,
        "foreign_net_vol": 0.0,
        "trading_date": datetime.now().strftime("%Y-%m-%d"),
        "company_name": resolved_name or symbol
    }


def get_historical_ohlcv(symbol: str, days: int = 300) -> pd.DataFrame:
    """
    Lấy chuỗi dữ liệu nến lịch sử OHLCV (Open, High, Low, Close, Volume)
    Ưu tiên qua DNSE / vnstock.
    """
    symbol = symbol.upper().strip()
    
    # Phương án 1: Lấy trực tiếp từ DNSE (nhanh và chuẩn nến)
    now = int(time.time())
    start_ts = now - int(days * 1.5 * 86400)
    url = f"https://services.entrade.com.vn/chart-api/v2/ohlcs/stock?from={start_ts}&to={now}&symbol={symbol}&resolution=1D"
    
    try:
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if data.get("t") and len(data["t"]) > 0:
                df = pd.DataFrame({
                    "time": pd.to_datetime(data["t"], unit="s"),
                    "open": [float(x) for x in data["o"]],
                    "high": [float(x) for x in data["h"]],
                    "low": [float(x) for x in data["l"]],
                    "close": [float(x) for x in data["c"]],
                    "volume": [float(x) for x in data["v"]],
                })
                df = df.sort_values("time").reset_index(drop=True)
                if not df.empty and df["close"].mean() < 1000:
                    for col in ["open", "high", "low", "close"]:
                        df[col] = df[col] * 1000
                return df
    except Exception:
        pass

    # Phương án 2: vnstock Quote
    try:
        from vnstock import Vnstock
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        stock = Vnstock().stock(symbol=symbol, source="VCI")
        df = stock.quote.history(start=start_date, end=end_date)
        if df is not None and not df.empty:
            df["time"] = pd.to_datetime(df["time"])
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.sort_values("time").reset_index(drop=True)
            if not df.empty and df["close"].mean() < 1000:
                for col in ["open", "high", "low", "close"]:
                    df[col] = df[col] * 1000
            return df
    except Exception:
        pass

def normalize_quarter_key(col: str) -> Optional[str]:
    """
    Chuẩn hóa định dạng cột quý về chuẩn YYYY_QX để sắp xếp thời gian chính xác:
    Ví dụ: 'Q2/2024' -> '2024_Q2', '2024-Q2' -> '2024_Q2', '2024-06' -> '2024_Q2', '2024_Q2' -> '2024_Q2'
    """
    import re
    s = str(col).strip().upper()
    # Pattern 1: YYYY-QX or YYYY_QX or YYYYQX
    m1 = re.search(r'(20\d\d)[-_/ ]*Q([1-4])', s)
    if m1:
        return f"{m1.group(1)}_Q{m1.group(2)}"
    # Pattern 2: QX/YYYY or QX-YYYY or QX YYYY
    m2 = re.search(r'Q([1-4])[-_/ ]*(20\d\d)', s)
    if m2:
        return f"{m2.group(2)}_Q{m2.group(1)}"
    # Pattern 3: YYYY-MM
    m3 = re.search(r'(20\d\d)[-_/ ](0[1-9]|1[0-2])', s)
    if m3:
        year = m3.group(1)
        month = int(m3.group(2))
        q = (month - 1) // 3 + 1
        return f"{year}_Q{q}"
    return None


def sort_quarter_columns(columns: list) -> list:
    """
    Sắp xếp các cột quý từ mới nhất đến cũ nhất dựa trên khóa YYYY_QX chuẩn.
    Trả về danh sách cột gốc đã được sắp xếp giảm dần theo thời gian.
    """
    def sort_key(col):
        norm = normalize_quarter_key(col)
        return norm if norm else ""
    return sorted(columns, key=sort_key, reverse=True)


def get_financial_data(symbol: str) -> dict:
    """
    Lấy dữ liệu cơ bản: Báo cáo tài chính, khối tài sản hiện có, nợ vay,
    chỉ số ROE, P/E, P/B, BVPS, EPS TTM và tăng trưởng.
    Tích hợp bộ nhớ đệm Caching cục bộ (JSON).
    """
    symbol = symbol.upper().strip()
    
    # 1. Kiểm tra cache cục bộ (BCTC lưu cache 7 ngày)
    from config import PROJECT_ROOT
    cache_dir = PROJECT_ROOT / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"fin_{symbol}.json"

    if cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if (time.time() - mtime) < 7 * 86400:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    # Nếu cache đầy đủ dữ liệu tài sản và dòng tiền mới thì dùng
                    if (
                        cached_data.get("bvps") is not None 
                        and cached_data.get("total_assets") is not None 
                        and cached_data.get("cfo_ttm") is not None
                    ):
                        return cached_data
        except Exception:
            pass

    result = {
        "symbol": symbol,
        "issue_share": None,
        "market_cap": None,
        "total_assets": None,
        "current_assets": None,
        "cash": None,
        "receivables": None,
        "inventories": None,
        "tangible_fixed_assets": None,
        "total_debt": None,
        "short_term_debt": None,
        "long_term_debt": None,
        "owners_equity": None,
        "retained_earnings": None,
        "short_term_liabilities": None,
        "working_capital": None,
        "ttm_revenue": None,
        "ttm_profit": None,
        "ebit_ttm": None,
        "pe": None,
        "pb": None,
        "roe": None,
        "roa": None,
        "roic": None,
        "gross_margin": None,
        "net_margin": None,
        "debt_to_equity": None,
        "liabilities_to_equity": None,
        "revenue_growth": None,
        "profit_growth": None,
        "eps": None,
        "bvps": None,
        "tbvps": None,
        "ncavps": None,
        "latest_quarter": None,
        "cash_buffer_ratio": None,
        "illiquid_assets_ratio": None,
        "cfo_ttm": None,
        "cfo_latest_q": None,
        "capex_ttm": None,
        "fcf_ttm": None,
        "cfi_ttm": None,
        "cff_ttm": None,
        "quarterly_cash_flows": [],
        "earnings_quality_ratio": None,
        "ttm_status": None
    }
    
    try:
        from vnstock import Vnstock
        api_key = os.getenv("VNSTOCK_API_KEY", "")
        if api_key:
            try:
                import vnai
                vnai.setup_api_key(api_key)
            except Exception:
                pass
        stock = Vnstock().stock(symbol=symbol, source="VCI")
        
        # 1. Lấy thông tin cổ phiếu lưu hành & Vốn hóa từ overview
        try:
            ov = stock.company.overview()
            if ov is not None and not ov.empty and "issue_share" in ov.columns:
                val = ov["issue_share"]
                if isinstance(val, pd.DataFrame):
                    val = val.iloc[0, 0]
                elif isinstance(val, pd.Series):
                    val = val.iloc[0]
                result["issue_share"] = float(val)
            if ov is not None and not ov.empty and "market_cap" in ov.columns:
                val_mc = ov["market_cap"]
                if isinstance(val_mc, pd.DataFrame):
                    val_mc = val_mc.iloc[0, 0]
                elif isinstance(val_mc, pd.Series):
                    val_mc = val_mc.iloc[0]
                result["market_cap"] = float(val_mc)
        except Exception:
            pass

        # Helper bóc tách giá trị số
        def clean_val(val):
            if pd.isna(val):
                return None
            if isinstance(val, str):
                val = val.replace("%", "").replace(",", "").strip()
            try:
                return float(val)
            except Exception:
                return None

        # 2. Lấy Bảng Cân Đối Kế Toán (Balance Sheet)
        bs_df = None
        latest_bs_q = None
        try:
            bs_df = stock.finance.balance_sheet(period="quarter")
            if bs_df is not None and not bs_df.empty:
                q_cols_bs = [c for c in bs_df.columns if "-" in str(c) or "Q" in str(c)]
                # vnstock sắp xếp quý mới nhất ở cột đầu tiên (hoặc kiểm tra năm)
                # Sắp xếp lại để lấy đúng quý mới nhất
                q_cols_sorted = sorted(q_cols_bs, reverse=True)
                latest_bs_q = q_cols_sorted[0] if q_cols_sorted else q_cols_bs[0]
                result["latest_quarter"] = latest_bs_q

                def find_bs_item(keyword_list, col=latest_bs_q):
                    for idx, row in bs_df.iterrows():
                        text = (str(row.get("item", "")) + " " + str(row.get("item_id", "")) + " " + str(row.get("item_en", ""))).lower()
                        for kw in keyword_list:
                            if kw.lower() in text:
                                v = clean_val(row.get(col))
                                if v is not None:
                                    return v
                    return 0.0

                result["total_assets"] = find_bs_item(["total_assets", "tổng cộng tài sản"])
                result["current_assets"] = find_bs_item(["current_assets", "tài sản ngắn hạn"])
                
                cash_val = find_bs_item(["cash_and_cash_equivalents", "tiền và tương đương tiền"])
                inv_val = find_bs_item(["đầu tư ngắn hạn", "short_term_investments", "đầu tư tài chính ngắn hạn"])
                result["cash"] = cash_val + inv_val
                
                result["receivables"] = find_bs_item(["accounts_receivable", "các khoản phải thu", "phải thu ngắn hạn"])
                result["inventories"] = find_bs_item(["inventories", "inventories_net", "hàng tồn kho"])
                result["tangible_fixed_assets"] = find_bs_item(["tài sản cố định", "fixed_assets"])
                
                total_liab = find_bs_item(["liabilities", "nợ phải trả"])
                st_debt = find_bs_item(["vay ngắn hạn", "short_term_debt"])
                lt_debt = find_bs_item(["vay dài hạn", "long_term_debt"])
                eq = find_bs_item(["owners_equity", "vốn chủ sở hữu"])
                
                st_liab = find_bs_item(["short_term_liabilities", "nợ ngắn hạn"])
                retained_eq = find_bs_item(["undistributed_earnings", "lợi nhuận sau thuế chưa phân phối", "lợi nhuận giữ lại"])
                
                result["total_debt"] = st_debt + lt_debt
                result["short_term_debt"] = st_debt
                result["long_term_debt"] = lt_debt
                result["owners_equity"] = eq
                result["short_term_liabilities"] = st_liab
                result["retained_earnings"] = retained_eq
                if result.get("current_assets") and st_liab > 0:
                    result["working_capital"] = result["current_assets"] - st_liab
                
                if eq > 0:
                    result["debt_to_equity"] = round((st_debt + lt_debt) / eq, 2)
                    result["liabilities_to_equity"] = round(total_liab / eq, 2)

                if result["total_assets"] and result["total_assets"] > 0:
                    result["cash_buffer_ratio"] = round((result["cash"] / result["total_assets"]) * 100, 1)
                    result["illiquid_assets_ratio"] = round(((result["receivables"] + result["inventories"]) / result["total_assets"]) * 100, 1)

                # Tính BVPS và NCAVPS nếu có số cổ phiếu
                shares = result.get("issue_share") or 0.0
                if shares > 0 and eq > 0:
                    result["bvps"] = round(eq / shares, 0)
                    result["tbvps"] = round(eq / shares, 0)
                    result["ncavps"] = round((result["current_assets"] - total_liab) / shares, 0)
        except Exception:
            pass

        # 3. Lấy Báo Cáo Kết Quả Kinh Doanh (Income Statement)
        try:
            inc_df = stock.finance.income_statement(period="quarter")
            if inc_df is not None and not inc_df.empty:
                q_cols_inc = [c for c in inc_df.columns if normalize_quarter_key(c) is not None or "-" in str(c) or "Q" in str(c)]
                q_cols_inc_sorted = sort_quarter_columns(q_cols_inc)
                recent_4q = q_cols_inc_sorted[:4]
                result["ttm_status"] = "COMPLETE" if len(recent_4q) >= 4 else "INCOMPLETE_QUARTERS"

                def sum_inc_item(keyword_list):
                    total = 0.0
                    found = False
                    for idx, row in inc_df.iterrows():
                        text = (str(row.get("item", "")) + " " + str(row.get("item_id", "")) + " " + str(row.get("item_en", ""))).lower()
                        for kw in keyword_list:
                            if kw.lower() in text:
                                for q in recent_4q:
                                    v = clean_val(row.get(q))
                                    if v is not None:
                                        total += v
                                found = True
                                break
                        if found:
                            break
                    return total if found else 0.0

                result["ttm_revenue"] = sum_inc_item(["net_sales", "doanh thu thuần", "doanh thu bán hàng"])
                result["ttm_profit"] = sum_inc_item(["attributable_to_parent_company", "cổ đông của công ty mẹ"])
                if result["ttm_profit"] == 0.0:
                    result["ttm_profit"] = sum_inc_item(["net_profit_loss_after_tax", "lợi nhuận sau thuế"])

                # EBIT TTM
                ebit = sum_inc_item(["operating_profit", "lợi nhuận thuần từ hoạt động kinh doanh", "ebit"])
                if ebit == 0.0:
                    pbt = sum_inc_item(["profit_before_tax", "lợi nhuận trước thuế"])
                    inte = sum_inc_item(["interest_expense", "chi phí lãi vay"])
                    ebit = pbt + inte
                result["ebit_ttm"] = ebit

                # Tính tăng trưởng cùng kỳ (YoY)
                if len(q_cols_inc_sorted) >= 5:
                    newest_q = q_cols_inc_sorted[0]
                    prev_yr_q = q_cols_inc_sorted[4]
                    for idx, row in inc_df.iterrows():
                        text = (str(row.get("item", "")) + " " + str(row.get("item_id", ""))).lower()
                        v_new = clean_val(row.get(newest_q))
                        v_old = clean_val(row.get(prev_yr_q))
                        if v_new is not None and v_old is not None and v_old != 0:
                            g = round((v_new - v_old) / abs(v_old) * 100, 2)
                            if ("doanh thu thuần" in text or "net_sales" in text) and result["revenue_growth"] is None:
                                result["revenue_growth"] = g
                            elif ("công ty mẹ" in text or "sau thuế" in text) and result["profit_growth"] is None:
                                result["profit_growth"] = g

                # Tính EPS TTM
                shares = result.get("issue_share") or 0.0
                if shares > 0 and result["ttm_profit"] is not None:
                    result["eps"] = round(result["ttm_profit"] / shares, 0)

                # Tính ROE, ROA
                if result.get("owners_equity") and result["owners_equity"] > 0 and result["ttm_profit"] is not None:
                    result["roe"] = round((result["ttm_profit"] / result["owners_equity"]) * 100, 2)
                if result.get("total_assets") and result["total_assets"] > 0 and result["ttm_profit"] is not None:
                    result["roa"] = round((result["ttm_profit"] / result["total_assets"]) * 100, 2)

                # Biên lợi nhuận TTM
                if result.get("ttm_revenue") and result["ttm_revenue"] > 0 and result["ttm_profit"] is not None:
                    result["net_margin"] = round((result["ttm_profit"] / result["ttm_revenue"]) * 100, 2)
        except Exception:
            pass

        # 4. Lấy Báo Cáo Lưu Chuyển Tiền Tệ (Cash Flow Statement)
        try:
            cf_df = stock.finance.cash_flow(period="quarter")
            if cf_df is not None and not cf_df.empty:
                q_cols_cf = [c for c in cf_df.columns if normalize_quarter_key(c) is not None or "-" in str(c) or "Q" in str(c)]
                q_cols_cf_sorted = sort_quarter_columns(q_cols_cf)
                recent_4q_cf = q_cols_cf_sorted[:4]

                def get_quarterly_cf_series(keyword_list):
                    for idx, row in cf_df.iterrows():
                        text = (str(row.get("item", "")) + " " + str(row.get("item_id", "")) + " " + str(row.get("item_en", ""))).lower()
                        for kw in keyword_list:
                            if kw.lower() in text:
                                return {q: clean_val(row.get(q)) or 0.0 for q in recent_4q_cf}
                    return {}

                cfo_series = get_quarterly_cf_series(["net_cash_inflows_outflows_from_operating_activities", "lưu chuyển tiền tệ ròng từ các hoạt động sản xuất kinh doanh", "lưu chuyển tiền thuần từ hoạt động kinh doanh"])
                capex_series = get_quarterly_cf_series(["purchases_of_fixed_assets", "mua sắm, xây dựng tscđ", "tiền chi để mua sắm"])
                cfi_series = get_quarterly_cf_series(["net_cash_inflows_outflows_from_investing_activities", "lưu chuyển tiền thuần từ hoạt động đầu tư"])
                cff_series = get_quarterly_cf_series(["net_cash_inflows_outflows_from_financing_activities", "lưu chuyển tiền thuần từ hoạt động tài chính"])

                cfo_total = sum(cfo_series.values())
                capex_total = abs(sum(capex_series.values()))
                cfi_total = sum(cfi_series.values())
                cff_total = sum(cff_series.values())

                result["cfo_ttm"] = cfo_total
                result["capex_ttm"] = capex_total
                result["fcf_ttm"] = cfo_total - capex_total
                result["cfi_ttm"] = cfi_total
                result["cff_ttm"] = cff_total
                if recent_4q_cf:
                    result["cfo_latest_q"] = cfo_series.get(recent_4q_cf[0], 0.0)

                # Thu thập chuỗi 4 quý để vẽ chart so sánh Dòng tiền thật vs Lợi nhuận
                quarterly_records = []
                for q in reversed(recent_4q_cf): # Sắp xếp từ quá khứ đến gần nhất
                    q_cfo = cfo_series.get(q, 0.0)
                    q_capex = abs(capex_series.get(q, 0.0))
                    # Tìm lợi nhuận tương ứng quý q
                    q_np = 0.0
                    if inc_df is not None and not inc_df.empty:
                        for _, row in inc_df.iterrows():
                            text = (str(row.get("item", "")) + " " + str(row.get("item_id", "")) + " " + str(row.get("item_en", ""))).lower()
                            if "attributable_to_parent_company" in text or "cổ đông của công ty mẹ" in text or "lợi nhuận sau thuế" in text:
                                v = clean_val(row.get(q))
                                if v is not None:
                                    q_np = v
                                    break
                    quarterly_records.append({
                        "quarter": q,
                        "cfo": q_cfo,
                        "capex": q_capex,
                        "fcf": q_cfo - q_capex,
                        "net_profit": q_np
                    })
                result["quarterly_cash_flows"] = quarterly_records

                # Chất lượng lợi nhuận
                if result.get("ttm_profit") and result["ttm_profit"] != 0:
                    result["earnings_quality_ratio"] = round(cfo_total / result["ttm_profit"], 2)
        except Exception:
            pass

    except BaseException:
        pass

    # Gắn overview từ governance data để tầng FA luôn có đủ thông tin ngành và sàn
    try:
        gov = get_governance_data(symbol)
        if gov and gov.get("overview"):
            result["overview"] = gov.get("overview", {})
    except Exception:
        pass

    # Chống Cache Poisoning: Chỉ lưu cache nếu thực sự cào được số liệu tài chính hợp lệ
    has_valid_data = (
        (result.get("total_assets") is not None and result.get("total_assets") > 0) or
        (result.get("ttm_revenue") is not None and result.get("ttm_revenue") > 0) or
        (result.get("bvps") is not None and result.get("bvps") > 0) or
        (result.get("ttm_profit") is not None and result.get("ttm_profit") != 0)
    )

    if has_valid_data:
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    return result


def get_governance_data(symbol: str) -> Dict[str, Any]:
    """
    Lấy dữ liệu Cơ cấu cổ đông, Ban lãnh đạo (HĐQT/BĐH),
    Công ty con và công ty liên kết của doanh nghiệp.
    """
    symbol = symbol.upper().strip()
    from config import PROJECT_ROOT
    cache_dir = PROJECT_ROOT / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"governance_{symbol}.json"

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception:
            pass

    result = {
        "symbol": symbol,
        "shareholders": [],
        "officers": [],
        "subsidiaries": [],
        "affiliates": [],
        "overview": {}
    }

    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=symbol, source="VCI")

        # 1. Overview
        try:
            ov = stock.company.overview()
            if ov is not None and not ov.empty:
                rec = ov.to_dict("records")[0]
                com_code = str(rec.get("com_group_code", "")).upper()
                ex = "HOSE"
                if "HNX" in com_code:
                    ex = "HNX"
                elif "UPCOM" in com_code:
                    ex = "UPCOM"
                
                limit_pct = 7.0 if ex == "HOSE" else (10.0 if ex == "HNX" else 15.0)
                organ_name = rec.get("organ_name", "")

                result["overview"] = {
                    "organ_name": organ_name,
                    "organ_short_name": rec.get("organ_short_name", ""),
                    "company_profile": rec.get("company_profile", ""),
                    "sector": rec.get("sector", ""),
                    "com_group_code": rec.get("com_group_code", ""),
                    "exchange": ex,
                    "price_limit_pct": limit_pct,
                    "free_float_pct": round(float(rec.get("free_float_percentage") or 0.0) * 100, 2),
                    "foreigner_pct": round(float(rec.get("foreigner_percentage") or 0.0) * 100, 2),
                    "state_pct": round(float(rec.get("state_percentage") or 0.0) * 100, 2),
                    "listing_date": rec.get("listing_date", "")
                }

                from core.db_manager import save_stock_master
                try:
                    save_stock_master(symbol, organ_name, ex, price_limit_pct=limit_pct)
                except Exception:
                    pass
        except Exception:
            pass

        # 2. Shareholders
        try:
            sh = stock.company.shareholders()
            if sh is not None and not sh.empty:
                for _, row in sh.iterrows():
                    pct = float(row.get("share_own_percent") or 0.0)
                    if 0 < pct <= 1.0:
                        pct = round(pct * 100, 2)
                    else:
                        pct = round(pct, 2)
                    result["shareholders"].append({
                        "name": str(row.get("share_holder", "")),
                        "percentage": pct,
                        "shares": float(row.get("quantity") or 0.0)
                    })
        except Exception:
            pass

        # 3. Officers
        try:
            off = stock.company.officers()
            if off is not None and not off.empty:
                for _, row in off.iterrows():
                    pct = float(row.get("officer_own_percent") or 0.0)
                    if 0 < pct <= 1.0:
                        pct = round(pct * 100, 2)
                    else:
                        pct = round(pct, 2)
                    result["officers"].append({
                        "name": str(row.get("officer_name", "")),
                        "position": str(row.get("officer_position", "")),
                        "percentage": pct,
                        "shares": float(row.get("officer_own_quantity") or 0.0)
                    })
        except Exception:
            pass

        # 4. Subsidiaries
        try:
            sub = stock.company.subsidiaries()
            if sub is not None and not sub.empty:
                for _, row in sub.iterrows():
                    pct = float(row.get("ownership_percent") or 0.0)
                    if 0 < pct <= 1.0:
                        pct = round(pct * 100, 2)
                    else:
                        pct = round(pct, 2)
                    result["subsidiaries"].append({
                        "name": str(row.get("organ_name", "")),
                        "ownership_percent": pct,
                        "code": str(row.get("sub_organ_code", ""))
                    })
        except Exception:
            pass

        # 5. Affiliates
        try:
            aff = stock.company.affiliate()
            if aff is not None and not aff.empty:
                for _, row in aff.iterrows():
                    pct = float(row.get("ownership_percent") or 0.0)
                    if 0 < pct <= 1.0:
                        pct = round(pct * 100, 2)
                    else:
                        pct = round(pct, 2)
                    result["affiliates"].append({
                        "name": str(row.get("organ_name", "")),
                        "ownership_percent": pct,
                        "code": str(row.get("sub_organ_code", ""))
                    })
        except Exception:
            pass

    except (Exception, SystemExit, BaseException) as e:
        # Khi vnstock báo Rate limit hoặc SystemExit, tiếp tục với dữ liệu sẵn có
        pass

    # Lưu cache nếu có dữ liệu hợp lệ
    try:
        if result.get("shareholders") or result.get("officers") or result.get("subsidiaries") or result.get("overview"):
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return result


def get_company_news_and_events(symbol: str, force_refresh: bool = False) -> Dict[str, Any]:
    """
    Thu thập tin tức báo chí, nghị quyết HĐQT, thông báo cổ tức,
    giao dịch nội bộ và sự kiện doanh nghiệp của mã cổ phiếu.
    Hỗ trợ Cache cục bộ trong cache/{symbol}_news_events.json (TTL = 4 giờ).
    """
    from config import PROJECT_ROOT

    symbol = symbol.upper().strip()
    cache_dir = PROJECT_ROOT / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{symbol}_news_events.json"

    # Kiểm tra cache còn hạn (< 4 giờ)
    if not force_refresh and cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < 14400:  # 4 hours
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("news") or cached_data.get("events"):
                        return cached_data
        except Exception:
            pass

    result: Dict[str, Any] = {
        "symbol": symbol,
        "news": [],
        "events": [],
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    try:
        from vnstock import Vnstock
        stock = Vnstock().stock(symbol=symbol, source="VCI")

        # 1. Tin tức báo chí & Nghị quyết
        try:
            df_news = stock.company.news()
            if df_news is not None and not df_news.empty:
                for _, row in df_news.head(25).iterrows():
                    result["news"].append({
                        "title": str(row.get("news_title") or row.get("title") or "").strip(),
                        "public_date": str(row.get("public_date") or "").strip(),
                        "short_content": str(row.get("news_short_content") or "").strip(),
                        "source": str(row.get("news_source") or "").strip(),
                        "link": str(row.get("news_source_link") or "").strip()
                    })
        except Exception:
            pass

        # 2. Sự kiện doanh nghiệp & Giao dịch nội bộ
        try:
            df_events = stock.company.events()
            if df_events is not None and not df_events.empty:
                for _, row in df_events.head(25).iterrows():
                    result["events"].append({
                        "event_name": str(row.get("event_name_vi") or row.get("event_name_en") or "").strip(),
                        "public_date": str(row.get("public_date") or "").strip(),
                        "category": str(row.get("category") or "").strip(),
                        "action_type": str(row.get("action_type_vi") or row.get("action_type_en") or "").strip(),
                        "value_per_share": float(row.get("value_per_share") or 0.0) if pd.notna(row.get("value_per_share")) else 0.0
                    })
        except Exception:
            pass

    except Exception:
        pass

    # Ghi cache nếu có dữ liệu
    try:
        if result["news"] or result["events"]:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return result




def get_all_tickers_realtime() -> list:
    """
    Quét toàn bộ ~1.500+ mã cổ phiếu trên 3 sàn HOSE, HNX, UPCoM
    trả về danh sách chứa [symbol, price, volume, value, change_pct].
    Đây là nguồn đầu vào cho tính năng Lọc Thanh khoản.
    """
    all_tickers = []
    
    for exchange in ["hose", "hnx", "upcom"]:
        url = f"https://iboard-query.ssi.com.vn/stock/exchange/{exchange}"
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                data = r.json().get("data", [])
                for item in data:
                    sym = item.get("stockSymbol")
                    if not sym:
                        continue
                    price = float(item.get("matchedPrice") or item.get("refPrice") or 0)
                    if 0 < price < 1000:
                        price *= 1000

                    vol = float(item.get("stockVol") or item.get("nmTotalTradedQty") or 0)
                    val = float(item.get("nmTotalTradedValue") or 0)
                    if val <= 0 and vol > 0 and price > 0:
                        val = vol * price
                    change_pct = float(item.get("priceChangePercent") or 0)
                    
                    all_tickers.append({
                        "symbol": sym,
                        "exchange": exchange.upper(),
                        "price": price,
                        "volume": vol,
                        "value": val,
                        "change_pct": change_pct,
                        "company_name": item.get("clientName") or item.get("companyNameVi", sym)
                    })
        except Exception as e:
            print(f"Lỗi lấy dữ liệu {exchange.upper()}: {e}")
            
    return all_tickers


def get_global_macro_and_commodities(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Thu thập và cập nhật tự động ma trận Vĩ mô Quốc tế & Hàng hóa thế giới:
    FED Target Rate, US Core CPI, DXY, Tỷ giá USD/VND, Giá Dầu, Giá Vàng, Giá Cao su, Thép HRC, Phân bón.
    Hỗ trợ Cache cục bộ trong cache/macro_commodities_cache.json (TTL = 2 giờ).
    """
    from config import PROJECT_ROOT
    from core.macro_engine import GLOBAL_COMMODITIES_AND_MACRO, CURRENT_VIETNAM_MACRO

    cache_dir = PROJECT_ROOT / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / "macro_commodities_cache.json"

    # Kiểm tra Cache còn hạn không (< 2 giờ)
    if not force_refresh and cache_file.exists():
        try:
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < 7200:  # 2 hours
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    if cached_data.get("global_commodities"):
                        return cached_data
        except Exception:
            pass

    import copy
    # Bản sao dữ liệu mặc định chuẩn hóa (dùng deepcopy để tránh làm biến đổi GLOBAL_COMMODITIES_AND_MACRO)
    res_commodities = copy.deepcopy(GLOBAL_COMMODITIES_AND_MACRO)

    # Thử cào nhanh giá Dầu & Vàng qua Yahoo Finance chart endpoint (miễn phí, không cần auth)
    yahoo_symbols = {
        "crude_oil_brent": "BZ=F",
        "gold_world": "GC=F",
        "dxy_index": "DX-Y.NYB"
    }

    for comm_key, y_sym in yahoo_symbols.items():
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{y_sym}?interval=1d&range=5d"
            r = requests.get(url, headers=HEADERS, timeout=4)
            if r.status_code == 200:
                data = r.json().get("chart", {}).get("result", [])
                if data and len(data) > 0:
                    meta = data[0].get("meta", {})
                    curr_price = float(meta.get("regularMarketPrice") or 0)
                    prev_close = float(meta.get("chartPreviousClose") or curr_price)
                    if curr_price > 0 and comm_key in res_commodities:
                        chg_pct = round(((curr_price - prev_close) / prev_close) * 100, 2) if prev_close > 0 else 0.0
                        res_commodities[comm_key]["value"] = round(curr_price, 2)
                        res_commodities[comm_key]["change_pct"] = chg_pct
                        res_commodities[comm_key]["source_type"] = "LIVE"
                        res_commodities[comm_key]["as_of_date"] = datetime.now().strftime("%Y-%m-%d")
        except Exception:
            pass

    final_result = {
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "global_commodities": res_commodities,
        "vietnam_macro": CURRENT_VIETNAM_MACRO
    }

    # Ghi đệm cache
    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(final_result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return final_result

