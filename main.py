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
from core.data_loader import get_realtime_quote, get_historical_ohlcv, get_financial_data, get_all_tickers_realtime
from core.fa_engine import analyze_fundamentals
from core.ta_engine import analyze_technicals
from core.risk_manager import calculate_trade_setup
from ai.council import InvestmentCouncil
from alerts.telegram_bot import send_telegram_alert

console = Console()


def analyze_single_ticker(symbol: str, mode: str = "full", save_report: bool = True, send_alert: bool = True) -> dict:
    """
    Quy trình bóc tách sâu 1 mã cổ phiếu.
    mode: "full" (cả FA và TA), "fa" (chỉ Cơ bản), "ta" (chỉ Kỹ thuật)
    """
    symbol = symbol.upper().strip()
    
    mode_text = "Toàn diện (FA & TA)"
    if mode == "fa":
        mode_text = "Cơ bản Doanh nghiệp (FA)"
    elif mode == "ta":
        mode_text = "Kỹ thuật & Dòng tiền (TA)"
        
    console.print(f"\n[bold cyan]⏳ Đang tải dữ liệu ({mode_text}) cho mã [yellow]{symbol}[/yellow]...[/bold cyan]")

    # 1. Thu thập dữ liệu chung
    quote = get_realtime_quote(symbol)
    current_price = quote.get("price", 0)

    # Nếu realtime chưa có giá, fallback ngay sang nến lịch sử gần nhất
    if current_price <= 0:
        df_tmp = get_historical_ohlcv(symbol, days=30)
        if not df_tmp.empty:
            current_price = float(df_tmp["close"].iloc[-1])
            quote["price"] = current_price

    # 2. Xử lý tùy theo mode
    fa_result = {}
    ta_result = {}
    trade_setup = {}
    df_ohlcv = None

    if mode in ["full", "ta"]:
        df_ohlcv = get_historical_ohlcv(symbol, days=250)
        ta_result = analyze_technicals(df_ohlcv)

    if mode in ["full", "fa"]:
        fin_data = get_financial_data(symbol)
        if fin_data.get("eps") and fin_data["eps"] > 0 and current_price > 0:
            fin_data["pe"] = round(current_price / fin_data["eps"], 2)
        if fin_data.get("bvps") and fin_data["bvps"] > 0 and current_price > 0:
            fin_data["pb"] = round(current_price / fin_data["bvps"], 2)
        fa_result = analyze_fundamentals(fin_data, current_price, quote)

    if current_price <= 0:
        console.print(f"[bold red]❌ Không tìm thấy dữ liệu giá hợp lệ cho mã {symbol}. Vui lòng kiểm tra lại mã.[/bold red]")
        return {}

    # Nếu full mode, tính trade setup và council
    if mode == "full":
        trade_setup = calculate_trade_setup(current_price, fa_result, ta_result, quote)
        from core.db_manager import save_eod_quote, save_recommendation
        save_eod_quote(quote)
        save_recommendation(trade_setup, quote)
        
        council = InvestmentCouncil()
        council_result = council.deliberate(symbol, quote, fa_result, ta_result, trade_setup)
        
        _render_terminal_dashboard(symbol, quote, fa_result, ta_result, trade_setup, council_result)
        
        if save_report:
            _save_markdown_report(symbol, quote, fa_result, ta_result, trade_setup, council_result)
            
        if send_alert:
            send_telegram_alert(symbol, trade_setup, quote.get("company_name", ""))
            
        return trade_setup

    elif mode == "fa":
        # Chỉ render báo cáo FA
        _render_terminal_fa(symbol, quote, fa_result)
        return fa_result

    elif mode == "ta":
        # Chỉ render báo cáo TA (giả lập một fa_result rỗng để tính trade_setup nếu cần stop loss)
        trade_setup = calculate_trade_setup(current_price, {"fa_total_score": 50}, ta_result, quote)
        _render_terminal_ta(symbol, quote, ta_result, trade_setup)
        return ta_result


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

## 💎 2. ĐỊNH GIÁ THEO KHỐI TÀI SẢN & RADAR PHÁT HIỆN THAO TÚNG (ASSET-BASED VALUATION)

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

## 🏢 3. BÓC TÁCH MÔ HÌNH KINH DOANH CỐT LÕI (CORE BUSINESS BREAKDOWN)
> **Tóm tắt mô hình:** {segments_data.get('business_model_summary', 'N/A')}

| Mảng hoạt động | % Doanh thu | % Lợi nhuận gộp | Biên lãi gộp | Vai trò chiến lược | Điểm nhấn triển vọng & Rủi ro |
| :--- | :---: | :---: | :---: | :--- | :--- |
{segments_md}
---

## 👥 4. QUẢN TRỊ DOANH NGHIỆP, CỔ ĐÔNG & MẠNG LƯỚI CÔNG TY CON (GOVERNANCE & SHELL RADAR)
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

## 🏛️ 5. PHẢN BIỆN ĐA GÓC NHÌN TỪ HỘI ĐỒNG ĐẦU TƯ AI

{council_result.get('council_report')}

---
*Báo cáo được khởi tạo tự động bởi Hệ thống Vietnam Stock Analyzer Terminal.*
"""
    report_path.write_text(full_md_content, encoding="utf-8")
    console.print(f"\n[bold green]📁 Đã xuất bản báo cáo chi tiết tại:[/bold green] [underline cyan]{report_path}[/underline cyan]")


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
    t_table.add_column("Chỉ tiêu", style="cyan")
    t_table.add_column("Thông số", style="bold white")
    
    t_table.add_row("Khuyến nghị", f"[{action_color}]{trade.get('action')}[/{action_color}]")
    t_table.add_row("Điểm Đồng thuận", f"{trade.get('consensus_score')}/100")
    t_table.add_row("Vùng mua", f"{trade.get('buy_zone')}")
    t_table.add_row("Cắt lỗ", f"{trade.get('stop_loss', 0):,.0f} (-{trade.get('stop_loss_pct', 0)}%)")
    t_table.add_row("Chốt lời TP1", f"{trade.get('take_profit_1', 0):,.0f}")
    t_table.add_row("Tỷ trọng NAV", f"Max {trade.get('max_position_size_pct', 0):.1f}%")

    console.print(t_table)

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
    seg_data = fa.get("segments", {})
    if seg_data and seg_data.get("segments"):
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

    # Bảng Quản trị Doanh nghiệp & Mạng lưới Công ty con
    gov = fa.get("governance", {})
    if gov:
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
    if seg_data and seg_data.get("segments"):
        s_table = Table(title=f"🏢 CƠ CẤU PHÂN KHÚC HOẠT ĐỘNG (CORE BUSINESS): {symbol}", header_style="bold green")
        s_table.add_column("Mảng kinh doanh", style="bold white")
        s_table.add_column("% Doanh thu", style="cyan", justify="right")
        s_table.add_column("% LN Gộp", style="bold green", justify="right")
        s_table.add_column("Biên gộp", style="yellow", justify="right")
        s_table.add_column("Vai trò", style="magenta")

        for s in seg_data.get("segments", []):
            s_table.add_row(
                s.get("name"),
                f"{s.get('rev_share_pct')}%",
                f"{s.get('gross_profit_share_pct')}%",
                f"{s.get('gross_margin_pct')}%",
                s.get("role")
            )
        console.print(s_table)
    
    # Hiển thị Quản trị & Cổ đông trong FA
    gov = fa.get("governance", {})
    if gov:
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


def get_liquidity_rating(value_vnd: float) -> str:
    if value_vnd >= 10_000_000_000:
        return "A (Cao)"
    elif value_vnd >= 2_000_000_000:
        return "B (Trung bình)"
    elif value_vnd >= 300_000_000:
        return "C (Thấp - Hidden Gem)"
    return "D (Chết thanh khoản)"


def run_market_screener(top_n: int = 10):
    """
    Quét danh mục TOÀN THỊ TRƯỜNG (HOSE, HNX, UPCoM):
    """
    console.print(Panel(
        f"[bold white]Đang khởi động Radar quét toàn bộ 1500+ mã trên TTCK Việt Nam...[/bold white]\n"
        f"Lọc thanh khoản tối thiểu 300 triệu VNĐ/phiên.",
        title="[bold green]🔍 BỘ LỌC TÀN CẦU THỊ TRƯỜNG (FULL-MARKET SCREENER)[/bold green]",
        border_style="green"
    ))

    # GIAI ĐOẠN 1: Quét toàn thị trường qua Realtime API
    console.print("[cyan]Bước 1: Nạp dữ liệu Realtime từ HOSE, HNX, UPCoM...[/cyan]")
    all_tickers = get_all_tickers_realtime()
    
    if not all_tickers:
        console.print("[red]Không thể lấy dữ liệu Realtime. Kiểm tra kết nối mạng.[/red]")
        return
        
    # Lọc thanh khoản (Liquidity Gate >= 300 triệu VNĐ)
    liquid_tickers = [t for t in all_tickers if t.get("value", 0) >= 300_000_000]
    
    # Ưu tiên xếp hạng theo Nổ Volume (vol_ratio không có sẵn trong realtime, nên tạm xếp theo change_pct và value)
    # Để tối ưu, ta chọn top 80 mã tăng giá mạnh nhất hoặc giao dịch sôi động nhất đưa vào OHLCV quét.
    liquid_tickers.sort(key=lambda x: (x.get("change_pct", 0), x.get("value", 0)), reverse=True)
    eval_pool = liquid_tickers[:80]
    
    console.print(f"[cyan]Đã lọc được {len(liquid_tickers)} mã đạt thanh khoản chuẩn. Đang phân tích TA {len(eval_pool)} mã dẫn đầu...[/cyan]")

    # Lấy TA
    ta_candidates = []
    for idx, t in enumerate(eval_pool, start=1):
        sym = t["symbol"]
        print(f"[{idx}/{len(eval_pool)}] Đang quét TA: {sym}...", end="\r")
        try:
            df_ohlcv = get_historical_ohlcv(sym, days=250)
            if df_ohlcv.empty:
                continue
            ta_result = analyze_technicals(df_ohlcv)
            t["ta_score"] = ta_result.get("ta_total_score", 50)
            t["vol_ratio"] = ta_result.get("indicators", {}).get("vol_ratio", 1.0)
            t["ta_result"] = ta_result
            ta_candidates.append(t)
        except Exception:
            pass

    # Sort theo nổ vol và điểm TA
    ta_candidates.sort(key=lambda x: (x["vol_ratio"] >= 1.2, x["ta_score"], x["vol_ratio"]), reverse=True)
    
    # GIAI ĐOẠN 2: Bóc tách BCTC cho top mã tiềm năng
    final_candidates = ta_candidates[:max(top_n * 2, 10)]
    console.print(f"\n[cyan]Bước 2: Phân tích Cơ bản FA chuyên sâu cho Top {len(final_candidates)} mã...[/cyan]")
    
    results = []
    for c in final_candidates:
        sym = c["symbol"]
        price = c["price"]
        ta_result = c["ta_result"]
        
        fin_data = get_financial_data(sym)
        fa_result = analyze_fundamentals(fin_data, price)
        trade = calculate_trade_setup(price, fa_result, ta_result, c)
        
        results.append({
            "symbol": sym,
            "exchange": c.get("exchange", ""),
            "price": price,
            "change_pct": c["change_pct"],
            "value": c["value"],
            "vol_ratio": c["vol_ratio"],
            "consensus_score": trade.get("consensus_score", 0),
            "action": trade.get("action", "QUAN SÁT"),
            "buy_zone": trade.get("buy_zone", ""),
            "stop_loss": trade.get("stop_loss", 0),
            "tp1": trade.get("take_profit_1", 0),
            "f_score": fa_result.get("f_score", 0),
            "pe": fa_result.get("ratios", {}).get("pe", "N/A"),
            "liquidity": get_liquidity_rating(c["value"])
        })

    # Xếp hạng tổng quát
    results.sort(key=lambda x: (x["consensus_score"], x["vol_ratio"]), reverse=True)

    console.print("\n")
    screen_table = Table(title=f"🏆 BẢNG XẾP HẠNG TOÀN THỊ TRƯỜNG (TOP {top_n} CỔ PHIẾU TIỀM NĂNG)", header_style="bold green")
    screen_table.add_column("Mã CP", style="bold yellow")
    screen_table.add_column("Giá", style="bold white")
    screen_table.add_column("Thanh khoản", style="cyan")
    screen_table.add_column("Nổ Vol", style="cyan")
    screen_table.add_column("Điểm Đồng Thuận", style="bold yellow")
    screen_table.add_column("FA (F-Score|P/E)", style="magenta")
    screen_table.add_column("Khuyến nghị", style="bold")
    screen_table.add_column("Vùng Mua", style="green")

    for r in results[:top_n]:
        action_col = "green" if "MUA MẠNH" in r["action"] else ("cyan" if "MUA" in r["action"] else "yellow")
        screen_table.add_row(
            f"{r['symbol']} ({r['exchange']})",
            f"{r['price']:,.0f} ({r['change_pct']:+.1f}%)",
            r['liquidity'],
            f"{r['vol_ratio']:.2f}x",
            f"{r['consensus_score']}/100",
            f"{r['f_score']}/9 | {r['pe']}",
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
        choices=["analyze", "scan", "bot", "fa", "ta"],
        default="analyze",
        help="Chế độ hoạt động:\n  analyze: Soi sâu 1 mã (FA + TA)\n  fa: Chỉ phân tích Cơ bản (BCTC)\n  ta: Chỉ phân tích Kỹ thuật (Chart)\n  scan: Quét toàn bộ TTCK\n  bot: Chạy Telegram Bot"
    )
    parser.add_argument(
        "--ticker", "-t",
        default="HPG",
        help="Mã cổ phiếu cần phân tích (ví dụ: HPG, FPT...)"
    )
    parser.add_argument(
        "--top",
        type=int,
        default=10,
        help="Số lượng mã hiển thị trong chế độ scan (mặc định: 10)"
    )

    args = parser.parse_args()

    if args.mode == "scan":
        run_market_screener(top_n=args.top)
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
