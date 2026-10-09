from pathlib import Path
from typing import Dict, Any
from config import PROMPTS_DIR
from ai.llm_router import LLMRouter


def _load_prompt(filename: str) -> str:
    path = PROMPTS_DIR / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


class InvestmentCouncil:
    """
    Hội đồng đầu tư AI đa góc nhìn (Multi-Agent Council):
    - Warren Buffett (Giá trị & Moat)
    - Peter Lynch (GARP & PEG)
    - William O'Neil (CANSLIM & Breakout)
    - Price Action & VSA (Dòng tiền lớn)
    - Chief Risk Officer (Phán quyết & Rủi ro)
    """

    def __init__(self, router: LLMRouter = None):
        self.router = router or LLMRouter()
        self.buffett_prompt = _load_prompt("buffett.md")
        self.lynch_prompt = _load_prompt("lynch.md")
        self.oneil_prompt = _load_prompt("oneil.md")
        self.vsa_prompt = _load_prompt("vsa.md")
        self.cro_prompt = _load_prompt("cro_arbiter.md")

    def deliberate(
        self,
        symbol: str,
        quote: Dict[str, Any],
        fa: Dict[str, Any],
        ta: Dict[str, Any],
        trade_setup: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Tổ chức phiên phản biện và tổng hợp luận điểm của 4 nhà đầu tư huyền thoại
        cùng Giám đốc Quản trị rủi ro.
        """
        # Chuẩn bị bản tóm tắt dữ liệu thị trường
        fin = fa.get("ratios", {})
        ind = ta.get("indicators", {})
        sector = fa.get("sector", "GENERAL")
        growth_qual = fa.get("growth_quality", {})
        val_warning = fa.get("valuation_warning", "")
        
        asset_val = fa.get("asset_valuation", {})
        segments_data = fa.get("segments", {})
        gov = fa.get("governance", {})
        own = gov.get("ownership", {})
        lead = gov.get("leadership", {})
        sub_web = gov.get("subsidiary_web", {})
        
        seg_summary = "\n[Bóc tách Mô hình Kinh doanh Cốt lõi & Phân khúc]:\n"
        seg_summary += f"- Tổng quan: {segments_data.get('business_model_summary', 'N/A')}\n"
        for s in segments_data.get("segments", []):
            seg_summary += f"  + {s.get('name')}: Chiếm {s.get('rev_share_pct')}% DT, {s.get('gross_profit_share_pct')}% Lợi nhuận gộp (Biên gộp: {s.get('gross_margin_pct')}%) | Vai trò: {s.get('role')}\n"

        top_sh_str = ", ".join([f"{s['name']} ({s['percentage']}%)" for s in own.get("top_shareholders", [])[:4]])
        gov_summary = f"""
[Quản trị Doanh nghiệp, Cổ đông & Mạng lưới Công ty con]:
- Điểm Quản trị (G-Score): {gov.get('g_score', 'N/A')}/100 ({gov.get('g_rating', 'N/A')})
- Cơ cấu sở hữu: {own.get('structure', 'N/A')}
- Trôi nổi (Free Float): {own.get('free_float_pct', 0)}% | Khối ngoại: {own.get('foreigner_pct', 0)}% | Nhà nước: {own.get('state_pct', 0)}%
- Cổ đông chủ chốt: {top_sh_str if top_sh_str else 'Chưa có dữ liệu'}
- Ban điều hành: Chủ tịch: {lead.get('chairman', 'Chưa rõ')} | CEO: {lead.get('ceo', 'Chưa rõ')}
- Tỷ lệ sở hữu của Ban Lãnh đạo (Skin in the game): {lead.get('insider_total_pct', 0)}% ({lead.get('skin_in_game_verdict', 'N/A')})
- Mạng lưới chân rết: {sub_web.get('subsidiary_count', 0)} công ty con, {sub_web.get('affiliate_count', 0)} công ty liên kết ({sub_web.get('conglomerate_type', 'N/A')})
- Radar Tăng vốn ảo & Trái phiếu hệ sinh thái: {sub_web.get('circular_capital_verdict', 'N/A')}
"""

        context_data = f"""
=== DỮ LIỆU THỰC TẾ CỔ PHIẾU {symbol} ({quote.get('company_name', symbol)}) ===
- Ngành nghề định giá: {sector}
- Giá khớp lệnh Realtime: {quote.get('price', 0):,.0f} VND (Biến động: {quote.get('change_pct', 0)}%)
- Khối lượng giao dịch: {quote.get('volume', 0):,.0f} CP (Gấp {ind.get('vol_ratio', 1.0):.2f}x lần MA20)
- Khối ngoại ròng: {quote.get('foreign_net_vol', 0):,.0f} CP

[Định giá theo Khối tài sản & Radar Thao túng / Bẫy giá trị]:
- Giá trị sổ sách mỗi cổ phiếu (BVPS): {asset_val.get('bvps', 0):,.0f} VND
- P/B thực tế: {asset_val.get('pb', 'N/A')}x | Chiết khấu tài sản: {asset_val.get('asset_discount_pct', 0)}%
- Tiền mặt ròng/CP: {asset_val.get('net_cash_per_share', 0):,.0f} VND
- Cấp độ rủi ro thao túng / thổi giá / bẫy giá trị: Cấp {asset_val.get('manipulation_risk_level', 1)}/5 ({asset_val.get('manipulation_verdict', 'N/A')})
- Chất lượng tài sản: {asset_val.get('asset_quality_verdict', 'N/A')} (Tỷ lệ đọng vốn Phải thu + Tồn kho: {asset_val.get('illiquid_ratio', 0)}%)
{gov_summary}
[Chỉ số Cơ bản - FA]:
- P/E: {fin.get('pe', 'N/A')} | P/B: {fin.get('pb', 'N/A')}
- ROE: {fin.get('roe', 'N/A')}% | ROA: {fin.get('roa', 'N/A')}%
- Biên lợi nhuận gộp: {fin.get('gross_margin', 'N/A')}% | Biên ròng: {fin.get('net_margin', 'N/A')}%
- Tỷ lệ Nợ vay/Vốn CSH: {fin.get('debt_to_equity', 'N/A')}
- Tăng trưởng LNST: {fin.get('profit_growth', 'N/A')}% | Tăng trưởng Doanh thu: {fin.get('revenue_growth', 'N/A')}%
- Đánh giá chất lượng tăng trưởng: {growth_qual.get('quality', 'Bình thường')}
- Cảnh báo định giá: {val_warning if val_warning else 'Không có'}
- Piotroski F-Score: {fa.get('f_score', 'N/A')}/9 điểm
- Peter Lynch PEG: {fa.get('lynch', {}).get('peg', 'N/A')}
{seg_summary}
[Chỉ số Kỹ thuật - TA]:
- EMA20: {ind.get('ema20', 0):,.0f} | EMA50: {ind.get('ema50', 0):,.0f}
- RSI 14: {ind.get('rsi14', 50):.1f}
- Hỗ trợ gần nhất: {ind.get('sup_20d', 0):,.0f} | Kháng cự gần nhất: {ind.get('res_20d', 0):,.0f}
- Trạng thái xu hướng: {'Downtrend ngắn/trung hạn' if trade_setup.get('in_downtrend') else 'Ổn định / Tích lũy'}
- Khối ngoại bán mạnh: {'CÓ' if trade_setup.get('heavy_foreign_sell') else 'Bình thường'}
- Pha thị trường Wyckoff: {ta.get('vsa', {}).get('phase', 'Tích lũy')}
- Tín hiệu Breakout: {'CÓ (Nổ vol)' if ta.get('oneil', {}).get('is_breakout') else 'Chưa bứt phá'}

[Thiết lập Giao dịch Đề xuất]:
- Vùng mua (Buy Zone): {trade_setup.get('buy_zone')} VND
- Điểm cắt lỗ (Stop Loss): {trade_setup.get('stop_loss', 0):,.0f} VND (-{trade_setup.get('stop_loss_pct', 0)}%)
- Mục tiêu chốt lời 1: {trade_setup.get('take_profit_1', 0):,.0f} VND (+{trade_setup.get('take_profit_1_pct', 0)}%)
- Mục tiêu chốt lời 2: {trade_setup.get('take_profit_2', 0):,.0f} VND (+{trade_setup.get('take_profit_2_pct', 0)}%)
- Tỷ lệ Risk/Reward (R:R): {trade_setup.get('risk_reward_ratio', 2.0)}:1
- Tỷ trọng tối đa: {trade_setup.get('max_position_size_pct', 10.0)}% NAV

"""

        # Nếu có LLM Provider trực tuyến và phản hồi tốt
        ai_deliberation = ""
        if self.router.provider != "offline":
            try:
                system_instruction = (
                    "Bạn là Trưởng ban Điều phối Hội đồng Tham mưu Đầu tư TTCK Việt Nam. "
                    "Hãy tuân thủ nghiêm ngặt quy chuẩn: Không mạo danh người thật, dùng danh xưng theo 'trường phái tư duy' "
                    "(ví dụ: Theo trường phái giá trị, Theo trường phái tăng trưởng, Theo trường phái dòng tiền...). "
                    "Hãy phân tích 5 góc nhìn: 1. Giá trị & Khối tài sản thật, 2. Tăng trưởng & Bóc tách Core Business, 3. Kỹ thuật, 4. Vĩ mô & Chu kỳ, 5. Quản trị rủi ro & Radar Thao túng. "
                    "Đặc biệt: Bóc tách rõ các mảng kinh doanh (Thủy điện, Xây lắp, BĐS... mảng nào là Cash Cow, mảng nào tạo DT lớn), "
                    "và đánh giá thị giá so với giá trị tài sản thật (BVPS, P/B) xem có bị thổi giá hay có biên an toàn."
                )
                ai_deliberation = self.router.generate(system_instruction, context_data)
            except Exception:
                ai_deliberation = ""

        # Nếu không có LLM hoặc AI trả về trống, sử dụng bộ giải trình định lượng chuẩn mực
        if not ai_deliberation:
            ai_deliberation = self._generate_rule_based_deliberation(symbol, quote, fa, ta, trade_setup)

        return {
            "symbol": symbol,
            "context_data": context_data,
            "council_report": ai_deliberation
        }

    def _generate_rule_based_deliberation(
        self,
        symbol: str,
        quote: Dict[str, Any],
        fa: Dict[str, Any],
        ta: Dict[str, Any],
        trade_setup: Dict[str, Any]
    ) -> str:
        """Sinh báo cáo phản biện đa góc nhìn chất lượng cao từ Engine định lượng"""
        buffett = fa.get("buffett", {})
        lynch = fa.get("lynch", {})
        oneil = ta.get("oneil", {})
        vsa = ta.get("vsa", {})
        growth_qual = fa.get("growth_quality", {})
        val_warning = fa.get("valuation_warning", "")
        asset_val = fa.get("asset_valuation", {})
        seg_data = fa.get("segments", {})

        report = f"""### 1. 🏛️ Góc nhìn Warren Buffett (Đầu tư Giá trị & Định giá Khối tài sản ròng)
* **Phán quyết:** **{buffett.get('verdict', 'QUAN SÁT')}** (Điểm số: {buffett.get('score', 0)}/100)
* **Luận điểm cốt lõi về Tài sản & Con hào kinh tế:**
"""
        for r in buffett.get("reasons", []):
            report += f"  - {r}\n"
        
        # Thêm luận điểm tài sản & radar thao túng
        bvps = asset_val.get("bvps", 0)
        pb = asset_val.get("pb", 1.0)
        report += f"  - **Khối tài sản ròng thực tế (BVPS):** {bvps:,.0f} VND/CP. Thị giá hiện tại ({trade_setup.get('current_price', 0):,.0f} VND) tương ứng P/B **{pb:.2f}x**.\n"
        for ar in asset_val.get("reasons", []):
            report += f"  - {ar}\n"
        report += f"  - *Giá trị hợp lý ước tính:* {buffett.get('fair_price', 0):,.0f} VND (Biên an toàn: {buffett.get('margin_of_safety_pct', 0)}%)\n"
        
        # Thêm kiểm định Liêm chính ban lãnh đạo (Management Integrity) theo Buffett
        gov = fa.get("governance", {})
        lead = gov.get("leadership", {})
        own = gov.get("ownership", {})
        sub_web = gov.get("subsidiary_web", {})

        if lead.get("legal_governance_flags") or gov.get("g_score", 100) < 40:
            report += "  - 🚨 *Tiêu chuẩn Liêm chính Ban Lãnh đạo (Management Integrity):* VI PHẠM NGHIÊM TRỌNG. Warren Buffett khẳng định: 'Không thể có một thương vụ tốt với người quản trị tồi'. Doanh nghiệp có dấu hiệu sở hữu mờ ám qua các công ty TNHH cá nhân hoặc có biến cố pháp lý/nợ BCTC, trường phái giá trị LOẠI BỎ NGAY LẬP TỨC khỏi danh mục.\n"

        if val_warning:
            report += f"  - ⚠️ *Cảnh báo định giá:* {val_warning}\n"
        report += "\n"

        report += f"""### 2. 📈 Góc nhìn Peter Lynch & Bóc tách Hoạt động Cốt lõi (Core Business)
* **Phán quyết:** **{lynch.get('verdict', 'THEO DÕI')}** (Điểm số: {lynch.get('score', 0)}/100)
* **Mô hình hoạt động cốt lõi:** {seg_data.get('business_model_summary', 'N/A')}
* **Bóc tách Cơ cấu Phân khúc Kinh doanh (Segment Breakdown):**
"""
        for seg in seg_data.get("segments", []):
            report += f"  * **{seg.get('name')}:** Chiếm **{seg.get('rev_share_pct')}% Doanh thu**, đóng góp **{seg.get('gross_profit_share_pct')}% Lợi nhuận gộp** (Biên lãi gộp: `{seg.get('gross_margin_pct')}%`).\n"
            report += f"    - *Vai trò:* {seg.get('role')} | *Trạng thái:* {seg.get('status')}\n"
            report += f"    - *Điểm nhấn:* {seg.get('highlights')}\n"
            report += f"    - *Rủi ro:* {seg.get('risks')}\n"

        report += "\n* **Chất lượng tăng trưởng & Hệ số PEG:**\n"
        for r in lynch.get("reasons", []):
            report += f"  - {r}\n"
        for r in growth_qual.get("reasons", []):
            report += f"  - {r}\n"
        report += f"  - *Hệ số định giá PEG:* {lynch.get('peg', 1.0)}x\n\n"

        report += f"""### 3. 🚀 Góc nhìn William O'Neil & Mark Minervini (CANSLIM & Xu hướng giá)
* **Phán quyết:** **{oneil.get('verdict', 'QUAN SÁT')}** (Điểm số: {oneil.get('score', 0)}/100)
* **Luận điểm cốt lõi:**
"""
        for r in oneil.get("reasons", []):
            report += f"  - {r}\n"
        if trade_setup.get("in_downtrend"):
            report += "  - ⚠️ *Cảnh báo xu hướng:* Giá đang nằm dưới EMA20 và EMA50, tuyệt đối không bắt dao rơi khi chưa xuất hiện nến tạo đáy đảo chiều.\n"
        report += f"  - *Khối lượng giao dịch:* Gấp {oneil.get('vol_ratio', 1.0):.2f}x lần mức trung bình 20 phiên\n\n"

        report += f"""### 4. 📊 Góc nhìn Price Action & Wyckoff VSA (Dòng tiền lớn)
* **Phán quyết:** **{vsa.get('verdict', 'TRUNG LẬP')}** (Điểm số: {vsa.get('score', 0)}/100)
* **Pha chu kỳ thị trường:** {vsa.get('phase', 'Tích lũy')}
* **Luận điểm cốt lõi:**
"""
        for r in vsa.get("reasons", []):
            report += f"  - {r}\n"
        if trade_setup.get("heavy_foreign_sell"):
            report += f"  - ⚠️ *Dòng tiền ngoại:* Khối ngoại bán ròng đột biến {quote.get('foreign_net_vol', 0):,.0f} CP, cần chờ hấp thụ hết cung giá rẻ.\n"
        report += f"  - *Chỉ số RSI 14:* {vsa.get('rsi', 50)}\n\n"

        report += f"""### 5. 👥 Bóc tách Quản trị Doanh nghiệp, Cổ đông & Mạng lưới Công ty con (Corporate Governance & Shell Radar)
* **Điểm Quản trị (G-Score):** **{gov.get('g_score', 'N/A')}/100** ({gov.get('g_rating', 'N/A')})
* **Cơ cấu Sở hữu & Cổ đông:**
  - **Mô hình:** {own.get('structure', 'N/A')}
  - *Tỷ lệ trôi nổi (Free Float):* `{own.get('free_float_pct', 0)}%` | *Khối ngoại:* `{own.get('foreigner_pct', 0)}%` | *Nhà nước:* `{own.get('state_pct', 0)}%`
  - *Đặc điểm:* {own.get('description', 'N/A')}
"""
        for sh in own.get("top_shareholders", [])[:5]:
            report += f"  - Cổ đông: **{sh.get('name')}** nắm **{sh.get('percentage')}%** ({sh.get('shares', 0):,.0f} CP)\n"

        report += f"""* **Hội đồng Quản trị & Ban Điều hành:**
  - **Chủ tịch HĐQT:** {lead.get('chairman', 'Chưa rõ')}
  - **Tổng Giám đốc (CEO):** {lead.get('ceo', 'Chưa rõ')}
  - **Mức độ cam kết vốn (Skin in the game):** `{lead.get('insider_total_pct', 0)}%` — {lead.get('skin_in_game_verdict', 'N/A')} ({lead.get('skin_in_game_note', '')})
"""
        for flag in lead.get("legal_governance_flags", []):
            report += f"  - {flag}\n"

        report += f"""* **Mạng lưới Công ty con & Radar Tăng vốn ảo / Trái phiếu hệ sinh thái:**
  - **Quy mô mạng lưới:** {sub_web.get('subsidiary_count', 0)} công ty con & {sub_web.get('affiliate_count', 0)} công ty liên kết ({sub_web.get('conglomerate_type', 'N/A')}).
  - **Phán quyết Radar:** **{sub_web.get('circular_capital_verdict', 'N/A')}**
"""
        for cnote in sub_web.get("circular_capital_notes", []):
            report += f"  - {cnote}\n"
        report += "\n"

        report += f"""### 6. ⚖️ Phán quyết của Chief Risk Officer (Giám đốc Quản trị rủi ro & Radar Thao túng)
* **TÍN HIỆU THỰC THI:** **{trade_setup.get('action')}** (Độ đồng thuận: {trade_setup.get('consensus_score')}/100 điểm)
* **Radar Phát hiện Thao túng / Bẫy giá trị:** **Cấp độ {asset_val.get('manipulation_risk_level', 1)}/5: {asset_val.get('manipulation_verdict', 'AN TOÀN')}**
* **Kiểm định Chất lượng Tài sản:** {asset_val.get('asset_quality_verdict', 'Lành mạnh')}
"""
        for n in asset_val.get("asset_quality_notes", []):
            report += f"  - {n}\n"

        report += f"""* **Kế hoạch hành động cụ thể:**
  * **Vùng mua khuyến nghị (Buy Zone):** `{trade_setup.get('buy_zone')}` VND
  * **Điểm cắt lỗ nghiêm ngặt (Stop Loss):** `{trade_setup.get('stop_loss', 0):,.0f}` VND (Chặn lỗ tối đa `-{trade_setup.get('stop_loss_pct', 0)}%`)
  * **Tỷ trọng phân bổ tối đa:** `{trade_setup.get('max_position_size_pct', 10.0):.1f}% NAV` (Nguyên tắc bảo toàn vốn cá nhân)
  * **Mục tiêu chốt lời 1 (TP1):** `{trade_setup.get('take_profit_1', 0):,.0f}` VND (`+{trade_setup.get('take_profit_1_pct', 0)}%`)
  * **Mục tiêu chốt lời 2 (TP2):** `{trade_setup.get('take_profit_2', 0):,.0f}` VND (`+{trade_setup.get('take_profit_2_pct', 0)}%`)
  * **Tỷ lệ Risk / Reward (R:R):** `{trade_setup.get('risk_reward_ratio')}:1` (Đạt chuẩn an toàn vốn)
"""
        return report

