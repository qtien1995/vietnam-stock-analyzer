"""
Module Quản lý Thư viện Prompts Tập Trung (Prompt Library Registry)
Tích hợp và bản địa hóa kho tri thức từ prompts.chat (Awesome ChatGPT Prompts):
- 6 Trường phái Hội đồng Cốt lõi (Buffett, Lynch, O'Neil, Wyckoff, Dalio, CRO)
- 5 Chuyên gia Phân tích Mở rộng (PE Fund Manager, DeepThink Red Team, Forensic Accountant, Stress-Tester, Unit Economics)
- Bộ câu hỏi 1-Click mẫu theo chuẩn Prompt Engineering
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
from config import PROMPTS_DIR


PERSONA_CATALOG: Dict[str, Dict[str, Any]] = {
    "buffett": {
        "id": "buffett",
        "name": "Warren Buffett & Benjamin Graham",
        "title": "Đầu tư Giá trị & Con hào Kinh tế",
        "badge": "🏛️ GIÁ TRỊ",
        "badge_color": "#10b981",
        "category": "core",
        "filename": "buffett.md",
        "description": "Thẩm định con hào kinh tế (Moat), biên an toàn (Margin of Safety), P/B so với giá trị sổ sách BVPS và năng lực sinh tiền thật.",
        "sample_questions": [
            "Biên an toàn hiện tại có đủ hấp dẫn để mua tích sản nắm giữ 3-5 năm không?",
            "Chất lượng tài sản và con hào kinh tế của doanh nghiệp có bền vững không?",
            "Ban lãnh đạo có liêm chính và thực sự cam kết gắn bó quyền lợi (Skin in the game) không?"
        ]
    },
    "lynch": {
        "id": "lynch",
        "name": "Peter Lynch & Philip Fisher",
        "title": "Tăng trưởng Chất lượng & GARP",
        "badge": "🚀 TĂNG TRƯỞNG",
        "badge_color": "#38bdf8",
        "category": "core",
        "filename": "lynch.md",
        "description": "Bóc tách mô hình kinh doanh cốt lõi (Core Business), phân khúc tạo dòng tiền, hệ số định giá PEG và chuỗi dự án gối đầu.",
        "sample_questions": [
            "Cổ phiếu này thuộc nhóm nào trong 6 loại của Peter Lynch và hệ số PEG hiện tại ra sao?",
            "Mảng kinh doanh nào đang là động lực tăng trưởng cốt lõi đóng góp lợi nhuận lớn nhất?",
            "Dự án gối đầu nào có tiềm năng tạo đột biến doanh thu trong 2-4 quý tới?"
        ]
    },
    "oneil": {
        "id": "oneil",
        "name": "William O'Neil & Mark Minervini",
        "title": "Kỹ thuật Xu hướng & CANSLIM SEPA",
        "badge": "📈 KỸ THUẬT",
        "badge_color": "#a855f7",
        "category": "core",
        "filename": "oneil.md",
        "description": "Đọc cấu trúc xu hướng Trend Template, mẫu hình thu hẹp biến động VCP, điểm nổ Pocket Pivot và thiết lập cắt lỗ nghiêm ngặt 7%.",
        "sample_questions": [
            "Cổ phiếu có thỏa mãn Trend Template hay đang nằm trong xu hướng giảm bắt dao rơi?",
            "Điểm mua Pivot kích hoạt giải ngân chuẩn xác nằm ở mốc giá nào kèm điều kiện khối lượng gì?",
            "Ngưỡng cắt lỗ kỷ luật thép 7% nằm ở mốc giá cụ thể nào để bảo vệ tài khoản?"
        ]
    },
    "wyckoff": {
        "id": "wyckoff",
        "name": "Richard Wyckoff & Tom Williams",
        "title": "Dòng tiền Lớn & Wyckoff VSA",
        "badge": "🌊 DÒNG TIỀN VSA",
        "badge_color": "#06b6d4",
        "category": "core",
        "filename": "vsa.md",
        "description": "Đọc dấu chân Smart Money qua tương quan Thân nến - Khối lượng (VSA), nhận diện pha Tích lũy/Phân phối và tỷ lệ lệnh mua chủ động.",
        "sample_questions": [
            "Dòng tiền lớn đang ở pha gom hàng tích lũy hay âm thầm xả hàng phân phối?",
            "Tỷ lệ lệnh mua chủ động và động thái khối ngoại phiên gần nhất phản ánh điều gì?",
            "Có xuất hiện thanh nến kiểm tra cung (Test Bar/No Supply) xác nhận cạn cung hay không?"
        ]
    },
    "dalio": {
        "id": "dalio",
        "name": "Ray Dalio & Howard Marks",
        "title": "Vĩ mô & Chu kỳ Kinh tế",
        "badge": "🌐 VĨ MÔ & CHU KỲ",
        "badge_color": "#f59e0b",
        "category": "core",
        "filename": "dalio_marks.md",
        "description": "Định vị vị thế ngành trong chu kỳ vĩ mô, đánh giá gió xuôi/gió ngược (lãi suất, tỷ giá, đầu tư công) và cảnh báo bẫy định giá đỉnh chu kỳ.",
        "sample_questions": [
            "Ngành nghề của doanh nghiệp đang ở pha nào trong chu kỳ kinh tế lớn?",
            "Môi trường lãi suất và tỷ giá USD/VND hiện tại đang là gió xuôi hay gió ngược với doanh nghiệp?",
            "Có nguy cơ mắc bẫy P/E đỉnh chu kỳ hoặc cơ hội gom hàng P/B đáy chu kỳ không?"
        ]
    },
    "taleb_cro": {
        "id": "taleb_cro",
        "name": "Nassim Taleb & CRO Arbiter",
        "title": "Quản trị Rủi ro & Trọng tài Đầu tư",
        "badge": "🛡️ BẢO VỆ VỐN",
        "badge_color": "#ef4444",
        "category": "core",
        "filename": "cro_arbiter.md",
        "description": "Trọng tài phán quyết: Bắt buộc tỷ lệ Risk/Reward >= 2:1, phân bổ vị thế tối đa % NAV, phân tích tử thi giả định (Pre-Mortem) kịch bản xấu nhất.",
        "sample_questions": [
            "Kịch bản xấu nhất (Pre-Mortem) nếu thương vụ này thua lỗ thì nguyên nhân là gì?",
            "Tỷ lệ Lợi nhuận/Rủi ro (R:R) và tỷ trọng giải ngân tối đa (% NAV) tham khảo là bao nhiêu?",
            "Điều kiện kích hoạt bán cắt lỗ dứt khoát không thương lượng là gì?"
        ]
    },
    "pe_fund": {
        "id": "pe_fund",
        "name": "Elite Private Equity Fund Manager",
        "title": "Thẩm định Quỹ PE 8 Tiêu chí",
        "badge": "🏢 PE FUND",
        "badge_color": "#14b8a6",
        "category": "extended",
        "filename": "pe_fund_manager.md",
        "description": "Thẩm định toàn diện 8 chiều theo chuẩn quỹ đầu tư quốc tế: Dòng tiền săn mồi, điểm số cơ bản hardcore, xúc tác ngành, win-rate và kế hoạch vốn.",
        "sample_questions": [
            "Chấm điểm cơ bản hardcore (thang 10) về tăng trưởng, ROE và tỷ lệ nợ vay?",
            "Dòng tiền cá mập và cơ cấu trôi nổi (Free Float) của cổ phiếu đang ủng hộ xu hướng nào?",
            "Đánh giá xác suất thắng (Win-Rate) và tỷ lệ Lợi nhuận/Rủi ro cho lệnh này?"
        ]
    },
    "red_team": {
        "id": "red_team",
        "name": "DeepThink Critical Analyst",
        "title": "Phản biện Độc lập & Red Team",
        "badge": "🥊 RED TEAM",
        "badge_color": "#e11d48",
        "category": "extended",
        "filename": "critical_thinker.md",
        "description": "Tấn công tàn nhẫn vào luận điểm tăng giá, vạch trần điểm mù, kiểm tra thiên kiến xác nhận và tìm ra lý do khiến khoản đầu tư thất bại.",
        "sample_questions": [
            "Vạch trần toàn bộ điểm mù và 3 lý do lớn nhất khiến thương vụ mua này có thể thất bại?",
            "Doanh nghiệp có dấu hiệu 'bán giấy lấy tiền', tăng vốn ảo hoặc chuyển lợi nhuận sang công ty con?",
            "Nếu thị trường gãy hỗ trợ và kẹt T+2.5, mức sụt giảm tối đa có thể lên tới bao nhiêu?"
        ]
    },
    "forensic": {
        "id": "forensic",
        "name": "Forensic Financial Auditor",
        "title": "Kiểm toán Pháp y BCTC & Dòng tiền",
        "badge": "🔍 PHÁP Y BCTC",
        "badge_color": "#8b5cf6",
        "category": "extended",
        "filename": "forensic_accountant.md",
        "description": "Soi mói Báo cáo Lưu chuyển Tiền tệ, độ lệch CFO vs LNST, tỷ lệ đọng vốn Khoản phải thu + Tồn kho, kiểm định chỉ số kiệt quệ Altman Z-Score.",
        "sample_questions": [
            "Dòng tiền kinh doanh thật (CFO) có đồng pha với Lợi nhuận sau thuế (LNST) hay có dấu hiệu xào nấu?",
            "Tỷ lệ đọng vốn Khoản phải thu và Tồn kho có đang bào mòn thanh khoản của doanh nghiệp?",
            "Chỉ số Altman Z-Score và nguy cơ kiệt quệ tài chính của doanh nghiệp ở mức nào?"
        ]
    },
    "stress_test": {
        "id": "stress_test",
        "name": "Business Risk & Scenario Stress-Tester",
        "title": "Mô phỏng 3 Kịch bản & Độ nhạy",
        "badge": "📉 STRESS-TEST",
        "badge_color": "#d97706",
        "category": "extended",
        "filename": "scenario_stress_test.md",
        "description": "Mô phỏng 3 kịch bản Bull / Base / Bear, phân tích độ nhạy với Lãi suất và Tỷ giá, xác định rõ điều kiện làm luận điểm mất hiệu lực.",
        "sample_questions": [
            "Mô phỏng 3 kịch bản giá mục tiêu (Tích cực / Cơ sở / Tiêu cực) và xác suất tương ứng?",
            "Biến số kinh tế nào (lãi suất, tỷ giá, giá đầu vào) có độ nhạy lớn nhất tới định giá?",
            "Những sự kiện cụ thể nào sẽ kích hoạt điều kiện mất hiệu lực toàn bộ kế hoạch nắm giữ?"
        ]
    },
    "unit_economics": {
        "id": "unit_economics",
        "name": "Revenue Model & Unit Economics",
        "title": "Bóc tách Mô hình Doanh thu & Biên lãi",
        "badge": "🔬 KINH TẾ ĐƠN VỊ",
        "badge_color": "#6366f1",
        "category": "extended",
        "filename": "unit_economics_core.md",
        "description": "Mổ xẻ cỗ máy tạo tiền: Biên lợi nhuận gộp từng phân khúc, mảng Cash Cow, năng lực định giá (Pricing Power) và điểm nghẽn mở rộng quy mô.",
        "sample_questions": [
            "Bóc tách doanh thu và biên lợi nhuận gộp từng phân khúc kinh doanh của doanh nghiệp?",
            "Doanh nghiệp có năng lực định giá (Pricing Power) để chuyển chi phí đầu vào sang khách hàng không?",
            "Điểm nghẽn lớn nhất (Bottleneck) cản trở doanh nghiệp mở rộng quy mô kinh doanh là gì?"
        ]
    }
}


class PromptLibrary:
    """Thư viện Quản lý Prompts thông minh kết hợp kho prompts.chat"""

    @staticmethod
    def get_prompt_content(filename_or_id: str) -> str:
        """Đọc nội dung file prompt từ thư mục prompts"""
        # Nếu truyền id, tìm tên file trong catalog
        filename = filename_or_id
        if filename_or_id in PERSONA_CATALOG:
            filename = PERSONA_CATALOG[filename_or_id]["filename"]

        if not filename.endswith(".md"):
            filename = f"{filename}.md"

        path = PROMPTS_DIR / filename
        if path.exists():
            return path.read_text(encoding="utf-8")
        return ""

    @staticmethod
    def list_personas(category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Lấy danh sách tất cả các persona trong catalog kèm câu hỏi gợi ý"""
        res = []
        for p in PERSONA_CATALOG.values():
            if category and p.get("category") != category:
                continue
            res.append(p)
        return res

    @staticmethod
    def get_persona(persona_id: str) -> Optional[Dict[str, Any]]:
        """Lấy thông tin chi tiết của một persona"""
        pid = (persona_id or "").lower().strip()
        # Aliases mapping
        alias_map = {
            "cro": "taleb_cro",
            "taleb": "taleb_cro",
            "vsa": "wyckoff",
            "dalio_marks": "dalio",
            "pe": "pe_fund",
            "pe_fund_manager": "pe_fund",
            "deepthink": "red_team",
            "critical": "red_team",
            "accountant": "forensic",
            "audit": "forensic",
            "scenario": "stress_test",
            "unit": "unit_economics"
        }
        actual_id = alias_map.get(pid, pid)
        return PERSONA_CATALOG.get(actual_id)

    @staticmethod
    def build_prompt_payload(
        persona_id: str,
        symbol: str,
        context: Dict[str, Any],
        custom_question: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Chuẩn bị System Instruction và User Prompt đầy đủ theo chuẩn prompts.chat
        """
        persona = PromptLibrary.get_persona(persona_id) or PERSONA_CATALOG["taleb_cro"]
        system_content = PromptLibrary.get_prompt_content(persona["filename"])

        # Trích xuất dữ liệu tài chính từ context
        price = float(context.get("price", 0.0))
        fair_price = float(context.get("fair_price", price))
        stop_loss = float(context.get("stop_loss", price * 0.93))
        sl_pct = float(context.get("stop_loss_pct", 7.0))
        tp1 = float(context.get("take_profit_1", price * 1.12))
        tp1_pct = float(context.get("take_profit_1_pct", 12.0))
        pb = float(context.get("pb", 1.0))
        bvps = float(context.get("bvps", 0.0))
        cfo_human = context.get("cfo_human", "Dương")
        fcf_human = context.get("fcf_human", "Dương")
        active_buy_pct = float(context.get("active_buy_pct", 50.0))
        foreign_net = float(context.get("foreign_net_vol", 0.0))
        sector = context.get("sector", "Doanh nghiệp")
        timing_verdict = context.get("timing_verdict", "Tích lũy quan sát")

        user_content = f"""
=== DỮ LIỆU ĐỊNH LƯỢNG THỰC TẾ MÃ CỔ PHIẾU {symbol.upper()} ===
- Ngành nghề cốt lõi: {sector}
- Thị giá hiện tại: {price:,.0f} VND
- Giá trị hợp lý ước tính (Fair Value): {fair_price:,.0f} VND
- Giá trị sổ sách mỗi cổ phiếu (BVPS): {bvps:,.0f} VND | P/B: {pb:.2f}x
- Dòng tiền kinh doanh thuần (CFO): {cfo_human} | Dòng tiền tự do (FCF): {fcf_human}
- Tỷ lệ khớp lệnh Mua chủ động: {active_buy_pct:.1f}% | Khối ngoại ròng: {foreign_net:,.0f} CP
- Trạng thái kỹ thuật: {timing_verdict}
- Ngưỡng cắt lỗ kỷ luật: {stop_loss:,.0f} VND (-{sl_pct}%)
- Mục tiêu chốt lời 1 (TP1): {tp1:,.0f} VND (+{tp1_pct}%)

CÂU HỎI / YÊU CẦU PHÂN TÍCH TỪ NHÀ ĐẦU TƯ:
"{custom_question if custom_question else 'Hãy phân tích đánh giá toàn diện mã này theo đúng vai trò và triết lý của bạn.'}"

LƯU Ý: Tuân thủ nghiêm ngặt AGENTS.md, chỉ dùng số liệu thật, không đoán mò, nêu rõ điều kiện làm luận điểm mất hiệu lực.
"""
        return {
            "system_instruction": system_content,
            "user_prompt": user_content.strip(),
            "persona_title": f"{persona['badge']} {persona['name']} ({persona['title']})"
        }
