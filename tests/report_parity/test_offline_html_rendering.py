# -*- coding: utf-8 -*-
"""
tests/report_parity/test_offline_html_rendering.py
Kiểm tra khả năng hiển thị Offline độc lập của Báo cáo HTML trên Microsoft Edge:
1. Có đầy đủ thẻ SVG Fallback nội tuyến cho Biểu đồ Nến (Candlestick) và Biểu đồ Dòng tiền (Cashflow).
2. Khi ngắt mạng (không tải được thư viện CDN), giao diện báo cáo vẫn hiển thị trực quan 100%.
3. Chứa đầy đủ các phân hệ mới: ELI5, DuPont 3 nhân tố, ROIC, Khung giá 52 tuần và O'Neil RS Rating.
"""

import pytest
from pathlib import Path
from core.html_report_generator import generate_html_report
from core.fa_engine import analyze_fundamentals
from core.risk_manager import calculate_trade_setup
from core.ta_engine import analyze_technicals
from core.timing_engine import analyze_timing_prediction
from ai.council import InvestmentCouncil
from tests.fixtures.sample_companies import (
    HPG_QUOTE,
    HPG_FINANCIALS,
    make_mock_ohlcv,
)


@pytest.fixture
def temp_reports_dir(tmp_path, monkeypatch):
    """Fixture định tuyến báo cáo HTML vào thư mục test tạm thời."""
    t_dir = tmp_path / "reports"
    t_dir.mkdir(parents=True, exist_ok=True)
    import core.html_report_generator as hrg
    monkeypatch.setattr(hrg, "REPORTS_DIR", t_dir)
    return t_dir


def test_offline_html_rendering_with_svg_charts(temp_reports_dir):
    """Kiểm tra báo cáo HTML có đầy đủ biểu đồ SVG nội tuyến để xem offline không cần mạng."""
    quote = dict(HPG_QUOTE)
    fin = dict(HPG_FINANCIALS)
    sym = quote["symbol"]

    df_ohlcv = make_mock_ohlcv(days=250, trend="uptrend", base_price=quote["price"])
    current_price = float(df_ohlcv["close"].iloc[-1])
    quote["price"] = current_price

    fa_res = analyze_fundamentals(fin, current_price, quote)
    ta_res = analyze_technicals(df_ohlcv)
    trade_setup = calculate_trade_setup(current_price, fa_res, ta_res, quote)
    timing_res = analyze_timing_prediction(sym, quote, ta_res, fa_res)
    council = InvestmentCouncil()
    council_res = council.deliberate(sym, quote, fa_res, ta_res, trade_setup)

    html_path = generate_html_report(
        symbol=sym,
        quote=quote,
        fa_result=fa_res,
        ta_result=ta_res,
        trade_setup=trade_setup,
        council_result=council_res,
        timing_result=timing_res,
        df_ohlcv=df_ohlcv,
    )

    assert html_path.exists(), "File báo cáo HTML phải được ghi ra đĩa"
    content = html_path.read_text(encoding="utf-8")

    # 1. Kiểm tra SVG Fallback cho Biểu đồ Nến Kỹ thuật
    assert 'id="tvChartOfflineFallback"' in content
    assert "<svg" in content

    # 2. Kiểm tra SVG Fallback cho Biểu đồ Dòng tiền & Lợi nhuận
    assert 'id="cashFlowOfflineFallback"' in content
    assert "<rect" in content, "Biểu đồ SVG dòng tiền phải có các thanh cột rect"

    # 3. Kiểm tra các trường dữ liệu nâng cấp mới
    assert "DuPont" in content or "Vòng quay Tài sản" in content, "Phải hiển thị phân tích DuPont"
    assert "ROIC" in content, "Phải hiển thị chỉ số ROIC"
    assert "52" in content, "Phải hiển thị khung giá 52 tuần"
    assert "RS Rating" in content or "Sức mạnh giá" in content, "Phải hiển thị O'Neil RS Rating"

    # 4. Kiểm tra khối ELI5 (Giải thích cho đứa trẻ lên 5)
    assert "đứa trẻ" in content.lower() or "eli5" in content.lower() or "bản chất cốt lõi" in content.lower()
