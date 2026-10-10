"""
Module Sinh Báo Cáo Phân Tích Dạng HTML Trực Quan (Standalone Responsive HTML Report Generator)
Tối ưu hóa hiển thị mượt mà trên cả Mobile (điện thoại) và Desktop (máy tính).
Thiết kế theo chuẩn giao diện Fintech / Bloomberg Terminal Dark Theme cao cấp.
Tích hợp biểu đồ tương tác so sánh Dòng tiền thật (CFO) vs Lợi nhuận (LNST) qua Chart.js.
Nâng cấp 7 Tầng phân tích chuyên sâu:
  - Tầng 1: Vĩ mô & Chu kỳ Ngành (Macro & Sector Matrix)
  - Tầng 2: Mô hình kinh doanh cốt lõi & Chi tiết từng dịch vụ (Core Business Breakdown)
  - Tầng 3: Danh mục dự án trọng điểm & Rà soát pháp lý / GPMB (Key Projects & Legal Audit)
  - Tầng 4: Sức khỏe tài chính & Bóc tách Dòng tiền thật (Cash Flow Forensic)
  - Tầng 5: Kiểm toán Ban Lãnh đạo, Tính minh bạch & Radar công ty sân sau (Governance & Shell Radar)
  - Tầng 6: Phân tích Kỹ thuật Nâng cao (VCP Minervini, VSA Nến gom/xả, Fibonacci, Overhead Supply)
  - Tầng 7: Bàn tròn Hội đồng Phản biện AI Đa trường phái (Council Grid 6 chuyên gia & Clash of Perspectives)
100% Tiếng Việt trong sáng, giải thích thuật ngữ dễ hiểu cho người không chuyên.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from config import REPORTS_DIR


def generate_html_report(
    symbol: str,
    quote: Dict[str, Any],
    fa_result: Dict[str, Any],
    ta_result: Dict[str, Any],
    trade_setup: Dict[str, Any],
    council_result: Dict[str, Any]
) -> Path:
    """
    Tạo file báo cáo HTML độc lập tại reports/YYYY-MM-DD_{symbol}.html.
    """
    symbol = symbol.upper().strip()
    today_str = datetime.now().strftime("%Y-%m-%d")
    html_filename = f"{today_str}_{symbol}.html"
    html_path = REPORTS_DIR / html_filename

    # Dữ liệu trích xuất giá & khuyến nghị
    current_price = trade_setup.get("current_price", quote.get("price", 0))
    change_pct = quote.get("change_pct", 0)
    chg_sign = "+" if change_pct > 0 else ""
    chg_color = "#10b981" if change_pct > 0 else ("#ef4444" if change_pct < 0 else "#f59e0b")

    action = trade_setup.get("action", "QUAN SÁT")
    consensus_score = trade_setup.get("consensus_score", 50)
    
    # Màu sắc hành động
    if "MUA MẠNH" in action:
        action_bg = "rgba(16, 185, 129, 0.15)"
        action_border = "#10b981"
        action_text = "#10b981"
    elif "MUA" in action:
        action_bg = "rgba(59, 130, 246, 0.15)"
        action_border = "#3b82f6"
        action_text = "#3b82f6"
    elif "THEO DÕI" in action:
        action_bg = "rgba(245, 158, 11, 0.15)"
        action_border = "#f59e0b"
        action_text = "#f59e0b"
    else:
        action_bg = "rgba(239, 68, 68, 0.15)"
        action_border = "#ef4444"
        action_text = "#ef4444"

    # 1. Trích xuất Vĩ mô & Ngành
    macro = fa_result.get("macro", {})
    sector_name = macro.get("sector_name", quote.get("industry", "Doanh nghiệp"))
    cycle_phase = macro.get("cycle_phase", "Bình thường")
    tailwind_score = macro.get("tailwind_score", 70)
    tailwind_color = "#10b981" if tailwind_score >= 80 else ("#3b82f6" if tailwind_score >= 70 else "#f59e0b")

    # 2. Trích xuất Dòng tiền & BCTC
    cf = fa_result.get("cash_flow", {})
    cfo_ttm = cf.get("cfo_ttm", 0)
    capex_ttm = cf.get("capex_ttm", 0)
    fcf_ttm = cf.get("fcf_ttm", 0)
    quality_grade = cf.get("quality_grade", "B")
    quality_grade_color = "#10b981" if quality_grade == "A" else ("#3b82f6" if quality_grade == "B" else ("#f59e0b" if quality_grade == "C" else "#ef4444"))
    altman_z = cf.get("altman_z", 0)
    z_zone = cf.get("z_zone", "SAFE")
    z_color = "#10b981" if z_zone == "SAFE" else ("#f59e0b" if z_zone == "GREY" else "#ef4444")
    
    fin = fa_result.get("ratios", {})
    net_profit_ttm = fin.get("ttm_profit", 0)
    f_score = fa_result.get("f_score", 0)
    f_color = "#10b981" if f_score >= 7 else ("#3b82f6" if f_score >= 5 else "#ef4444")

    # Dữ liệu vẽ chart dòng tiền (quý)
    quarterly_cf = cf.get("quarterly_cash_flows", [])
    chart_quarters = [q["quarter"] for q in quarterly_cf] if quarterly_cf else ["Q3", "Q4", "Q1", "Q2"]
    chart_cfo = [round(q["cfo"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]
    chart_np = [round(q["net_profit"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]
    chart_fcf = [round(q["fcf"] / 1e9, 1) for q in quarterly_cf] if quarterly_cf else [0, 0, 0, 0]

    # 3. Trích xuất Tài sản & Radar thao túng
    asset_val = fa_result.get("asset_valuation", {})
    pb = asset_val.get("pb", "N/A")
    bvps = asset_val.get("bvps", 0)
    manip_level = asset_val.get("manipulation_risk_level", 1)
    manip_color = "#10b981" if manip_level <= 2 else ("#f59e0b" if manip_level == 3 else "#ef4444")

    # 4. Trích xuất Quản trị Ban Lãnh đạo & Sân sau
    gov = fa_result.get("governance", {})
    g_score = gov.get("g_score", 60)
    g_color = "#10b981" if g_score >= 75 else ("#3b82f6" if g_score >= 60 else ("#f59e0b" if g_score >= 45 else "#ef4444"))
    own = gov.get("ownership", {})
    lead = gov.get("leadership", {})
    sub_web = gov.get("subsidiary_web", {})

    integrity_verdict = gov.get("integrity_verdict", "Ban điều hành minh bạch, định hướng phát triển cốt lõi ổn định.")
    shell_risk_desc = gov.get("shell_risk_desc", "Không phát hiện dấu hiệu giao dịch sân sau hay rút ruột vốn nghiêm trọng.")
    dividend_evidence = gov.get("dividend_evidence", "Lịch sử chi trả cổ tức bình thường.")
    leadership_analysis_vi = gov.get("leadership_analysis_vi", "Lãnh đạo có năng lực điều hành ổn định trong ngành.")

    # 5. Phân khúc hoạt động & Chi tiết dịch vụ
    segments_data = fa_result.get("segments", {}).get("segments", [])
    business_model_summary = fa_result.get("segments", {}).get("business_model_summary", "Mô hình kinh doanh tổng hợp.")

    # Render segments bảng tóm tắt
    seg_rows_html = ""
    for s in segments_data:
        seg_rows_html += f"""
        <tr>
            <td style="font-weight: 600; color: #f1f5f9;">{s.get('name')}</td>
            <td style="text-align: right; color: #38bdf8; font-weight: 600;">{s.get('rev_share_pct')}%</td>
            <td style="text-align: right; color: #34d399; font-weight: 600;">{s.get('gross_profit_share_pct')}%</td>
            <td style="text-align: right; color: #fbbf24; font-weight: 600;">{s.get('gross_margin_pct')}%</td>
            <td><span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid rgba(139, 92, 246, 0.4);">{s.get('role')}</span></td>
            <td style="font-size: 0.84rem; color: #94a3b8;">{s.get('highlights')}</td>
        </tr>
        """

    # Render khối chi tiết từng dịch vụ (Service Description)
    seg_detail_cards_html = ""
    for idx, s in enumerate(segments_data, 1):
        serv_desc = s.get("service_description") or f"Hoạt động cung ứng sản phẩm và dịch vụ trong phân khúc {s.get('name')}."
        seg_detail_cards_html += f"""
        <div style="background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 12px; padding: 16px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <div style="font-weight: 700; color: #38bdf8; font-size: 0.95rem;">
                    #{idx}. {s.get('name')} <span style="font-size: 0.8rem; color: #94a3b8; font-weight: normal;">(Chiếm {s.get('rev_share_pct')}% DT • {s.get('gross_profit_share_pct')}% Lãi gộp)</span>
                </div>
                <span class="badge" style="background: rgba(52, 211, 153, 0.15); color: #34d399;">Biên lãi {s.get('gross_margin_pct')}%</span>
            </div>
            <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                <b>Cơ chế hoạt động & tạo tiền:</b> {serv_desc}
            </div>
        </div>
        """

    # 6. Danh mục Dự án Trọng điểm (Projects)
    projects_list = fa_result.get("segments", {}).get("projects", [])
    project_rows_html = ""
    if projects_list:
        for p in projects_list:
            p_name = p.get("name", "")
            p_scale = p.get("scale", "")
            p_status = p.get("progress_status") or p.get("status", "Đang triển khai")
            p_profit = p.get("profit_contribution", "Đóng góp doanh thu")
            p_legal = p.get("legal_and_hurdles") or p.get("bottlenecks_and_risks", "Pháp lý đầy đủ")
            flag = p.get("flag", "")
            if not flag:
                p_text_lower = (p_status + " " + p_legal).lower()
                if "100%" in p_text_lower or "hoàn tất" in p_text_lower or "không có vướng" in p_text_lower or "hoàn chỉnh" in p_text_lower:
                    flag = "TÍCH CỰC"
                elif "vướng" in p_text_lower or "chờ" in p_text_lower:
                    flag = "CẢNH BÁO"
                else:
                    flag = "TIẾN ĐỘ BÌNH THƯỜNG"

            if flag == "TÍCH CỰC":
                p_flag_badge = '<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981;">TÍCH CỰC</span>'
            elif flag == "CẢNH BÁO":
                p_flag_badge = '<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444;">CẦN THEO DÕI</span>'
            else:
                p_flag_badge = '<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b;">TIẾN ĐỘ BÌNH THƯỜNG</span>'

            project_rows_html += f"""
            <tr>
                <td style="font-weight: 700; color: #f1f5f9;">{p_name}</td>
                <td style="color: #38bdf8; font-weight: 600;">{p_scale}</td>
                <td style="color: #cbd5e1; font-size: 0.85rem;">{p_status}</td>
                <td style="color: #34d399; font-size: 0.85rem; font-weight: 500;">{p_profit}</td>
                <td style="color: #cbd5e1; font-size: 0.85rem;">{p_legal}</td>
                <td style="text-align: center;">{p_flag_badge}</td>
            </tr>
            """
    else:
        project_rows_html = """
        <tr>
            <td colspan="6" style="text-align: center; color: #94a3b8; padding: 20px;">
                Dữ liệu các dự án riêng lẻ đang được cập nhật thêm theo báo cáo phân tích mới nhất.
            </td>
        </tr>
        """

    # 7. Phân tích Kỹ thuật Nâng cao (Advanced TA)
    ind = ta_result.get("indicators", {})
    vol_ratio = ind.get("vol_ratio", 1.0)
    rsi14 = ind.get("rsi14", 50)
    vsa_phase = ta_result.get("vsa", {}).get("phase", "Tích lũy")
    is_breakout = ta_result.get("oneil", {}).get("is_breakout", False)

    adv_ta = ta_result.get("advanced_ta", {})
    vcp_data = adv_ta.get("vcp") if isinstance(adv_ta.get("vcp"), dict) else {}
    vsa_sig = adv_ta.get("vsa_signals") if isinstance(adv_ta.get("vsa_signals"), dict) else {}
    fibo_data = adv_ta.get("fibonacci") if isinstance(adv_ta.get("fibonacci"), dict) else {}
    
    overhead_raw = adv_ta.get("overhead_supply_detail") or adv_ta.get("overhead_supply")
    if isinstance(overhead_raw, dict):
        overhead_data = overhead_raw
    else:
        oh_val = float(overhead_raw) if overhead_raw else 0.0
        overhead_data = {
            "resistance_cluster": f"{oh_val:,.0f} đ (Đỉnh cũ)" if oh_val > 0 else "Không có vùng kẹp lớn",
            "supply_intensity": "Thấp" if current_price >= oh_val and oh_val > 0 else "Vừa phải",
            "explanation": f"Kháng cự nguồn cung kẹp hàng tại đỉnh cũ quanh {oh_val:,.0f} đ."
        }

    vcp_contractions_str = " &rarr; ".join(vcp_data.get("contractions", ["Không có biến động lớn"]))
    vsa_signals_list = vsa_sig.get("signal_descriptions", ["Vận động khối lượng dao động bình thường quanh trung bình 20 phiên."])
    vsa_signals_html = "".join([f"<li>{s}</li>" for s in vsa_signals_list])

    # 8. Bàn tròn Hội đồng AI Đa trường phái (Council Grid & Clash)
    council_members = council_result.get("members", [])
    voting_summary = council_result.get("voting_summary", {})
    clash_data = council_result.get("clash_of_perspectives", [])

    bull_count = voting_summary.get("bull_count", 0)
    bear_count = voting_summary.get("bear_count", 0)
    watch_count = voting_summary.get("watch_count", max(0, len(council_members) - bull_count - bear_count))
    consensus_score = voting_summary.get("consensus_score", trade_setup.get("consensus_score", 50))
    verdict = voting_summary.get("action") or voting_summary.get("verdict", trade_setup.get("action", "QUAN SÁT"))

    council_cards_html = ""
    for m in council_members:
        st_color = m.get("stance_color", "#3b82f6")
        badge = m.get("badge", "👤 CHUYÊN GIA")
        avatar = badge.split()[0] if badge else "👤"
        name = m.get("name", "Chuyên gia AI")
        role = m.get("role_title") or m.get("role", "Thành viên Hội đồng")
        stance = m.get("stance", "QUAN SÁT")
        score = m.get("score", 50)
        core_thesis = m.get("core_thesis") or m.get("key_thesis", "")
        invalidation = m.get("invalidation") or m.get("invalidation_condition", "Không có điều kiện cụ thể.")
        
        args_list = m.get("arguments", [])
        args_html = "".join([f"<li style='margin-bottom: 4px;'>{a}</li>" for a in args_list]) if args_list else ""

        council_cards_html += f"""
        <div style="background: rgba(15, 23, 42, 0.75); border: 1px solid var(--border); border-radius: 14px; padding: 18px; display: flex; flex-direction: column; justify-content: space-between;">
            <div>
                <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 1.8rem;">{avatar}</span>
                        <div>
                            <div style="font-weight: 700; color: #fff; font-size: 1rem;">{name}</div>
                            <div style="font-size: 0.78rem; color: #94a3b8;">{role}</div>
                        </div>
                    </div>
                    <span class="badge" style="background: rgba(255,255,255,0.06); color: {st_color}; border: 1px solid {st_color}; font-size: 0.75rem;">
                        {stance} ({score}/100)
                    </span>
                </div>
                
                <div style="margin-bottom: 10px; font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                    <b style="color: #38bdf8;">Luận điểm cốt lõi:</b> {core_thesis}
                </div>

                {f'<ul class="bullet-list" style="margin-bottom: 12px; font-size: 0.84rem;">{args_html}</ul>' if args_html else ''}
            </div>
            
            <div style="border-top: 1px solid rgba(255,255,255,0.08); padding-top: 10px; margin-top: 10px; font-size: 0.82rem; color: #f87171; line-height: 1.5;">
                <b>⚠️ Điều kiện mất hiệu lực:</b> {invalidation}
            </div>
        </div>
        """

    # Clash of perspectives HTML
    clash_html = ""
    if isinstance(clash_data, list):
        for idx, cl in enumerate(clash_data, 1):
            clash_html += f"""
            <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 18px; margin-bottom: 16px;">
                <div style="font-weight: 700; color: #f87171; font-size: 0.95rem; margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                    <span>⚔️ ĐỐI ĐẦU TRANH BIỆN #{idx}: {cl.get('topic', 'Va chạm góc nhìn')}</span>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 14px; margin-bottom: 14px;">
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border-left: 3px solid #38bdf8;">
                        <div style="font-size: 0.82rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px;">{cl.get('side_a', {}).get('speaker')}</div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">"{cl.get('side_a', {}).get('argument')}"</div>
                    </div>
                    <div style="background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border-left: 3px solid #fbbf24;">
                        <div style="font-size: 0.82rem; font-weight: 700; color: #fbbf24; margin-bottom: 4px;">{cl.get('side_b', {}).get('speaker')}</div>
                        <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">"{cl.get('side_b', {}).get('argument')}"</div>
                    </div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 8px; padding: 12px;">
                    <span style="font-weight: 700; color: #34d399; font-size: 0.85rem;">🛡️ Phán quyết Điều hòa của Chief Risk Officer (CRO):</span>
                    <p style="font-size: 0.85rem; color: #e2e8f0; margin-top: 4px; line-height: 1.5;">{cl.get('cro_synthesis')}</p>
                </div>
            </div>
            """
    elif isinstance(clash_data, str) and clash_data.strip():
        clash_html = f"""
        <div style="background: rgba(30, 41, 59, 0.6); border: 1px solid rgba(239, 68, 68, 0.3); border-radius: 14px; padding: 18px; margin-bottom: 16px;">
            <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">
                {clash_data.replace(chr(10), '<br>')}
            </div>
        </div>
        """

    # Council full text report
    council_text = council_result.get("council_report", "")
    council_report_html = ""
    if council_text:
        formatted_council = council_text.replace("### ", '<h4 style="color: #38bdf8; margin: 18px 0 8px 0;">').replace("\n- ", "<br>&bull; ")
        council_report_html = f"""
        <details style="margin-top: 24px; background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 12px; padding: 16px;">
            <summary style="cursor: pointer; font-weight: 700; color: #94a3b8; font-size: 0.9rem;">
                📜 Xem Toàn văn Báo cáo Thảo luận Chi tiết của Ban Điều phối Hội đồng AI &darr;
            </summary>
            <div style="margin-top: 14px; font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                {formatted_council}
            </div>
        </details>
        """

    # Render shareholders
    sh_rows_html = ""
    for sh in own.get("top_shareholders", [])[:5]:
        sh_rows_html += f"""
        <tr>
            <td style="color: #f1f5f9; font-weight: 500;">{sh.get('name')}</td>
            <td style="text-align: right; color: #38bdf8; font-weight: 600;">{sh.get('percentage')}%</td>
            <td style="text-align: right; color: #94a3b8;">{sh.get('shares', 0):,.0f} CP</td>
        </tr>
        """

    # Macro drivers list
    macro_drivers_html = "".join([f"<li>{d}</li>" for d in macro.get("macro_drivers", [])])
    key_metrics_html = "".join([f"<li>{m}</li>" for m in macro.get("key_metrics_to_watch", [])])
    red_flags_html = "".join([f"<li style='color: #f87171;'>⚠️ {rf}</li>" for rf in cf.get("red_flags", [])]) if cf.get("red_flags") else "<li style='color: #34d399;'>✅ Không phát hiện cờ đỏ tài chính nghiêm trọng về dòng tiền.</li>"

    val_warn_text = trade_setup.get('value_warning', '')
    val_warn_html = f"<div style='margin-top: 8px; color: #f87171; font-size: 0.85rem;'>⚠️ <b>Cảnh báo định giá:</b> {val_warn_text}</div>" if val_warn_text else ""

    val_gap_text = trade_setup.get('valuation_gap_explanation', '')
    val_gap_html = f"<div style='margin-top: 8px; color: #38bdf8; font-size: 0.85rem;'>💡 <b>Lý giải chênh lệch thị giá vs giá trị thực:</b> {val_gap_text}</div>" if val_gap_text else ""

    # HTML Template
    html_content = f"""<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Báo cáo Chiến lược Toàn diện {symbol} | Vietnam Stock Analyzer</title>
    <!-- Chart.js via CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --bg-main: #0a0e17;
            --bg-card: #111827;
            --bg-card-alt: #1a2333;
            --border: #263345;
            --border-highlight: #3b82f6;
            --text-primary: #f8fafc;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent-green: #10b981;
            --accent-red: #ef4444;
            --accent-blue: #3b82f6;
            --accent-amber: #f59e0b;
            --accent-purple: #8b5cf6;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background-color: var(--bg-main);
            color: var(--text-primary);
            line-height: 1.5;
            padding-bottom: 60px;
            -webkit-font-smoothing: antialiased;
        }}

        /* Header Bar */
        .top-navbar {{
            position: sticky;
            top: 0;
            z-index: 100;
            background: rgba(10, 14, 23, 0.96);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid var(--border);
            padding: 12px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .brand-title {{
            font-size: 0.9rem;
            font-weight: 700;
            color: var(--text-secondary);
            letter-spacing: 0.5px;
            text-transform: uppercase;
        }}

        .report-time {{
            font-size: 0.78rem;
            color: var(--text-muted);
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px 16px;
        }}

        /* Executive Header */
        .hero-card {{
            background: linear-gradient(145deg, #131c2e, #0f172a);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
        }}

        .hero-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            flex-wrap: wrap;
            gap: 16px;
        }}

        .hero-left h1 {{
            font-size: 2.2rem;
            font-weight: 800;
            letter-spacing: -0.5px;
            color: #fff;
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .hero-left p {{
            color: var(--text-secondary);
            font-size: 0.95rem;
            margin-top: 4px;
        }}

        .price-badge-group {{
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-top: 10px;
        }}

        .hero-price {{
            font-size: 1.8rem;
            font-weight: 800;
            color: {chg_color};
        }}

        .hero-change {{
            font-size: 1.05rem;
            font-weight: 700;
            color: {chg_color};
            background: rgba(255, 255, 255, 0.05);
            padding: 4px 10px;
            border-radius: 8px;
        }}

        .hero-action-box {{
            text-align: right;
            background: {action_bg};
            border: 1px solid {action_border};
            padding: 16px 22px;
            border-radius: 14px;
        }}

        .hero-action-label {{
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-secondary);
            font-weight: 600;
        }}

        .hero-action-title {{
            font-size: 1.35rem;
            font-weight: 800;
            color: {action_text};
            margin-top: 2px;
        }}

        .consensus-meter {{
            font-size: 0.85rem;
            color: var(--text-secondary);
            margin-top: 4px;
        }}

        /* Section Layout */
        .section-title {{
            font-size: 1.25rem;
            font-weight: 700;
            margin: 34px 0 16px 0;
            display: flex;
            align-items: center;
            gap: 10px;
            color: #f8fafc;
        }}

        .card-grid-2 {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 20px;
        }}

        .card-grid-3 {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 18px;
        }}

        .card {{
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 14px;
            padding: 20px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        }}

        .card-header {{
            font-size: 1rem;
            font-weight: 700;
            color: #f1f5f9;
            margin-bottom: 14px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            padding-bottom: 10px;
        }}

        /* Badges */
        .badge {{
            display: inline-block;
            font-size: 0.75rem;
            font-weight: 700;
            padding: 4px 10px;
            border-radius: 6px;
            letter-spacing: 0.3px;
        }}

        /* Tables */
        .table-responsive {{
            overflow-x: auto;
            -webkit-overflow-scrolling: touch;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.88rem;
        }}

        th, td {{
            padding: 10px 12px;
            border-bottom: 1px solid var(--border);
            text-align: left;
        }}

        th {{
            background: rgba(15, 23, 42, 0.8);
            color: var(--text-muted);
            font-weight: 600;
            font-size: 0.78rem;
            text-transform: uppercase;
        }}

        /* Bullet lists */
        ul.bullet-list {{
            list-style: none;
            padding: 0;
        }}

        ul.bullet-list li {{
            position: relative;
            padding-left: 20px;
            margin-bottom: 8px;
            font-size: 0.88rem;
            color: #cbd5e1;
            line-height: 1.45;
        }}

        ul.bullet-list li::before {{
            content: "•";
            position: absolute;
            left: 4px;
            color: var(--accent-blue);
            font-size: 1.1rem;
        }}

        /* Progress Bar */
        .progress-bar-bg {{
            background: rgba(255, 255, 255, 0.1);
            height: 8px;
            border-radius: 4px;
            overflow: hidden;
            margin: 8px 0;
        }}

        .progress-bar-fill {{
            height: 100%;
            border-radius: 4px;
        }}

        /* Mobile Optimization */
        @media (max-width: 768px) {{
            .hero-header {{
                flex-direction: column;
                align-items: stretch;
            }}
            .hero-action-box {{
                text-align: left;
            }}
            .card-grid-2, .card-grid-3 {{
                grid-template-columns: 1fr;
            }}
            .hero-left h1 {{
                font-size: 1.8rem;
            }}
            .container {{
                padding: 12px 10px;
            }}
        }}
    </style>
</head>
<body>

    <!-- Top Navbar -->
    <div class="top-navbar">
        <div class="brand-title">🏛️ VIETNAM STOCK ANALYZER &bull; BÁO CÁO NGHIÊN CỨU CHIẾN LƯỢC</div>
        <div class="report-time">{datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
    </div>

    <div class="container">

        <!-- EXECUTIVE HERO CARD -->
        <div class="hero-card">
            <div class="hero-header">
                <div class="hero-left">
                    <h1>
                        {symbol}
                        <span class="badge" style="background: rgba(59, 130, 246, 0.2); color: #60a5fa; border: 1px solid #3b82f6;">{quote.get('exchange', 'HOSE')}</span>
                        <span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc; border: 1px solid #8b5cf6;">{sector_name}</span>
                    </h1>
                    <p>{quote.get('company_name', symbol)}</p>
                    <div class="price-badge-group">
                        <span class="hero-price">{current_price:,.0f} đ</span>
                        <span class="hero-change">{chg_sign}{change_pct:.2f}%</span>
                        <span style="font-size: 0.85rem; color: #94a3b8; margin-left: 10px;">Khối lượng: <b>{quote.get('volume', 0):,.0f}</b> CP ({vol_ratio:.2f}x MA20)</span>
                    </div>
                </div>

                <div class="hero-action-box">
                    <div class="hero-action-label">Phán quyết Giám đốc Quản trị Rủi ro (CRO)</div>
                    <div class="hero-action-title">{action}</div>
                    <div class="consensus-meter">Độ đồng thuận Hội đồng AI: <b>{consensus_score}/100</b> điểm ({voting_summary.get('bull_count', 0)} Ủng hộ / {voting_summary.get('watch_count', 0)} Quan sát / {voting_summary.get('bear_count', 0)} Phản đối)</div>
                </div>
            </div>

            <!-- Tách bạch 2 Kế hoạch: Đầu tư Giá trị vs Lướt sóng Kỹ thuật -->
            <div style="margin-top: 20px; display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 16px;">
                <!-- Box 1: Đầu tư Giá trị -->
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 18px;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #38bdf8; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                        <span>🏛️ ĐẦU TƯ GIÁ TRỊ (BUFFETT & GRAHAM)</span>
                        <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8; border: 1px solid #38bdf8;">{trade_setup.get('value_status', 'ĐỊNH GIÁ HỢP LÝ')}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • Giá trị thực nội tại ước tính: <b style="color: #fff; font-size: 1.05rem;">{trade_setup.get('fair_price', current_price):,.0f} đ</b><br>
                        • Vùng gom an toàn (Biên an toàn &ge; 15%): <b style="color: #34d399; font-size: 1rem;">{trade_setup.get('value_buy_zone')}</b><br>
                        • Cơ sở định giá: <i>{trade_setup.get('value_rationale')}</i>
                        {val_gap_html}
                        {val_warn_html}
                    </div>
                </div>

                <!-- Box 2: Lướt sóng Kỹ thuật -->
                <div style="background: rgba(30, 41, 59, 0.7); border: 1px solid #334155; border-radius: 12px; padding: 18px;">
                    <div style="font-size: 0.9rem; font-weight: 700; color: #fbbf24; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; border-bottom: 1px solid rgba(255,255,255,0.06); padding-bottom: 8px;">
                        <span>🏄 LƯỚT SÓNG NGẮN HẠN (SWING TRADING / KỸ THUẬT)</span>
                        <span class="badge" style="background: rgba(251, 191, 36, 0.15); color: #fbbf24; border: 1px solid #fbbf24;">R:R {trade_setup.get('risk_reward_ratio')}:1</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.7;">
                        • Vùng mua lướt sóng: <b style="color: #38bdf8;">{trade_setup.get('swing_buy_zone')} đ</b><br>
                        • Cắt lỗ nghiêm ngặt (SL): <b style="color: #f87171;">{trade_setup.get('stop_loss', 0):,.0f} đ (-{trade_setup.get('stop_loss_pct', 0)}%)</b><br>
                        • Chốt lời (Mục tiêu 1 &bull; 2): <b style="color: #34d399;">{trade_setup.get('take_profit_1', 0):,.0f} đ (+{trade_setup.get('take_profit_1_pct', 0)}%) &bull; {trade_setup.get('take_profit_2', 0):,.0f} đ (+{trade_setup.get('take_profit_2_pct', 0)}%)</b><br>
                        • Tỷ trọng giải ngân tối đa: <b>Max {trade_setup.get('max_position_size_pct', 10.0):.1f}% tổng danh mục</b><br>
                        • Kỷ luật giao dịch: <i>{trade_setup.get('swing_strategy_note')}</i>
                    </div>
                </div>
            </div>
        </div>

        <!-- TẦNG 1: VĨ MÔ & CHU KỲ NGÀNH -->
        <div class="section-title">🌐 TẦNG 1: BỐI CẢNH VĨ MÔ & CHU KỲ NGÀNH (MACRO & SECTOR MATRIX)</div>
        <div class="card-grid-2">
            <div class="card">
                <div class="card-header">
                    <span>Định vị Chu kỳ Ngành: {sector_name}</span>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: {tailwind_color}; border: 1px solid {tailwind_color};">{macro.get('sentiment', 'TÍCH CỰC')}</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <span style="font-size: 0.8rem; color: var(--text-muted); text-transform: uppercase;">Pha chu kỳ hiện tại:</span>
                    <div style="font-size: 1.1rem; font-weight: 700; color: #fff; margin-top: 2px;">{cycle_phase}</div>
                    <p style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px;">{macro.get('phase_description', '')}</p>
                </div>

                <div style="margin-top: 14px;">
                    <div style="display: flex; justify-content: space-between; font-size: 0.82rem;">
                        <span style="color: var(--text-secondary);">Điểm số Gió xuôi Vĩ mô (Thuận buồm xuôi gió)</span>
                        <span style="font-weight: 700; color: {tailwind_color};">{tailwind_score}/100</span>
                    </div>
                    <div class="progress-bar-bg">
                        <div class="progress-bar-fill" style="width: {tailwind_score}%; background: {tailwind_color};"></div>
                    </div>
                </div>

                <div style="margin-top: 16px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">Động lực Vĩ mô Trọng tâm Hỗ trợ:</div>
                    <ul class="bullet-list">
                        {macro_drivers_html}
                    </ul>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>Trí tuệ Chu kỳ: Ray Dalio & Howard Marks</span>
                    <span class="badge" style="background: rgba(139, 92, 246, 0.2); color: #c084fc;">CHU KỲ VĨ MÔ</span>
                </div>
                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #a78bfa; margin-bottom: 4px;">Ray Dalio (Cỗ máy Kinh tế & Tín dụng):</div>
                    <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">{macro.get('dalio_verdict', 'N/A')}</p>
                </div>

                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #fbbf24; margin-bottom: 4px;">Howard Marks (Tâm lý Đám đông & Bẫy Chu kỳ):</div>
                    <p style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">{macro.get('marks_verdict', 'N/A')}</p>
                </div>

                <div style="border-top: 1px solid rgba(255, 255, 255, 0.08); padding-top: 12px; margin-top: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">Chỉ số Đặc thù Cần Giám sát Kỹ:</div>
                    <ul class="bullet-list">
                        {key_metrics_html}
                    </ul>
                </div>
            </div>
        </div>

        <!-- TẦNG 2: MÔ HÌNH KINH DOANH CỐT LÕI & CHI TIẾT TỪNG DỊCH VỤ -->
        <div class="section-title">🏢 TẦNG 2: MÔ HÌNH KINH DOANH CỐT LÕI & CƠ CHẾ SINH TIỀN TỪ DỊCH VỤ</div>
        <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">
                <span>Bóc tách Phân khúc Hoạt động (Core Business Breakdown)</span>
                <span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #c084fc;">CƠ CẤU DOANH THU & LỢI NHUẬN</span>
            </div>
            <div style="font-size: 0.9rem; color: #cbd5e1; margin-bottom: 14px; line-height: 1.6;">
                <b>Tóm lược mô hình hoạt động:</b> {business_model_summary}
            </div>
            <div class="table-responsive" style="margin-bottom: 18px;">
                <table>
                    <thead>
                        <tr>
                            <th>Mảng kinh doanh</th>
                            <th style="text-align: right;">% Doanh thu</th>
                            <th style="text-align: right;">% Lợi nhuận gộp</th>
                            <th style="text-align: right;">Biên lãi gộp</th>
                            <th>Vai trò chiến lược</th>
                            <th>Điểm nhấn triển vọng</th>
                        </tr>
                    </thead>
                    <tbody>
                        {seg_rows_html}
                    </tbody>
                </table>
            </div>

            <div style="font-size: 0.95rem; font-weight: 700; color: #38bdf8; margin: 16px 0 10px 0;">
                🔎 Chi tiết Dịch vụ là gì? Bán cho ai? Cơ chế thu tiền thực tế ra sao:
            </div>
            <div>
                {seg_detail_cards_html}
            </div>
        </div>

        <!-- TẦNG 3: DANH MỤC DỰ ÁN TRỌNG ĐIỂM & TIẾN ĐỘ THỰC TẾ -->
        <div class="section-title">🏗️ TẦNG 3: DANH MỤC DỰ ÁN TRỌNG ĐIỂM & TIẾN ĐỘ THỰC TẾ (KEY PROJECTS & LEGAL AUDIT)</div>
        <div class="card" style="margin-bottom: 20px;">
            <div class="card-header">
                <span>Tiến độ Triển khai, Đóng góp Lợi nhuận & Rà soát Vướng mắc Pháp lý / GPMB</span>
                <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">PROJECT PIPELINE</span>
            </div>
            <div style="font-size: 0.88rem; color: #94a3b8; margin-bottom: 14px;">
                Bảng theo dõi các dự án động lực đóng góp dòng tiền trong ngắn hạn và danh mục dự án gối đầu cho chu kỳ tăng trưởng dài hạn:
            </div>
            <div class="table-responsive">
                <table>
                    <thead>
                        <tr>
                            <th>Tên Dự án</th>
                            <th>Quy mô</th>
                            <th>Hiện trạng thực tế</th>
                            <th>Đóng góp Lợi nhuận</th>
                            <th>Pháp lý / Giải phóng mặt bằng (GPMB)</th>
                            <th style="text-align: center;">Đánh giá</th>
                        </tr>
                    </thead>
                    <tbody>
                        {project_rows_html}
                    </tbody>
                </table>
            </div>
        </div>

        <!-- TẦNG 4: SỨC KHỎE TÀI CHÍNH & BÓC TÁCH DÒNG TIỀN THẬT -->
        <div class="section-title">🔬 TẦNG 4: SỨC KHỎE BÁO CÁO TÀI CHÍNH & BÓC TÁCH DÒNG TIỀN THẬT</div>
        <div class="card-grid-3" style="margin-bottom: 20px;">
            <div class="card" style="border-left: 4px solid {quality_grade_color};">
                <div class="card-header">
                    <span>Chất lượng Lợi nhuận</span>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: {quality_grade_color};">HẠNG {quality_grade}</span>
                </div>
                <div style="font-size: 1.1rem; font-weight: 700; color: {quality_grade_color};">{cf.get('quality_verdict', 'LÀNH MẠNH')}</div>
                <p style="font-size: 0.82rem; color: #94a3b8; margin-top: 6px;">{cf.get('quality_desc', '')}</p>
                <div style="margin-top: 10px; font-size: 0.85rem;">
                    Tỷ lệ Tiền thật / Lãi kế toán (CFO / LNST): <b style="color: #38bdf8;">{cf.get('earnings_quality_ratio', 1.0):.2f}x</b>
                    <br><span style="font-size: 0.78rem; color: #64748b;">(Tỷ lệ &ge; 1.0x nghĩa là lãi bao nhiêu tiền mặt về bấy nhiêu)</span>
                </div>
            </div>

            <div class="card" style="border-left: 4px solid {z_color};">
                <div class="card-header">
                    <span>Altman Z''-Score (Nguy cơ Phá sản)</span>
                    <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: {z_color};">{z_zone}</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {z_color};">{altman_z:.2f} điểm</div>
                <div style="font-size: 0.85rem; font-weight: 600; color: #fff; margin-top: 2px;">{cf.get('z_verdict', 'AN TOÀN')}</div>
                <p style="font-size: 0.78rem; color: #94a3b8; margin-top: 4px;">{cf.get('z_desc', '')}</p>
            </div>

            <div class="card" style="border-left: 4px solid {f_color};">
                <div class="card-header">
                    <span>Piotroski F-Score (Độ khỏe Tài chính)</span>
                    <span class="badge" style="background: rgba(16, 185, 129, 0.15); color: {f_color};">{f_score}/9 ĐIỂM</span>
                </div>
                <div style="font-size: 1.6rem; font-weight: 800; color: {f_color};">{f_score}/9</div>
                <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 4px; line-height: 1.6;">
                    ROA (Sinh lời trên tài sản): <b>{fin.get('roa', 0):.1f}%</b><br>
                    ROE (Sinh lời trên vốn chủ): <b>{fin.get('roe', 0):.1f}%</b><br>
                    Nợ vay / Vốn CSH: <b>{fin.get('debt_to_equity', 0)}x</b>
                </div>
            </div>
        </div>

        <!-- Biểu đồ Dòng tiền & Cờ đỏ -->
        <div class="card-grid-2">
            <div class="card">
                <div class="card-header">
                    <span>So sánh Dòng tiền thật (CFO) vs LNST Kế toán (Tỷ VNĐ)</span>
                    <span class="badge" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">4 QUÝ GẦN NHẤT</span>
                </div>
                <div style="height: 240px; position: relative;">
                    <canvas id="cashFlowChart"></canvas>
                </div>
                <div style="font-size: 0.78rem; color: var(--text-muted); text-align: center; margin-top: 10px;">
                    Cột xanh dương: Lợi nhuận sau thuế &bull; Cột xanh lá: Tiền kinh doanh thực thu (CFO) &bull; Đường vàng: Dòng tiền tự do (FCF)
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>Rà soát Cờ đỏ Kế toán (Forensic Audit)</span>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: #ef4444;">CẢNH BÁO RỦI RO</span>
                </div>
                <ul class="bullet-list" style="margin-bottom: 16px;">
                    {red_flags_html}
                </ul>

                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Chỉ tiêu Dòng tiền</th>
                                <th style="text-align: right;">Giá trị (VND)</th>
                                <th>Ý nghĩa thực tế</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>Tiền kinh doanh thật (CFO 4 quý)</td>
                                <td style="text-align: right; font-weight: 700; color: #34d399;">{cfo_ttm:,.0f} đ</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Tiền mặt thực tế thu về từ bán hàng</td>
                            </tr>
                            <tr>
                                <td>Đầu tư mua sắm TSCĐ (CapEx 4 quý)</td>
                                <td style="text-align: right; color: #f87171;">{capex_ttm:,.0f} đ</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Tiền chi ra mở rộng hạ tầng, nhà xưởng</td>
                            </tr>
                            <tr>
                                <td>Dòng tiền tự do (FCF 4 quý)</td>
                                <td style="text-align: right; font-weight: 700; color: {'#34d399' if fcf_ttm > 0 else '#f87171'};">{fcf_ttm:,.0f} đ</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Tiền còn lại để trả cổ tức sau khi đã tái đầu tư</td>
                            </tr>
                            <tr>
                                <td>Lợi nhuận sau thuế (LNST 4 quý)</td>
                                <td style="text-align: right; color: #38bdf8;">{net_profit_ttm:,.0f} đ</td>
                                <td style="font-size: 0.8rem; color: #94a3b8;">Lợi nhuận ghi nhận trên sổ sách kế toán</td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TẦNG 5: KIỂM TOÁN BAN LÃNH ĐẠO, TÍNH MINH BẠCH & CÔNG TY SÂN SAU -->
        <div class="section-title">👥 TẦNG 5: KIỂM TOÁN BAN LÃNH ĐẠO, TÍNH MINH BẠCH & RADAR CÔNG TY SÂN SAU</div>
        <div class="card-grid-2" style="margin-bottom: 20px;">
            <div class="card">
                <div class="card-header">
                    <span>Kiểm toán Đạo đức & Tính Minh bạch Ban Điều hành</span>
                    <span class="badge" style="background: rgba(59, 130, 246, 0.15); color: {g_color};">G-SCORE {g_score}/100</span>
                </div>
                <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin-bottom: 6px;">
                    {integrity_verdict}
                </div>
                <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 12px;">
                    • <b>Đánh giá Ban lãnh đạo:</b> {leadership_analysis_vi}<br>
                    • <b>Cam kết cùng cổ đông (Skin in the game):</b> {lead.get('insider_total_pct', 0)}% cổ phần ({lead.get('skin_in_game_verdict', 'N/A')})<br>
                    • <b>Chủ tịch:</b> {lead.get('chairman', 'Chưa rõ')} &bull; <b>Tổng Giám đốc:</b> {lead.get('ceo', 'Chưa rõ')}
                </div>

                <div style="background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); border-radius: 10px; padding: 12px; margin-top: 10px;">
                    <span style="font-size: 0.85rem; font-weight: 700; color: #34d399;">💵 Bằng chứng Tiền thật qua Lịch sử Cổ tức:</span>
                    <p style="font-size: 0.84rem; color: #cbd5e1; margin-top: 4px; line-height: 1.5;">{dividend_evidence}</p>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <span>Radar Rủi ro Công ty Sân sau & Rút ruột Vốn</span>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.15); color: {'#34d399' if sub_web.get('shell_company_risk_level', 1) <= 2 else '#f87171'};">MỨC ĐỘ RỦI RO: {sub_web.get('shell_company_risk_level', 1)}/5</span>
                </div>
                <div style="font-size: 0.95rem; font-weight: 700; color: {'#34d399' if sub_web.get('shell_company_risk_level', 1) <= 2 else '#f87171'}; margin-bottom: 8px;">
                    {shell_risk_desc}
                </div>
                <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6; margin-bottom: 14px;">
                    • <b>Cảnh báo Tăng vốn ảo & Trái phiếu nội bộ:</b> {sub_web.get('circular_capital_verdict', 'An toàn')}<br>
                    • <b>Quy mô hệ sinh thái:</b> {sub_web.get('subsidiary_count', 0)} công ty con, {sub_web.get('affiliate_count', 0)} công ty liên kết<br>
                    • <b>Tỷ lệ cho vay bên liên quan:</b> {sub_web.get('related_party_loans_ratio', 0.0):.1f}% tổng tài sản
                </div>

                <div class="table-responsive">
                    <table>
                        <thead>
                            <tr>
                                <th>Top Cổ đông Nắm giữ Lớn</th>
                                <th style="text-align: right;">Tỷ lệ sở hữu</th>
                                <th style="text-align: right;">Số lượng CP</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sh_rows_html}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- TẦNG 6: PHÂN TÍCH KỸ THUẬT NÂNG CAO -->
        <div class="section-title">📈 TẦNG 6: PHÂN TÍCH KỸ THUẬT NÂNG CAO (VCP, VSA, FIBONACCI & OVERHEAD SUPPLY)</div>
        <div class="card-grid-2" style="margin-bottom: 20px;">
            <!-- Box 1: VCP Minervini & VSA -->
            <div class="card">
                <div class="card-header">
                    <span>Mô hình Thu hẹp Biến động VCP & Hành vi Nến VSA</span>
                    <span class="badge" style="background: rgba(139, 92, 246, 0.15); color: #c084fc;">MÔ HÌNH GIÁ VÀ KHỐI LƯỢNG</span>
                </div>
                <div style="margin-bottom: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8;">Mô hình VCP Minervini (Thu hẹp độ biến động):</div>
                    <div style="font-size: 0.95rem; font-weight: 700; color: #fff; margin-top: 2px;">{vcp_data.get('vcp_stage', 'Đang vận động tích lũy')}</div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; margin-top: 4px; line-height: 1.5;">
                        • Chuỗi thu hẹp biên độ: <b style="color: #fbbf24;">{vcp_contractions_str}</b><br>
                        • Đánh giá Minervini: <i>{vcp_data.get('vcp_verdict', 'N/A')}</i>
                    </div>
                </div>

                <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #34d399; margin-bottom: 6px;">Đọc Dấu vết Dòng tiền Lớn (VSA - Smart Money Signals):</div>
                    <ul class="bullet-list">
                        {vsa_signals_html}
                    </ul>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 6px;">
                        Hành động Cá mập / Tay to: <b style="color: #fff;">{vsa_sig.get('smart_money_action', 'Theo dõi quan sát')}</b>
                    </div>
                </div>
            </div>

            <!-- Box 2: Fibonacci & Vùng kẹp hàng Overhead Supply -->
            <div class="card">
                <div class="card-header">
                    <span>Mốc Hỗ trợ Fibonacci & Vùng Cung Kẹp Hàng Đỉnh Cũ</span>
                    <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24;">VÙNG GIÁ QUAN TRỌNG</span>
                </div>
                <div style="margin-bottom: 14px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px;">Mốc Hỗ trợ Fibonacci Retracement (Nhịp sóng gần nhất):</div>
                    <div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.6;">
                        • Đáy sóng: <b>{fibo_data.get('swing_low', 0):,.0f} đ</b> &bull; Đỉnh sóng: <b>{fibo_data.get('swing_high', 0):,.0f} đ</b><br>
                        • Fibo 38.2%: <b style="color: #34d399;">{fibo_data.get('fibo_382', 0):,.0f} đ</b> (Hỗ trợ nhịp sóng khỏe)<br>
                        • Fibo 50.0%: <b style="color: #fbbf24;">{fibo_data.get('fibo_500', 0):,.0f} đ</b> (Mốc cân bằng cung cầu)<br>
                        • Fibo 61.8%: <b style="color: #f87171;">{fibo_data.get('fibo_618', 0):,.0f} đ</b> (Hỗ trợ vàng sống còn)<br>
                        • Vị trí hiện tại: <i>{fibo_data.get('current_fibo_zone', 'N/A')}</i>
                    </div>
                </div>

                <div style="border-top: 1px solid rgba(255,255,255,0.06); padding-top: 12px; margin-top: 12px;">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #f87171; margin-bottom: 4px;">Áp lực Vùng Cung Kẹp Hàng Đỉnh Cũ (Overhead Supply):</div>
                    <div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
                        • Vùng kẹp hàng: <b style="color: #fca5a5;">{overhead_data.get('resistance_cluster', 'Không có vùng kẹp lớn')}</b><br>
                        • Áp lực bán tiềm tàng: <b style="color: {'#34d399' if overhead_data.get('supply_intensity') == 'Thấp' else '#f87171'};">{overhead_data.get('supply_intensity', 'Thấp')}</b><br>
                        • Chi tiết: <i>{overhead_data.get('explanation', 'Cung trên đầu đã được hấp thụ tốt.')}</i>
                    </div>
                </div>
            </div>
        </div>

        <!-- TẦNG 7: BÀN TRÒN HỘI ĐỒNG PHẢN BIỆN AI ĐA TRƯỜNG PHÁI -->
        <div class="section-title">🏛️ TẦNG 7: BÀN TRÒN HỘI ĐỒNG PHẢN BIỆN AI ĐA TRƯỜNG PHÁI (COUNCIL ROUNDTABLE)</div>
        
        <!-- Bảng biểu quyết tổng hợp -->
        <div class="card" style="margin-bottom: 20px; background: linear-gradient(145deg, #162032, #0f172a);">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: gap; gap: 14px; margin-bottom: 12px;">
                <div>
                    <div style="font-size: 1.15rem; font-weight: 800; color: #fff;">KẾT QUẢ BIỂU QUYẾT 6 THÀNH VIÊN HỘI ĐỒNG AI</div>
                    <div style="font-size: 0.85rem; color: #94a3b8; margin-top: 2px;">
                        Độ đồng thuận tổng hợp: <b style="color: #38bdf8; font-size: 1.05rem;">{voting_summary.get('consensus_score', 50)}/100 điểm</b> &bull; Kết luận: <b style="color: #34d399;">{voting_summary.get('verdict', 'THEO DÕI')}</b>
                    </div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <span class="badge" style="background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; font-size: 0.85rem; padding: 6px 12px;">🟢 {voting_summary.get('bull_count', 0)} TÁN THÀNH MUA</span>
                    <span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; font-size: 0.85rem; padding: 6px 12px;">🟡 {voting_summary.get('watch_count', 0)} THEO DÕI</span>
                    <span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #f87171; border: 1px solid #ef4444; font-size: 0.85rem; padding: 6px 12px;">🔴 {voting_summary.get('bear_count', 0)} PHẢN ĐỐI TRÁNH</span>
                </div>
            </div>
        </div>

        <!-- Khối tranh biện đối đầu (Clash of Perspectives) -->
        {clash_html}

        <!-- Lưới Card 6 Chuyên gia AI -->
        <div style="font-size: 1rem; font-weight: 700; color: #38bdf8; margin: 24px 0 12px 0;">
            📋 Ý kiến Chi tiết Từng Chuyên gia Hội đồng & Điều kiện Mất hiệu lực:
        </div>
        <div class="card-grid-3">
            {council_cards_html}
        </div>

        <!-- Báo cáo Thảo luận Chi tiết Toàn văn (Details Accordion) -->
        {council_report_html}

        <!-- Footer -->
        <div style="text-align: center; color: var(--text-muted); font-size: 0.8rem; margin-top: 50px; padding-top: 20px; border-top: 1px solid var(--border); line-height: 1.6;">
            Báo cáo phân tích chiến lược được khởi tạo tự động bởi Hệ thống <b>Vietnam Stock Analyzer</b>.<br>
            <i>Lưu ý: Báo cáo đóng vai trò tham mưu hỗ trợ quyết định khách quan dựa trên dữ liệu báo cáo tài chính và thuật toán phân tích, không phải lời kêu gọi đầu tư hay cam kết sinh lời. Quyết định mua bán cuối cùng thuộc về nhà đầu tư.</i>
        </div>

    </div>

    <!-- Script Vẽ Biểu đồ Chart.js Dòng tiền thật -->
    <script>
        const ctx = document.getElementById('cashFlowChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {json.dumps(chart_quarters)},
                datasets: [
                    {{
                        label: 'Lợi nhuận sau thuế kế toán (Tỷ đ)',
                        data: {json.dumps(chart_np)},
                        backgroundColor: 'rgba(56, 189, 248, 0.7)',
                        borderColor: '#38bdf8',
                        borderWidth: 1,
                        borderRadius: 4
                    }},
                    {{
                        label: 'Tiền kinh doanh thật - CFO (Tỷ đ)',
                        data: {json.dumps(chart_cfo)},
                        backgroundColor: 'rgba(52, 211, 153, 0.7)',
                        borderColor: '#34d399',
                        borderWidth: 1,
                        borderRadius: 4
                    }},
                    {{
                        type: 'line',
                        label: 'Dòng tiền tự do - FCF (Tỷ đ)',
                        data: {json.dumps(chart_fcf)},
                        borderColor: '#fbbf24',
                        backgroundColor: '#fbbf24',
                        borderWidth: 2,
                        tension: 0.3,
                        pointRadius: 4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{
                    legend: {{
                        labels: {{
                            color: '#94a3b8',
                            font: {{ size: 11 }}
                        }}
                    }}
                }},
                scales: {{
                    x: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }}
                    }},
                    y: {{
                        grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                        ticks: {{ color: '#94a3b8', font: {{ size: 11 }} }}
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""

    html_path.write_text(html_content, encoding="utf-8")
    return html_path
