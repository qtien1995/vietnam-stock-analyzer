import pytest
from ai.prompt_library import PromptLibrary, PERSONA_CATALOG
from ai.interactive_advisor import CouncilAdvisor
from config import PROMPTS_DIR


class TestPromptLibrary:
    def test_all_catalog_prompts_exist_on_disk(self):
        """Kiểm tra toàn bộ 11 file prompt trong catalog đều tồn tại trên đĩa và không rỗng"""
        assert len(PERSONA_CATALOG) >= 11
        for pid, meta in PERSONA_CATALOG.items():
            filename = meta["filename"]
            filepath = PROMPTS_DIR / filename
            assert filepath.exists(), f"File prompt {filename} cho persona {pid} không tồn tại!"
            content = filepath.read_text(encoding="utf-8").strip()
            assert len(content) > 100, f"Nội dung prompt {filename} quá ngắn hoặc bị rỗng!"

    def test_list_personas(self):
        """Kiểm tra hàm list_personas lấy đủ danh sách personas"""
        personas = PromptLibrary.list_personas()
        assert len(personas) >= 11
        core_personas = PromptLibrary.list_personas(category="core")
        extended_personas = PromptLibrary.list_personas(category="extended")
        assert len(core_personas) == 6
        assert len(extended_personas) == 5

    def test_persona_aliases(self):
        """Kiểm tra các alias thông dụng của chuyên gia"""
        assert PromptLibrary.get_persona("pe")["id"] == "pe_fund"
        assert PromptLibrary.get_persona("deepthink")["id"] == "red_team"
        assert PromptLibrary.get_persona("audit")["id"] == "forensic"
        assert PromptLibrary.get_persona("cro")["id"] == "taleb_cro"
        assert PromptLibrary.get_persona("vsa")["id"] == "wyckoff"

    def test_build_prompt_payload(self):
        """Kiểm tra sinh payload hoàn chỉnh cho LLM"""
        context = {
            "price": 28500,
            "fair_price": 32000,
            "stop_loss": 26500,
            "stop_loss_pct": 7.0,
            "pb": 1.45,
            "bvps": 19600,
            "cfo_human": "Dương 1,200 tỷ",
            "sector": "Thép & Vật liệu xây dựng"
        }
        payload = PromptLibrary.build_prompt_payload(
            persona_id="pe_fund",
            symbol="HPG",
            context=context,
            custom_question="Đánh giá khả năng bứt phá định giá?"
        )
        assert "system_instruction" in payload
        assert "user_prompt" in payload
        assert "persona_title" in payload
        assert len(payload["system_instruction"]) > 200
        assert "HPG" in payload["user_prompt"]
        assert "28,500" in payload["user_prompt"]

    def test_council_advisor_all_personas_fallback(self):
        """Kiểm tra CouncilAdvisor sinh câu trả lời định lượng chi tiết cho cả 11 chuyên gia"""
        advisor = CouncilAdvisor()
        context = {
            "price": 25000,
            "fair_price": 29000,
            "stop_loss": 23250,
            "stop_loss_pct": 7.0,
            "take_profit_1": 28000,
            "take_profit_1_pct": 12.0,
            "pb": 1.2,
            "bvps": 20800,
            "cfo_human": "Dương 500 tỷ",
            "fcf_human": "Dương 300 tỷ",
            "active_buy_pct": 58.5,
            "foreign_net_vol": 1200000,
            "sector": "Chứng khoán",
            "timing_verdict": "VCP Thu hẹp biến động",
            "risk_reward_ratio": 2.5,
            "max_position_size_pct": 15.0
        }

        test_personas = [
            "buffett", "lynch", "oneil", "wyckoff", "dalio", "taleb_cro",
            "pe_fund", "red_team", "forensic", "stress_test", "unit_economics"
        ]

        for p_id in test_personas:
            res = advisor.answer_question(
                symbol="SSI",
                question="Thương vụ này có đáng giải ngân không?",
                expert_id=p_id,
                context=context
            )
            assert res["symbol"] == "SSI"
            assert res["expert_id"] == p_id
            assert "answer" in res
            assert len(res["answer"]) > 50, f"Câu trả lời của {p_id} quá ngắn!"
            assert "SSI" in res["answer"]
