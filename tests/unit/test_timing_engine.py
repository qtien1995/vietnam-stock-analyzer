# -*- coding: utf-8 -*-
"""
tests/unit/test_timing_engine.py
Kiểm tra Module Động cơ Phân tích Thời điểm Kỹ thuật (Timing & Setup Engine):
1. Setup quality score nằm trong miền giới hạn chuẩn [0, 100].
2. Điểm kích hoạt Pivot và ngưỡng gãy sóng hợp lý so với thị giá.
3. Ước tính áp lực cung/cầu (Proxy) bảo toàn tổng tỷ lệ 100%.
4. Lịch xúc tác sự kiện (Catalyst Calendar) trả về đủ trường và ngày còn lại không âm.
"""

import pytest
from datetime import datetime
from core.timing_engine import analyze_timing_prediction, get_upcoming_catalysts
from tests.fixtures.sample_companies import HPG_QUOTE, make_mock_ohlcv
from core.ta_engine import analyze_technicals
from core.fa_engine import analyze_fundamentals
from tests.fixtures.sample_companies import HPG_FINANCIALS


def test_timing_metrics_and_transparency():
    """Kiểm tra tính minh bạch và miền giá trị của Timing Engine."""
    quote = dict(HPG_QUOTE)
    df_ohlcv = make_mock_ohlcv(days=250, trend="uptrend", base_price=quote["price"])
    current_price = float(df_ohlcv["close"].iloc[-1])
    quote["price"] = current_price
    quote["change_pct"] = 1.5
    quote["volume"] = 15_000_000
    quote["foreign_net_vol"] = 500_000

    ta_result = analyze_technicals(df_ohlcv)
    fa_result = analyze_fundamentals(dict(HPG_FINANCIALS), current_price, quote)

    timing = analyze_timing_prediction("HPG", quote, ta_result, fa_result)

    # 1. Setup Quality Score trong khoảng [0, 100]
    score = timing.get("setup_quality_score")
    assert score is not None, "setup_quality_score không được None"
    assert 0 <= score <= 100, f"setup_quality_score ({score}) phải nằm trong [0, 100]"

    # 2. Điểm kích hoạt Pivot > 0 và Breakdown price > 0
    pivot = timing.get("pivot_price")
    breakdown = timing.get("breakdown_price")
    assert pivot is not None and pivot > 0, "pivot_price phải là số dương"
    assert breakdown is not None and breakdown > 0, "breakdown_price phải là số dương"
    assert breakdown < current_price or breakdown < pivot, "Ngưỡng gãy sóng phải thấp hơn pivot"

    # 3. Tỷ lệ bên mua / bên bán chủ động cộng lại bằng 100%
    buy_pct = timing.get("active_buy_pct", 50.0)
    sell_pct = timing.get("active_sell_pct", 50.0)
    assert abs((buy_pct + sell_pct) - 100.0) < 0.01, "Tổng % mua và % bán chủ động phải bằng 100%"

    # 4. Kiểm tra không có cam kết chắc chắn thắng hoặc bịa đặt kỳ hạn T+1..T+3 cố định
    summary_text = str(timing)
    assert "chắc chắn 100%" not in summary_text
    assert "bảo đảm sinh lời" not in summary_text


def test_upcoming_catalysts_structure():
    """Kiểm tra cấu trúc và tính toán thời gian của Lịch Xúc tác Sự kiện Trọng yếu."""
    catalysts = get_upcoming_catalysts("HPG", current_dt=datetime(2025, 4, 15))
    assert isinstance(catalysts, list)
    assert len(catalysts) >= 2, "Phải có ít nhất 2 sự kiện xúc tác (Đáo hạn Phái sinh, BCTC hoặc ETF)"

    for cat in catalysts:
        assert "event_name" in cat
        assert "date_str" in cat
        assert "days_left" in cat
        assert "impact_level" in cat
        assert "trading_hint" in cat
        assert cat["days_left"] >= 0, f"Số ngày còn lại ({cat['days_left']}) của sự kiện không được âm"
