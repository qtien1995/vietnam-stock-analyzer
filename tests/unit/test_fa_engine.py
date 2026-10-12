import pytest
from core.fa_engine import (
    analyze_fundamentals,
    calculate_piotroski_score
)
from tests.fixtures.sample_companies import (
    HPG_QUOTE,
    HPG_FINANCIALS,
    VCB_QUOTE,
    VCB_FINANCIALS,
    NEGATIVE_EPS_QUOTE,
    NEGATIVE_EPS_FINANCIALS,
    MISSING_DATA_FINANCIALS
)


def test_hpg_healthy_manufacturing_fa():
    """Kiểm tra phân tích FA đối với doanh nghiệp sản xuất chuẩn mực (HPG)."""
    price = HPG_QUOTE["price"]
    result = analyze_fundamentals(HPG_FINANCIALS, price, HPG_QUOTE)

    assert result["fa_total_score"] > 0
    assert result["f_score"] >= 4
    assert result["piotroski_details"]["variant"] == "MODIFIED_STATIC"

    ratios = result["ratios"]
    assert ratios["pe"] is not None
    assert ratios["pe"] > 0
    assert ratios["pe_status"] == "VALID"
    assert ratios["pb"] is not None
    assert ratios["pb"] > 0
    assert ratios["pb_status"] == "VALID"
    assert ratios["roe"] is not None
    assert ratios["roa"] is not None

    cf = result["cash_flow"]
    assert cf["quality_grade"] in ["A", "B", "C", "D"]
    assert cf["altman_z"] > 0
    assert cf["z_status"] in ["VALID", "SAFE"]

    asset_val = result["asset_valuation"]
    assert asset_val["bvps"] == 18057.0
    assert asset_val["pb"] == round(price / 18057.0, 2)
    assert 1 <= asset_val["manipulation_risk_level"] <= 5


def test_vcb_bank_exemption_fa():
    """Kiểm tra phân tích FA đối với Ngân hàng: Miễn trừ Altman Z'' và không crash vì thiếu hàng tồn kho."""
    price = VCB_QUOTE["price"]
    result = analyze_fundamentals(VCB_FINANCIALS, price, VCB_QUOTE)

    cf = result["cash_flow"]
    assert cf["z_status"] == "NOT_APPLICABLE"
    assert "tài chính" in cf["z_desc"].lower() or "ngân hàng" in cf["z_desc"].lower() or "bank" in cf["z_desc"].lower()

    ratios = result["ratios"]
    assert ratios["pe"] is not None
    assert ratios["pb"] is not None


def test_negative_eps_loss_making_company():
    """Kiểm tra xử lý doanh nghiệp lỗ nặng: P/E và PEG phải là None, tuyệt đối không gán mặc định 15.0."""
    price = NEGATIVE_EPS_QUOTE["price"]
    result = analyze_fundamentals(NEGATIVE_EPS_FINANCIALS, price, NEGATIVE_EPS_QUOTE)

    ratios = result["ratios"]
    assert ratios["pe"] is None
    assert ratios["pe_status"] == "NEGATIVE_EARNINGS"
    assert ratios["pb"] is None
    assert ratios["pb_status"] == "NEGATIVE_EQUITY"

    lynch = result["lynch"]
    assert lynch["peg"] is None
    assert lynch["peg_status"] in ["NEGATIVE_EPS", "NEGATIVE_GROWTH"]

    asset_val = result["asset_valuation"]
    assert asset_val["pb"] is None
    assert asset_val["bvps"] < 0 or asset_val["bvps"] is None


def test_missing_data_financials():
    """Kiểm tra xử lý dữ liệu tài chính trống: Không được crash và trả về trạng thái rõ ràng."""
    price = 10000.0
    mock_quote = {"symbol": "EMPTY", "company_name": "Công ty Trống", "price": price}
    result = analyze_fundamentals(MISSING_DATA_FINANCIALS, price, mock_quote)

    assert result is not None
    ratios = result["ratios"]
    assert ratios["pe"] is None
    assert ratios["pb"] is None
    assert ratios["pe_status"] in ["INSUFFICIENT_DATA", "MISSING_DATA"]
    assert ratios["pb_status"] in ["INSUFFICIENT_DATA", "MISSING_DATA"]


def test_piotroski_f_score_static_bounds():
    """Kiểm tra hàm F-score tính điểm nằm trong khoảng 0-9 và có metadata."""
    res = calculate_piotroski_score(HPG_FINANCIALS)
    assert 0 <= res["score"] <= 9
    assert isinstance(res["criteria_met"], list)
    assert res["variant"] == "MODIFIED_STATIC"
