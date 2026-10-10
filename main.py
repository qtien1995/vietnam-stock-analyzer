import sys
import argparse
from datetime import datetime
from pathlib import Path

# Fix Windows console UTF-8 display and line buffering
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown

from config import REPORTS_DIR, DEFAULT_WATCHLIST
from core.stock_service import (
    run_screener,
    analyze_ticker_full,
    analyze_ticker_fa,
    analyze_ticker_ta
)
from core.performance_tracker import (
    evaluate_all_recommendations,
    render_performance_terminal_dashboard
)

console = Console()


def analyze_single_ticker(symbol: str, mode: str = "full", save_report: bool = True, send_alert: bool = True) -> dict:
    """
    Quy trình bóc tách sâu 1 mã cổ phiếu qua lớp Stock Service.
    mode: "full" (cả FA và TA), "fa" (chỉ Cơ bản), "ta" (chỉ Kỹ thuật)
    """
    symbol = symbol.upper().strip()
    
    mode_text = "Toàn diện (Vĩ mô & FA & TA)"
    if mode == "fa":
        mode_text = "Cơ bản Doanh nghiệp (FA)"
    elif mode == "ta":
        mode_text = "Kỹ thuật & Dòng tiền (TA)"
        
    console.print(f"\n[bold cyan]⏳ Đang tải dữ liệu ({mode_text}) cho mã [yellow]{symbol}[/yellow]...[/bold cyan]")

    if mode == "full":
        res = analyze_ticker_full(symbol, save_report=save_report, send_alert=send_alert)
        if "error" in res:
            console.print(f"[bold red]❌ {res['error']}[/bold red]")
            return {}

        _render_terminal_dashboard(
            symbol,
            res["quote"],
            res["fa_result"],
            res["ta_result"],
            res["trade_setup"],
            res["council_result"]
        )

        if save_report:
            _save_markdown_report(symbol, res["quote"], res["fa_result"], res["ta_result"], res["trade_setup"], res["council_result"])
            if res.get("html_path"):
                console.print(f"[bold green]🌐 Đã xuất bản báo cáo HTML trực quan (Mobile & Desktop) tại:[/bold green] [underline cyan]{res['html_path']}[/underline cyan]")

        return res["trade_setup"]

    elif mode == "fa":
        res = analyze_ticker_fa(symbol)
        _render_terminal_fa(symbol, res["quote"], res["fa_result"])
        return res["fa_result"]

    elif mode == "ta":
        res = analyze_ticker_ta(symbol)
        _render_terminal_ta(symbol, res["quote"], res["ta_result"], res["trade_setup"])
        return res["ta_result"]



def _save_markdown_report(symbol, quote, fa_result, ta_result, trade_setup, council_result):
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"{today_str}_{symbol}.md"
    report_path = REPORTS_DIR / report_filename

    asset_val = fa_result.get("asset_valuation", {})
    segments_data = fa_result.get("segments", {})
    fin = fa_result.get("ratios", {})

    gov = fa_result.get("governance", {})
    own = gov.get("ownership", {})
    lead = gov.get("leadership", {})
    sub_web = gov.get("subsidiary_web", {})

    # Bảng phân khúc Markdown
    segments_md = ""
    for s in segments_data.get("segments", []):
        segments_md += f"| **{s.get('name')}** | **{s.get('rev_share_pct')}%** | **{s.get('gross_profit_share_pct')}%** | `{s.get('gross_margin_pct')}%` | {s.get('role')} | {s.get('highlights')} |\n"

    # Bảng cổ đông Markdown
    sh_md = ""
    for sh in own.get("top_shareholders", [])[:6]:
        sh_md += f"| **{sh.get('name')}** | **{sh.get('percentage')}%** | {sh.get('shares', 0):,.0f} CP |\n"

    # Bảng công ty con Markdown
    sub_md = ""
    for sub in sub_web.get("key_subsidiaries", [])[:6]:
        sub_md += f"| **{sub.get('name')}** | **{sub.get('ownership_percent')}%** | Công ty con trực thuộc |\n"

    macro = fa_result.get("macro", {})
    cf = fa_result.get("cash_flow", {})

    full_md_content = f"""# 📊 BÁO CÁO PHÂN TÍCH CHIẾN LƯỢC: {symbol} - {quote.get('company_name', symbol)}
> **Ngày phân tích:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
> **Nguồn dữ liệu:** Giá Khớp lệnh Realtime & Báo cáo Tài chính Độc lập

---

## 🎯 1. TỔNG QUAN TÍN HIỆU & KẾ HOẠCH GIAO DỊCH
| Thông số | Giá trị | Ý nghĩa |
| :--- | :--- | :--- |
| **Khuyến nghị** | **{trade_setup.get('action')}** | {trade_setup.get('action_summary')} |
| **Độ đồng thuận Hội đồng** | **{trade_setup.get('consensus_score')}/100 điểm** | FA: {trade_setup.get('fa_score')}/100 - TA: {trade_setup.get('ta_score')}/100 |
| **Giá khớp lệnh hiện tại** | **{trade_setup.get('current_price', 0):,.0f} VND** | Biến động phiên: {quote.get('change_pct', 0)}% |
| **Vùng mua (Buy Zone)** | **{trade_setup.get('buy_zone')} VND** | Vùng giá giải ngân tối ưu |
| **Tỷ trọng vốn tối đa** | **{trade_setup.get('max_position_size_pct', 0):.1f}% NAV** | Tỷ trọng giải ngân an toàn (Giới hạn rủi ro 1.5% NAV) |
| **Điểm cắt lỗ (Stop Loss)** | **{trade_setup.get('stop_loss', 0):,.0f} VND** | **-{trade_setup.get('stop_loss_pct', 0)}%** (Nguyên tắc bảo toàn vốn) |
| **Mục tiêu 1 (Take Profit 1)** | **{trade_setup.get('take_profit_1', 0):,.0f} VND** | **+{trade_setup.get('take_profit_1_pct', 0)}%** |
| **Tỷ lệ Risk / Reward (R:R)** | **{trade_setup.get('risk_reward_ratio')}:1** | Lợi nhuận tiềm năng gấp {trade_setup.get('risk_reward_ratio')} lần rủi ro |

---

## 🌐 2. BỐI CẢNH VĨ MÔ & CHU KỲ NGÀNH (MACRO & SECTOR MATRIX)
> **Ngành nghề:** **{macro.get('sector_name', 'Chưa rõ')}** &bull; **Pha chu kỳ:** `{macro.get('cycle_phase', 'Bình thường')}`  
> **Điểm Gió xuôi Vĩ mô:** **{macro.get('tailwind_score', 70)}/100** ({macro.get('sentiment', 'TRUNG TÍNH')})  
> **Ray Dalio (Cỗ máy vĩ mô):** {macro.get('dalio_verdict', 'N/A')}  
> **Howard Marks (Tâm lý chu kỳ):** {macro.get('marks_verdict', 'N/A')}  

---

## 🔬 3. VI MÔ - SỨC KHỎE BCTC & BÓC TÁCH DÒNG TIỀN THẬT (CASH FLOW FORENSIC)
| Chỉ tiêu Dòng tiền & Sức khỏe | Giá trị thực tế | Đánh giá Chất lượng & Rủi ro |
| :--- | :--- | :--- |
| **Chất lượng Lợi nhuận** | **Hạng {cf.get('quality_grade', 'B')}: {cf.get('quality_verdict', 'LÀNH MẠNH')}** | {cf.get('quality_desc', '')} |
| **Dòng tiền thuần HĐKD (CFO TTM)** | **{cf.get('cfo_ttm', 0):,.0f} VND** | Tiền mặt thực thu từ hoạt động kinh doanh cốt lõi |
| **Chi tiêu vốn (CapEx TTM)** | **{cf.get('capex_ttm', 0):,.0f} VND** | Dòng tiền chi mua sắm tài sản cố định mở rộng |
| **Dòng tiền tự do (FCF TTM)** | **{cf.get('fcf_ttm', 0):,.0f} VND** | {cf.get('fcf_verdict', '')} |
| **Chỉ số Altman Z''-Score** | **{cf.get('altman_z', 0):.2f} điểm** | **{cf.get('z_verdict', 'AN TOÀN')}** ({cf.get('z_desc', '')}) |
| **Piotroski F-Score** | **{fa_result.get('f_score', 0)}/9 điểm** | Sức khỏe bảng cân đối kế toán |

---

## 💎 4. ĐỊNH GIÁ THEO KHỐI TÀI SẢN & RADAR PHÁT HIỆN THAO TÚNG (ASSET-BASED VALUATION)
| Chỉ tiêu Tài sản | Giá trị thực tế | Ý nghĩa & Đánh giá an toàn vốn |
| :--- | :--- | :--- |
| **Giá trị sổ sách (BVPS)** | **{asset_val.get('bvps', 0):,.0f} VND/CP** | Giá trị tài sản ròng thuộc về mỗi cổ đông sau khi trả hết nợ |
| **Thị giá / Giá trị tài sản (P/B)** | **{asset_val.get('pb', 'N/A')}x** | Thị trường đang trả {asset_val.get('pb', 'N/A')} đồng cho mỗi 1 đồng tài sản ròng |
| **Mức Chiết khấu / Thặng dư** | **{asset_val.get('asset_discount_pct', 0):+.1f}%** | {'Chiết khấu rẻ hơn vốn chủ sở hữu' if asset_val.get('asset_discount_pct', 0) > 0 else 'Thị giá cao hơn tài sản sổ sách'} |
| **Radar Cảnh báo Thao túng** | **CẤP {asset_val.get('manipulation_risk_level', 1)}/5: {asset_val.get('manipulation_verdict')}** | Mức độ an toàn trước rủi ro 'bơm thổi' giá ảo |
| **Bộ đệm Tiền mặt & Tiền gửi** | **{asset_val.get('cash_ratio', 0):.1f}% Tổng tài sản** | Dự trữ tiền mặt phòng thủ thanh khoản |
| **Tỷ lệ tài sản đọng vốn** | **{asset_val.get('illiquid_ratio', 0):.1f}% Tổng tài sản** | Tỷ trọng Các khoản phải thu + Hàng tồn kho |
| **Kiểm định Chất lượng Tài sản** | **{asset_val.get('asset_quality_verdict')}** | Đánh giá mức độ trung thực và khả năng thanh lý tài sản |

---

## 🏢 5. BÓC TÁCH MÔ HÌNH KINH DOANH CỐT LÕI (CORE BUSINESS BREAKDOWN)
> **Tóm tắt mô hình:** {segments_data.get('business_model_summary', 'N/A')}

| Mảng hoạt động | % Doanh thu | % Lợi nhuận gộp | Biên lãi gộp | Vai trò chiến lược | Điểm nhấn triển vọng & Rủi ro |
| :--- | :---: | :---: | :---: | :--- | :--- |
{segments_md}
---

## 👥 6. QUẢN TRỊ DOANH NGHIỆP, CỔ ĐÔNG & MẠNG LƯỚI CÔNG TY CON (GOVERNANCE & SHELL RADAR)
> **Điểm Quản trị (G-Score):** **{gov.get('g_score', 'N/A')}/100** ({gov.get('g_rating', 'N/A')})  
> **Cơ cấu Sở hữu:** {own.get('structure', 'N/A')} — *Trôi nổi:* `{own.get('free_float_pct', 0)}%` | *Khối ngoại:* `{own.get('foreigner_pct', 0)}%` | *Nhà nước:* `{own.get('state_pct', 0)}%`  
> **Ban Điều hành:** Chủ tịch: **{lead.get('chairman', 'Chưa rõ')}** | CEO: **{lead.get('ceo', 'Chưa rõ')}** (Skin in the game: `{lead.get('insider_total_pct', 0)}%` — {lead.get('skin_in_game_verdict', 'N/A')})  
> **Radar Tăng vốn ảo & Trái phiếu hệ sinh thái:** **{sub_web.get('circular_capital_verdict', 'N/A')}** ({sub_web.get('subsidiary_count', 0)} công ty con, {sub_web.get('affiliate_count', 0)} công ty liên kết)

### Danh sách Cổ đông Chủ chốt:
| Cổ đông lớn | Tỷ lệ sở hữu | Số lượng cổ phiếu |
| :--- | :---: | :---: |
{sh_md}

### Mạng lưới Công ty con Trọng yếu:
| Tên Đơn vị Thành viên | Tỷ lệ Biểu quyết | Vai trò trong Hệ sinh thái |
| :--- | :---: | :--- |
{sub_md}
---

## 🏛️ 7. PHẢN BIỆN ĐA GÓC NHÌN TỪ HỘI ĐỒNG ĐẦU TƯ AI

{council_result.get('council_report')}

---
*Báo cáo được khởi tạo tự động bởi Hệ thống Vietnam Stock Analyzer Terminal.*
"""
    report_path.write_text(full_md_content, encoding="utf-8")
    console.print(f"\n[bold green]📁 Đã xuất bản báo cáo chi tiết tại:[/bold green] [underline cyan]{report_path}[/underline cyan]")


def _render_segments_table(symbol: str, seg_data: dict):
    """Bảng Bóc tách Mô hình kinh doanh cốt lõi (Segments)"""
    if not seg_data or not seg_data.get("segments"):
        return
    s_table = Table(title=f"🏢 BÓC TÁCH MÔ HÌNH KINH DOANH CỐT LÕI (CORE BUSINESS): {symbol}", header_style="bold green")
    s_table.add_column("Mảng kinh doanh", style="bold white")
    s_table.add_column("% Doanh thu", style="cyan", justify="right")
    s_table.add_column("% LN Gộp", style="bold green", justify="right")
    s_table.add_column("Biên gộp", style="yellow", justify="right")
    s_table.add_column("Vai trò chiến lược", style="magenta")

    for s in seg_data.get("segments", []):
        s_table.add_row(
            s.get("name"),
            f"{s.get('rev_share_pct')}%",
            f"{s.get('gross_profit_share_pct')}%",
            f"{s.get('gross_margin_pct')}%",
            s.get("role")
        )
    console.print(s_table)


def _render_governance_table(gov: dict):
    """Bảng Quản trị Doanh nghiệp & Mạng lưới Công ty con"""
    if not gov:
        return
    own = gov.get("ownership", {})
    lead = gov.get("leadership", {})
    sub_web = gov.get("subsidiary_web", {})

    g_color = "green" if gov.get("g_score", 0) >= 70 else ("yellow" if gov.get("g_score", 0) >= 50 else "red")
    g_table = Table(title=f"👥 QUẢN TRỊ DOANH NGHIỆP & CƠ CẤU CỔ ĐÔNG (G-SCORE: {gov.get('g_score')}/100)", header_style="bold blue")
    g_table.add_column("Hạng mục", style="cyan")
    g_table.add_column("Thông số", style="bold white")
    g_table.add_column("Đánh giá Rủi ro Quản trị", style="white")

    g_table.add_row("Điểm Quản trị (G-Score)", f"[{g_color}]{gov.get('g_score')}/100[/{g_color}]", f"[{g_color}]{gov.get('g_rating')}[/{g_color}]")
    g_table.add_row("Cơ cấu Sở hữu", f"Trôi nổi {own.get('free_float_pct', 0)}% | Ngoại {own.get('foreigner_pct', 0)}%", f"{own.get('structure')}")
    g_table.add_row("Cam kết Lãnh đạo (Skin in game)", f"{lead.get('insider_total_pct', 0)}% vốn CSH", f"{lead.get('skin_in_game_verdict')}")
    g_table.add_row("Mạng lưới Chân rết", f"{sub_web.get('subsidiary_count', 0)} cty con / {sub_web.get('affiliate_count', 0)} liên kết", f"{sub_web.get('conglomerate_type')}")
    
    c_color = "red" if sub_web.get("circular_capital_risk_level", 1) >= 4 else ("yellow" if sub_web.get("circular_capital_risk_level") == 3 else "green")
    g_table.add_row("Radar Tăng vốn ảo & Nợ", f"[{c_color}]Cấp {sub_web.get('circular_capital_risk_level', 1)}/5[/{c_color}]", f"[{c_color}]{sub_web.get('circular_capital_verdict')}[/{c_color}]")
    
    console.print(g_table)


def _render_terminal_dashboard(symbol, quote, fa, ta, trade, council):
    """In giao diện bảng Full (Cả FA và TA)"""
    current_price = trade.get("current_price", 0)
    change_pct = quote.get("change_pct", 0)
    chg_color = "green" if change_pct > 0 else ("red" if change_pct < 0 else "yellow")

    console.print(Panel(
        f"[bold white]{symbol} - {quote.get('company_name', symbol)}[/bold white]\n"
        f"Giá hiện tại: [bold {chg_color}]{current_price:,.0f} VND[/bold {chg_color}] ({change_pct:+.2f}%) | "
        f"Khối lượng: [bold cyan]{quote.get('volume', 0):,.0f}[/bold cyan] CP",
        title="[bold yellow]🏛️ THÔNG TIN THỊ TRƯỜNG REALTIME[/bold yellow]",
        border_style="bright_blue"
    ))

    # Bảng Tín hiệu
    action_color = trade.get("action_color", "white")
    t_table = Table(title="🎯 KẾ HOẠCH GIAO DỊCH (CHIEF RISK OFFICER)", header_style="bold magenta")
    t_table.add_column("Trường phái / Hạng mục", style="cyan")
    t_table.add_column("Kế hoạch & Vùng mua", style="bold white")
    t_table.add_column("Lý do & Kỷ luật rủi ro", style="yellow")
    
    t_table.add_row("Khuyến nghị tổng hợp", f"[{action_color}]{trade.get('action')}[/{action_color}]", f"Đồng thuận: {trade.get('consensus_score')}/100 | Tỷ trọng Max {trade.get('max_position_size_pct', 0):.1f}% NAV")
    
    val_status_color = "red" if "ĐẮT" in trade.get("value_status", "") else ("green" if "RẺ" in trade.get("value_status", "") else "cyan")
    t_table.add_row(
        "🏛️ Đầu tư Giá trị (Buffett)",
        f"{trade.get('value_buy_zone')}\n(Giá trị thực: [bold]{trade.get('fair_price', current_price):,.0f} đ[/bold])",
        f"[{val_status_color}]{trade.get('value_status')}[/{val_status_color}]: {trade.get('value_rationale', '')}"
    )
    
    t_table.add_row(
        "🏄 Lướt sóng Ngắn hạn (Swing)",
        f"Vùng mua: [bold green]{trade.get('swing_buy_zone')}[/bold green]\nCắt lỗ: [bold red]{trade.get('stop_loss', 0):,.0f} đ[/bold red] (-{trade.get('stop_loss_pct', 0)}%)\nChốt lời TP1: [bold cyan]{trade.get('take_profit_1', 0):,.0f} đ[/bold cyan] (+{trade.get('take_profit_1_pct', 0)}%)",
        f"R:R = {trade.get('risk_reward_ratio')}:1\n{trade.get('swing_strategy_note', '')}"
    )

    console.print(t_table)

    # Bảng Vĩ mô & Chu kỳ Ngành
    macro = fa.get("macro", {})
    if macro:
        m_table = Table(title="🌐 VĨ MÔ & CHU KỲ NGÀNH (RAY DALIO & HOWARD MARKS)", header_style="bold blue")
        m_table.add_column("Chỉ tiêu Vĩ mô", style="cyan")
        m_table.add_column("Trạng thái", style="bold yellow")
        m_table.add_column("Nhận định & Tác động", style="white")

        t_color = "green" if macro.get("tailwind_score", 70) >= 80 else ("cyan" if macro.get("tailwind_score", 70) >= 70 else "yellow")
        m_table.add_row("Ngành & Pha chu kỳ", f"{macro.get('sector_name')}", f"Pha: {macro.get('cycle_phase')}")
        m_table.add_row("Gió xuôi Vĩ mô", f"[{t_color}]{macro.get('tailwind_score')}/100[/{t_color}]", f"[{t_color}]{macro.get('sentiment')}[/{t_color}]")
        m_table.add_row("Động lực chính", "Catalysts", f"{macro.get('macro_drivers', [''])[0]}")
        console.print(m_table)

    # Bảng Dòng tiền thật & Altman Z-Score
    cf = fa.get("cash_flow", {})
    if cf:
        cf_table = Table(title="🔬 BÓC TÁCH DÒNG TIỀN THẬT & ALTMAN Z''-SCORE (CASH FLOW FORENSIC)", header_style="bold green")
        cf_table.add_column("Chỉ tiêu", style="cyan")
        cf_table.add_column("Giá trị", style="bold white")
        cf_table.add_column("Kiểm định Chất lượng", style="white")

        q_color = "green" if cf.get("quality_grade") in ["A", "B"] else "red"
        z_color = "green" if cf.get("z_zone") == "SAFE" else ("yellow" if cf.get("z_zone") == "GREY" else "red")

        cf_table.add_row("Chất lượng Lợi nhuận", f"[{q_color}]Hạng {cf.get('quality_grade')}[/{q_color}]", f"[{q_color}]{cf.get('quality_verdict')}[/{q_color}]")
        cf_table.add_row("Tiền HĐKD thật (CFO TTM)", f"{cf.get('cfo_ttm', 0):,.0f} đ", f"Tỷ lệ CFO/LNST: {cf.get('earnings_quality_ratio', 1.0):.2f}x")
        cf_table.add_row("Dòng tiền tự do (FCF)", f"{cf.get('fcf_ttm', 0):,.0f} đ", f"CapEx: {cf.get('capex_ttm', 0):,.0f} đ")
        cf_table.add_row("Altman Z''-Score", f"[{z_color}]{cf.get('altman_z', 0):.2f}[/{z_color}]", f"[{z_color}]{cf.get('z_verdict')}[/{z_color}]")
        console.print(cf_table)

    # Bảng Định giá Tài sản & Radar Thao túng
    asset_val = fa.get("asset_valuation", {})
    if asset_val:
        a_table = Table(title="💎 ĐỊNH GIÁ THEO KHỐI TÀI SẢN & RADAR THAO TÚNG", header_style="bold cyan")
        a_table.add_column("Chỉ tiêu", style="cyan")
        a_table.add_column("Thông số", style="bold yellow")
        a_table.add_column("Đánh giá An toàn vốn", style="white")

        risk_color = "green" if asset_val.get("manipulation_risk_level", 1) <= 2 else ("yellow" if asset_val.get("manipulation_risk_level") == 3 else "red")
        
        a_table.add_row("Giá trị sổ sách (BVPS)", f"{asset_val.get('bvps', 0):,.0f} đ", "Giá trị tài sản ròng thuộc về mỗi cổ phiếu")
        a_table.add_row("Hệ số Định giá P/B", f"{asset_val.get('pb', 'N/A')}x", f"Chiết khấu tài sản: {asset_val.get('asset_discount_pct', 0):+.1f}%")
        a_table.add_row("Radar Thao túng", f"[{risk_color}]Cấp {asset_val.get('manipulation_risk_level')}/5[/{risk_color}]", f"[{risk_color}]{asset_val.get('manipulation_verdict')}[/{risk_color}]")
        a_table.add_row("Chất lượng tài sản", f"{asset_val.get('asset_quality_verdict')}", f"Đọng vốn: {asset_val.get('illiquid_ratio', 0):.1f}% | Tiền mặt: {asset_val.get('cash_ratio', 0):.1f}%")
        
        console.print(a_table)

    # Bảng Bóc tách Mô hình kinh doanh cốt lõi (Segments)
    _render_segments_table(symbol, fa.get("segments", {}))

    # Bảng Quản trị Doanh nghiệp & Mạng lưới Công ty con
    _render_governance_table(fa.get("governance", {}))


def _render_terminal_fa(symbol, quote, fa):
    """Giao diện chỉ hiển thị Phân tích cơ bản (FA)"""
    fin = fa.get("ratios", {})
    asset_val = fa.get("asset_valuation", {})
    seg_data = fa.get("segments", {})

    console.print(f"\n[bold yellow]🏛️ CHUYÊN SÂU CƠ BẢN DOANH NGHIỆP: {symbol}[/bold yellow]")
    
    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Chỉ tiêu Cơ bản")
    t.add_column("Giá trị", justify="right")
    
    t.add_row("Piotroski F-Score", f"{fa.get('f_score')}/9")
    t.add_row("P/E Ratio", f"{fin.get('pe')}x" if fin.get('pe') else "N/A")
    t.add_row("P/B Ratio", f"{asset_val.get('pb', fin.get('pb'))}x" if asset_val.get('pb', fin.get('pb')) else "N/A")
    t.add_row("Giá trị sổ sách (BVPS)", f"{asset_val.get('bvps', 0):,.0f} đ" if asset_val.get('bvps') else "N/A")
    t.add_row("ROE (%)", f"{fin.get('roe')}%" if fin.get('roe') else "N/A")
    t.add_row("Biên Lợi nhuận ròng", f"{fin.get('net_margin')}%" if fin.get('net_margin') else "N/A")
    t.add_row("Nợ vay / Vốn CSH", f"{fin.get('debt_to_equity')}x" if fin.get('debt_to_equity') else "N/A")
    t.add_row("Radar Thao túng", f"{asset_val.get('manipulation_verdict', 'N/A')}")
    
    console.print(t)

    # Hiển thị phân khúc nếu có
    _render_segments_table(symbol, seg_data)
    
    # Hiển thị Quản trị & Cổ đông trong FA
    _render_governance_table(fa.get("governance", {}))

    # Verdicts
    console.print(f"\n[bold green]Warren Buffett (Moat & Giá trị):[/bold green] {fa.get('buffett', {}).get('reasons', [''])[0]}")
    console.print(f"[bold magenta]Peter Lynch (Tăng trưởng GARP):[/bold magenta] {fa.get('lynch', {}).get('reasons', [''])[0]}")
    if fa.get("valuation_warning"):
        console.print(f"[bold red]Cảnh báo Rủi ro Định giá:[/bold red] {fa.get('valuation_warning')}")


def _render_terminal_ta(symbol, quote, ta, trade):
    """Giao diện chỉ hiển thị Phân tích kỹ thuật (TA)"""
    ind = ta.get("indicators", {})
    console.print(f"\n[bold cyan]📈 CHUYÊN SÂU KỸ THUẬT CHART & DÒNG TIỀN: {symbol}[/bold cyan]")
    
    t = Table(show_header=True, header_style="bold yellow")
    t.add_column("Chỉ báo Kỹ thuật")
    t.add_column("Trạng thái", justify="right")
    
    t.add_row("Giá hiện tại", f"{ind.get('close', 0):,.0f}")
    t.add_row("EMA 20 (Ngắn hạn)", f"{ind.get('ema20', 0):,.0f}")
    t.add_row("EMA 50 (Trung hạn)", f"{ind.get('ema50', 0):,.0f}")
    t.add_row("Volume Ratio (so MA20)", f"{ind.get('vol_ratio', 1.0):.2f}x")
    t.add_row("RSI 14", f"{ind.get('rsi14', 50):.1f}")
    t.add_row("Vùng hỗ trợ", f"{ind.get('sup_20d', 0):,.0f}")
    
    console.print(t)
    
    console.print(f"\n[bold green]O'Neil (CANSLIM/Breakout):[/bold green] {ta.get('oneil', {}).get('reasons', [''])[0]}")
    console.print(f"[bold magenta]Wyckoff VSA (Dòng tiền):[/bold magenta] Pha {ta.get('vsa', {}).get('phase')} - {ta.get('vsa', {}).get('reasons', [''])[0]}")
    console.print(f"\n[bold white]Kế hoạch Điểm vào:[/bold white] Mua vùng {trade.get('buy_zone')}. Cắt lỗ tại {trade.get('stop_loss', 0):,.0f}.")


from core.stock_service import get_liquidity_rating, matches_sector_filter


def run_market_screener(top_n: int = 10, sector_filter: str = None):
    """
    Quét danh mục TOÀN THỊ TRƯỜNG (HOSE, HNX, UPCoM) thông qua StockService:
    Lọc thanh khoản tối thiểu 300 triệu VNĐ/phiên, hỗ trợ lọc theo nhóm ngành.
    """
    filter_label = f" (Nhóm ngành: {sector_filter})" if sector_filter else " (Toàn thị trường)"
    console.print(Panel(
        f"[bold white]Đang khởi động Radar quét toàn bộ 1500+ mã trên TTCK Việt Nam{filter_label}...[/bold white]\n"
        f"Lọc thanh khoản tối thiểu 300 triệu VNĐ/phiên.",
        title="[bold green]🔍 BỘ LỌC TOÀN CẦU THỊ TRƯỜNG (FULL-MARKET SCREENER)[/bold green]",
        border_style="green"
    ))

    def on_progress(msg: str):
        if "Đang quét TA" in msg:
            print(msg, end="\r")
        else:
            console.print(f"[cyan]{msg}[/cyan]")

    results = run_screener(
        top_n=top_n,
        sector_filter=sector_filter,
        progress_callback=on_progress
    )

    if not results:
        console.print("[yellow]Không tìm thấy mã nào thỏa mãn điều kiện lọc hoặc lỗi kết nối realtime.[/yellow]")
        return

    console.print("\n")
    screen_table = Table(title=f"🏆 BẢNG XẾP HẠNG TOÀN THỊ TRƯỜNG (TOP {min(len(results), top_n)} CỔ PHIẾU TIỀM NĂNG)", header_style="bold green")
    screen_table.add_column("Mã CP (Sàn)", style="bold yellow")
    screen_table.add_column("Nhóm Ngành", style="bold blue")
    screen_table.add_column("Giá Khớp", style="bold white")
    screen_table.add_column("Nổ Vol", style="cyan")
    screen_table.add_column("Đồng Thuận", style="bold yellow")
    screen_table.add_column("FA (F | CFO)", style="magenta")
    screen_table.add_column("Khuyến nghị", style="bold")
    screen_table.add_column("Vùng Mua", style="green")

    for r in results[:top_n]:
        action_col = "green" if "MUA MẠNH" in r["action"] else ("cyan" if "MUA" in r["action"] else "yellow")
        screen_table.add_row(
            f"{r['symbol']} ({r['exchange']})",
            r["sector_name"],
            f"{r['price']:,.0f} ({r['change_pct']:+.1f}%)",
            f"{r['vol_ratio']:.2f}x",
            f"{r['consensus_score']}/100",
            f"{r['f_score']}/9 | Hạng {r['cfo_grade']}",
            f"[{action_col}]{r['action']}[/{action_col}]",
            r["buy_zone"]
        )

    console.print(screen_table)


def main():
    parser = argparse.ArgumentParser(
        description="Vietnam Stock Market Analyzer - Hệ thống Phân tích Chứng khoán Cục bộ Đa AI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["analyze", "scan", "bot", "fa", "ta", "track"],
        default="analyze",
        help="Chế độ hoạt động:\n  analyze: Soi sâu 1 mã (FA + TA)\n  fa: Chỉ phân tích Cơ bản (BCTC)\n  ta: Chỉ phân tích Kỹ thuật (Chart)\n  scan: Quét toàn bộ TTCK\n  track: PDCA - Đánh giá hiệu suất khuyến nghị quá khứ\n  bot: Chạy Telegram Bot"
    )
    parser.add_argument(
        "--ticker", "-t",
        default="HPG",
        help="Mã cổ phiếu cần phân tích (ví dụ: HPG, FPT...)"
    )
    parser.add_argument(
        "--sector", "-s",
        default=None,
        help="Lọc theo nhóm ngành khi scan (ví dụ: KCN, Bán lẻ, Ngân hàng, Thép...)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Số lượng mã hiển thị trong chế độ scan (mặc định: 10)"
    )

    args = parser.parse_args()

    if args.mode == "scan":
        run_market_screener(top_n=args.top, sector_filter=args.sector)
    elif args.mode == "track":
        perf_data = evaluate_all_recommendations()
        render_performance_terminal_dashboard(perf_data)
    elif args.mode == "bot":
        from alerts.telegram_interactive_bot import start_interactive_bot
        start_interactive_bot()
    elif args.mode == "fa":
        analyze_single_ticker(symbol=args.ticker, mode="fa")
    elif args.mode == "ta":
        analyze_single_ticker(symbol=args.ticker, mode="ta")
    else:
        analyze_single_ticker(symbol=args.ticker, mode="full")


if __name__ == "__main__":
    main()
