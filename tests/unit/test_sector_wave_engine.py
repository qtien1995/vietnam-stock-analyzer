# -*- coding: utf-8 -*-
"""
tests/unit/test_sector_wave_engine.py
Kiểm tra Module Phân tích Sóng Ngành & Động lực Luân chuyển Dòng tiền (Sector Wave Engine):
1. Danh mục 10 Sóng Ngành lớn của TTCK Việt Nam (2020 - 2026+).
2. Thuật toán chấm điểm nhiệt (Heat Score) và phân loại 4 Pha chu kỳ sóng.
3. Ánh xạ vị thế cổ phiếu: Leader (Đầu đàn) vs Runner (Chạy theo Beta cao).
4. Tích hợp với Macro Engine và Mô hình dữ liệu chuẩn AnalysisResult.
"""

import pytest
from core.sector_wave_engine import (
    SECTOR_WAVES_CATALOG,
    evaluate_sector_wave_radar,
    get_wave_context_for_ticker
)
from core.macro_engine import analyze_macro_and_sector_cycle
from core.models import MacroAndSectorAssessment, AnalysisResult
from tests.fixtures.sample_companies import HPG_QUOTE, HPG_FINANCIALS, make_mock_ohlcv
from core.ta_engine import analyze_technicals
from core.fa_engine import analyze_fundamentals
from core.risk_manager import calculate_trade_setup
from core.timing_engine import analyze_timing_prediction
from ai.council import InvestmentCouncil


def test_sector_waves_catalog_integrity():
    """Kiểm tra tính đầy đủ và cấu trúc của 10 Sóng Ngành lớn."""
    assert len(SECTOR_WAVES_CATALOG) >= 10, "Phải có tối thiểu 10 sóng ngành lớn"

    required_wave_ids = [
        "WAVE_OIL_GAS_GEOPOLITICS",
        "WAVE_TECH_AI_SEMICONDUCTOR",
        "WAVE_STEEL_INFRA_TARIFF",
        "WAVE_SECURITIES_LIQUIDITY",
        "WAVE_RESIDENTIAL_REAL_ESTATE",
        "WAVE_INDUSTRIAL_PARK_FDI",
        "WAVE_CHEMICAL_FERTILIZER",
        "WAVE_PUBLIC_INFRASTRUCTURE",
        "WAVE_EXPORT_SHIPPING",
        "WAVE_RETAIL_DOMESTIC"
    ]

    for wave_id in required_wave_ids:
        assert wave_id in SECTOR_WAVES_CATALOG, f"Thiếu sóng ngành: {wave_id}"
        wave = SECTOR_WAVES_CATALOG[wave_id]
        assert wave.get("name_vi"), f"Sóng {wave_id} thiếu name_vi"
        assert wave.get("wave_characteristics"), f"Sóng {wave_id} thiếu wave_characteristics"
        assert len(wave.get("core_catalysts", [])) >= 2, f"Sóng {wave_id} phải có ít nhất 2 core_catalysts"
        assert len(wave.get("leaders", [])) >= 1, f"Sóng {wave_id} phải có ít nhất 1 leader"
        assert len(wave.get("high_beta_runners", [])) >= 1, f"Sóng {wave_id} phải có ít nhất 1 high_beta_runners"
        assert wave.get("trading_rule"), f"Sóng {wave_id} thiếu trading_rule"


def test_evaluate_sector_wave_radar_scoring():
    """Kiểm tra thuật toán tính điểm nhiệt Heat Score và phân bổ Pha sóng."""
    radar = evaluate_sector_wave_radar()

    assert len(radar) == len(SECTOR_WAVES_CATALOG)

    # 1. Kết quả phải được sắp xếp giảm dần theo heat_score
    scores = [w["heat_score"] for w in radar]
    assert scores == sorted(scores, reverse=True), "Radar phải sắp xếp giảm dần theo heat_score"

    # 2. Miền giá trị Heat Score phải từ 0 đến 100
    for w in radar:
        hs = w["heat_score"]
        assert 0 <= hs <= 100, f"Heat score ({hs}) ngoài khoảng [0, 100]"
        phase = w["phase"].upper()
        assert any(p in phase for p in ["PHA 1", "PHA 2", "PHA 3", "PHA 4"]), f"Phase không hợp lệ: {phase}"

    # 3. Sóng Dầu khí (Brent tăng + Hormuz) hoặc Bán dẫn/Thép phải có heat score cao
    oil_wave = next((w for w in radar if w["wave_id"] == "WAVE_OIL_GAS_GEOPOLITICS"), None)
    assert oil_wave is not None
    assert oil_wave["heat_score"] >= 65, "Sóng Dầu khí phải có điểm nhiệt cao khi giá dầu bứt phá"


def test_get_wave_context_for_ticker_leaders_and_runners():
    """Kiểm tra phân định Leader vs Runner cho từng mã cổ phiếu cụ thể."""
    # PVD / PVS: Leader sóng Dầu khí
    pvd_wave = get_wave_context_for_ticker("PVD")
    assert pvd_wave["has_wave"] is True
    assert pvd_wave["wave_id"] == "WAVE_OIL_GAS_GEOPOLITICS"
    assert "LEADER" in pvd_wave["role"]
    assert any("Hormuz" in c or "Trung Đông" in c for c in pvd_wave["catalysts"])

    # PVC: Runner sóng Dầu khí
    pvc_wave = get_wave_context_for_ticker("PVC")
    assert pvc_wave["has_wave"] is True
    assert pvc_wave["wave_id"] == "WAVE_OIL_GAS_GEOPOLITICS"
    assert "RUNNER" in pvc_wave["role"]

    # FPT: Leader sóng Công nghệ AI
    fpt_wave = get_wave_context_for_ticker("FPT")
    assert fpt_wave["has_wave"] is True
    assert fpt_wave["wave_id"] == "WAVE_TECH_AI_SEMICONDUCTOR"
    assert "LEADER" in fpt_wave["role"]

    # HPG: Leader sóng Thép
    hpg_wave = get_wave_context_for_ticker("HPG")
    assert hpg_wave["has_wave"] is True
    assert hpg_wave["wave_id"] == "WAVE_STEEL_INFRA_TARIFF"
    assert "LEADER" in hpg_wave["role"]

    # VIX: Runner sóng Chứng khoán
    vix_wave = get_wave_context_for_ticker("VIX")
    assert vix_wave["has_wave"] is True
    assert vix_wave["wave_id"] == "WAVE_SECURITIES_LIQUIDITY"
    assert "RUNNER" in vix_wave["role"]

    # Mã không thuộc sóng nào
    unknown_wave = get_wave_context_for_ticker("XYZ999", "GENERAL")
    assert unknown_wave["has_wave"] is False


def test_macro_engine_integration():
    """Kiểm tra analyze_macro_and_sector_cycle tự động đính kèm sector_wave."""
    res = analyze_macro_and_sector_cycle("PVD")
    assert "sector_wave" in res
    assert res["sector_wave"]["has_wave"] is True
    assert res["sector_wave"]["wave_id"] == "WAVE_OIL_GAS_GEOPOLITICS"

    # Kiểm tra model MacroAndSectorAssessment
    macro_model = MacroAndSectorAssessment(**res)
    assert macro_model.sector_wave.get("has_wave") is True
    assert macro_model.sector_wave.get("wave_id") == "WAVE_OIL_GAS_GEOPOLITICS"


def test_canonical_analysis_result_includes_wave():
    """Kiểm tra AnalysisResult from_components nhận và lưu trữ sector_wave toàn vẹn."""
    quote = dict(HPG_QUOTE)
    df_ohlcv = make_mock_ohlcv(days=250, trend="uptrend", base_price=quote["price"])
    current_price = float(df_ohlcv["close"].iloc[-1])
    quote["price"] = current_price

    ta_result = analyze_technicals(df_ohlcv)
    fa_result = analyze_fundamentals(dict(HPG_FINANCIALS), current_price, quote)
    trade_setup = calculate_trade_setup(current_price, fa_result, ta_result, quote)
    timing_result = analyze_timing_prediction("HPG", quote, ta_result, fa_result)
    council = InvestmentCouncil()
    council_result = council.deliberate("HPG", quote, fa_result, ta_result, trade_setup)

    analysis_result = AnalysisResult.from_components(
        symbol="HPG",
        quote=quote,
        fa_result=fa_result,
        ta_result=ta_result,
        trade_setup=trade_setup,
        timing_result=timing_result,
        council_result=council_result,
        html_report_path=None
    )

    assert analysis_result.fa.macro.sector_wave.get("has_wave") is True
    assert analysis_result.fa.macro.sector_wave.get("wave_id") == "WAVE_STEEL_INFRA_TARIFF"
    assert "LEADER" in analysis_result.fa.macro.sector_wave.get("role", "")
