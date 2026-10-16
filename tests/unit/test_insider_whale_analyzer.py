import pytest
from core.insider_whale_analyzer import analyze_whale_and_insider_news


def test_analyze_whale_and_insider_news_basic():
    symbol = "HPG"
    quote = {
        "symbol": "HPG",
        "price": 28000.0,
        "volume": 15000000.0,
        "foreign_buy": 2000000.0,
        "foreign_sell": 1500000.0,
        "exchange": "HOSE"
    }
    fa_result = {
        "governance": {
            "g_score": 85,
            "ownership": {
                "free_float_pct": 55.0,
                "foreigner_pct": 25.0,
                "state_pct": 0.0,
                "top_shareholders": [
                    {"name": "Trần Đình Long", "percentage": 26.08, "shares": 1500000000.0},
                    {"name": "Vũ Thị Hiền", "percentage": 7.34, "shares": 400000000.0}
                ]
            },
            "leadership": {
                "chairman": "Trần Đình Long",
                "ceo": "Nguyễn Việt Thắng",
                "insider_total_pct": 34.5,
                "skin_in_game_verdict": "RẤT CAO"
            }
        }
    }
    ta_result = {
        "indicators": {
            "ema20": 27500.0,
            "ema50": 26800.0,
            "sma200": 25000.0,
            "week_52_high": 31000.0,
            "week_52_low": 21000.0,
            "rsi": 58.0,
            "vol_ratio": 1.35
        },
        "vsa": {
            "phase": "Đẩy giá (Mark-up)"
        }
    }
    news_and_events = {
        "news": [
            {"title": "HPG công bố kết quả kinh doanh quý 3", "public_date": "2026-10-10", "source": "Báo Đầu Tư"}
        ],
        "events": [
            {"event_name": "Giao dịch nội bộ: Mua cổ phiếu", "public_date": "2026-10-05", "category": "INSIDER_TRADING"}
        ]
    }

    res = analyze_whale_and_insider_news(symbol, quote, fa_result, ta_result, news_and_events)

    assert res["symbol"] == "HPG"
    assert "holding_structure" in res
    assert "market_maker_behavior" in res
    assert "leadership_and_news_forensic" in res
    assert "actionable_playbook" in res

    # Kiểm tra holding
    holding = res["holding_structure"]
    assert holding["insider_pct"] == 34.5
    assert holding["foreigner_pct"] == 25.0
    assert 0 <= holding["true_free_float_pct"] <= 100
    assert "whale_dominance" in holding

    # Kiểm tra hành vi tạo lập
    mm = res["market_maker_behavior"]
    assert mm["status"] in [
        "GOM HÀNG LẶNG LẼ (QUIET ACCUMULATION / DRY UP)",
        "RUNG LẮC RŨ BỎ (SHAKEOUT / ABSORPTION)",
        "ĐẨY GIÁ THỬ CUNG (MARK-UP / POCKET PIVOT)",
        "PHÂN PHỐI / KÉO XẢ (DISTRIBUTION / BULL TRAP)",
        "ĐÈ GIÁ / THẢ TRÔI (MARK-DOWN / EXHAUSTION)"
    ]
    assert 0 <= mm["shakeout_risk_score"] <= 100

    # Kiểm tra bẫy tin tức
    lead = res["leadership_and_news_forensic"]
    assert "news_trap_diagnosis" in lead
    assert lead["has_recent_insider_deal"] is True
    assert len(lead["recent_news_highlights"]) == 1


def test_market_maker_behavior_classification_distribution():
    """Kiểm tra nhận diện pha phân phối khi giá sát đỉnh và quá mua."""
    quote = {"price": 95000.0, "volume": 5000000.0}
    fa_result = {"governance": {"g_score": 75, "ownership": {}, "leadership": {}}}
    ta_result = {
        "indicators": {
            "ema20": 92000.0,
            "ema50": 85000.0,
            "week_52_high": 98000.0,
            "week_52_low": 40000.0,
            "rsi": 76.0,
            "vol_ratio": 2.2
        },
        "vsa": {"phase": "Phân phối"}
    }
    res = analyze_whale_and_insider_news("TEST", quote, fa_result, ta_result)
    assert res["market_maker_behavior"]["status"] == "PHÂN PHỐI / KÉO XẢ (DISTRIBUTION / BULL TRAP)"
    assert res["market_maker_behavior"]["shakeout_risk_score"] >= 70


def test_market_maker_behavior_classification_accumulation():
    """Kiểm tra nhận diện pha gom hàng khi giá chiết khấu sâu và cạn kiệt thanh khoản."""
    quote = {"price": 32000.0, "volume": 300000.0}
    fa_result = {"governance": {"g_score": 80, "ownership": {}, "leadership": {}}}
    ta_result = {
        "indicators": {
            "ema20": 34000.0,
            "ema50": 36000.0,
            "week_52_high": 85000.0,
            "week_52_low": 30000.0,
            "rsi": 28.0,
            "vol_ratio": 0.65
        },
        "vsa": {"phase": "Cạn cung"}
    }
    res = analyze_whale_and_insider_news("DGC", quote, fa_result, ta_result)
    assert res["market_maker_behavior"]["status"] == "GOM HÀNG LẶNG LẼ (QUIET ACCUMULATION / DRY UP)"


def test_news_trap_diagnosis_shakeout_on_bad_news():
    """Kiểm tra chẩn đoán chiêu bài tin xấu rũ bỏ ở đáy."""
    quote = {"price": 31000.0, "volume": 400000.0}
    fa_result = {"governance": {"g_score": 80, "ownership": {}, "leadership": {}}}
    ta_result = {
        "indicators": {
            "ema20": 33000.0,
            "ema50": 35000.0,
            "week_52_high": 80000.0,
            "week_52_low": 29000.0,
            "rsi": 25.0,
            "vol_ratio": 0.7
        }
    }
    news_events = {
        "news": [
            {"title": "Cổ phiếu gặp khó khăn vì lợi nhuận sụt giảm mạnh", "public_date": "2026-10-12"}
        ]
    }
    res = analyze_whale_and_insider_news("DGC", quote, fa_result, ta_result, news_events)
    trap = res["leadership_and_news_forensic"]["news_trap_diagnosis"]
    assert "TIN XẤU" in trap["trap_type"]
