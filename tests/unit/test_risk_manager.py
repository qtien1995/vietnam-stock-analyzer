import pytest
from core.risk_manager import calculate_trade_setup
from tests.fixtures.sample_companies import HPG_QUOTE, HPG_FINANCIALS, NEGATIVE_EPS_QUOTE, NEGATIVE_EPS_FINANCIALS


def test_valid_trade_setup_uptrend():
    """Kiểm tra tính toán trade setup hợp lệ khi có xu hướng tăng và nền tảng tốt."""
    price = 28500.0
    mock_quote = {"symbol": "HPG", "exchange": "HOSE", "price": price, "foreign_net_vol": 100000}
    mock_fa = {
        "fa_total_score": 75,
        "f_score": 7,
        "buffett": {"fair_price": 32000.0},
        "asset_valuation": {"bvps": 18057.0, "pb": 1.58, "manipulation_risk_level": 1},
        "cash_flow": {"quality_grade": "A", "z_zone": "SAFE"}
    }
    mock_ta = {
        "ta_total_score": 80,
        "indicators": {
            "ema20": 28000.0,
            "ema50": 27000.0,
            "sup_20d": 27500.0,
            "res_20d": 30500.0,
            "atr14": 800.0
        }
    }

    setup = calculate_trade_setup(price, mock_fa, mock_ta, mock_quote)

    assert setup["has_valid_setup"] is True
    assert setup["setup_status"] == "VALID_SETUP"
    assert setup["stop_loss"] < price
    assert setup["stop_loss_pct"] > 0
    assert setup["stop_loss_pct"] <= 7.0  # HOSE limit
    assert setup["take_profit_1"] > price
    assert setup["max_position_size_pct"] > 0.0
    assert setup["risk_reward_ratio"] >= 1.5


def test_disqualified_trade_setup_downtrend():
    """Kiểm tra Setup Validation Gate chặn đứng khi cổ phiếu nằm sâu trong Downtrend."""
    price = 14000.0
    mock_quote = {"symbol": "DOWN", "exchange": "HOSE", "price": price, "foreign_net_vol": -1000000}
    mock_fa = {
        "fa_total_score": 35,
        "f_score": 2,
        "cash_flow": {"quality_grade": "D", "z_zone": "DISTRESS"},
        "asset_valuation": {"manipulation_risk_level": 4}
    }
    mock_ta = {
        "ta_total_score": 30,
        "indicators": {
            "ema20": 16000.0,
            "ema50": 18000.0,
            "sup_20d": 13500.0,
            "res_20d": 17000.0,
            "atr14": 600.0
        }
    }

    setup = calculate_trade_setup(price, mock_fa, mock_ta, mock_quote)

    assert setup["has_valid_setup"] is False
    assert setup["setup_status"] == "NO_VALID_SETUP"
    assert setup["max_position_size_pct"] == 0.0
    assert setup["stop_loss"] == 0.0
    assert setup["take_profit_1"] == 0.0
    assert "ĐỨNG NGOÀI" in setup["buy_zone"] or "KHÔNG CÓ" in setup["buy_zone"]


def test_exchange_stop_loss_boundaries():
    """Kiểm tra biên độ cắt lỗ tối đa thích ứng theo quy tắc từng sàn (HOSE 7%, HNX 10%, UPCoM 14%)."""
    price = 30000.0
    mock_fa = {"fa_total_score": 70, "cash_flow": {"z_zone": "SAFE", "quality_grade": "B"}}
    # Hỗ trợ cực sâu để ép stop loss chạm ngưỡng trần biên độ sàn
    mock_ta = {
        "ta_total_score": 75,
        "indicators": {
            "ema20": 29000.0,
            "ema50": 28000.0,
            "sup_20d": 20000.0,
            "atr14": 4000.0
        }
    }

    # 1. HOSE
    setup_hose = calculate_trade_setup(price, mock_fa, mock_ta, {"exchange": "HOSE", "price": price})
    assert setup_hose["stop_loss_pct"] <= 7.05

    # 2. HNX
    setup_hnx = calculate_trade_setup(price, mock_fa, mock_ta, {"exchange": "HNX", "price": price})
    assert setup_hnx["stop_loss_pct"] <= 10.05

    # 3. UPCOM
    setup_upcom = calculate_trade_setup(price, mock_fa, mock_ta, {"exchange": "UPCOM", "price": price})
    assert setup_upcom["stop_loss_pct"] <= 14.05
