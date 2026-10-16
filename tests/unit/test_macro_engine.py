# -*- coding: utf-8 -*-
"""
tests/unit/test_macro_engine.py
Kiểm tra Module Phân tích Vĩ mô & Chu kỳ Ngành (Macro & Sector Cycle Engine):
1. Nguồn gốc dữ liệu vĩ mô (source_type: LIVE | CACHED | REFERENCE_BENCHMARK) và thời điểm as_of_date.
2. Phân loại ngành động (Dynamic Sector Classification) cho các mã cổ phiếu.
3. Điểm số Gió xuôi Vĩ mô (Macro Tailwind Score) và định vị pha chu kỳ.
"""

import pytest
from core.macro_engine import (
    GLOBAL_COMMODITIES_AND_MACRO,
    CURRENT_VIETNAM_MACRO,
    classify_sector,
    analyze_macro_and_sector_cycle,
    SECTOR_PROFILES,
)


def test_macro_provenance_and_labels():
    """Kiểm tra tính minh bạch nguồn gốc dữ liệu hàng hóa & vĩ mô quốc tế."""
    assert len(GLOBAL_COMMODITIES_AND_MACRO) >= 5

    valid_sources = {"LIVE", "CACHED", "REFERENCE_BENCHMARK"}

    for key, data in GLOBAL_COMMODITIES_AND_MACRO.items():
        assert "name" in data, f"Key {key} thiếu name"
        assert "value" in data, f"Key {key} thiếu value"
        assert "unit" in data, f"Key {key} thiếu unit"
        assert "source_type" in data, f"Key {key} thiếu trường source_type (ISSUE-04)"
        assert data["source_type"] in valid_sources, f"Key {key} source_type '{data['source_type']}' không hợp lệ"
        assert "as_of_date" in data, f"Key {key} thiếu trường as_of_date (ISSUE-04)"
        assert len(str(data["as_of_date"])) >= 4, f"as_of_date của {key} không được rỗng"

    # Kiểm tra các thông số vĩ mô Việt Nam
    assert "sbv_refinancing_rate_pct" in CURRENT_VIETNAM_MACRO
    assert "monetary_policy" in CURRENT_VIETNAM_MACRO
    assert "usd_vnd_trend" in CURRENT_VIETNAM_MACRO


def test_sector_classification_and_tailwinds():
    """Kiểm tra phân loại ngành và điểm hỗ trợ chu kỳ vĩ mô."""
    # Phân loại ngành cho các mã phổ biến
    sec_hpg = classify_sector("HPG")
    assert "STEEL" in sec_hpg or sec_hpg in SECTOR_PROFILES, f"HPG phải được phân loại ngành hợp lệ: {sec_hpg}"

    sec_vcb = classify_sector("VCB")
    assert "BANK" in sec_vcb or sec_vcb in SECTOR_PROFILES, f"VCB phải được phân loại ngành hợp lệ: {sec_vcb}"

    # Kiểm tra tính điểm Gió xuôi Vĩ mô
    macro_hpg = analyze_macro_and_sector_cycle("HPG")
    assert "tailwind_score" in macro_hpg
    assert 0 <= macro_hpg["tailwind_score"] <= 100
    assert "cycle_phase" in macro_hpg
    assert "sentiment" in macro_hpg
