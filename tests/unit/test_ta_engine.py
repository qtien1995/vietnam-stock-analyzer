import pytest
import pandas as pd
import numpy as np
from core.ta_engine import (
    calculate_indicators,
    evaluate_oneil_momentum,
    evaluate_vsa_price_action,
    detect_advanced_patterns_and_vsa,
    analyze_technicals
)
from tests.fixtures.sample_companies import make_mock_ohlcv


def test_calculate_indicators_domains():
    """Kiểm tra các chỉ báo kỹ thuật cốt lõi tính đúng miền giá trị toán học."""
    df = make_mock_ohlcv(days=250, trend="uptrend", base_price=28000.0)
    df_ind = calculate_indicators(df)

    assert "ema20" in df_ind.columns
    assert "ema50" in df_ind.columns
    assert "sma200" in df_ind.columns
    assert "rsi14" in df_ind.columns
    assert "atr14" in df_ind.columns
    assert "macd" in df_ind.columns

    # Miền giá trị RSI: [0, 100]
    valid_rsi = df_ind["rsi14"].dropna()
    assert (valid_rsi >= 0).all() and (valid_rsi <= 100).all()

    # ATR > 0
    valid_atr = df_ind["atr14"].dropna()
    assert (valid_atr > 0).all()

    # EMA20 > 0
    assert (df_ind["ema20"] > 0).all()


def test_oneil_momentum_evaluation():
    """Kiểm tra thuật toán O'Neil CANSLIM / Minervini trên nến tăng trưởng."""
    df = make_mock_ohlcv(days=250, trend="uptrend", base_price=28000.0)
    df_ind = calculate_indicators(df)
    latest = df_ind.iloc[-1]
    prev = df_ind.iloc[-2]

    oneil = evaluate_oneil_momentum(latest, prev)
    assert 0 <= oneil["score"] <= 100
    assert "is_breakout" in oneil
    assert "vol_ratio" in oneil
    assert "verdict" in oneil
    assert isinstance(oneil["reasons"], list)


def test_vsa_price_action_evaluation():
    """Kiểm tra nhận diện pha Wyckoff VSA."""
    df = make_mock_ohlcv(days=250, trend="uptrend", base_price=28000.0)
    df_ind = calculate_indicators(df)
    latest = df_ind.iloc[-1]
    prev = df_ind.iloc[-2]

    vsa = evaluate_vsa_price_action(latest, prev)
    assert 0 <= vsa["score"] <= 100
    assert "phase" in vsa
    assert "verdict" in vsa
    assert isinstance(vsa["reasons"], list)


def test_detect_advanced_patterns_and_fibonacci():
    """Kiểm tra nhận diện mẫu hình nền giá và các mốc Fibonacci Retracement."""
    df = make_mock_ohlcv(days=250, trend="uptrend", base_price=28000.0)
    df_ind = calculate_indicators(df)

    res = detect_advanced_patterns_and_vsa(df_ind)
    assert "pattern_name" in res
    assert "vsa_signal" in res
    assert res["fibo_382"] > 0
    assert res["fibo_500"] > 0
    assert res["fibo_618"] > 0
    # Thứ tự các mốc Fibo retracement từ đỉnh xuống đáy: fibo_382 >= fibo_500 >= fibo_618
    assert res["fibo_382"] >= res["fibo_500"] >= res["fibo_618"]


def test_analyze_technicals_empty_or_short_df():
    """Kiểm tra chuỗi nến rỗng hoặc quá ngắn không gây crash."""
    empty_df = pd.DataFrame()
    res_empty = analyze_technicals(empty_df)
    assert res_empty["ta_total_score"] == 50
    assert res_empty["oneil"]["verdict"] == "THIẾU DỮ LIỆU"

    short_df = make_mock_ohlcv(days=3)
    res_short = analyze_technicals(short_df)
    assert res_short["ta_total_score"] == 50
