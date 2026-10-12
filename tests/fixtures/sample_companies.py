"""
Frozen Fixtures for Vietnamese Stocks Across Different Sectors and Edge Cases.
Independent of live APIs, ensuring deterministic, reproducible tests.
"""

from typing import Dict, Any
import pandas as pd
import numpy as np


# --------------------------------------------------------------------------
# 1. Manufacturing Champion: HPG (Hòa Phát) - Healthy Manufacturing
# --------------------------------------------------------------------------
HPG_QUOTE: Dict[str, Any] = {
    "symbol": "HPG",
    "company_name": "CTCP Tập đoàn Hòa Phát",
    "exchange": "HOSE",
    "price_limit_pct": 7.0,
    "source": "SSI_REALTIME",
    "price": 28500.0,
    "ref_price": 28000.0,
    "change": 500.0,
    "change_pct": 1.79,
    "high": 28800.0,
    "low": 28100.0,
    "open": 28200.0,
    "volume": 25000000.0,
    "value": 712500000000.0,
    "foreign_net_vol": 1500000.0,
    "trading_date": "2026-10-10"
}

HPG_FINANCIALS: Dict[str, Any] = {
    "symbol": "HPG",
    "issue_share": 5814785700.0,
    "market_cap": 165721392450000.0,
    "total_assets": 195000000000000.0,
    "current_assets": 95000000000000.0,
    "cash": 32000000000000.0,
    "receivables": 12000000000000.0,
    "inventories": 41000000000000.0,
    "tangible_fixed_assets": 78000000000000.0,
    "total_debt": 65000000000000.0,
    "short_term_debt": 52000000000000.0,
    "long_term_debt": 13000000000000.0,
    "owners_equity": 105000000000000.0,
    "retained_earnings": 38000000000000.0,
    "short_term_liabilities": 75000000000000.0,
    "working_capital": 20000000000000.0,
    "ttm_revenue": 140000000000000.0,
    "ttm_profit": 12500000000000.0,
    "ebit_ttm": 16000000000000.0,
    "pe": 13.25,
    "pb": 1.58,
    "roe": 11.9,
    "roa": 6.4,
    "roic": 8.5,
    "gross_margin": 13.5,
    "net_margin": 8.9,
    "debt_to_equity": 0.62,
    "liabilities_to_equity": 0.86,
    "revenue_growth": 18.5,
    "profit_growth": 35.0,
    "eps": 2150.0,
    "bvps": 18057.0,
    "tbvps": 18057.0,
    "ncavps": 3439.0,
    "latest_quarter": "2026-Q3",
    "cfo_ttm": 18000000000000.0,
    "capex_ttm": 12000000000000.0,
    "fcf_ttm": 6000000000000.0,
    "cfi_ttm": -14000000000000.0,
    "cff_ttm": -2000000000000.0,
    "quarterly_cash_flows": [
        {"quarter": "2025-Q4", "cfo": 4000000000000.0, "capex": 3000000000000.0, "fcf": 1000000000000.0, "net_profit": 2800000000000.0},
        {"quarter": "2026-Q1", "cfo": 4500000000000.0, "capex": 3000000000000.0, "fcf": 1500000000000.0, "net_profit": 3000000000000.0},
        {"quarter": "2026-Q2", "cfo": 4800000000000.0, "capex": 3000000000000.0, "fcf": 1800000000000.0, "net_profit": 3200000000000.0},
        {"quarter": "2026-Q3", "cfo": 4700000000000.0, "capex": 3000000000000.0, "fcf": 1700000000000.0, "net_profit": 3500000000000.0}
    ],
    "earnings_quality_ratio": 1.44
}


# --------------------------------------------------------------------------
# 2. Commercial Banking Leader: VCB (Vietcombank) - Bank Model
# --------------------------------------------------------------------------
VCB_QUOTE: Dict[str, Any] = {
    "symbol": "VCB",
    "company_name": "Ngân hàng TMCP Ngoại thương Việt Nam",
    "exchange": "HOSE",
    "price_limit_pct": 7.0,
    "source": "SSI_REALTIME",
    "price": 92000.0,
    "ref_price": 91500.0,
    "change": 500.0,
    "change_pct": 0.55,
    "high": 92500.0,
    "low": 91200.0,
    "open": 91500.0,
    "volume": 2800000.0,
    "value": 257600000000.0,
    "foreign_net_vol": 450000.0,
    "trading_date": "2026-10-10"
}

VCB_FINANCIALS: Dict[str, Any] = {
    "symbol": "VCB",
    "issue_share": 5589091400.0,
    "market_cap": 514196408800000.0,
    "total_assets": 1900000000000000.0,
    "current_assets": 0.0,  # Banks do not report current assets
    "cash": 45000000000000.0,
    "receivables": 0.0,
    "inventories": 0.0,
    "tangible_fixed_assets": 8500000000000.0,
    "total_debt": 0.0,      # Deposits and interbank funding, not corporate non-fin debt
    "owners_equity": 175000000000000.0,
    "retained_earnings": 72000000000000.0,
    "short_term_liabilities": 0.0,
    "working_capital": 0.0,
    "ttm_revenue": 68000000000000.0,  # Net interest income + fee income
    "ttm_profit": 35000000000000.0,
    "ebit_ttm": 43500000000000.0,
    "pe": 14.69,
    "pb": 2.94,
    "roe": 20.0,
    "roa": 1.84,
    "roic": 20.0,
    "gross_margin": None,   # Undefined for Banks
    "net_margin": 51.5,
    "debt_to_equity": None, # Undefined for Banks
    "revenue_growth": 9.5,
    "profit_growth": 11.2,
    "eps": 6262.0,
    "bvps": 31310.0,
    "latest_quarter": "2026-Q3",
    "cfo_ttm": 42000000000000.0,
    "capex_ttm": 3500000000000.0,
    "fcf_ttm": 38500000000000.0,
    "quarterly_cash_flows": []
}


# --------------------------------------------------------------------------
# 3. Loss-Making Company: NEGATIVE_EPS (Severe Losses)
# --------------------------------------------------------------------------
NEGATIVE_EPS_QUOTE: Dict[str, Any] = {
    "symbol": "HVN_SAMPLE",
    "company_name": "Doanh nghiệp Lỗ Nặng Demo",
    "exchange": "HOSE",
    "price_limit_pct": 7.0,
    "source": "SSI_REALTIME",
    "price": 14200.0,
    "ref_price": 14200.0,
    "change": 0.0,
    "change_pct": 0.0,
    "high": 14500.0,
    "low": 13900.0,
    "open": 14200.0,
    "volume": 1200000.0,
    "value": 17040000000.0,
    "foreign_net_vol": -250000.0,
    "trading_date": "2026-10-10"
}

NEGATIVE_EPS_FINANCIALS: Dict[str, Any] = {
    "symbol": "HVN_SAMPLE",
    "issue_share": 2214394000.0,
    "market_cap": 31444394800000.0,
    "total_assets": 60000000000000.0,
    "current_assets": 15000000000000.0,
    "cash": 3000000000000.0,
    "receivables": 6000000000000.0,
    "inventories": 3000000000000.0,
    "tangible_fixed_assets": 32000000000000.0,
    "total_debt": 38000000000000.0,
    "short_term_debt": 25000000000000.0,
    "long_term_debt": 13000000000000.0,
    "owners_equity": -8500000000000.0,  # Negative Equity!
    "retained_earnings": -18000000000000.0,
    "short_term_liabilities": 45000000000000.0,
    "working_capital": -30000000000000.0,
    "ttm_revenue": 75000000000000.0,
    "ttm_profit": -5200000000000.0,      # Negative Profit!
    "ebit_ttm": -3000000000000.0,
    "pe": None,     # Must be None, NEVER 15.0
    "pb": None,     # Must be None, NEVER 1.5
    "roe": None,    # Negative Equity + Negative Profit -> Must be None
    "roa": -8.67,
    "roic": None,
    "gross_margin": 4.5,
    "net_margin": -6.93,
    "debt_to_equity": -4.47,
    "revenue_growth": 12.0,
    "profit_growth": -25.0,
    "eps": -2348.0,
    "bvps": -3838.0,
    "latest_quarter": "2026-Q3",
    "cfo_ttm": -1500000000000.0,
    "capex_ttm": 2000000000000.0,
    "fcf_ttm": -3500000000000.0,
    "quarterly_cash_flows": []
}


# --------------------------------------------------------------------------
# 4. Incomplete / Missing Financials Ticker
# --------------------------------------------------------------------------
MISSING_DATA_FINANCIALS: Dict[str, Any] = {
    "symbol": "EMPTY_TICKER",
    "issue_share": None,
    "market_cap": None,
    "total_assets": None,
    "current_assets": None,
    "cash": None,
    "receivables": None,
    "inventories": None,
    "tangible_fixed_assets": None,
    "total_debt": None,
    "owners_equity": None,
    "working_capital": None,
    "ttm_revenue": None,
    "ttm_profit": None,
    "pe": None,
    "pb": None,
    "roe": None,
    "roa": None,
    "eps": None,
    "bvps": None,
    "cfo_ttm": None,
    "fcf_ttm": None,
    "latest_quarter": None
}


# --------------------------------------------------------------------------
# 5. Synthetic OHLCV Generator Helper
# --------------------------------------------------------------------------
def make_mock_ohlcv(days: int = 250, trend: str = "uptrend", base_price: float = 28000.0) -> pd.DataFrame:
    """Tạo chuỗi nến giả lập xác định phục vụ unit test TA và Risk Manager."""
    dates = pd.date_range(end=pd.Timestamp.now(), periods=days, freq="B")
    np.random.seed(42)
    
    if trend == "uptrend":
        drift = 0.0015
    elif trend == "downtrend":
        drift = -0.002
    else:
        drift = 0.0

    returns = np.random.normal(drift, 0.015, days)
    price_series = base_price * np.exp(np.cumsum(returns))

    df = pd.DataFrame({
        "time": dates,
        "open": price_series * (1 - 0.005),
        "high": price_series * (1 + 0.012),
        "low": price_series * (1 - 0.012),
        "close": price_series,
        "volume": np.random.uniform(5000000, 20000000, days)
    })
    return df
