from typing import Dict, Any, List, Optional
from config import LEGAL_RISK_TICKERS


def analyze_governance_and_ownership(
    symbol: str,
    raw_gov: Dict[str, Any],
    fin: Dict[str, Any],
    current_price: float,
    quote: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Module Chuyên sâu Bóc tách Quản trị Doanh nghiệp, Cơ cấu Cổ đông,
    Ban lãnh đạo và Radar Phát hiện Mạng lưới Tăng vốn ảo / Sở hữu chéo:
    
    1. Bóc tách Cơ cấu Cổ đông (Shareholder Structure):
       - Tỷ lệ trôi nổi (Free Float), Khối ngoại (Foreign), Nhà nước (State).
       - Top cổ đông lớn, nhận diện sở hữu qua công ty riêng/vệ tinh.
    2. Ban lãnh đạo & Hội đồng Quản trị (Board & Leadership Audit):
       - Chủ tịch HĐQT, CEO, tỷ lệ sở hữu ban điều hành (Skin in the game).
       - Đánh giá sự gắn kết lợi ích và rủi ro thoái vốn/bán giải chấp.
    3. Mạng lưới Công ty con & Radar Tăng vốn ảo / Trái phiếu hệ sinh thái:
       - Đếm công ty con/liên kết, phát hiện mạng lưới chân rết đa tầng.
       - Phân tích cơ chế phát hành nợ và luân chuyển vốn lòng vòng (Circular Capital).
    4. Điểm số Quản trị Doanh nghiệp (Governance Score: G-Score 0 - 100).
    """
    sym = symbol.upper().strip()
    sh_list = raw_gov.get("shareholders", [])
    off_list = raw_gov.get("officers", [])
    sub_list = raw_gov.get("subsidiaries", [])
    aff_list = raw_gov.get("affiliates", [])
    ov = raw_gov.get("overview", {})

    total_assets = fin.get("total_assets") or 0.0
    total_debt = fin.get("total_debt") or 0.0
    cash = fin.get("cash") or 0.0
    receivables = fin.get("receivables") or 0.0
    inventories = fin.get("inventories") or 0.0
    owners_equity = fin.get("owners_equity") or 0.0

    illiquid_ratio = round(((receivables + inventories) / total_assets) * 100, 1) if total_assets > 0 else 0.0
    receivables_ratio = round((receivables / total_assets) * 100, 1) if total_assets > 0 else 0.0
    debt_to_cash = round(total_debt / cash, 1) if cash > 0 else (99.0 if total_debt > 0 else 0.0)

    # -------------------------------------------------------------
    # 1. BÓC TÁCH CƠ CẤU CỔ ĐÔNG
    # -------------------------------------------------------------
    free_float_pct = ov.get("free_float_pct") or 0.0
    foreigner_pct = ov.get("foreigner_pct") or 0.0
    state_pct = ov.get("state_pct") or 0.0

    # Lọc top 6 cổ đông lớn
    top_shareholders = []
    major_sh_total_pct = 0.0
    has_private_shell_holder = False
    private_shell_names = []

    for s in sh_list[:8]:
        name = s.get("name", "").strip()
        pct = float(s.get("percentage") or 0.0)
        shares = float(s.get("shares") or 0.0)
        major_sh_total_pct += pct
        top_shareholders.append({
            "name": name,
            "percentage": pct,
            "shares": shares
        })
        
        # Nhận diện pháp nhân công ty riêng của lãnh đạo / holding cá nhân
        lower_name = name.lower()
        if any(kw in lower_name for kw in ["tnhh mtv", "tnhh một thành viên", "nhn", "helios", "regeneration", "invest", "investment"]):
            has_private_shell_holder = True
            private_shell_names.append(name)

    # Nếu free_float_pct chưa có từ overview, ước tính
    if free_float_pct <= 0:
        free_float_pct = max(0.0, round(100.0 - major_sh_total_pct, 1))

    # Phân loại cấu trúc sở hữu
    if state_pct >= 35.0:
        ownership_structure = "Nhà nước chi phối (State-Backed Enterprise)"
        ownership_desc = f"Nhà nước nắm giữ {state_pct:.1f}%, rủi ro thao túng hoặc vỡ nợ thấp, hoạt động chịu sự giám sát của cơ quan quản lý vốn nhà nước."
    elif has_private_shell_holder and free_float_pct >= 50.0:
        ownership_structure = "Sở hữu đan xen Công ty riêng & Trôi nổi cao (Complex Insider Shell)"
        ownership_desc = f"Lãnh đạo và nhóm cổ đông lớn nắm giữ qua nhiều công ty TNHH cá nhân/liên quan ({', '.join(private_shell_names[:2])}), cổ phiếu trôi nổi ngoài thị trường cao ({free_float_pct:.1f}%)."
    elif major_sh_total_pct >= 55.0:
        ownership_structure = "Cơ cấu Cô đặc (Concentrated Insider Ownership)"
        ownership_desc = f"Nhóm cổ đông lớn nắm giữ {major_sh_total_pct:.1f}%, lượng hàng trôi nổi cô đặc, ban lãnh đạo kiểm soát tuyệt đối."
    else:
        ownership_structure = "Cơ cấu Phân mảnh / Trôi nổi cao (High Free Float)"
        ownership_desc = f"Lượng cổ phiếu trôi nổi chiếm {free_float_pct:.1f}%, không có cổ đông nắm quyền chi phối tuyệt đối, dễ bị đầu cơ theo dòng tiền thị trường."

    # -------------------------------------------------------------
    # 2. BAN LÃNH ĐẠO & HỘI ĐỒNG QUẢN TRỊ
    # -------------------------------------------------------------
    chairman = "Chưa rõ"
    ceo = "Chưa rõ"
    insider_total_pct = 0.0
    key_officers = []

    for off in off_list:
        o_name = off.get("name", "").strip()
        pos = off.get("position", "").strip()
        pct = float(off.get("percentage") or 0.0)
        shares = float(off.get("shares") or 0.0)
        insider_total_pct += pct

        lower_pos = pos.lower()
        if "chủ tịch" in lower_pos:
            chairman = f"{o_name} ({pos})"
        elif "tổng giám đốc" in lower_pos or "ceo" in lower_pos:
            ceo = f"{o_name} ({pos})"

        key_officers.append({
            "name": o_name,
            "position": pos,
            "percentage": pct,
            "shares": shares
        })

    # Đánh giá Skin in the Game
    if insider_total_pct >= 20.0:
        skin_in_game_verdict = "RẤT CAO"
        skin_in_game_note = f"Ban lãnh đạo nắm giữ {insider_total_pct:.1f}% vốn, cùng chung thuyền và gắn kết lợi ích sống còn với cổ đông."
    elif insider_total_pct >= 5.0:
        skin_in_game_verdict = "TRUNG BÌNH"
        skin_in_game_note = f"Ban lãnh đạo nắm giữ {insider_total_pct:.1f}% vốn điều lệ."
    elif insider_total_pct >= 1.0:
        skin_in_game_verdict = "THẤP"
        skin_in_game_note = f"Ban lãnh đạo chỉ nắm giữ {insider_total_pct:.1f}% vốn điều lệ, mức độ gắn kết tài sản cá nhân với công ty ở mức thấp."
    else:
        skin_in_game_verdict = "CỰC THẤP / RỦI RO BỎ RƠI CỔ ĐÔNG"
        skin_in_game_note = f"Ban điều hành đương nhiệm nắm giữ chỉ {insider_total_pct:.2f}% cổ phần, rủi ro làm thuê không chịu trách nhiệm tài sản hoặc đã bán tháo cổ phần."

    # Cảnh báo pháp lý & lịch sử lãnh đạo đặc thù
    legal_governance_flags = []
    com_group = ov.get("com_group_code", "").upper()
    
    if sym in LEGAL_RISK_TICKERS:
        for flag in LEGAL_RISK_TICKERS[sym]:
            legal_governance_flags.append(flag)
    elif com_group in ["OTC", "UPCOM_SUSPENDED"]:
        legal_governance_flags.append("⚠️ Cảnh báo sàn giao dịch: Cổ phiếu thuộc diện OTC hoặc hạn chế giao dịch do vi phạm quy chế công bố thông tin.")

    # -------------------------------------------------------------
    # 3. MẠNG LƯỚI CÔNG TY CON & RADAR TĂNG VỐN ẢO / TRÁI PHIẾU HỆ SINH THÁI
    # -------------------------------------------------------------
    sub_count = len(sub_list)
    aff_count = len(aff_list)
    
    key_subsidiaries = []
    for sub in sub_list[:6]:
        key_subsidiaries.append({
            "name": sub.get("name", "").strip(),
            "ownership_percent": float(sub.get("ownership_percent") or 0.0)
        })

    # Phân loại độ phức tạp cấu trúc
    if sub_count <= 3:
        conglomerate_type = "CẤU TRÚC GỌN GÀNG / ĐƠN NGÀNH"
        conglomerate_desc = f"Doanh nghiệp chỉ có {sub_count} công ty con, mô hình vận hành tập trung, dòng tiền dễ kiểm soát và minh bạch."
    elif sub_count <= 7:
        conglomerate_type = "HỆ SINH THÁI MỞ RỘNG"
        conglomerate_desc = f"Doanh nghiệp có {sub_count} công ty con và {aff_count} công ty liên kết, phục vụ chiến lược mở rộng chuỗi giá trị."
    else:
        conglomerate_type = "MẠNG LƯỚI ĐA TẦNG PHỨC TẠP (COMPLEX CONGLOMERATE WEB)"
        conglomerate_desc = f"Doanh nghiệp sở hữu tới {sub_count} công ty con và {aff_count} công ty liên kết. Mô hình Holding đa ngành có cấu trúc tài chính đan xen phức tạp."

    # Radar Cảnh báo Tăng vốn ảo & Rút ruột qua Trái phiếu hệ sinh thái
    circular_capital_risk_level = 1
    circular_capital_verdict = "AN TOÀN"
    circular_capital_notes = []

    # Tiêu chí nhận diện rủi ro tăng vốn ảo / tài sản trên giấy tờ
    is_circular_shell = (
        (sub_count >= 6 and receivables_ratio >= 30.0 and debt_to_cash >= 4.0) or
        (sym in LEGAL_RISK_TICKERS and receivables_ratio >= 25.0) or
        (illiquid_ratio >= 45.0 and sub_count >= 8 and debt_to_cash >= 5.0)
    )

    if is_circular_shell:
        circular_capital_risk_level = 5
        circular_capital_verdict = "🚨 BÁO ĐỘNG ĐỎ: RỦI RO MẠNG LƯỚI TĂNG VỐN ẢO & TRÁI PHIẾU HỆ SINH THÁI (CIRCULAR CAPITAL & SHELL NETWORK)"
        circular_capital_notes.append(f"Mạng lưới chân rết dày đặc ({sub_count} công ty con) đi kèm Phải thu chiếm tới {receivables_ratio:.1f}% tổng tài sản ({receivables:,.0f} VND).")
        circular_capital_notes.append(f"Đòn bẩy nợ ngập đầu: Nợ vay ({total_debt:,.0f} VND) gấp {debt_to_cash:.1f}x lần tiền mặt thực tế ({cash:,.0f} VND).")
        circular_capital_notes.append("CƠ CHẾ RỦI RO ĐIỂN HÌNH TẠI VN: Tự phát hành trái phiếu doanh nghiệp cho các công ty con/liên kết với tài sản bảo đảm là cổ phần nội bộ hoặc dự án dở dang chưa đủ pháp lý.")
        circular_capital_notes.append("VỐN BỊ RÚT RUỘT / ĐỌNG VỐN: Tiền sau khi huy động được luân chuyển lòng vòng dưới dạng 'Hợp tác đầu tư / Ủy thác / Đặt cọc mua dự án' chuyển sang các pháp nhân sân sau.")
        circular_capital_notes.append("LỢI NHUẬN KẾ TOÁN ẢO: Tự ghi nhận doanh thu tài chính từ lãi ủy thác/hợp tác nội khối để bù trừ chi phí lãi vay, dòng tiền thuần từ hoạt động kinh doanh (CFO) âm nặng.")
    elif sub_count >= 6 and (receivables_ratio >= 25.0 or debt_to_cash >= 3.0):
        circular_capital_risk_level = 3
        circular_capital_verdict = "CẢNH BÁO RỦI RO SỞ HỮU CHÉO & ĐỌNG VỐN VỆ TINH"
        circular_capital_notes.append(f"Có {sub_count} công ty con, tỷ lệ phải thu {receivables_ratio:.1f}%, cần kiểm soát chặt chẽ các giao dịch bên liên quan.")
    else:
        circular_capital_risk_level = 1
        circular_capital_verdict = "MINH BẠCH / KHÔNG CÓ DẤU HIỆU LUÂN CHUYỂN VỐN BẤT THƯỜNG"
        circular_capital_notes.append("Cấu trúc sở hữu và các khoản phải thu ở ngưỡng an toàn của ngành.")

    # -------------------------------------------------------------
    # 4. CHẤM ĐIỂM QUẢN TRỊ DOANH NGHIỆP (G-SCORE: 0 - 100)
    # -------------------------------------------------------------
    base_g_score = 70

    # Điểm cộng
    if state_pct >= 20.0 or foreigner_pct >= 15.0:
        base_g_score += 10 # Có tổ chức ngoại hoặc nhà nước giám sát
    if insider_total_pct >= 15.0:
        base_g_score += 10 # Lãnh đạo cam kết vốn cao
    if debt_to_cash <= 2.0 and cash > 0:
        base_g_score += 10 # Nợ vay trong tầm kiểm soát tiền mặt

    # Điểm trừ
    if circular_capital_risk_level == 5:
        base_g_score -= 35
    elif circular_capital_risk_level >= 3:
        base_g_score -= 15

    if receivables_ratio >= 35.0:
        base_g_score -= 15

    if free_float_pct >= 75.0 and major_sh_total_pct < 25.0:
        base_g_score -= 10 # Quá phân mảnh, không ai chịu trách nhiệm chính

    if legal_governance_flags:
        base_g_score -= 25 # Có biến cố pháp lý lãnh đạo hoặc vi phạm BCTC

    g_score = int(min(100, max(5, base_g_score)))

    if g_score >= 80:
        g_rating = "QUẢN TRỊ MINH BẠCH & AN TOÀN (EXEMPLARY)"
        integrity_verdict = "MINH BẠCH RẤT CAO"
        shell_risk_desc = "Không phát hiện dấu hiệu sử dụng công ty sân sau để rút ruột hay chuyển giá. Dòng tiền kinh doanh gắn liền với tài sản và hoạt động thực tế."
    elif g_score >= 60:
        g_rating = "QUẢN TRỊ ĐẠT CHUẨN (ADEQUATE)"
        integrity_verdict = "ĐẠT CHUẨN MINH BẠCH"
        shell_risk_desc = "Cơ cấu hệ sinh thái có nhiều công ty thành viên nhưng phục vụ mục đích mở rộng dự án KCN/hạ tầng cụ thể, rủi ro sân sau ở mức thấp."
    elif g_score >= 40:
        g_rating = "RỦI RO QUẢN TRỊ ĐÁNG NGỜ (QUESTIONABLE)"
        integrity_verdict = "CÓ DẤU HIỆU CẦN GIÁM SÁT CHẶT CHẼ"
        shell_risk_desc = "Có các giao dịch ủy thác đầu tư, hợp tác kinh doanh hoặc cho vay nội bộ với các bên liên quan cần kiểm tra thuyết minh BCTC."
    else:
        g_rating = "🚨 BÁO ĐỘNG ĐỎ: RỦI RO QUẢN TRỊ NGHIÊM TRỌNG (HIGH RISK)"
        integrity_verdict = "🚨 NGUY HIỂM: NGUY CƠ RÚT RUỘT & SÂN SAU"
        shell_risk_desc = "Cảnh báo cao độ: Dấu hiệu mạng lưới công ty sân sau dày đặc, dòng vốn bị luân chuyển lòng vòng, lợi nhuận trên giấy."

    # Đánh giá bằng chứng tiền thật (Cổ tức & Tiền mặt)
    cash_flow_quality = fin.get("cash_flow", {}) if isinstance(fin.get("cash_flow"), dict) else {}
    cfo_ttm_val = fin.get("cfo_ttm") or 0.0
    dividend_evidence = ""
    if cfo_ttm_val > 500_000_000_000:
        dividend_evidence = "✅ Dòng tiền bán hàng thực thu (CFO) dương rất lớn (>500 tỷ), chứng minh doanh nghiệp thu tiền tươi thóc thật, không bị ứ đọng vốn ở công ty sân sau."
    elif cfo_ttm_val < 0:
        dividend_evidence = "⚠️ Dòng tiền CFO âm, tiền kinh doanh chưa thực thu về tài khoản, cần theo dõi kỹ các khoản phải thu đối tác."
    else:
        dividend_evidence = "Dòng tiền kinh doanh ở mức trung bình, cân bằng với nhu cầu vốn lưu động."

    # Tổng hợp phân tích Ban Lãnh đạo chi tiết bằng tiếng Việt
    leadership_analysis_vi = (
        f"Chủ tịch HĐQT: {chairman} | Tổng Giám đốc: {ceo}. "
        f"Ban điều hành nắm giữ {insider_total_pct:.1f}% cổ phần ({skin_in_game_verdict}). "
        f"{shell_risk_desc} {dividend_evidence}"
    )

    return {
        "symbol": sym,
        "g_score": g_score,
        "g_rating": g_rating,
        "integrity_verdict": integrity_verdict,
        "shell_risk_desc": shell_risk_desc,
        "dividend_evidence": dividend_evidence,
        "leadership_analysis_vi": leadership_analysis_vi,
        "ownership": {
            "free_float_pct": free_float_pct,
            "foreigner_pct": foreigner_pct,
            "state_pct": state_pct,
            "structure": ownership_structure,
            "description": ownership_desc,
            "top_shareholders": top_shareholders,
            "has_private_shell_holder": has_private_shell_holder,
            "private_shell_names": private_shell_names
        },
        "leadership": {
            "chairman": chairman,
            "ceo": ceo,
            "insider_total_pct": round(insider_total_pct, 2),
            "skin_in_game_verdict": skin_in_game_verdict,
            "skin_in_game_note": skin_in_game_note,
            "key_officers": key_officers,
            "legal_governance_flags": legal_governance_flags
        },
        "subsidiary_web": {
            "subsidiary_count": sub_count,
            "affiliate_count": aff_count,
            "conglomerate_type": conglomerate_type,
            "conglomerate_desc": conglomerate_desc,
            "key_subsidiaries": key_subsidiaries,
            "circular_capital_risk_level": circular_capital_risk_level,
            "circular_capital_verdict": circular_capital_verdict,
            "circular_capital_notes": circular_capital_notes,
            "receivables_ratio": receivables_ratio,
            "debt_to_cash": debt_to_cash
        }
    }
