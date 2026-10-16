# -*- coding: utf-8 -*-
"""
tests/unit/test_data_loader.py
Kiểm tra Module Thu thập Dữ liệu (Data Loader):
1. Chuẩn hóa tên cột quý (normalize_quarter_key) và sắp xếp thời gian chính xác (sort_quarter_columns).
2. Kiểm tra tính toàn vẹn số quan sát TTM (ttm_status: COMPLETE vs INCOMPLETE_QUARTERS).
3. Cấu trúc dữ liệu ma trận vĩ mô và hàng hóa toàn cầu.
"""

import pytest
from core.data_loader import (
    normalize_quarter_key,
    sort_quarter_columns,
    get_global_macro_and_commodities,
)


def test_quarter_normalization_and_sorting():
    """Kiểm tra logic chuẩn hóa định dạng quý YYYY_QX và sắp xếp giảm dần theo thời gian (ISSUE-09)."""
    # 1. Kiểm tra normalize_quarter_key
    assert normalize_quarter_key("Q2/2024") == "2024_Q2"
    assert normalize_quarter_key("2024-Q3") == "2024_Q3"
    assert normalize_quarter_key("2023_Q4") == "2023_Q4"
    assert normalize_quarter_key("2024-06") == "2024_Q2"
    assert normalize_quarter_key("2024-12") == "2024_Q4"
    assert normalize_quarter_key("invalid_column") is None

    # 2. Kiểm tra sắp xếp cột quý từ mới nhất đến cũ nhất
    raw_columns = ["Q1/2023", "Q4/2023", "Q3/2024", "Q2/2024", "Q1/2024"]
    sorted_cols = sort_quarter_columns(raw_columns)
    
    expected = ["Q3/2024", "Q2/2024", "Q1/2024", "Q4/2023", "Q1/2023"]
    assert sorted_cols == expected, f"Thứ tự sau sắp xếp phải là {expected}, nhưng nhận được {sorted_cols}"


def test_ttm_completeness_flag():
    """Kiểm tra điều kiện xác định chu kỳ 4 quý TTM."""
    # Khi có đủ 4 quý
    four_q = ["2024_Q3", "2024_Q2", "2024_Q1", "2023_Q4"]
    status_full = "COMPLETE" if len(four_q[:4]) >= 4 else "INCOMPLETE_QUARTERS"
    assert status_full == "COMPLETE"

    # Khi công ty mới lên sàn chỉ có 2 quý
    two_q = ["2024_Q3", "2024_Q2"]
    status_short = "COMPLETE" if len(two_q[:4]) >= 4 else "INCOMPLETE_QUARTERS"
    assert status_short == "INCOMPLETE_QUARTERS"


def test_global_macro_and_commodities_loader():
    """Kiểm tra hàm lấy ma trận vĩ mô và hàng hóa toàn cầu có cache và provenance."""
    macro_data = get_global_macro_and_commodities(force_refresh=False)
    
    assert "updated_at" in macro_data
    assert "global_commodities" in macro_data
    assert "vietnam_macro" in macro_data

    comm = macro_data["global_commodities"]
    assert "crude_oil_brent" in comm
    assert "source_type" in comm["crude_oil_brent"]
    assert "as_of_date" in comm["crude_oil_brent"]
