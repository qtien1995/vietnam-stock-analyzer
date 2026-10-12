import pytest
import json
from core.models import AnalysisResult, MarketQuote, DataQualityStatus
from core.fa_engine import analyze_fundamentals
from core.ta_engine import analyze_technicals
from core.risk_manager import calculate_trade_setup
from core.timing_engine import analyze_timing_prediction
from ai.council import InvestmentCouncil
from tests.fixtures.sample_companies import HPG_QUOTE, HPG_FINANCIALS, make_mock_ohlcv


def test_canonical_analysis_result_serialization():
    """Kiểm tra tạo lập canonical AnalysisResult, serialize sang JSON và chuyển đổi backward-compatible."""
    symbol = "HPG"
    df_ohlcv = make_mock_ohlcv(days=250, trend="uptrend", base_price=28000.0)
    price = round(float(df_ohlcv["close"].iloc[-1]), 0)
    quote = dict(HPG_QUOTE)
    quote["price"] = price

    ta_result = analyze_technicals(df_ohlcv)
    fa_result = analyze_fundamentals(HPG_FINANCIALS, price, quote)
    trade_setup = calculate_trade_setup(price, fa_result, ta_result, quote)
    timing_result = analyze_timing_prediction(symbol, quote, ta_result, fa_result)

    council = InvestmentCouncil()
    council_result = council.deliberate(symbol, quote, fa_result, ta_result, trade_setup)

    analysis_result = AnalysisResult.from_components(
        symbol=symbol,
        quote=quote,
        fa_result=fa_result,
        ta_result=ta_result,
        trade_setup=trade_setup,
        timing_result=timing_result,
        council_result=council_result,
        html_report_path="reports/HPG_20261012.html"
    )

    # 1. Kiểm tra validation và kiểu dữ liệu Pydantic
    assert analysis_result.symbol == "HPG"
    assert analysis_result.quote.price == price
    assert analysis_result.fa.f_score.score >= 4
    assert analysis_result.ta.ta_total_score > 0
    assert analysis_result.trade_setup.has_valid_setup is True
    assert len(analysis_result.council.members) == 6

    # 2. Serialize sang JSON
    json_str = analysis_result.model_dump_json()
    assert json_str is not None
    data_dict = json.loads(json_str)
    assert data_dict["symbol"] == "HPG"
    assert "schema_version" in data_dict

    # 3. Kiểm tra backward compatibility với legacy dictionary
    legacy = analysis_result.to_legacy_dict()
    assert legacy["symbol"] == "HPG"
    assert "fa_result" in legacy
    assert "ta_result" in legacy
    assert "trade_setup" in legacy
    assert "council_result" in legacy
    assert legacy["current_price"] == price
