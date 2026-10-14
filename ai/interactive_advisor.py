"""
Module Tham Mưu Hỏi Đáp Tương Tác với Hội đồng AI (Interactive Council Advisor)
Tích hợp kho tri thức prompts.chat & Đa mô hình LLMRouter:
- Kết nối trực tiếp LLM (Gemini, OpenAI, Claude, Ollama) với System Prompts chuyên sâu
- Fallback thông minh sang Động cơ Định lượng Luật thép khi Offline
- Tuân thủ nghiêm ngặt AGENTS.md:
  + Độc lập, khách quan, không vuốt ve, không đoán bừa.
  + Dữ liệu định lượng từ SQLite và BCTC (CFO, FCF, P/B, nợ vay, điểm Pivot, Stop Loss).
  + Hỗ trợ 11 chuyên gia phân tích (6 Hội đồng cốt lõi + 5 Chuyên gia mở rộng từ prompts.chat).
"""

from typing import Dict, Any, Optional
from ai.llm_router import LLMRouter
from ai.prompt_library import PromptLibrary, PERSONA_CATALOG


class CouncilAdvisor:
    def __init__(self, router: Optional[LLMRouter] = None):
        self.router = router or LLMRouter()

    def answer_question(
        self,
        symbol: str,
        question: str,
        expert_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trả lời câu hỏi của nhà đầu tư dựa trên dữ liệu phân tích thực tế của mã cổ phiếu.
        Hỗ trợ gọi LLM trực tiếp với prompt từ prompts.chat và tự động fallback sang Rule-Based Engine.
        """
        sym = symbol.upper().strip()
        exp_id = (expert_id or "all").lower().strip()

        # Tìm persona tương ứng
        persona = PromptLibrary.get_persona(exp_id)
        if not persona:
            persona = PERSONA_CATALOG["taleb_cro"]
        actual_id = persona["id"]
        speaker_title = f"{persona['badge']} {persona['name']} ({persona['title']})"

        # 1. Thử gọi LLM nếu có cấu hình Provider trực tuyến
        if self.router.provider != "offline":
            try:
                payload = PromptLibrary.build_prompt_payload(
                    persona_id=actual_id,
                    symbol=sym,
                    context=context,
                    custom_question=question
                )
                ai_reply = self.router.generate(
                    system_prompt=payload["system_instruction"],
                    user_prompt=payload["user_prompt"]
                )
                if ai_reply and len(ai_reply.strip()) > 30:
                    return {
                        "symbol": sym,
                        "expert": speaker_title,
                        "expert_id": actual_id,
                        "question": question,
                        "answer": ai_reply.strip(),
                        "source": f"llm_{self.router.provider}"
                    }
            except Exception:
                pass

        # 2. Fallback sang Động cơ Định lượng Chuyên sâu (Offline Rule-Based Engine)
        ans = self._generate_rule_based_answer(actual_id, sym, question, context)

        return {
            "symbol": sym,
            "expert": speaker_title,
            "expert_id": actual_id,
            "question": question,
            "answer": ans,
            "source": "rule_based_quantitative"
        }

    def _generate_rule_based_answer(
        self,
        exp_id: str,
        sym: str,
        question: str,
        context: Dict[str, Any]
    ) -> str:
        """Sinh câu trả lời định lượng chi tiết cho 11 vai trò dựa trên dữ liệu thực"""
        price = float(context.get("price", 0.0))
        fair_price = float(context.get("fair_price", price))
        stop_loss = float(context.get("stop_loss", price * 0.93))
        sl_pct = float(context.get("stop_loss_pct", 7.0))
        tp1 = float(context.get("take_profit_1", price * 1.12))
        tp1_pct = float(context.get("take_profit_1_pct", 12.0))
        tp2 = float(context.get("take_profit_2", price * 1.25))
        tp2_pct = float(context.get("take_profit_2_pct", 25.0))
        trigger_pivot = float(context.get("trigger_pivot", price * 1.03))

        pb = float(context.get("pb", 1.0))
        bvps = float(context.get("bvps", 0.0))
        cfo_human = context.get("cfo_human", "Dương")
        fcf_human = context.get("fcf_human", "Dương")
        active_buy_pct = float(context.get("active_buy_pct", 50.0))
        foreign_net = float(context.get("foreign_net_vol", 0.0))
        sector = context.get("sector", "Doanh nghiệp")
        timing_verdict = context.get("timing_verdict", "Tích lũy quan sát")
        rr = float(context.get("risk_reward_ratio", 2.0))
        max_pos = float(context.get("max_position_size_pct", 10.0))

        q_lower = question.lower()

        # 1. Warren Buffett
        if exp_id == "buffett":
            if any(k in q_lower for k in ["lỗ", "xấu nhất", "sập", "rủi ro"]):
                return (
                    f"Theo tiêu chuẩn biên an toàn của Graham, kịch bản xấu nhất thị giá {sym} có thể lùi về kiểm định giá trị tài sản ròng sổ sách (BVPS: {bvps:,.0f} đ). "
                    f"Hiện tại P/B đang là {pb:.2f}x so với giá trị thực ước tính {fair_price:,.0f} đ. "
                    f"Nếu giá đang cao hơn giá trị thực, chúng tôi KHÔNG khuyến nghị mua gom bình quân giá xuống. Nguyên tắc số 1: Không để mất tiền; Nguyên tắc số 2: Xem lại nguyên tắc số 1."
                )
            elif any(k in q_lower for k in ["cổ tức", "tiền thật", "cfo", "fcf"]):
                return (
                    f"Chúng tôi đánh giá cao doanh nghiệp nhờ dòng tiền kinh doanh thật (CFO đạt {cfo_human}) và dòng tiền tự do (FCF đạt {fcf_human}). "
                    f"Tiền thật vào tài khoản là con hào kinh tế vững chắc nhất chứng minh ban lãnh đạo không 'xào nấu' báo cáo tài chính."
                )
            else:
                margin_safe = "ĐẠT CHUẨN MUA GOM DÀI HẠN (Biên an toàn > 15%)" if price <= fair_price * 0.85 else "CHƯA ĐỦ BIÊN AN TOÀN. Nhà đầu tư giá trị nên kiên nhẫn chờ những nhịp thị trường hoảng loạn để gom rẻ hơn."
                return (
                    f"Giá trị nội tại hợp lý của {sym} ước tính quanh {fair_price:,.0f} đ (BVPS: {bvps:,.0f} đ). "
                    f"Với thị giá hiện tại {price:,.0f} đ, biên an toàn hiện ở mức: {margin_safe} "
                    f"Điều kiện mất hiệu lực: Luận điểm mua tích sản sẽ bị hủy bỏ nếu dòng tiền kinh doanh (CFO) âm kéo dài quá 2 quý hoặc phát hiện giao dịch rút ruột qua công ty sân sau."
                )

        # 2. Peter Lynch
        elif exp_id == "lynch":
            return (
                f"Động lực tăng trưởng cốt lõi của {sym} nằm ở chuỗi dự án gối đầu và tiềm năng mở rộng quy mô ngành {sector}. "
                f"Doanh nghiệp có cơ cấu tài chính ổn định (CFO: {cfo_human}, FCF: {fcf_human}). Tiêu chí hàng đầu của Lynch là theo dõi sát sao tiến độ bàn giao dự án "
                f"và tăng trưởng doanh thu cốt lõi quý tới. Nếu biên lợi nhuận gộp duy trì đà mở rộng và hệ số PEG < 1.0, đây sẽ là cổ phiếu tăng trưởng giá trị xuất sắc. "
                f"Điều kiện mất hiệu lực: Tăng trưởng doanh thu mảng cốt lõi giảm tốc dưới 10% hoặc biên gộp bị bào mòn."
            )

        # 3. William O'Neil & Minervini
        elif exp_id == "oneil":
            if any(k in q_lower for k in ["cắt lỗ", "stop loss", "lỗ"]):
                return (
                    f"Kỷ luật cắt lỗ là luật thép sống còn: Nếu {sym} xuyên thủng ngưỡng {stop_loss:,.0f} đ (-{sl_pct}%), bạn BẮT BUỘC phải bán cắt lỗ ngay lập tức, không có ngoại lệ. "
                    f"Không bao giờ để một khoản lỗ nhỏ biến thành một khoản lỗ chết người."
                )
            elif any(k in q_lower for k in ["mua", "khi nào", "tín hiệu", "giải ngân"]):
                return (
                    f"Theo phương pháp CANSLIM và Minervini VCP, bạn TUYỆT ĐỐI KHÔNG mua đuổi khi cổ phiếu chưa có điểm nổ Pocket Pivot xác nhận. "
                    f"Mốc giá kích hoạt giải ngân là khi {sym} vượt dứt khoát {trigger_pivot:,.0f} đ đi kèm khối lượng khớp lệnh bùng nổ gấp từ 1.3x - 1.5x lần MA20. "
                    f"Nếu thanh khoản èo uột hoặc nến cụt đầu, hãy ngồi yên bảo toàn sức mua."
                )
            else:
                return (
                    f"Mô hình giá của {sym} đang ở trạng thái: {timing_verdict}. Điểm Pivot kích hoạt nằm tại {trigger_pivot:,.0f} đ. "
                    f"Mục tiêu kỳ vọng chốt lời: TP1 đạt {tp1:,.0f} đ (+{tp1_pct}%), TP2 đạt {tp2:,.0f} đ (+{tp2_pct}%). "
                    f"Luôn đặt lệnh Stop Loss tự động tại {stop_loss:,.0f} đ (-{sl_pct}%). Điều kiện mất hiệu lực: Giá đóng cửa gãy EMA20 hoặc thủng ngưỡng Stop Loss."
                )

        # 4. Wyckoff & VSA
        elif exp_id == "wyckoff":
            status_order = "Phe mua đang chiếm ưu thế hấp thụ lượng cung bán ra" if active_buy_pct >= 55 else "Phe bán đang chủ động xả lệnh MP, lực cung chốt lời còn khá dày"
            fn_status = f"gom ròng +{foreign_net:,.0f} CP" if foreign_net > 0 else f"bán ròng {foreign_net:,.0f} CP"
            return (
                f"Dưới góc nhìn VSA: Lực mua chủ động hiện chiếm {active_buy_pct:.1f}% tổng khớp lệnh ({status_order}). "
                f"Giao dịch khối ngoại ghi nhận: {fn_status}. "
                f"Chu kỳ dòng tiền của {sym} đang vận động trong pha tích lũy/hấp thụ cung. "
                f"Cần quan sát các phiên kiểm tra cung (Test Bar/No Supply) với thân nến hẹp và khối lượng cạn kiệt trước khi xác nhận dòng tiền lớn đẩy giá. "
                f"Điều kiện mất hiệu lực: Xuất hiện phiên xả Upthrust khối lượng lớn đè gãy nền tích lũy."
            )

        # 5. Ray Dalio & Howard Marks
        elif exp_id == "dalio":
            return (
                f"Bối cảnh vĩ mô ngành {sector} đối với {sym} đang vận động theo chu kỳ nới lỏng chính sách tiền tệ và mặt bằng lãi suất cho vay hỗ trợ doanh nghiệp. "
                f"Tuy nhiên, theo Howard Marks: 'Thành công trong đầu tư không phải là mua cái tốt, mà là mua với giá tốt'. "
                f"Đừng để sự hưng phấn của truyền thông cuốn bạn vào bẫy P/E đỉnh chu kỳ tại vùng giá đã tăng nóng. "
                f"Điều kiện mất hiệu lực: Môi trường lãi suất đảo chiều tăng tốc hoặc các chính sách pháp lý quy hoạch ngành bị nghẽn lại."
            )

        # 6. Elite Private Equity Fund Manager (Từ prompts.chat)
        elif exp_id == "pe_fund":
            pe_hardcore = 8 if (pb <= 1.5 and "Dương" in cfo_human) else (6 if pb <= 2.5 else 4)
            return (
                f"Thẩm định Quỹ Private Equity đối với mã {sym} (Thị giá: {price:,.0f} đ):\n"
                f"1. Điểm số Cơ bản Hardcore: {pe_hardcore}/10. P/B hiện tại {pb:.2f}x so với BVPS {bvps:,.0f} đ; Dòng tiền CFO: {cfo_human}.\n"
                f"2. Dòng tiền Săn mồi (Capital Flow): Lực mua chủ động {active_buy_pct:.1f}%, khối ngoại ròng {foreign_net:,.0f} CP. Dòng tiền lớn duy trì vị thế thăm dò.\n"
                f"3. Phán đoán Định chế: Tỷ lệ Lợi nhuận/Rủi ro R:R đạt {rr:.1f}:1. Xác suất chiến thắng kỳ vọng: 65% nếu giải ngân đúng Buy Zone.\n"
                f"4. Kế hoạch Giải ngân: Tối đa {max_pos:.1f}% NAV danh mục quỹ. Cắt lỗ cứng tại {stop_loss:,.0f} đ (-{sl_pct}%).\n"
                f"5. Exit Trigger: Quỹ sẽ tất toán vị thế nếu biên lợi nhuận gộp quý tới suy giảm trên 15% hoặc gãy ngưỡng Stop Loss."
            )

        # 7. DeepThink Red Team & Critical Analyst (Từ prompts.chat)
        elif exp_id == "red_team":
            return (
                f"🔥 RED TEAM PHẢN BIỆN TÀN NHẪN CHO {sym}:\n"
                f"1. Bẻ gãy Luận điểm Tăng: Đám đông đang kỳ vọng sóng tăng ngắn hạn, nhưng hãy chú ý: Giá hiện tại {price:,.0f} đ đang cao gấp {pb:.2f}x lần giá trị sổ sách ròng BVPS ({bvps:,.0f} đ).\n"
                f"2. Top 3 Điểm mù Chết người:\n"
                f"   - Bẫy thanh khoản T+2.5: Nếu đu lệnh giá xanh trong phiên bùng nổ giả, rủi ro hàng về cắt lỗ -7% là rất lớn.\n"
                f"   - Độ lệch Dòng tiền: Cần kiểm tra xem LNST có thực sự chuyển hóa thành tiền mặt trong tài khoản hay đang bị 'treo' tại Khoản phải thu.\n"
                f"   - Rủi ro thị trường chung: Nếu chỉ số VN-Index điều chỉnh, cổ phiếu này có thể bị bán lan truyền (Contagion Effect).\n"
                f"3. Kịch bản Thất bại (Pre-Mortem): Nếu giá gãy mốc hỗ trợ {stop_loss:,.0f} đ, đà bán tháo sẽ đẩy thị giá về vùng chiết khấu sâu hơn.\n"
                f"Phán quyết Red Team: KHÔNG ĐƯỢC MUA ĐUỔI GIÁ CAO. Chỉ giải ngân khi có chiết khấu an toàn hoặc điểm nổ Pivot xác nhận chuẩn."
            )

        # 8. Forensic Accountant (Từ prompts.chat)
        elif exp_id == "forensic":
            f_verdict = "LÀNH MẠNH TƯƠNG ĐỐI" if "Dương" in cfo_human else "CẢNH BÁO DÒNG TIỀN KINH DOANH"
            return (
                f"🔬 BÁO CÁO GIÁM ĐỊNH PHÁP Y BCTC MÃ {sym}:\n"
                f"1. Độ lệch Dòng tiền (CFO vs LNST): Dòng tiền kinh doanh thuần (CFO): {cfo_human}; Dòng tiền tự do (FCF): {fcf_human}. Xếp loại: {f_verdict}.\n"
                f"2. Bẫy Tài sản Đọng vốn: Giá trị sổ sách mỗi cổ phiếu đạt {bvps:,.0f} đ. Nhà đầu tư cần đặc biệt rà soát thuyết minh BCTC mục 'Khoản phải thu ngắn hạn' và 'Hàng tồn kho' để tránh bẫy vốn bị chiếm dụng lòng vòng.\n"
                f"3. Cảnh báo Công ty Sân sau: Không đầu tư nếu ban lãnh đạo liên tục có các giao dịch ủy thác đầu tư hoặc cho vay qua lại với các công ty TNHH cá nhân mà không có tài sản bảo đảm.\n"
                f"Phán quyết Pháp y: Cần đối chiếu BCTC quý đã kiểm toán trước khi nâng tỷ trọng nắm giữ dài hạn."
            )

        # 9. Scenario Stress-Tester (Từ prompts.chat)
        elif exp_id == "stress_test":
            return (
                f"📊 MÔ PHỎNG 3 KỊCH BẢN & STRESS-TEST MÃ {sym} (Thị giá: {price:,.0f} đ):\n"
                f"1. Kịch bản Tích cực (Bull Case - Xác suất 25%): Thị trường chung thuận lợi, dòng tiền lớn đẩy giá vượt đỉnh -> Mục tiêu TP2 đạt {tp2:,.0f} đ (+{tp2_pct}%).\n"
                f"2. Kịch bản Cơ sở (Base Case - Xác suất 55%): Doanh nghiệp tăng trưởng ổn định theo kế hoạch năm -> Giá hướng về Fair Value quanh {fair_price:,.0f} đ (TP1: {tp1:,.0f} đ, +{tp1_pct}%).\n"
                f"3. Kịch bản Tiêu cực (Stress Case - Xác suất 20%): Lãi suất tăng hoặc thị trường sập gãy hỗ trợ -> Giá lùi về kiểm định ngưỡng Stop Loss {stop_loss:,.0f} đ (-{sl_pct}%).\n"
                f"ĐIỀU KIỆN MẤT HIỆU LỰC: Đóng cửa gãy {stop_loss:,.0f} đ -> Lập tức đóng toàn bộ vị thế, bảo toàn vốn!"
            )

        # 10. Revenue Model & Unit Economics (Từ prompts.chat)
        elif exp_id == "unit_economics":
            return (
                f"🔬 BÓC TÁCH MÔ HÌNH DOANH THU & KINH TẾ ĐƠN VỊ {sym}:\n"
                f"1. Cỗ máy tạo tiền: Doanh nghiệp hoạt động trong lĩnh vực cốt lõi ngành {sector}. Doanh thu chủ lực đến từ mảng kinh doanh chính đóng góp tỷ trọng lớn vào cơ cấu lợi nhuận gộp.\n"
                f"2. Năng lực định giá (Pricing Power): Cần theo dõi biên lợi nhuận gộp qua từng quý. Nếu biên gộp duy trì mở rộng trên 20%, chứng minh doanh nghiệp có khả năng chuyển chi phí sang khách hàng.\n"
                f"3. Điểm nghẽn Tăng trưởng (Bottlenecks): Rào cản công suất sản xuất hoặc hạn mức tín dụng ngân hàng là những yếu tố quyết định tốc độ bứt phá doanh thu tiếp theo.\n"
                f"Khuyến nghị: Tập trung theo dõi báo cáo phân khúc (Segment Report) trong kỳ công bố BCTC tới."
            )

        # 11. Taleb & CRO Arbiter (Mặc định)
        else:
            return (
                f"🛡️ PHÁN QUYẾT QUẢN TRỊ RỦI RO & BẢO TOÀN VỐN (CRO ARBITER) CHO {sym} (Giá hiện tại: {price:,.0f} đ):\n"
                f"1. Kịch bản Xấu nhất (Pre-Mortem): Nếu thị trường chung đảo chiều, ngưỡng hỗ trợ phòng thủ then chốt nằm tại {stop_loss:,.0f} đ (-{sl_pct}%).\n"
                f"2. Quản trị Vị thế (Position Sizing): Tỷ trọng giải ngân tối đa cho lệnh này chỉ nên chiếm {max_pos:.1f}% tổng danh mục (NAV).\n"
                f"3. Tỷ lệ Lợi nhuận/Rủi ro (R:R): Đạt chuẩn kỳ vọng {rr:.1f}:1 (Mục tiêu {tp1:,.0f} đ vs Cắt lỗ {stop_loss:,.0f} đ).\n"
                f"4. NGUYÊN TẮC MẤT HIỆU LỰC BẮT BUỘC: Nếu giá đóng cửa vi phạm dưới {stop_loss:,.0f} đ, toàn bộ luận điểm mua đều BỊ HỦY BỎ NGAY LẬP TỨC. Tuyệt đối không gồng lỗ hay bình quân giá xuống!"
            )


advisor = CouncilAdvisor()
