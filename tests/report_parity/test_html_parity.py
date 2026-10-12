# -*- coding: utf-8 -*-
"""
tests/report_parity/test_html_parity.py
Kiểm tra tính nhất quán 100% giữa Python Engine / AnalysisResult và Báo cáo HTML sinh ra.
Quy tắc:
1. Số liệu hiển thị trên HTML phải xuất phát trực tiếp từ kết quả tính toán động của Engine.
2. Không chấp nhận số liệu mặc định (P/E=15.0, StopLoss=7% cứng khi không có setup).
3. Cổ phiếu bị loại bỏ (Disqualified setup) không được hiển thị điểm mua/cắt lỗ giả.
4. Báo cáo HTML phải chứa SVG fallback đầy đủ cho môi trường offline trên Microsoft Edge.
"""

import pytest
from pathlib import Path
from core.html_report_generator import generate_html_report
from core.fa_engine import analyze_fundamentals
from core.risk_manager import calculate_trade_setup
from core.ta_engine import analyze_technicals
from ai.council import InvestmentCouncil
from tests.fixtures.sample_companies import (
    HPG_QUOTE,
    HPG_FINANCIALS,
    VCB_QUOTE,
    VCB_FINANCIALS,
    NEGATIVE_EPS_QUOTE,
    NEGATIVE_EPS_FINANCIALS,
    make_mock_ohlcv,
)


@pytest.fixture
def clean_reports_dir(tmp_path, monkeypatch):
    """Fixture trỏ REPORTS_DIR sang thư mục tạm để không làm bẩn reports/ thực tế."""
    test_reports = tmp_path / "reports"
    test_reports.mkdir(parents=True, exist_ok=True)
    import core.html_report_generator as hrg
    monkeypatch.setattr(hrg, "REPORTS_DIR", test_reports)
    return test_reports


class TestHtmlParityHealthySetup:
    """Kiểm tra báo cáo HTML cho cổ phiếu đủ điều kiện (HPG)."""

    def test_hpg_report_parity_and_offline_svg(self, clean_reports_dir):
        quote = dict(HPG_QUOTE)
        fin = dict(HPG_FINANCIALS)
        sym = quote["symbol"]

        df_ohlcv = make_mock_ohlcv(days=250, trend="uptrend", base_price=quote["price"])
        quote["price"] = float(df_ohlcv["close"].iloc[-1])
        current_price = quote["price"]

        fa_res = analyze_fundamentals(fin, current_price, quote)
        ta_res = analyze_technicals(df_ohlcv)
        trade_setup = calculate_trade_setup(current_price, fa_res, ta_res, quote)
        council = InvestmentCouncil()
        council_res = council.deliberate(sym, quote, fa_res, ta_res, trade_setup)

        html_path = generate_html_report(
            symbol=sym,
            quote=quote,
            fa_result=fa_res,
            ta_result=ta_res,
            trade_setup=trade_setup,
            council_result=council_res,
            df_ohlcv=df_ohlcv,
        )

        assert html_path.exists(), "File báo cáo HTML phải được tạo thành công"
        content = html_path.read_text(encoding="utf-8")
        assert len(content) > 15000, "Báo cáo HTML phải đầy đủ nội dung"

        # 1. Kiểm tra SVG Fallbacks cho Edge Offline
        assert '<div id="cashFlowOfflineFallback"' in content
        assert '<div id="tvChartOfflineFallback"' in content
        assert "<svg" in content, "Phải chứa thẻ SVG nhúng trực tiếp phục vụ xem offline"

        # 2. Kiểm tra tính nhất quán của Trade Setup
        assert trade_setup["has_valid_setup"] is True
        sl_val = trade_setup["stop_loss"]
        assert sl_val > 0
        sl_str = f"{sl_val:,.0f} đ"
        assert sl_str in content, f"Mức cắt lỗ {sl_str} từ Engine phải xuất hiện chính xác trên HTML"

        tp1_val = trade_setup["take_profit_1"]
        tp1_str = f"{tp1_val:,.0f} đ"
        assert tp1_str in content, f"Mục tiêu chốt lời {tp1_str} phải xuất hiện trên HTML"

        # 3. Kiểm tra P/E và P/B động từ fa_res
        pe_val = fa_res["ratios"]["pe"]
        assert pe_val is not None
        assert f"{pe_val:.1f}" in content, f"P/E {pe_val:.1f} phải xuất hiện trên báo cáo"

        # 4. Kiểm tra Hội đồng AI không trích dẫn mạo danh
        assert "Buffett sẽ mua" not in content
        assert "Tán thành" in content or "Theo dõi" in content or "Phản đối" in content or "TÁN THÀNH" in content


class TestHtmlParityDisqualifiedSetup:
    """Kiểm tra báo cáo HTML cho cổ phiếu bị loại bỏ / không có điểm mua an toàn."""

    def test_disqualified_stock_no_fake_setup(self, clean_reports_dir):
        quote = dict(NEGATIVE_EPS_QUOTE)
        fin = dict(NEGATIVE_EPS_FINANCIALS)
        sym = quote["symbol"]

        df_ohlcv = make_mock_ohlcv(days=250, trend="downtrend", base_price=quote["price"])
        quote["price"] = float(df_ohlcv["close"].iloc[-1])
        current_price = quote["price"]

        fa_res = analyze_fundamentals(fin, current_price, quote)
        ta_res = analyze_technicals(df_ohlcv)
        trade_setup = calculate_trade_setup(current_price, fa_res, ta_res, quote)
        council = InvestmentCouncil()
        council_res = council.deliberate(sym, quote, fa_res, ta_res, trade_setup)

        html_path = generate_html_report(
            symbol=sym,
            quote=quote,
            fa_result=fa_res,
            ta_result=ta_res,
            trade_setup=trade_setup,
            council_result=council_res,
            df_ohlcv=df_ohlcv,
        )

        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")

        # 1. Setup Validation Gate
        assert trade_setup["has_valid_setup"] is False
        assert trade_setup["max_position_size_pct"] == 0.0

        # 2. Không được hiển thị điểm mua/cắt lỗ lừa dối
        assert "KHÔNG CÓ ĐIỂM MUA HỢP LỆ" in content
        assert "0% (Đứng ngoài quan sát)" in content
        assert "KHÔNG CÓ VÙNG MUA (BẢO TOÀN VỐN)" in content
        assert "N/A (Chưa mở vị thế)" in content

        # 3. Kiểm tra P/E âm không bị gán số dương mặc định 15.0
        assert fa_res["ratios"]["pe"] is None
        assert fa_res["ratios"]["pe_status"] == "NEGATIVE_EARNINGS"


class TestHtmlParityBankNotApplicable:
    """Kiểm tra báo cáo HTML cho ngân hàng (VCB) — Altman Z exempt."""

    def test_bank_altman_z_exempt_in_html(self, clean_reports_dir):
        quote = dict(VCB_QUOTE)
        fin = dict(VCB_FINANCIALS)
        sym = quote["symbol"]

        df_ohlcv = make_mock_ohlcv(days=250, trend="uptrend", base_price=quote["price"])
        quote["price"] = float(df_ohlcv["close"].iloc[-1])
        current_price = quote["price"]

        fa_res = analyze_fundamentals(fin, current_price, quote)
        ta_res = analyze_technicals(df_ohlcv)
        trade_setup = calculate_trade_setup(current_price, fa_res, ta_res, quote)
        council = InvestmentCouncil()
        council_res = council.deliberate(sym, quote, fa_res, ta_res, trade_setup)

        assert fa_res["cash_flow"]["z_status"] == "NOT_APPLICABLE"

        html_path = generate_html_report(
            symbol=sym,
            quote=quote,
            fa_result=fa_res,
            ta_result=ta_res,
            trade_setup=trade_setup,
            council_result=council_res,
            df_ohlcv=df_ohlcv,
        )

        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")
        assert "NOT_APPLICABLE" in content or "N/A" in content or "Ngân hàng" in content
