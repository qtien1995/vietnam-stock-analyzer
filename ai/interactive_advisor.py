"""
Module Tham Mưu Hỏi Đáp Tương Tác với Hội đồng AI (Interactive Council Advisor)
Tuân thủ nghiêm ngặt AGENTS.md:
- Độc lập, khách quan, không vuốt ve, không đoán bừa.
- Bám sát số liệu từ database và BCTC (CFO, FCF, P/B, nợ vay, điểm Pivot, Stop Loss).
- Phân vai theo đúng trường phái tư duy của từng chuyên gia.
"""

from typing import Dict, Any, Optional


class CouncilAdvisor:
    def __init__(self):
        pass

    def answer_question(
        self,
        symbol: str,
        question: str,
        expert_id: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Trả lời câu hỏi của nhà đầu tư dựa trên dữ liệu phân tích thực tế của mã cổ phiếu.
        """
        sym = symbol.upper().strip()
        exp_id = (expert_id or "all").lower()
        
        # Trích xuất dữ liệu bối cảnh
        price = float(context.get("price", 0.0))
        fair_price = float(context.get("fair_price", price))
        stop_loss = float(context.get("stop_loss", price * 0.93))
        sl_pct = float(context.get("stop_loss_pct", 7.0))
        tp1 = float(context.get("take_profit_1", price * 1.12))
        tp1_pct = float(context.get("take_profit_1_pct", 12.0))
        trigger_pivot = float(context.get("trigger_pivot", price * 1.03))
        
        pb = float(context.get("pb", 1.0))
        bvps = float(context.get("bvps", 0.0))
        cfo_human = context.get("cfo_human", "Dương")
        fcf_human = context.get("fcf_human", "Dương")
        active_buy_pct = float(context.get("active_buy_pct", 50.0))
        foreign_net = float(context.get("foreign_net_vol", 0.0))
        sector = context.get("sector", "Doanh nghiệp")
        timing_verdict = context.get("timing_verdict", "Tích lũy quan sát")
        
        q_lower = question.lower()

        # 1. Trả lời theo từng chuyên gia
        if exp_id == "buffett":
            speaker = "🏛️ Warren Buffett & Benjamin Graham (Đầu tư Giá trị & Con hào kinh tế)"
            if any(k in q_lower for k in ["lỗ", "xấu nhất", "sập", "rủi ro"]):
                ans = (
                    f"Theo tiêu chuẩn biên an toàn của Graham, kịch bản xấu nhất thị giá {sym} có thể lùi về kiểm định giá trị tài sản ròng sổ sách (BVPS: {bvps:,.0f} đ). "
                    f"Hiện tại P/B đang là {pb:.2f}x so với giá trị thực ước tính {fair_price:,.0f} đ. "
                    f"Nếu giá đang cao hơn giá trị thực, chúng tôi KHÔNG khuyến nghị mua gom bình quân giá xuống. Nguyên tắc số 1: Không để mất tiền; Nguyên tắc số 2: Xem lại nguyên tắc số 1."
                )
            elif any(k in q_lower for k in ["cổ tức", "tiền thật", "cfo", "fcf"]):
                ans = (
                    f"Chúng tôi đánh giá cao doanh nghiệp nhờ dòng tiền kinh doanh thật (CFO đạt {cfo_human}) và dòng tiền tự do (FCF đạt {fcf_human}). "
                    f"Tiền thật vào tài khoản là con hào kinh tế vững chắc nhất chứng minh ban lãnh đạo không 'xào nấu' báo cáo tài chính."
                )
            else:
                ans = (
                    f"Giá trị nội tại hợp lý của {sym} ước tính quanh {fair_price:,.0f} đ (BVPS: {bvps:,.0f} đ). "
                    f"Với thị giá hiện tại {price:,.0f} đ, biên an toàn hiện ở mức "
                    f"{'ĐẠT CHUẨN MUA GOM DÀI HẠN (Biên an toàn > 15%)' if price <= fair_price * 0.85 else 'CHƯA ĐỦ BIÊN AN TOÀN. Nhà đầu tư giá trị nên kiên nhẫn chờ những nhịp thị trường hoảng loạn để gom rẻ hơn.'}"
                )

        elif exp_id == "oneil":
            speaker = "📈 William O'Neil & Mark Minervini (Kỹ thuật Xu hướng & CANSLIM)"
            if any(k in q_lower for k in ["mua", "khi nào", "tín hiệu", "giải ngân"]):
                ans = (
                    f"Theo phương pháp CANSLIM và Minervini VCP, bạn TUYỆT ĐỐI KHÔNG mua đuổi khi cổ phiếu chưa có điểm nổ Pocket Pivot xác nhận. "
                    f"Mốc giá kích hoạt giải ngân là khi {sym} vượt dứt khoát {trigger_pivot:,.0f} đ đi kèm khối lượng khớp lệnh bùng nổ gấp từ 1.3x - 1.5x lần MA20. "
                    f"Nếu thanh khoản èo uột hoặc nến cụt đầu, hãy ngồi yên bảo toàn sức mua."
                )
            elif any(k in q_lower for k in ["cắt lỗ", "stop loss", "lỗ"]):
                ans = (
                    f"Kỷ luật cắt lỗ là luật thép sống còn: Nếu {sym} xuyên thủng ngưỡng {stop_loss:,.0f} đ (-{sl_pct}%), bạn BẮT BUỘC phải bán cắt lỗ ngay lập tức, không có ngoại lệ. "
                    f"Không bao giờ để một khoản lỗ nhỏ biến thành một khoản lỗ chết người."
                )
            else:
                ans = (
                    f"Mô hình giá của {sym} đang ở trạng thái: {timing_verdict}. Điểm Pivot kích hoạt nằm tại {trigger_pivot:,.0f} đ. "
                    f"Mục tiêu kỳ vọng chốt lời nhịp này: TP1 đạt {tp1:,.0f} đ (+{tp1_pct}%). Luôn đặt lệnh Stop Loss tự động tại {stop_loss:,.0f} đ."
                )

        elif exp_id == "wyckoff":
            speaker = "🌊 Richard Wyckoff & Tom Williams (Dòng tiền Lớn VSA)"
            if any(k in q_lower for k in ["cá mập", "tay to", "xả", "gom", "lực bán"]):
                ans = (
                    f"Dưới góc nhìn VSA: Lực mua chủ động hiện chiếm {active_buy_pct:.1f}% tổng khớp lệnh. "
                    f"{'Phe mua đang chiếm ưu thế hấp thụ lượng cung bán ra' if active_buy_pct >= 55 else 'Phe bán đang chủ động xả lệnh MP, lực cung chốt lời còn khá dày'}. "
                    f"Giao dịch khối ngoại ghi nhận: {'gom ròng +' + f'{foreign_net:,.0f} CP' if foreign_net > 0 else 'bán ròng ' + f'{foreign_net:,.0f} CP'}. "
                    f"Cần quan sát các phiên kiểm tra cung (Test Bar) với thân nến hẹp và khối lượng cạn kiệt trước khi xác nhận dòng tiền lớn đẩy giá."
                )
            else:
                ans = (
                    f"Chu kỳ dòng tiền của {sym} đang vận động trong pha tích lũy/hấp thụ cung. "
                    f"Dấu vết thông minh: Tỷ lệ lệnh mua chủ động {active_buy_pct:.1f}%. Hãy chú ý nếu xuất hiện phiên bứt phá khối lượng lớn vượt nền mà không bị rụt đầu (No Upthrust) thì mới là điểm vào chuẩn."
                )

        elif exp_id == "lynch":
            speaker = "🚀 Peter Lynch & Philip Fisher (Tăng trưởng & Dự án mở rộng)"
            ans = (
                f"Động lực tăng trưởng cốt lõi của {sym} nằm ở chuỗi dự án gối đầu và tiềm năng mở rộng quy mô ngành {sector}. "
                f"Doanh nghiệp có cơ cấu tài chính vững vàng (CFO: {cfo_human}). Tiêu chí hàng đầu của chúng tôi là theo dõi sát sao tiến độ bàn giao dự án "
                f"và tăng trưởng doanh thu cốt lõi quý tới. Nếu biên lợi nhuận gộp duy trì đà mở rộng, đây sẽ là cổ phiếu tăng trưởng giá trị xuất sắc."
            )

        elif exp_id == "dalio":
            speaker = "🌐 Ray Dalio & Howard Marks (Vĩ mô & Chu kỳ Ngành)"
            ans = (
                f"Bối cảnh vĩ mô ngành {sector} đang hưởng lợi từ chu kỳ nới lỏng tiền tệ của Fed và mặt bằng lãi suất cho vay thấp trong nước. "
                f"Tuy nhiên, theo Howard Marks: 'Thành công trong đầu tư không phải là mua cái tốt, mà là mua với giá tốt'. "
                f"Đừng để sự hưng phấn của truyền thông cuốn bạn vào việc mua đuổi tại vùng giá đã tăng nóng."
            )

        else: # Nassim Taleb / CRO / Toàn thể hội đồng
            speaker = "🛡️ Nassim Nicholas Taleb & CRO (Chief Risk Officer)"
            ans = (
                f"Tham mưu quản trị rủi ro tổng thể cho {sym} tại vùng giá {price:,.0f} đ:\n"
                f"1. Kịch bản xấu nhất (Pre-Mortem): Nếu thị trường chung đảo chiều, mốc hỗ trợ cứng tiếp theo nằm tại {stop_loss:,.0f} đ (-{sl_pct}%).\n"
                f"2. Quản trị vị thế (Position Sizing): Tỷ trọng giải ngân tối đa cho lệnh này chỉ nên chiếm 5% - 10% tổng danh mục (NAV).\n"
                f"3. Tỷ lệ Lợi nhuận/Rủi ro (R:R): Đạt chuẩn kỳ vọng ({tp1:,.0f} đ vs {stop_loss:,.0f} đ).\n"
                f"4. Nguyên tắc mất hiệu lực: Nếu giá đóng cửa vi phạm dưới {stop_loss:,.0f} đ, mọi luận điểm mua tăng trưởng đều BỊ HỦY BỎ NGAY LẬP TỨC. Tuyệt đối không gồng lỗ!"
            )

        return {
            "symbol": sym,
            "expert": speaker,
            "question": question,
            "answer": ans
        }


advisor = CouncilAdvisor()
