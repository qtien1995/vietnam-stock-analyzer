from typing import Dict, Any, Optional
from config import FA_WEIGHTS, LEGAL_RISK_TICKERS
from core.segment_analyzer import analyze_company_segments
from core.governance_analyzer import analyze_governance_and_ownership
from core.data_loader import get_governance_data
from core.macro_engine import analyze_macro_and_sector_cycle, classify_sector


def get_sector(symbol: str, overview_data: Optional[Dict[str, Any]] = None) -> str:
    """Xác định ngành nghề đặc thù của cổ phiếu qua bộ lọc động toàn thị trường."""
    return classify_sector(symbol, overview_data)


def calculate_piotroski_score(fin: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tính điểm Piotroski F-Score (0 - 9 điểm) theo chuẩn mực kế toán của GS. Joseph Piotroski:
    [Khả năng sinh lời - Profitability]
    1. ROA > 0 (Lợi nhuận ròng trên tổng tài sản dương)
    2. CFO > 0 (Dòng tiền thuần hoạt động kinh doanh dương)
    3. ΔROA > 0 (Biến động ROA dương so với cùng kỳ)
    4. CFO > Net Profit (Chất lượng lợi nhuận thực tế vượt lợi nhuận kế toán dồn tích - Accrual test)
    [Cơ cấu vốn & Thanh khoản - Leverage & Liquidity]
    5. ΔLeverage <= 0 (Đòn bẩy nợ dài hạn giảm hoặc không tăng so với cùng kỳ)
    6. ΔCurrent Ratio > 0 (Hệ số thanh toán hiện hành được cải thiện)
    7. Không pha loãng cổ phiếu (Số cổ phiếu lưu hành không tăng đột biến)
    [Hiệu quả hoạt động - Operating Efficiency]
    8. ΔGross Margin > 0 (Biên lợi nhuận gộp cải thiện)
    9. ΔAsset Turnover > 0 (Vòng quay tổng tài sản tăng)

    Trả về dict gồm:
    - score: int (0 - 9)
    - variant: 'STANDARD' (khi có đủ dữ liệu 2 kỳ) hoặc 'MODIFIED_STATIC' (khi chỉ có số liệu 1 kỳ)
    - criteria_met: List các tiêu chí thỏa mãn
    - criteria_failed: List các tiêu chí không đạt
    """
    score = 0
    ticker = fin.get("symbol", "").upper()
    sector = get_sector(ticker)

    roa = fin.get("roa")
    cfo = fin.get("cfo_ttm")
    profit = fin.get("ttm_profit")
    profit_growth = fin.get("profit_growth")
    rev_growth = fin.get("revenue_growth")
    debt_eq = fin.get("debt_to_equity")
    working_cap = fin.get("working_capital")
    gross_margin = fin.get("gross_margin")

    criteria_met = []
    criteria_failed = []

    # 1. Sinh lời: ROA dương
    if roa is not None and roa > 0:
        score += 1
        criteria_met.append("ROA dương (Sinh lời trên tài sản > 0)")
    else:
        criteria_failed.append("ROA âm hoặc không xác định")

    # 2. Sinh lời: Dòng tiền thuần HĐKD (CFO) dương
    if cfo is not None and cfo > 0:
        score += 1
        criteria_met.append("Dòng tiền thuần HĐKD (CFO) dương")
    else:
        criteria_failed.append("Dòng tiền thuần HĐKD âm hoặc thiếu số liệu")

    # 3. Tăng trưởng sinh lời (Proxy ΔROA từ tăng trưởng lợi nhuận ròng)
    if profit_growth is not None and profit_growth > 0:
        score += 1
        criteria_met.append("Tăng trưởng lợi nhuận dương so với cùng kỳ (ΔROA > 0)")
    else:
        criteria_failed.append("Tăng trưởng lợi nhuận âm hoặc đi lùi")

    # 4. Chất lượng dòng tiền: CFO > Lợi nhuận sau thuế (Accrual test)
    if cfo is not None and profit is not None:
        if (cfo > 0 and profit > 0 and cfo >= profit * 0.8) or (cfo > 0 and profit <= 0):
            score += 1
            criteria_met.append("CFO vượt trội hoặc tương đương LNST (Chất lượng lợi nhuận cao)")
        else:
            criteria_failed.append("CFO thấp hơn nhiều so với LNST (Lợi nhuận dồn tích trên sổ sách)")
    else:
        criteria_failed.append("Thiếu dữ liệu đối chiếu CFO vs LNST")

    # 5. Đòn bẩy nợ:
    if sector in ["BANK", "SECURITIES"]:
        score += 1
        criteria_met.append("Ngành tài chính (Đòn bẩy huy động tiền gửi đặc thù, miễn trừ tiêu chí nợ phi tài chính)")
    else:
        if debt_eq is not None and debt_eq <= 1.2:
            score += 1
            criteria_met.append("Đòn bẩy nợ an toàn (Nợ vay/Vốn CSH <= 1.2x)")
        else:
            criteria_failed.append("Đòn bẩy nợ cao hoặc thiếu dữ liệu nợ")

    # 6. Thanh khoản: Vốn lưu động dương
    if sector in ["BANK", "SECURITIES"]:
        score += 1
        criteria_met.append("Ngành tài chính (Mô hình thanh khoản theo quy định riêng của NHNN / UBCK)")
    else:
        if working_cap is not None and working_cap > 0:
            score += 1
            criteria_met.append("Vốn lưu động ròng dương (Working Capital > 0)")
        else:
            criteria_failed.append("Vốn lưu động âm (Rủi ro thanh khoản ngắn hạn)")

    # 7. Tăng trưởng sinh lời vượt trội (hoặc Không phát hành pha loãng)
    if profit_growth is not None and profit_growth > 12.0:
        score += 1
        criteria_met.append("Tốc độ tăng trưởng lợi nhuận cao (> 12% YoY)")
    else:
        criteria_failed.append("Tốc độ tăng trưởng lợi nhuận chưa vượt 12%")

    # 8. Hiệu quả kinh doanh: Biên lợi nhuận gộp
    if sector in ["BANK", "SECURITIES"]:
        score += 1
        criteria_met.append("Ngành tài chính (Áp dụng tiêu chí biên lãi thuần NIM)")
    else:
        if gross_margin is not None and gross_margin >= 15.0:
            score += 1
            criteria_met.append(f"Biên lợi nhuận gộp lành mạnh ({gross_margin:.1f}% >= 15%)")
        else:
            criteria_failed.append("Biên lợi nhuận gộp mỏng (< 15%) hoặc thiếu dữ liệu")

    # 9. Hiệu quả hoạt động: Doanh thu tăng trưởng dương
    if rev_growth is not None and rev_growth > 5.0:
        score += 1
        criteria_met.append(f"Doanh thu tăng trưởng tích cực ({rev_growth:.1f}% > 5%)")
    else:
        criteria_failed.append("Doanh thu đi lùi hoặc tăng trưởng dưới 5%")

    final_score = min(9, max(0, score))
    return {
        "score": final_score,
        "variant": "MODIFIED_STATIC",
        "criteria_met": criteria_met,
        "criteria_failed": criteria_failed
    }


def evaluate_buffett_moat(fin: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Đánh giá doanh nghiệp theo trường phái Warren Buffett & Định giá theo từng ngành:
    - Trung thực tuyệt đối: Không tự gán P/E = 15.0 hay P/B = 1.5 khi thiếu số liệu.
    - Cổ phiếu lỗ (EPS âm) => P/E = None (ghi rõ trạng thái).
    - Ngân hàng / Chứng khoán: Trọng tâm P/B và ROE.
    - Công nghệ: Cho phép P/E cao hơn nếu tăng trưởng cao, cảnh báo Multiple Contraction nếu > 24x.
    - Thép / Chu kỳ: Cảnh báo bẫy giá trị đỉnh chu kỳ.
    - Sản xuất / Bán lẻ: P/E tham chiếu 14-16x.
    """
    ticker = fin.get("symbol", "").upper()
    sector = get_sector(ticker)
    roe = fin.get("roe")
    debt_eq = fin.get("debt_to_equity")
    
    eps_val = fin.get("eps")
    if eps_val is not None and eps_val > 0 and current_price > 0:
        pe = round(current_price / eps_val, 2)
        pe_status = "VALID"
    elif eps_val is not None and eps_val <= 0:
        pe = None
        pe_status = "NEGATIVE_EARNINGS"
    elif fin.get("pe") is not None and float(fin.get("pe")) > 0:
        pe = float(fin.get("pe"))
        pe_status = "VALID"
    else:
        pe = None
        pe_status = "INSUFFICIENT_DATA"
        
    bvps_val = fin.get("bvps")
    if bvps_val is not None and bvps_val > 0 and current_price > 0:
        pb = round(current_price / bvps_val, 2)
        pb_status = "VALID"
    elif bvps_val is not None and bvps_val <= 0:
        pb = None
        pb_status = "NEGATIVE_EQUITY"
    elif fin.get("pb") is not None and float(fin.get("pb")) > 0:
        pb = float(fin.get("pb"))
        pb_status = "VALID"
    else:
        pb = None
        pb_status = "INSUFFICIENT_DATA"

    score = 0
    reasons = []
    valuation_warning = ""

    # 1. HIỆU QUẢ SINH LỜI (ROE BENCHMARK)
    if roe is not None:
        if roe >= 18.0:
            score += 35
            reasons.append(f"ROE xuất sắc ({roe:.1f}%), thể hiện lợi thế cạnh tranh con hào kinh tế bền vững.")
        elif roe >= 14.0:
            score += 25
            reasons.append(f"ROE đạt chuẩn đầu tư ({roe:.1f}%).")
        elif roe > 0:
            score += 10
            reasons.append(f"ROE ({roe:.1f}%) ở mức trung bình, chưa thực sự vượt trội theo tiêu chuẩn Buffett.")
        else:
            score += 0
            reasons.append(f"Cảnh báo: ROE âm hoặc bằng 0 ({roe:.1f}%), doanh nghiệp đang kinh doanh thua lỗ.")
    else:
        score += 5
        reasons.append("Thiếu dữ liệu ROE để đánh giá con hào kinh tế.")

    # 2. CẤU TRÚC VỐN & ĐÒN BẨY NỢ
    if sector == "BANK":
        score += 30
        reasons.append(f"Ngân hàng ({ticker}): Kinh doanh đòn bẩy tiền gửi đặc thù, miễn trừ tiêu chí Nợ/Vốn.")
    elif sector == "SECURITIES":
        score += 25
        d_val = debt_eq if debt_eq is not None else 1.0
        reasons.append(f"Chứng khoán ({ticker}): Đòn bẩy nợ margin {d_val:.2f}x trong ngưỡng kiểm soát.")
    else:
        if debt_eq is not None:
            if debt_eq <= 0.8:
                score += 30
                reasons.append(f"Cấu trúc tài chính rất an toàn, nợ vay/vốn chủ chỉ {debt_eq:.2f}x.")
            elif debt_eq <= 1.5:
                score += 20
                reasons.append(f"Nợ vay ở mức kiểm soát được ({debt_eq:.2f}x).")
            else:
                score += 5
                reasons.append(f"Đòn bẩy nợ cao ({debt_eq:.2f}x), rủi ro chi phí lãi vay khi thị trường biến động.")
        else:
            score += 10
            reasons.append("Chưa đủ thông tin tỷ lệ nợ vay trên vốn chủ sở hữu.")

    # 3. ĐỊNH GIÁ ĐẶC THÙ THEO NGÀNH & TÍNH GIÁ TRỊ HỢP LÝ
    fair_price = current_price

    if sector == "BANK":
        fair_pb = 1.35
        if pb is not None and pb > 0 and bvps_val and bvps_val > 0:
            fair_price = round(bvps_val * fair_pb, 0)
            if pb <= 1.2:
                score += 35
                reasons.append(f"Định giá ngân hàng hấp dẫn với P/B {pb:.2f}x (tham chiếu ngành {fair_pb}x).")
            elif pb <= 1.5:
                score += 25
                reasons.append(f"Định giá ngân hàng ở mức hợp lý với P/B {pb:.2f}x.")
            else:
                score += 10
                valuation_warning = f"P/B ({pb:.2f}x) cao hơn mặt bằng chung ngân hàng"
                reasons.append(f"P/B {pb:.2f}x tương đối cao so với trung bình ngành ngân hàng.")
        else:
            fair_price = current_price
            reasons.append("Thiếu số liệu P/B để xác định giá trị hợp lý ngân hàng.")

    elif sector == "SECURITIES":
        fair_pb = 1.50
        if pb is not None and pb > 0 and bvps_val and bvps_val > 0:
            fair_price = round(bvps_val * fair_pb, 0)
            if pb <= 1.3:
                score += 35
                reasons.append(f"Định giá ngành chứng khoán hấp dẫn với P/B {pb:.2f}x.")
            elif pb <= 1.7:
                score += 25
                reasons.append(f"Định giá chứng khoán hợp lý với P/B {pb:.2f}x.")
            else:
                score += 10
                valuation_warning = f"P/B ({pb:.2f}x) ở vùng cao của chu kỳ chứng khoán"
                reasons.append(f"P/B {pb:.2f}x ở vùng biên trên của chu kỳ ngành chứng khoán.")
        else:
            fair_price = current_price
            reasons.append("Thiếu số liệu P/B ngành chứng khoán.")

    elif sector in ["TECH", "TECH_TELECOM"]:
        fair_pe = 19.0
        if pe is not None and pe > 0 and eps_val and eps_val > 0:
            fair_price = round(eps_val * fair_pe, 0)
            if pe <= 15.0:
                score += 35
                reasons.append(f"Cổ phiếu công nghệ định giá rất hời với P/E {pe:.1f}x.")
            elif pe <= 22.0:
                score += 25
                reasons.append(f"Định giá công nghệ hợp lý với P/E {pe:.1f}x (tham chiếu 19x).")
            else:
                score += 5
                valuation_warning = f"Nguy cơ Multiple Contraction: P/E ({pe:.1f}x) cao"
                reasons.append(f"Cảnh báo: P/E {pe:.1f}x ở mức cao, rủi ro điều chỉnh bội số định giá nếu tăng trưởng chậm lại.")
        else:
            fair_price = round(bvps_val * 2.0, 0) if bvps_val and bvps_val > 0 else current_price
            reasons.append("EPS không khả dụng hoặc âm, không áp dụng định giá P/E công nghệ.")

    elif sector in ["STEEL_CYCLICAL", "STEEL_MATERIALS"]:
        fair_pe = 8.5
        if pe is not None and pe > 0 and eps_val and eps_val > 0:
            fair_price = round(eps_val * fair_pe, 0)
            if pe <= 7.0 and roe and roe >= 15.0:
                score += 35
                reasons.append(f"Cổ phiếu chu kỳ định giá hấp dẫn với P/E {pe:.1f}x.")
            elif pe <= 11.0:
                score += 25
                reasons.append(f"Định giá chu kỳ hợp lý với P/E {pe:.1f}x.")
            else:
                score += 10
                reasons.append(f"P/E {pe:.1f}x phản ánh lợi nhuận đang ở vùng trũng chu kỳ hoặc thị giá cao.")
        else:
            fair_price = round(bvps_val * 1.1, 0) if bvps_val and bvps_val > 0 else current_price
            reasons.append("Cổ phiếu chu kỳ đang trong giai đoạn trũng lợi nhuận, chuyển sang tham chiếu tài sản sổ sách.")

    elif sector in ["INDUSTRIAL_REAL_ESTATE", "RUBBER_AND_INDUSTRIAL_PARK"]:
        fair_pb = 1.50
        if pb is not None and pb > 0 and bvps_val and bvps_val > 0:
            fair_price = round(bvps_val * fair_pb, 0)
            if pb <= 1.25:
                score += 35
                reasons.append(f"Định giá BĐS KCN hấp dẫn với P/B {pb:.2f}x (tham chiếu {fair_pb}x).")
            elif pb <= 1.65:
                score += 25
                reasons.append(f"Định giá BĐS KCN ở vùng hợp lý với P/B {pb:.2f}x.")
            else:
                score += 10
                valuation_warning = f"P/B ({pb:.2f}x) cao hơn mặt bằng chung ngành KCN"
                reasons.append(f"P/B {pb:.2f}x đang ở vùng biên trên của chu kỳ cho thuê đất KCN.")
        else:
            fair_price = current_price
            reasons.append("Chưa đủ dữ liệu tài sản BĐS KCN.")

    else:
        # Ngành sản xuất / bán lẻ thông thường
        fair_pe = 14.5
        if pe is not None and pe > 0 and eps_val and eps_val > 0:
            fair_price = round(eps_val * fair_pe, 0)
            if pe <= 11.0:
                score += 35
                reasons.append(f"Thị giá hấp dẫn với P/E {pe:.1f}x.")
            elif pe <= 16.0:
                score += 25
                reasons.append(f"Định giá hợp lý với P/E {pe:.1f}x.")
            else:
                score += 10
                valuation_warning = f"P/E ({pe:.1f}x) cao hơn trung bình thị trường"
                reasons.append(f"P/E {pe:.1f}x hơi cao so với mức sinh lời hiện tại.")
        elif bvps_val and bvps_val > 0:
            fair_price = round(bvps_val * 1.0, 0)
            score += 10
            reasons.append("EPS âm hoặc thiếu số liệu; tham chiếu định giá bảo vệ vốn theo giá trị sổ sách.")
        else:
            fair_price = current_price
            score += 5
            reasons.append("Thiếu cả EPS và BVPS để xây dựng mô hình định giá cơ bản.")

    margin_of_safety = round(((fair_price - current_price) / fair_price) * 100, 1) if fair_price > 0 else 0.0

    # Kiểm tra rủi ro dòng tiền cốt lõi theo trường phái Buffett
    cfo_ttm = fin.get("cfo_ttm")
    if cfo_ttm is not None and cfo_ttm < 0:
        score = max(5, score - 30)
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + "Cảnh báo Lợi nhuận trên giấy (CFO âm)"
        reasons.append(f"Cảnh báo Buffett: Dòng tiền thuần HĐKD (CFO) âm ({cfo_ttm:,.0f} đ) - vi phạm nguyên tắc dòng tiền thực.")

    verdict = "MUA TÍCH SẢN" if score >= 75 else ("QUAN SÁT CHỜ CHIẾT KHẤU" if score >= 45 else "TRÁNH XA (KHÔNG ĐẠT CHUẨN)")

    return {
        "score": score,
        "sector": sector,
        "verdict": verdict,
        "pe": pe,
        "pe_status": pe_status,
        "pb": pb,
        "pb_status": pb_status,
        "fair_price": round(fair_price, 0),
        "margin_of_safety_pct": margin_of_safety,
        "valuation_warning": valuation_warning,
        "reasons": reasons
    }


def evaluate_peter_lynch(fin: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Đánh giá theo phong cách Peter Lynch (GARP - Growth at a Reasonable Price):
    - Hệ số PEG (P/E chia cho Tốc độ tăng trưởng lợi nhuận).
    - Quy tắc nghiêm ngặt: Không tính PEG khi P/E âm, khi tăng trưởng <= 0 hoặc thiếu dữ liệu.
    """
    eps_val = fin.get("eps")
    if eps_val is not None and eps_val > 0 and current_price > 0:
        pe = round(current_price / eps_val, 2)
    elif fin.get("pe") is not None and float(fin.get("pe")) > 0:
        pe = float(fin.get("pe"))
    else:
        pe = None

    profit_growth = fin.get("profit_growth")
    revenue_growth = fin.get("revenue_growth")
    growth = profit_growth if profit_growth is not None else revenue_growth

    score = 0
    reasons = []
    peg_status = "VALID"

    if pe is None:
        peg = None
        peg_status = "NEGATIVE_EPS"
        score = 15
        category = "Không áp dụng (Doanh nghiệp thua lỗ hoặc thiếu P/E)"
        verdict = "TRÁNH XA (EPS ÂM)"
        reasons.append("Doanh nghiệp có lợi nhuận âm (lỗ) hoặc thiếu số liệu P/E, không thỏa mãn tiêu chí PEG của Peter Lynch.")

    elif growth is None:
        peg = None
        peg_status = "INSUFFICIENT_DATA"
        score = 40
        category = "Chưa đủ dữ liệu tăng trưởng để tính PEG"
        verdict = "THEO DÕI (THIẾU DỮ LIỆU TĂNG TRƯỞNG)"
        reasons.append("Thiếu dữ liệu tăng trưởng cùng kỳ, không đủ căn cứ để tính PEG chuẩn mực.")

    elif growth <= 0:
        peg = None
        peg_status = "NEGATIVE_GROWTH"
        score = 20
        category = "Cổ phiếu Lợi nhuận đi lùi (Declining / Turnaround Risk)"
        verdict = "TRÁNH XA (TĂNG TRƯỞNG ÂM)"
        reasons.append(f"Tăng trưởng lợi nhuận âm ({growth:+.1f}%), loại khỏi tiêu chí mua tăng trưởng PEG.")

    else:
        # P/E và Growth đều hợp lệ và > 0
        peg = round(pe / growth, 2)
        peg_status = "VALID"

        if peg <= 0.7:
            score = 90
            category = "Cổ phiếu Tăng trưởng giá rẻ (Fast Grower Undervalued)"
            reasons.append(f"Hệ số PEG cực kỳ hấp dẫn ({peg} <= 0.7) với tốc độ tăng trưởng {growth:.1f}%.")
        elif peg <= 1.0:
            score = 75
            category = "Cổ phiếu Tăng trưởng giá hợp lý (GARP)"
            reasons.append(f"Hệ số PEG đạt chuẩn xuất sắc ({peg} <= 1.0).")
        elif peg <= 1.5:
            score = 55
            category = "Cổ phiếu Tăng trưởng trung bình (Stalwart)"
            reasons.append(f"Hệ số PEG ở mức chấp nhận được ({peg}).")
        else:
            score = 30
            category = "Cổ phiếu Định giá quá cao so với tăng trưởng (Overvalued)"
            reasons.append(f"Hệ số PEG cao ({peg}), thị giá tăng nhanh hơn tốc độ tăng trưởng thực tế.")

        verdict = "MUA TĂNG TRƯỞNG" if score >= 70 else ("THEO DÕI" if score >= 50 else "ĐẮT QUÁ MỨC")

    # Kiểm tra dòng tiền hỗ trợ tăng trưởng
    cfo_ttm = fin.get("cfo_ttm")
    if cfo_ttm is not None and cfo_ttm < 0:
        score = max(10, score - 25)
        reasons.append("Cảnh báo Peter Lynch: Dòng tiền HĐKD (CFO) âm, tăng trưởng không chuyển hóa thành tiền mặt thật.")
        if score < 50:
            verdict = "TRÁNH XA (DÒNG TIỀN YẾU)"

    return {
        "score": score,
        "peg": peg,
        "peg_status": peg_status,
        "category": category,
        "verdict": verdict,
        "reasons": reasons
    }


def evaluate_growth_and_earnings_quality(fin: Dict[str, Any]) -> Dict[str, Any]:
    """Phân tích chất lượng tăng trưởng & Bóc tách Doanh thu vs Lợi nhuận."""
    profit_growth = fin.get("profit_growth")
    revenue_growth = fin.get("revenue_growth")
    
    reasons = []
    quality = "Bình thường"
    growth_score = 50

    if profit_growth is not None and revenue_growth is not None:
        if profit_growth > 25.0 and revenue_growth < 5.0:
            quality = "Chất lượng lợi nhuận cần lưu ý (Lợi nhuận đi trước doanh thu)"
            reasons.append(f"Lợi nhuận tăng mạnh ({profit_growth:+.1f}%) nhưng doanh thu chỉ tăng {revenue_growth:+.1f}%, cần kiểm tra thu nhập bất thường.")
            growth_score = 60
        elif profit_growth > 15.0 and revenue_growth > 15.0:
            quality = "Tăng trưởng cốt lõi rất mạnh (Core Business Growth)"
            reasons.append(f"Cả Doanh thu ({revenue_growth:+.1f}%) và Lợi nhuận ({profit_growth:+.1f}%) cùng tăng trưởng 2 chữ số.")
            growth_score = 90
        elif profit_growth <= 0 and revenue_growth <= 0:
            quality = "Kinh doanh đang suy giảm (Declining)"
            reasons.append(f"Cả Doanh thu ({revenue_growth:+.1f}%) và Lợi nhuận ({profit_growth:+.1f}%) đều sụt giảm trong kỳ báo cáo gần nhất.")
            growth_score = 25
        elif profit_growth > 0:
            quality = "Tăng trưởng ổn định"
            reasons.append(f"Lợi nhuận duy trì đà tăng trưởng dương ({profit_growth:+.1f}%).")
            growth_score = 70
        else:
            quality = "Lợi nhuận suy giảm"
            reasons.append(f"Lợi nhuận sụt giảm ({profit_growth:+.1f}%), cần theo dõi kỳ tiếp theo.")
            growth_score = 30
    else:
        reasons.append("Thiếu dữ liệu so sánh tăng trưởng doanh thu/lợi nhuận theo quý.")

    return {
        "quality": quality,
        "growth_score": growth_score,
        "reasons": reasons
    }


def evaluate_dupont_decomposition(fin: Dict[str, Any]) -> Dict[str, Any]:
    """
    Phân rã Tỷ suất sinh lời ROE theo Mô hình DuPont 3 nhân tố:
    ROE = (Net Profit / Revenue) * (Revenue / Total Assets) * (Total Assets / Owners' Equity)
        = Net Margin * Asset Turnover * Equity Multiplier
    Giúp bóc tách bản chất sinh lời: Do sản phẩm có biên lợi nhuận cao (Net Margin),
    sử dụng tài sản hiệu quả (Asset Turnover) hay do dùng đòn bẩy nợ cao (Financial Leverage).
    """
    revenue = fin.get("ttm_revenue") or fin.get("revenue")
    profit = fin.get("ttm_profit") or fin.get("net_profit")
    assets = fin.get("total_assets")
    equity = fin.get("owners_equity")
    reported_roe = fin.get("roe")

    net_margin = None
    asset_turnover = None
    equity_multiplier = None
    calculated_roe = None
    driver = "CÂN BẰNG"
    explanation = ""

    if revenue and revenue > 0 and profit is not None:
        net_margin = round((profit / revenue) * 100, 2)
    elif fin.get("net_margin") is not None:
        net_margin = float(fin.get("net_margin"))

    if revenue and revenue > 0 and assets and assets > 0:
        asset_turnover = round(revenue / assets, 2)

    if assets and assets > 0 and equity and equity > 0:
        equity_multiplier = round(assets / equity, 2)

    if net_margin is not None and asset_turnover is not None and equity_multiplier is not None:
        calculated_roe = round((net_margin / 100.0) * asset_turnover * equity_multiplier * 100.0, 2)
    elif reported_roe is not None:
        calculated_roe = float(reported_roe)

    # Đánh giá nhân tố thúc đẩy chính
    if equity_multiplier and equity_multiplier >= 3.5:
        driver = "ĐÒN BẨY NỢ CAO (FINANCIAL LEVERAGE)"
        explanation = f"ROE ({calculated_roe or 'N/A'}%) phụ thuộc chủ yếu vào đòn bẩy tài chính cao (Tài sản/VCSH = {equity_multiplier:.1f}x), cần chú ý rủi ro chi phí lãi vay."
    elif net_margin and net_margin >= 20.0:
        driver = "BIÊN LỢI NHUẬN CAO (PRICING POWER)"
        explanation = f"ROE ({calculated_roe or 'N/A'}%) được thúc đẩy bởi biên lãi ròng vượt trội ({net_margin:.1f}%), thể hiện lợi thế cạnh tranh và quyền định giá sản phẩm."
    elif asset_turnover and asset_turnover >= 1.2:
        driver = "VÒNG QUAY TÀI SẢN CAO (OPERATIONAL EFFICIENCY)"
        explanation = f"ROE ({calculated_roe or 'N/A'}%) xuất phát từ hiệu suất khai thác tài sản xuất sắc (Vòng quay = {asset_turnover:.2f} vòng/năm)."
    else:
        driver = "CƠ CẤU VẬN HÀNH BÌNH THƯỜNG"
        explanation = f"Các nhân tố DuPont cân bằng (Biên ròng: {net_margin or 'N/A'}%, Vòng quay: {asset_turnover or 'N/A'}x, Đòn bẩy: {equity_multiplier or 'N/A'}x)."

    return {
        "net_margin_pct": net_margin,
        "asset_turnover": asset_turnover,
        "equity_multiplier": equity_multiplier,
        "calculated_roe": calculated_roe,
        "primary_driver": driver,
        "explanation": explanation
    }


def calculate_roic(fin: Dict[str, Any], tax_rate: float = 0.20) -> Optional[float]:
    """
    Tính Tỷ suất sinh lời trên Vốn Đầu tư (ROIC - Return on Invested Capital):
    ROIC = NOPAT / Invested Capital
         = (EBIT * (1 - t)) / (Total Debt + Owners' Equity - Cash)
    """
    ebit = fin.get("ebit_ttm")
    if ebit is None and fin.get("ttm_profit"):
        ebit = fin.get("ttm_profit") / (1 - tax_rate)

    if not ebit or ebit <= 0:
        return None

    total_debt = fin.get("total_debt") or 0.0
    equity = fin.get("owners_equity") or 0.0
    cash = fin.get("cash") or 0.0

    invested_capital = total_debt + equity - cash
    if invested_capital <= 0:
        return None

    nopat = ebit * (1 - tax_rate)
    return round((nopat / invested_capital) * 100, 2)



def evaluate_asset_based_valuation(fin: Dict[str, Any], current_price: float) -> Dict[str, Any]:
    """
    Định giá cổ phiếu dựa trên Khối tài sản hiện có & Phân tích chất lượng tài sản (Asset Quality):
    1. Định giá tài sản:
       - BVPS: Vốn chủ sở hữu / Số CP lưu hành.
       - TBVPS: Vốn chủ - Tài sản vô hình.
       - NCAVPS (Net-Net Graham): (Tài sản ngắn hạn - Nợ phải trả) / Số CP.
       - Net Cash/Share: (Tiền mặt - Nợ vay) / Số CP.
       - P/B = Thị giá / BVPS (nếu BVPS > 0).
    2. Đánh giá Bội số Định giá Tài sản (Asset Valuation Multiple) khách quan:
       - Tránh quy kết hình sự / thao túng từ P/B cao.
       - Phân biệt Món hời tài sản thật vs Bẫy giá trị (Value Trap).
    """
    bvps = fin.get("bvps")
    tbvps = fin.get("tbvps") if fin.get("tbvps") is not None else bvps
    ncavps = fin.get("ncavps")
    shares = fin.get("issue_share") or 0.0
    cash = fin.get("cash") or 0.0
    total_debt = fin.get("total_debt") or 0.0
    total_assets = fin.get("total_assets") or 0.0
    receivables = fin.get("receivables") or 0.0
    inventories = fin.get("inventories") or 0.0
    roe = fin.get("roe")

    if bvps is not None and bvps > 0 and current_price > 0:
        pb = round(current_price / bvps, 2)
        asset_discount_pct = round(((bvps - current_price) / bvps) * 100, 1)
    else:
        pb = None
        asset_discount_pct = 0.0

    net_cash_per_share = round((cash - total_debt) / shares, 0) if shares > 0 else 0.0

    # Đánh giá chất lượng tài sản
    illiquid_ratio = round(((receivables + inventories) / total_assets) * 100, 1) if total_assets > 0 else 0.0
    cash_ratio = round((cash / total_assets) * 100, 1) if total_assets > 0 else 0.0
    receivables_ratio = round((receivables / total_assets) * 100, 1) if total_assets > 0 else 0.0
    debt_to_cash = round(total_debt / cash, 1) if cash > 0 else (99.0 if total_debt > 0 else 0.0)

    asset_quality_verdict = "Lành mạnh"
    asset_quality_notes = []
    if cash_ratio >= 10.0:
        asset_quality_notes.append(f"Bộ đệm tiền mặt an toàn ({cash_ratio:.1f}% tổng tài sản, ~{cash:,.0f} VND).")
    elif cash_ratio < 3.0 and total_assets > 0:
        asset_quality_notes.append(f"Cảnh báo: Tỷ lệ tiền mặt mỏng ({cash_ratio:.1f}% tổng tài sản), rủi ro thanh khoản ngắn hạn.")
    else:
        asset_quality_notes.append(f"Dự trữ tiền mặt ở mức bình thường ({cash_ratio:.1f}% tổng tài sản).")

    if illiquid_ratio > 65.0:
        asset_quality_verdict = "Rủi ro đọng vốn cao (Tồn kho & Phải thu lớn)"
        asset_quality_notes.append(f"Cảnh báo tài sản: Phải thu và Tồn kho chiếm {illiquid_ratio:.1f}% tổng tài sản, rủi ro đọng vốn kéo dài.")
    elif illiquid_ratio > 40.0:
        asset_quality_notes.append(f"Phải thu và Tồn kho chiếm {illiquid_ratio:.1f}% tổng tài sản.")

    # Đánh giá mức độ định giá tài sản (Asset Multiple Evaluation)
    valuation_risk_level = 1
    valuation_verdict = "ĐỊNH GIÁ HỢP LÝ"
    valuation_warning = ""
    reasons = []

    sym_code = fin.get("symbol", "").upper().strip()

    # Bẫy giá trị (Value Trap): P/B < 1.0 nhưng tài sản đọng vốn lớn hoặc nợ ngập đầu
    is_value_trap = (
        (pb is not None and pb < 1.0 and bvps and bvps > 0) and
        (
            illiquid_ratio > 45.0 or 
            debt_to_cash > 5.0 or
            receivables_ratio > 35.0 or
            sym_code in LEGAL_RISK_TICKERS
        )
    )

    if pb is None:
        valuation_risk_level = 4
        valuation_verdict = "VỐN CHỦ ÂM HOẶC THIẾU SỐ LIỆU TÀI SẢN"
        valuation_warning = "Không thể tính P/B do vốn chủ âm hoặc thiếu số liệu BCTC"
        reasons.append("Doanh nghiệp âm vốn chủ sở hữu do lỗ lũy kế hoặc thiếu BCTC, rủi ro tài chính cao.")

    elif is_value_trap:
        valuation_risk_level = 4
        valuation_verdict = "CẢNH BÁO BẪY GIÁ TRỊ (VALUE TRAP RISK)"
        valuation_warning = f"P/B {pb:.2f}x rẻ danh nghĩa: Tài sản đọng vốn {illiquid_ratio:.1f}%, nợ vay gấp {debt_to_cash:.1f}x tiền mặt!"
        reasons.append(f"Cảnh báo Bẫy giá trị: Thị giá ({current_price:,.0f} đ) thấp hơn sổ sách (BVPS {bvps:,.0f} đ, P/B {pb:.2f}x) nhưng chất lượng tài sản tiềm ẩn rủi ro lớn.")
        reasons.append(f"Các khoản Phải thu & Tồn kho chiếm {illiquid_ratio:.1f}% tổng tài sản, nợ vay gấp {debt_to_cash:.1f}x tiền mặt.")
        reasons.append("Tài sản thực khó chuyển đổi thành tiền mặt bảo vệ cổ đông; nguy cơ trích lập dự phòng bào mòn vốn chủ.")

    elif pb < 1.0 and bvps and bvps > 0:
        valuation_risk_level = 1
        valuation_verdict = "MÓN HỜI TÀI SẢN CHIẾT KHẤU SÂU (DEEP ASSET DISCOUNT)"
        reasons.append(f"Thị giá ({current_price:,.0f} đ) thấp hơn giá trị tài sản ròng sổ sách (BVPS: {bvps:,.0f} đ).")
        reasons.append(f"Chiết khấu {asset_discount_pct:.1f}% so với vốn chủ sở hữu, tạo biên an toàn tài sản.")

    elif pb <= 2.2:
        valuation_risk_level = 2
        valuation_verdict = "ĐỊNH GIÁ HỢP LÝ THEO TÀI SẢN (FAIR ASSET VALUATION)"
        reasons.append(f"Hệ số P/B ở mức {pb:.2f}x, tương xứng với quy mô vốn và tài sản hiện có.")

    elif pb <= 3.8:
        valuation_risk_level = 3
        valuation_verdict = "ĐỊNH GIÁ THẶNG DƯ (VALUATION PREMIUM)"
        if roe and roe >= 18.0:
            reasons.append(f"P/B ở mức cao ({pb:.2f}x) nhưng được bảo chứng bởi hiệu quả sinh lời ROE xuất sắc ({roe:.1f}%).")
        else:
            reasons.append(f"P/B {pb:.2f}x tương đối đắt so với tài sản hiện hữu, đòi hỏi tăng trưởng cao để duy trì thị giá.")

    elif pb <= 6.0:
        valuation_risk_level = 4
        valuation_verdict = "ĐỊNH GIÁ THẶNG DƯ CAO / ĐẦU CƠ DÒNG TIỀN (HIGH SPECULATIVE PREMIUM)"
        valuation_warning = f"Thị giá gấp {pb:.1f} lần giá trị sổ sách trong khi ROE chỉ {roe or 0:.1f}%"
        reasons.append(f"Thị giá ({current_price:,.0f} đ) cao gấp {pb:.1f}x lần tài sản sổ sách ({bvps:,.0f} đ).")
        reasons.append("Rủi ro điều chỉnh de-rating nếu dòng tiền đầu cơ rút bớt.")

    else:
        valuation_risk_level = 5
        valuation_verdict = "ĐỊNH GIÁ TÁCH RỜI TÀI SẢN THỰC (EXTREME MULTIPLE / DE-RATING RISK)"
        valuation_warning = f"Thị giá gấp {pb:.1f}x lần tài sản sổ sách! Rủi ro điều chỉnh bội số rất cao"
        reasons.append(f"Hệ số P/B đạt {pb:.1f}x, phản ánh kỳ vọng tăng trưởng cực đại hoặc dòng tiền đầu cơ mạnh.")
        reasons.append("Rủi ro điều chỉnh giảm định giá (Multiple Contraction) rất lớn khi tăng trưởng không đạt kỳ vọng.")

    return {
        "bvps": bvps,
        "tbvps": tbvps,
        "ncavps": ncavps,
        "pb": pb,
        "net_cash_per_share": net_cash_per_share,
        "asset_discount_pct": asset_discount_pct,
        "manipulation_risk_level": valuation_risk_level,
        "manipulation_verdict": valuation_verdict,
        "manipulation_warning": valuation_warning,
        "asset_quality_verdict": asset_quality_verdict,
        "asset_quality_notes": asset_quality_notes,
        "illiquid_ratio": illiquid_ratio,
        "cash_ratio": cash_ratio,
        "reasons": reasons
    }


def evaluate_cash_flow_and_forensic(fin: Dict[str, Any], sector: str = "GENERAL") -> Dict[str, Any]:
    """
    Bóc tách Báo cáo Lưu chuyển Tiền tệ (Cash Flow Statement), 
    Chất lượng Lợi nhuận và Mô hình Cảnh báo Kiệt quệ Tài chính Altman Z''-Score.
    Miễn trừ chỉ số Altman Z''-Score đối với nhóm Ngân hàng và Chứng khoán.
    """
    cfo_ttm = fin.get("cfo_ttm")
    capex_ttm = fin.get("capex_ttm") or 0.0
    fcf_ttm = fin.get("fcf_ttm") if fin.get("fcf_ttm") is not None else ((cfo_ttm - capex_ttm) if cfo_ttm is not None else None)
    cfi_ttm = fin.get("cfi_ttm")
    cff_ttm = fin.get("cff_ttm")
    ttm_profit = fin.get("ttm_profit")
    total_assets = fin.get("total_assets") or 0.0
    total_debt = fin.get("total_debt") or 0.0
    owners_equity = fin.get("owners_equity") or 0.0
    retained_earnings = fin.get("retained_earnings") or 0.0
    current_assets = fin.get("current_assets") or 0.0
    short_term_liab = fin.get("short_term_liabilities") or (total_debt * 0.6)
    working_capital = fin.get("working_capital")
    if working_capital is None:
        working_capital = current_assets - short_term_liab
    ebit_ttm = fin.get("ebit_ttm") or ((ttm_profit * 1.25) if ttm_profit else 0.0)
    quarterly_cf = fin.get("quarterly_cash_flows", [])

    red_flags = []
    
    # 1. Đánh giá chất lượng lợi nhuận (CFO vs Net Profit)
    earnings_quality_ratio = None
    if ttm_profit is not None and cfo_ttm is not None:
        if ttm_profit > 0:
            earnings_quality_ratio = round(cfo_ttm / ttm_profit, 2)
            if earnings_quality_ratio >= 1.0:
                quality_grade = "A"
                quality_verdict = "XUẤT SẮC (DÒNG TIỀN THẬT DỒI DÀO)"
                quality_desc = f"CFO ({cfo_ttm:,.0f} đ) vượt trội so với LNST ({ttm_profit:,.0f} đ) - Tỷ lệ {earnings_quality_ratio:.2f}x. Tiền mặt thực thu lớn hơn lợi nhuận kế toán."
            elif earnings_quality_ratio >= 0.7:
                quality_grade = "B"
                quality_verdict = "LÀNH MẠNH (ĐẠT CHUẨN)"
                quality_desc = f"CFO ({cfo_ttm:,.0f} đ) tương đương LNST ({ttm_profit:,.0f} đ) - Tỷ lệ {earnings_quality_ratio:.2f}x. Vòng quay tiền mặt ổn định."
            elif earnings_quality_ratio >= 0.2:
                quality_grade = "C"
                quality_verdict = "TRUNG BÌNH - NGUY CƠ ĐỌNG VỐN"
                quality_desc = f"CFO ({cfo_ttm:,.0f} đ) thấp hơn nhiều so với LNST ({ttm_profit:,.0f} đ) - Tỷ lệ chỉ {earnings_quality_ratio:.2f}x. Lợi nhuận bị chiếm dụng vốn qua công nợ."
                red_flags.append(f"CFO thấp hơn nhiều so với LNST (Tỷ lệ {earnings_quality_ratio:.2f}x), tiền bị giam ở công nợ hoặc hàng tồn kho.")
            else:
                quality_grade = "D"
                quality_verdict = "BÁO ĐỘNG ĐỎ: LỢI NHUẬN TRÊN GIẤY!"
                quality_desc = f"CFO âm hoặc gần bằng 0 ({cfo_ttm:,.0f} đ) trong khi LNST dương ({ttm_profit:,.0f} đ). Doanh nghiệp báo lãi nhưng thực chất không thu được tiền mặt về!"
                red_flags.append("🚨 BÁO ĐỘNG ĐỎ DÒNG TIỀN: CFO âm nặng trong khi LNST dương. Nguy cơ lợi nhuận ảo trên sổ sách kế toán!")
        else:
            quality_grade = "D" if cfo_ttm < 0 else "C"
            quality_verdict = "DOANH NGHIỆP ĐANG LỖ HOẶC THÂM HỤT TIỀN"
            quality_desc = f"LNST âm ({ttm_profit:,.0f} đ), CFO ghi nhận {cfo_ttm:,.0f} đ."
            if cfo_ttm < 0:
                red_flags.append("Cả CFO và LNST đều âm, doanh nghiệp đang thâm hụt tiền mặt trong hoạt động kinh doanh.")
    else:
        quality_grade = "B"
        quality_verdict = "THIẾU SỐ LIỆU DÒNG TIỀN ĐẦY ĐỦ"
        quality_desc = "Chưa có đủ số liệu lưu chuyển tiền tệ để đánh giá tỷ số CFO/LNST."

    # Kiểm tra FCF
    if fcf_ttm is not None:
        if fcf_ttm > 0:
            fcf_verdict = f"Dương ({fcf_ttm:,.0f} đ). Doanh nghiệp tự chủ tài chính tốt sau chi tiêu vốn CapEx."
        else:
            fcf_verdict = f"Âm ({fcf_ttm:,.0f} đ). Nhu cầu vốn đầu tư CapEx ({capex_ttm:,.0f} đ) vượt quá dòng tiền kinh doanh tạo ra."
            if capex_ttm > 0 and abs(fcf_ttm) > owners_equity * 0.3 and owners_equity > 0:
                red_flags.append("CapEx mở rộng vượt quá khả năng tạo tiền từ CFO, gia tăng áp lực nợ vay.")
    else:
        fcf_verdict = "Chưa có đủ số liệu CapEx để tính FCF."

    # 2. TÍNH TOÁN ALTMAN Z''-SCORE (EMERGING MARKETS)
    altman_z = 0.0
    z_zone = "SAFE"
    z_verdict = "AN TOÀN TÀI CHÍNH (SAFE ZONE)"

    if sector in ["BANK", "SECURITIES"]:
        altman_z = None
        z_zone = "NOT_APPLICABLE"
        z_verdict = "KHÔNG ÁP DỤNG CHO NGÀNH TÀI CHÍNH"
        z_desc = "Mô hình Altman Z''-Score thiết kế cho doanh nghiệp sản xuất/thương mại, không áp dụng cho định chế tài chính."
    elif total_assets > 0:
        x1 = working_capital / total_assets
        x2 = retained_earnings / total_assets
        x3 = ebit_ttm / total_assets
        tot_liab = total_assets - owners_equity if total_assets > owners_equity else total_debt
        x4 = (owners_equity / tot_liab) if tot_liab > 0 else 3.0

        altman_z = round(6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4, 2)

        if altman_z >= 2.60:
            z_zone = "SAFE"
            z_verdict = "VÙNG AN TOÀN CAO (SAFE ZONE)"
            z_desc = f"Chỉ số Altman Z''-Score đạt {altman_z:.2f} (> 2.60). Rủi ro kiệt quệ tài chính thấp."
        elif altman_z >= 1.10:
            z_zone = "GREY"
            z_verdict = "VÙNG XÁM CẢNH BÁO (GREY ZONE)"
            z_desc = f"Chỉ số Altman Z''-Score đạt {altman_z:.2f} (trong ngưỡng 1.10 - 2.60). Sức khỏe tài chính trung bình."
        else:
            z_zone = "DISTRESS"
            z_verdict = "VÙNG NGUY HIỂM KIỆT QUỆ TÀI CHÍNH (DISTRESS ZONE)"
            z_desc = f"Chỉ số Altman Z''-Score rớt xuống {altman_z:.2f} (< 1.10). Báo động rủi ro thanh toán nợ vay cao."
            red_flags.append(f"Altman Z''-Score ở mức báo động {altman_z:.2f} (< 1.10), cảnh báo rủi ro kiệt quệ tài chính.")
    else:
        altman_z = None
        z_zone = "INSUFFICIENT_DATA"
        z_verdict = "THIẾU DỮ LIỆU TÀI SẢN"
        z_desc = "Không đủ dữ liệu tài sản để tính Altman Z''-Score."

    return {
        "cfo_ttm": cfo_ttm or 0.0,
        "capex_ttm": capex_ttm,
        "fcf_ttm": fcf_ttm or 0.0,
        "cfi_ttm": cfi_ttm or 0.0,
        "cff_ttm": cff_ttm or 0.0,
        "earnings_quality_ratio": earnings_quality_ratio or 1.0,
        "quality_grade": quality_grade,
        "quality_verdict": quality_verdict,
        "quality_desc": quality_desc,
        "fcf_verdict": fcf_verdict,
        "altman_z": altman_z,
        "z_zone": z_zone,
        "z_status": z_zone,
        "z_verdict": z_verdict,
        "z_desc": z_desc,
        "red_flags": red_flags,
        "quarterly_cash_flows": quarterly_cf,
        "ttm_profit": ttm_profit or 0.0
    }


def analyze_fundamentals(fin: Dict[str, Any], current_price: float, quote: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Tổng hợp toàn bộ phân tích cơ bản (FA) đa chiều theo chu trình Top-Down:
    1. Vĩ mô & Ma trận Chu kỳ ngành (Macro & Sector Cycle)
    2. Bóc tách Báo cáo Lưu chuyển Tiền tệ & Dòng tiền Thật (Cash Flow Forensic)
    3. Mô hình Cảnh báo Kiệt quệ Tài chính Altman Z''-Score
    4. Piotroski F-Score (Sức khỏe bảng cân đối)
    5. Warren Buffett (Moat & Định giá theo ngành)
    6. Định giá theo Khối tài sản & Đánh giá Bội số tài sản
    7. Peter Lynch (GARP & PEG)
    8. Bóc tách Mô hình kinh doanh cốt lõi (Core Business Segments - Không bịa số liệu)
    9. Bóc tách Quản trị, Cơ cấu Cổ đông & Mạng lưới Công ty con (G-Score)
    """
    symbol = fin.get("symbol", "").upper().strip()
    f_score_res = calculate_piotroski_score(fin)
    f_score = f_score_res["score"]
    
    buffett = evaluate_buffett_moat(fin, current_price)
    lynch = evaluate_peter_lynch(fin, current_price)
    growth_quality = evaluate_growth_and_earnings_quality(fin)
    asset_valuation = evaluate_asset_based_valuation(fin, current_price)
    dupont = evaluate_dupont_decomposition(fin)
    roic = calculate_roic(fin)

    # 1. Phân tích Quản trị Doanh nghiệp & Cổ đông
    gov_data = get_governance_data(symbol)
    overview_data = (gov_data.get("overview") if gov_data else None) or fin.get("overview")

    # 2. Phân tích Vĩ mô & Chu kỳ Ngành
    macro_analysis = analyze_macro_and_sector_cycle(symbol, overview_data)
    sector_key = macro_analysis.get("sector_key", buffett.get("sector", "GENERAL"))

    cash_flow = evaluate_cash_flow_and_forensic(fin, sector=sector_key)

    # 3. Phân tích Mảng kinh doanh cốt lõi (Segments - Xác minh thực tế)
    company_name = quote.get("company_name", "") if quote else ""
    segments = analyze_company_segments(
        symbol,
        company_name=company_name,
        sector=sector_key
    )

    governance = analyze_governance_and_ownership(
        symbol,
        gov_data,
        fin,
        current_price,
        quote
    )

    # Chấm điểm tổng hợp FA (thang 100)
    asset_score = 50
    if asset_valuation["manipulation_risk_level"] == 1:
        asset_score = 90
    elif asset_valuation["manipulation_risk_level"] == 2:
        asset_score = 75
    elif asset_valuation["manipulation_risk_level"] == 3:
        asset_score = 50
    elif asset_valuation["manipulation_risk_level"] == 4:
        asset_score = 25
    else:
        asset_score = 10

    g_score_val = governance.get("g_score", 60)
    macro_tailwind = macro_analysis.get("tailwind_score", 70)

    cf_score = 85 if cash_flow["quality_grade"] == "A" else (70 if cash_flow["quality_grade"] == "B" else (40 if cash_flow["quality_grade"] == "C" else 15))
    if cash_flow["z_zone"] == "SAFE":
        cf_score = min(100, cf_score + 10)
    elif cash_flow["z_zone"] == "DISTRESS":
        cf_score = max(5, cf_score - 25)

    raw_fa_score = (
        macro_tailwind * FA_WEIGHTS.get("macro", 0.15) +
        (f_score / 9.0 * 100) * FA_WEIGHTS.get("f_score", 0.15) +
        buffett["score"] * FA_WEIGHTS.get("buffett", 0.15) +
        asset_score * FA_WEIGHTS.get("asset_valuation", 0.15) +
        cf_score * FA_WEIGHTS.get("cash_flow", 0.15) +
        lynch["score"] * FA_WEIGHTS.get("lynch", 0.10) +
        g_score_val * FA_WEIGHTS.get("governance", 0.15)
    )

    valuation_warning = buffett.get("valuation_warning", "")
    if asset_valuation.get("manipulation_warning"):
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + asset_valuation["manipulation_warning"]

    if cash_flow["quality_grade"] == "D":
        raw_fa_score = max(5, raw_fa_score - 25)
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + "Cảnh báo Lợi nhuận trên giấy (CFO âm)"
    if cash_flow["z_zone"] == "DISTRESS":
        raw_fa_score = max(5, raw_fa_score - 20)
        valuation_warning = (valuation_warning + " | " if valuation_warning else "") + "Cảnh báo Rủi ro Kiệt quệ Tài chính (Altman Z < 1.1)"

    if governance.get("subsidiary_web", {}).get("circular_capital_risk_level", 1) >= 4:
        raw_fa_score = max(5, raw_fa_score - 30)
    elif g_score_val < 40:
        raw_fa_score = max(5, raw_fa_score - 25)
    elif asset_valuation["manipulation_risk_level"] >= 4:
        raw_fa_score = max(5, raw_fa_score - 15)
    elif valuation_warning:
        raw_fa_score = max(10, raw_fa_score - 10)

    fa_total_score = int(min(100, max(0, raw_fa_score)))

    # Đồng bộ các trạng thái định giá chuẩn xác vào dict ratios
    ratios_dict = dict(fin)
    ratios_dict["pe"] = buffett.get("pe")
    ratios_dict["pe_status"] = buffett.get("pe_status", "VALID")
    ratios_dict["pb"] = buffett.get("pb")
    ratios_dict["pb_status"] = buffett.get("pb_status", "VALID")
    ratios_dict["roic"] = roic
    ratios_dict["dupont"] = dupont

    # Xác định trạng thái Data Quality tổng thể
    has_essential_data = (
        fin.get("total_assets") is not None and 
        fin.get("owners_equity") is not None and
        (fin.get("eps") is not None or fin.get("ttm_profit") is not None)
    )
    if has_essential_data:
        dq_status = "VALID" if not valuation_warning else "VALID_WITH_WARNINGS"
    else:
        dq_status = "INSUFFICIENT_DATA"

    return {
        "sector": sector_key,
        "sector_name": macro_analysis.get("sector_name", "Doanh nghiệp"),
        "f_score": f_score,
        "piotroski_details": f_score_res,
        "fa_total_score": fa_total_score,
        "data_quality_status": dq_status,
        "macro": macro_analysis,
        "cash_flow": cash_flow,
        "buffett": buffett,
        "lynch": lynch,
        "growth_quality": growth_quality,
        "asset_valuation": asset_valuation,
        "dupont": dupont,
        "roic": roic,
        "segments": segments,
        "governance": governance,
        "valuation_warning": valuation_warning,
        "ratios": ratios_dict
    }
