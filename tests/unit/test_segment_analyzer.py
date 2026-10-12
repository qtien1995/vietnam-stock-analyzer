import pytest
from core.segment_analyzer import analyze_company_segments, load_segment_profile


def test_verified_segment_profile_hpg():
    """Kiểm tra mã HPG có hồ sơ phân khúc chuẩn trong data/segments/HPG.json."""
    result = analyze_company_segments("HPG", "CTCP Tập đoàn Hòa Phát", "Thép")

    assert result["has_detailed_segments"] is True
    assert result["source"] == "VERIFIED_FILE"
    assert len(result["segments"]) > 0
    # Tổng tỷ trọng doanh thu phải xấp xỉ 100%
    total_rev = sum(s["rev_share_pct"] for s in result["segments"])
    assert 95.0 <= total_rev <= 105.0


def test_unverified_segment_profile_unknown_ticker():
    """Kiểm tra mã chưa có hồ sơ: KHÔNG ĐƯỢC sinh ra phân khúc hoặc dự án giả tạo."""
    result = analyze_company_segments("XYZ_UNKNOWN_TICKER", "Công ty Vô Danh", "Bất động sản")

    assert result["has_detailed_segments"] is False
    assert result["source"] == "UNVERIFIED"
    assert result["segments"] == []
    assert result["projects"] == []
    assert "chưa có hồ sơ bóc tách phân khúc" in result["business_model_summary"]
