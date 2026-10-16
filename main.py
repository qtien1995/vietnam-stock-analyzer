import sys
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

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
    analyze_ticker_ta,
    generate_eli5_summary,
    get_sector_waves_overview
)
from core.dashboard_generator import generate_dashboard_html
from core.data_loader import get_global_macro_and_commodities


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
            res["council_result"],
            res.get("timing_result"),
            res.get("insider_whale_result")
        )

        if save_report:
            _save_markdown_report(
                symbol,
                res["quote"],
                res["fa_result"],
                res["ta_result"],
                res["trade_setup"],
                res["council_result"],
                res.get("timing_result"),
                res.get("insider_whale_result")
            )
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



def _save_markdown_report(symbol, quote, fa_result, ta_result, trade_setup, council_result, timing_result=None, insider_whale=None):
    today_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"{today_str}_{symbol}.md"
    report_path = REPORTS_DIR / report_filename


    asset_val = fa_result.get("asset_valuation", {})
    segments_data = fa_result.get("segments", {})
    fin = fa_result.get("ratios", {})
    dupont = fa_result.get("dupont") or fin.get("dupont") or {}
    roic = fa_result.get("roic") if fa_result.get("roic") is not None else fin.get("roic")
    gov = fa_result.get("governance", {})
    own = gov.get("ownership", {})
    lead = gov.get("leadership", {})
    sub_web = gov.get("subsidiary_web", {})
    macro = fa_result.get("macro", {})
    cf = fa_result.get("cash_flow", {})
    ind = ta_result.get("indicators", {})
    adv_ta = ta_result.get("advanced_ta", {})
    buffett = fa_result.get("buffett", {})
    lynch = fa_result.get("lynch", {})
    oneil = ta_result.get("oneil", {})
    vsa = ta_result.get("vsa", {})

    # 1. Tạo tóm tắt ELI5
    eli5 = generate_eli5_summary(symbol, quote, fa_result, ta_result, trade_setup)

    # Bảng phân khúc Markdown
    segments_md = ""
    for s in segments_data.get("segments", []):
        segments_md += f"| **{s.get('name')}** | **{s.get('rev_share_pct')}%** | **{s.get('gross_profit_share_pct')}%** | `{s.get('gross_margin_pct')}%` | {s.get('role')} | {s.get('highlights')} |\n"
    if not segments_md:
        segments_md = "| Hoạt động kinh doanh cốt lõi | 100% | N/A | N/A | Vận hành cốt lõi | Chi tiết trong Thuyết minh BCTC kiểm toán |\n"

    # Bảng cổ đông Markdown
    sh_md = ""
    for sh in own.get("top_shareholders", [])[:6]:
        sh_md += f"| **{sh.get('name')}** | **{sh.get('percentage')}%** | {sh.get('shares', 0):,.0f} CP |\n"
    if not sh_md:
        sh_md = "| Đang cập nhật danh sách cổ đông lớn | N/A | N/A |\n"

    # Bảng công ty con Markdown
    sub_md = ""
    for sub in sub_web.get("key_subsidiaries", [])[:6]:
        sub_md += f"| **{sub.get('name')}** | **{sub.get('ownership_percent')}%** | Công ty con trực thuộc |\n"
    if not sub_md:
        sub_md = "| Mạng lưới trực thuộc công ty mẹ | 100% | Vận hành nội bộ |\n"

    altman_z_val = cf.get('altman_z')
    altman_z_str = f"{float(altman_z_val):.2f} điểm" if isinstance(altman_z_val, (int, float)) and altman_z_val is not None else "N/A"
    disc_pct = asset_val.get('asset_discount_pct')
    disc_str = f"{float(disc_pct):+.1f}%" if isinstance(disc_pct, (int, float)) and disc_pct is not None else "N/A"
    cash_ratio_str = f"{float(asset_val.get('cash_ratio') or 0.0):.1f}%"
    illiquid_ratio_str = f"{float(asset_val.get('illiquid_ratio') or 0.0):.1f}%"

    current_price = float(trade_setup.get("current_price", quote.get("price", 0.0)))
    fair_price = float(trade_setup.get("fair_price") or buffett.get("fair_price") or current_price)
    fair_p_str = f"{fair_price:,.0f} VND" if fair_price > 0 else "N/A"

    # Thông tin timing
    timing = timing_result or {}
    surge = timing.get("surge_scenario", {})
    crash = timing.get("crash_scenario", {})
    pulse = timing.get("smart_money_pulse", {})
    pivot_p = float(surge.get("trigger_pivot_price") or current_price * 1.03)
    fail_p = float(crash.get("failure_trigger_level") or current_price * 0.95)

    # Radar Sóng Ngành
    sw = macro.get("sector_wave", {})
    if sw and sw.get("has_wave"):
        cats_md = "\n".join([f"  * {c}" for c in sw.get("catalysts", [])])
        sw_md = f"""### 5. Radar Sóng Ngành & Động Lực Luân Chuyển Dòng Tiền (Sector Wave Radar):
- **Tên Sóng Ngành:** **{sw.get('wave_name')}**
- **Pha Chu Kỳ Sóng:** `{sw.get('phase')}`
- **Độ Nhiệt Sóng (Heat Score):** **{sw.get('heat_score', 50)}/100 điểm**
- **Vai Trò của {symbol}:** **{sw.get('role')}**
- **Nhóm Dẫn Dắt (Leaders):** `{', '.join(sw.get('leaders', []))}`
- **Nhóm Chạy Theo (Runners / High-Beta):** `{', '.join(sw.get('runners', []))}`
- **Chất Xúc Tác Kích Hoạt Sóng:**
{cats_md}
- **Bối Cảnh Lịch Sử Tương Đồng:** *{sw.get('historical_reference', 'N/A')}*
- **Chiến Lược Giao Dịch Đón Sóng:** {sw.get('trading_rule', 'N/A')}
- **Cảnh Báo Rủi Ro Sóng Tàn:** ⚠️ {sw.get('warning', 'N/A')}
"""
    else:
        sw_md = f"""### 5. Radar Sóng Ngành & Động Lực Luân Chuyển Dòng Tiền:
- Hiện chưa ghi nhận mã **{symbol}** nằm trong 10 đợt sóng ngành tâm điểm lớn của thị trường. Cổ phiếu đang tích lũy theo nội lực riêng.
"""

    # Bảng Tạo Lập & Tin Tức Lãnh Đạo Markdown
    iw_md = ""
    if insider_whale and isinstance(insider_whale, dict):
        iw_hold = insider_whale.get("holding_structure", {})
        iw_mm = insider_whale.get("market_maker_behavior", {})
        iw_lead = insider_whale.get("leadership_and_news_forensic", {})
        iw_play = insider_whale.get("actionable_playbook", {})
        iw_trap = iw_lead.get("news_trap_diagnosis", {})

        ev_md = "\n".join([f"  * {ev}" for ev in iw_mm.get("shakeout_evidence", [])])
        news_md = "\n".join([f"  * **[{nw.get('date', '')}]** {nw.get('title', '')}" for nw in iw_lead.get("recent_news_highlights", [])[:4]])
        events_md = "\n".join([f"  * **[{ev.get('date', '')}]** {ev.get('event_name', '')} *({ev.get('category', '')})*" for ev in iw_lead.get("recent_events", [])[:4]])

        iw_md = f"""
---

## 🦈 PHÂN HỆ: BÓC TÁCH TẠO LẬP, TAY TO GIỮ HÀNG & RADAR TIN TỨC LÃNH ĐẠO
### 1. Bản Đồ Cổ Đông & Phân Bổ Trôi Nổi Thực Tế (Holding Matrix):
- **Cơ cấu phân bổ:** Nội bộ/Lãnh đạo: `{iw_hold.get('insider_pct', 0)}%` | Khối ngoại: `{iw_hold.get('foreigner_pct', 0)}%` | Nhà nước: `{iw_hold.get('state_pct', 0)}%` | Trôi nổi tự do F0: `{iw_hold.get('true_free_float_pct', 0)}%`
- **Độ cô đặc cổ phiếu:** **{iw_hold.get('concentration_grade', '')}** — *{iw_hold.get('concentration_desc', '')}*
- **Quyền lực chi phối cuộc chơi:** {iw_hold.get('whale_dominance', '')}

### 2. Chẩn Đoán Hành Vi Cá Mập & Đội Lái (Market Maker Dynamics):
- **Trạng thái hành vi:** **{iw_mm.get('status', 'N/A')}**
- **Bóc tách hành động của Tay to:** {iw_mm.get('whale_action_desc', '')}
- **Chỉ số Áp lực Rung lắc & Ép bán:** **{iw_mm.get('shakeout_risk_score', 40)}/100 ({iw_mm.get('shakeout_risk_level', '')})**
- **Dẫn chứng rung lắc thực tế:**
{ev_md if ev_md else "  * Chưa phát hiện dấu hiệu rung lắc bất thường."}
- **Khối ngoại khớp lệnh hôm nay:** `{iw_mm.get('foreign_flow_today', 'N/A')}`

### 3. Radar Tin Tức Báo Chí & Bẫy Thao Túng Truyền Thông (News Trap Radar):
- **Chẩn đoán bẫy truyền thông:** **{iw_trap.get('trap_type', 'TRUNG TÍNH')}**
- **Bóc tách tương quan Vùng giá vs Tin tức:** {iw_trap.get('explanation', '')}
- **⚠️ Cảnh báo cho NĐT cá nhân:** {iw_trap.get('warning', '')}
- **Uy tín Ban Lãnh đạo:** **{iw_lead.get('leadership_credibility', '')}** — *{iw_lead.get('leadership_behavior_desc', '')}*

### 4. Tin Tức & Sự Kiện / Giao Dịch Nội Bộ Gần Nhất:
**Top Tin Báo Chí & Nghị Quyết:**
{news_md if news_md else "  * Chưa ghi nhận tin tức mới trong 30 ngày qua"}

**Sự Kiện & Giao Dịch Cổ Đông:**
{events_md if events_md else "  * Chưa ghi nhận sự kiện mới trong 30 ngày qua"}

### 5. Cẩm Nang Thực Chiến Dành Cho Nhà Đầu Tư:
- **Nguyên tắc ứng phó rung lắc:** {iw_play.get('shakeout_rule', '')}
- **Bộ lọc '3 Câu hỏi Vàng' trước tin tức:** {iw_play.get('news_filter_rule', '')}
"""


    # Xung đột quan điểm lớn nhất (Conflict Spotlight)
    clash_list = council_result.get("clash_of_perspectives", [])
    clash_text = ""
    if clash_list:
        for c in clash_list:
            topic = c.get("topic") or c.get("theme") or "Mâu thuẫn định giá vs Dòng tiền"
            side_a = c.get("side_a", {})
            side_b = c.get("side_b", {})
            cro = c.get("cro_synthesis") or c.get("arbiter_verdict") or ""
            clash_text += f"- **{topic}**\n"
            if side_a:
                clash_text += f"  * *{side_a.get('speaker', 'Phe A')}:* {side_a.get('argument', '')}\n"
            if side_b:
                clash_text += f"  * *{side_b.get('speaker', 'Phe B')}:* {side_b.get('argument', '')}\n"
            if cro:
                clash_text += f"  * *Trọng tài CRO:* {cro}\n"
    else:
        clash_text = f"- **Định giá Tài sản (P/B {asset_val.get('pb', 'N/A')}x) vs Dòng tiền Thực (CFO TTM {cf.get('cfo_ttm', 0):,.0f} đ)**: Cổ phiếu có định giá tài sản hấp dẫn nhưng cần dòng tiền kinh doanh xác nhận tăng trưởng để tránh bẫy giá trị."

    full_md_content = f"""# 🏛️ BÁO CÁO PHÂN TÍCH CHIẾN LƯỢC 360°: {symbol} - {quote.get('company_name', symbol)}
> **Ngày phân tích:** {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}  
> **Kiến trúc:** Zero-Server Local Terminal | **Nguồn dữ liệu:** Giá Khớp lệnh Realtime & BCTC Độc lập  
> **Nguyên tắc:** Dữ liệu chuẩn xác, không bịa đặt, quản trị rủi ro nghiêm ngặt.

---

## 🧒 PHÂN HỆ 1: GIẢI THÍCH CHO ĐỨA TRẺ LÊN 5 (ELI5 — BẢN CHẤT CỐT LÕI)
*Trước khi đi vào ma trận số liệu kỹ thuật phức tạp, hãy nhìn nhận doanh nghiệp bằng các ví dụ đời thường:*
- **🏬 Tiệm này bán cái gì kiếm tiền?**  
  {eli5.get('what_they_sell')}
- **💰 Tiền thật hay tiền trên giấy?**  
  {eli5.get('real_or_paper_money')}
- **🪤 Cổ phiếu này đang là món hời hay chiếc bẫy chuột?**  
  {eli5.get('bargain_or_trap')}
- **🦈 Đội lái và "cá mập" đang làm gì?**  
  {eli5.get('shark_action')}
- **🐷 Lời khuyên bỏ heo đất:**  
  {eli5.get('piggy_bank_advice')}

---

## 🎯 PHÂN HỆ 2: PHÁN QUYẾT HỘI ĐỒNG & KẾ HOẠCH GIAO DỊCH
> **Kết luận Hội đồng:** **{trade_setup.get('action')}** (Đồng thuận: **{trade_setup.get('consensus_score')}/100 điểm**)  
> **Lý giải hành động:** {trade_setup.get('action_summary', '')}

### 🏛️ Kế hoạch 1: Đầu tư Giá trị (Tích sản theo Buffett & Graham)
- **Giá trị thực ước tính (Fair Value):** `{fair_p_str}` (Biên an toàn: `{buffett.get('margin_of_safety_pct', 0):.1f}%`)
- **Vùng gom an toàn:** `{trade_setup.get('value_buy_zone')}`
- **Hệ số P/B thực tế:** `{asset_val.get('pb', 'N/A')}x` (Mức chiết khấu tài sản: `{disc_str}`)
- **Trạng thái định giá:** `{trade_setup.get('value_status')}` — {trade_setup.get('value_rationale', '')}

### 🏄 Kế hoạch 2: Lướt sóng Ngắn hạn (Swing / Kỹ thuật theo Minervini & Wyckoff)
- **Vùng mua tối ưu:** `{trade_setup.get('swing_buy_zone', trade_setup.get('buy_zone'))}`
- **Điểm cắt lỗ kỷ luật (Stop Loss):** `{trade_setup.get('stop_loss', 0):,.0f} VND` (**-{trade_setup.get('stop_loss_pct', 0)}%**, bảo toàn vốn &le; 7% HOSE)
- **Mục tiêu chốt lời 1 (TP1):** `{trade_setup.get('take_profit_1', 0):,.0f} VND` (**+{trade_setup.get('take_profit_1_pct', 0)}%**)
- **Mục tiêu chốt lời 2 (TP2):** `{trade_setup.get('take_profit_2', 0):,.0f} VND` (**+{trade_setup.get('take_profit_2_pct', 0)}%**)
- **Tỷ lệ Risk / Reward (R:R):** `{trade_setup.get('risk_reward_ratio')}:1` (Đạt chuẩn tối thiểu &ge; 2:1)
- **Tỷ trọng giải ngân tối đa:** `{trade_setup.get('max_position_size_pct', 0):.1f}% NAV` (Giới hạn rủi ro 1.5% NAV)

---

## 🏛️ PHÂN HỆ 3: BẢNG GÓC NHÌN 5 TRƯỜNG PHÁI & ĐIỂM MÂU THUẪN LỚN NHẤT
| Trường Phái Đầu Tư | Đại Diện Huyền Thoại | Phán Quyết | Điểm Số | Luận Điểm Cốt Lõi |
| :--- | :--- | :--- | :---: | :--- |
| **1. Giá trị & Con hào kinh tế** | Graham – Buffett – Munger | `{buffett.get('verdict', 'QUAN SÁT')}` | {buffett.get('score', 50)}/100 | {buffett.get('reasons', ['Định giá tài sản & dòng tiền'])[0]} |
| **2. Tăng trưởng chất lượng (GARP)** | Peter Lynch – Fisher | `{lynch.get('verdict', 'THEO DÕI')}` | {lynch.get('score', 50)}/100 | {lynch.get('reasons', ['Chất lượng tăng trưởng & PEG'])[0]} |
| **3. Kỹ thuật & Dòng tiền lớn** | Minervini – O'Neil – Wyckoff | `{oneil.get('verdict', 'QUAN SÁT')}` | {oneil.get('score', 50)}/100 | {oneil.get('reasons', ['CANSLIM Breakout & Xu hướng'])[0]} |
| **4. Vĩ mô & Chu kỳ ngành** | Ray Dalio – Howard Marks | `{macro.get('sentiment', 'TRUNG TÍNH')}` | {macro.get('tailwind_score', 70)}/100 | {macro.get('dalio_verdict', 'Chu kỳ ngành & động lực vĩ mô')} |
| **5. Quản trị rủi ro & Trọng tài** | Nassim Taleb – CRO Arbiter | `{trade_setup.get('action')}` | {trade_setup.get('consensus_score', 50)}/100 | Kỷ luật cắt lỗ nghiêm ngặt, lọc bẫy giá trị và setup hợp lệ |

### ⚡ Điểm Mâu Thuẫn Lớn Nhất (Conflict Spotlight):
{clash_text}

---

## 🔬 PHÂN HỆ 4: BÓC TÁCH CHUYÊN SÂU CƠ BẢN (FA DEEP-DIVE 360°)
### 1. Báo cáo Kết quả Kinh doanh & Dòng tiền Thật (Cash Flow Forensic):
| Chỉ tiêu Dòng tiền & Sức khỏe | Giá trị thực tế | Đánh giá Chất lượng & Rủi ro |
| :--- | :--- | :--- |
| **Chất lượng Lợi nhuận** | **Hạng {cf.get('quality_grade', 'B')}: {cf.get('quality_verdict', 'LÀNH MẠNH')}** | {cf.get('quality_desc', '')} |
| **Dòng tiền thuần HĐKD (CFO TTM)** | **{cf.get('cfo_ttm', 0):,.0f} VND** | Tiền mặt thực thu từ hoạt động kinh doanh cốt lõi |
| **Chi tiêu vốn (CapEx TTM)** | **{cf.get('capex_ttm', 0):,.0f} VND** | Dòng tiền chi mua sắm tài sản cố định mở rộng |
| **Dòng tiền tự do (FCF TTM)** | **{cf.get('fcf_ttm', 0):,.0f} VND** | {cf.get('fcf_verdict', '')} |
| **Tỷ lệ Tiền thật / Lãi sổ sách (CFO/LNST)**| **{float(cf.get('earnings_quality_ratio') or 0):.2f}x** | Chuẩn an toàn &ge; 1.0x (Tiền mặt về tương xứng lợi nhuận) |
| **Chỉ số Kiệt quệ Altman Z''-Score** | **{altman_z_str}** | **{cf.get('z_verdict', 'AN TOÀN')}** ({cf.get('z_desc', '')}) |
| **Piotroski F-Score** | **{fa_result.get('f_score', 0)}/9 điểm** | Sức khỏe bảng cân đối kế toán (Đạt chuẩn khi &ge; 5/9) |

### 2. Mô hình Phân rã DuPont (3 Nhân tố) & Hiệu quả Vốn Đầu tư (ROIC):
- **Phân rã ROE DuPont:** Biên lãi ròng (`{dupont.get('net_margin_pct', 'N/A')}%`) &times; Vòng quay tài sản (`{dupont.get('asset_turnover', 'N/A')}x`) &times; Đòn bẩy tài sản/VCSH (`{dupont.get('equity_multiplier', 'N/A')}x`) &rarr; **ROE:** `{dupont.get('calculated_roe', fin.get('roe', 'N/A'))}%`
- **Động lực thúc đẩy chính:** **{dupont.get('primary_driver', 'CÂN BẰNG')}** — *{dupont.get('explanation', '')}*
- **Tỷ suất sinh lời trên Vốn đầu tư (ROIC):** `{f"{float(roic):.2f}%" if roic is not None else "N/A"}` (Hiệu quả sinh tiền mặt của vốn hoạt động)

### 3. Kiểm toán Bảng Cân đối & Tài sản Đọng Vốn:
- **Giá trị sổ sách (BVPS):** `{asset_val.get('bvps', 0):,.0f} VND/CP` | **P/B:** `{asset_val.get('pb', 'N/A')}x` (Chiết khấu: `{disc_str}`)
- **Tiền mặt & tiền gửi:** `{cash_ratio_str}` tổng tài sản | **Tài sản đọng vốn (Phải thu + Tồn kho):** `{illiquid_ratio_str}` tổng tài sản
- **Đánh giá chất lượng tài sản:** {asset_val.get('asset_quality_verdict', 'Bình thường')}

### 4. Bóc tách Mô hình Kinh doanh Cốt lõi & Phân khúc Hoạt động:
> **Tóm tắt mô hình:** {segments_data.get('business_model_summary', 'N/A')}

| Mảng hoạt động | % Doanh thu | % Lợi nhuận gộp | Biên lãi gộp | Vai trò chiến lược | Điểm nhấn triển vọng & Rủi ro |
| :--- | :---: | :---: | :---: | :--- | :--- |
{segments_md}

### 5. Quản trị Doanh nghiệp, Cổ đông & Radar Hệ sinh thái (G-Score):
> **Điểm Quản trị (G-Score):** **{gov.get('g_score', 'N/A')}/100** ({gov.get('g_rating', 'N/A')})  
> **Cơ cấu Sở hữu:** {own.get('structure', 'N/A')} — *Trôi nổi:* `{own.get('free_float_pct', 0)}%` | *Khối ngoại:* `{own.get('foreigner_pct', 0)}%` | *Nhà nước:* `{own.get('state_pct', 0)}%`  
> **Ban Điều hành:** Chủ tịch: **{lead.get('chairman', 'Chưa rõ')}** | CEO: **{lead.get('ceo', 'Chưa rõ')}** (Skin in the game: `{lead.get('insider_total_pct', 0)}%` — {lead.get('skin_in_game_verdict', 'N/A')})  
> **Radar Chân rết & Tăng vốn ảo:** **{sub_web.get('circular_capital_verdict', 'N/A')}** ({sub_web.get('subsidiary_count', 0)} công ty con, {sub_web.get('affiliate_count', 0)} công ty liên kết)

#### Danh sách Cổ đông Chủ chốt:
| Cổ đông lớn | Tỷ lệ sở hữu | Số lượng cổ phiếu |
| :--- | :---: | :---: |
{sh_md}

#### Mạng lưới Công ty con Trọng yếu:
| Tên Đơn vị Thành viên | Tỷ lệ Biểu quyết | Vai trò trong Hệ sinh thái |
| :--- | :---: | :--- |
{sub_md}

{sw_md}
{iw_md}
---


## 📈 PHÂN HỆ 5: BÓC TÁCH CHUYÊN SÂU KỸ THUẬT (TA DEEP-DIVE 360°)
### 1. Hệ thống Chỉ báo & Xu hướng Giá:
| Chỉ báo Kỹ thuật | Giá trị Thực tế | Trạng thái & Ý nghĩa |
| :--- | :--- | :--- |
| **Giá khớp lệnh hiện tại** | **{current_price:,.0f} VND** | So với EMA20: `{(current_price - float(ind.get('ema20', current_price))) / float(ind.get('ema20', 1)) * 100:+.1f}%` |
| **Đường xu hướng EMA20 / EMA50** | EMA20: `{float(ind.get('ema20', 0)):,.0f}` | EMA50: `{float(ind.get('ema50', 0)):,.0f}` ({'Uptrend' if current_price > float(ind.get('ema20', 0)) > float(ind.get('ema50', 0)) else 'Downtrend / Chờ tích lũy'}) |
| **Đường dài hạn SMA200** | `{float(ind.get('sma200', 0)):,.0f} VND` | Xu thế dài hạn năm |
| **Khung giá 52 Tuần (52-Week Range)** | Đáy: `{float(ind.get('low_52w', current_price)):,.0f}` | Đỉnh: `{float(ind.get('high_52w', current_price)):,.0f} VND` |
| **O'Neil RS Rating (Sức mạnh giá)** | **{int(ind.get('rs_rating', 50))}/99 điểm** | {'Top 20% cổ phiếu mạnh nhất thị trường' if int(ind.get('rs_rating', 50)) >= 80 else 'Xung lực giá tích cực / trung bình'} |
| **Chỉ báo Động lượng RSI 14** | **{float(ind.get('rsi14', 50)):.1f}** | {'Quá mua - Rung lắc' if float(ind.get('rsi14', 50)) >= 70 else ('Quá bán - Cạn lực bán' if float(ind.get('rsi14', 50)) <= 35 else 'Vùng trung tính lành mạnh')} |
| **Chỉ báo MACD & Histogram** | MACD: `{float(ind.get('macd', 0)):.1f}` | Histogram: `{float(ind.get('macd_hist', 0)):.1f}` |
| **Độ biến động thực tế ATR 14** | `{float(ind.get('atr14', 0)):,.0f} VND` | Biên độ dao động bình quân mỗi phiên |
| **Khối lượng vs MA20** | **{float(ind.get('vol_ratio', 1.0)):.2f}x MA20** | Khối lượng khớp: `{quote.get('volume', 0):,.0f} CP` |
| **Hỗ trợ & Kháng cự 20 phiên** | Hỗ trợ: `{float(ind.get('sup_20d', 0)):,.0f}` | Kháng cự: `{float(ind.get('res_20d', 0)):,.0f} VND` |

### 2. Mô hình Nền giá VCP (Minervini) & Wyckoff VSA:
- **Mô hình Thu hẹp Biến động (VCP):** `{adv_ta.get('pattern_name', 'Đang tích lũy')}` — *{adv_ta.get('pattern_verdict', '')}*
- **Chu kỳ Wyckoff VSA:** `{vsa.get('phase', 'Tích lũy')}`
- **Tín hiệu Nến VSA đặc thù:** `{adv_ta.get('vsa_signal', 'Bình thường')}` — *{adv_ta.get('vsa_signal_desc', '')}*
- **Fibonacci Retracement then chốt:** Fibo 38.2%: `{float(adv_ta.get('fibo_382', 0)):,.0f} đ` | Fibo 50.0%: `{float(adv_ta.get('fibo_500', 0)):,.0f} đ` | Fibo 61.8%: `{float(adv_ta.get('fibo_618', 0)):,.0f} đ`
- **Vùng Cung Kẹp Hàng (Overhead Supply):** `{float(adv_ta.get('overhead_supply', 0)):,.0f} đ` (Áp lực bán chờ chốt hòa vốn tại đỉnh cũ)

---

## ⚡ PHÂN HỆ 6: ĐỘNG CƠ THỜI ĐIỂM (TIMING MATRIX) & THƯỚC ĐO GIÁ
> **Phán quyết Thời điểm:** **{timing.get('timing_verdict', 'THEO DÕI VÙNG HỖ TRỢ')}**  
> **Điểm Điều kiện Kỹ thuật:** **{timing.get('setup_quality_score', 50)}/100 điểm**  
> **Xung lực Mua/Bán chủ động:** Mua chủ động: `{pulse.get('active_buy_pct', 50)}%` vs Bán chủ động: `{pulse.get('active_sell_pct', 50)}%` (Khối ngoại: `{pulse.get('foreign_net_vol', 0):,.0f} CP`)

### 1. Khi nào tăng? (Kịch bản Bứt phá):
- **Mốc Pivot kích hoạt:** **{pivot_p:,.0f} VND** kèm điều kiện Volume bùng nổ > 1.3x MA20.
- **Khung thời gian dự kiến:** {surge.get('timing_window', 'Đang tích lũy trong nền giá')}
- **Chất xúc tác hỗ trợ:**
"""
    for cat in surge.get("catalysts", ["Dòng tiền tích lũy cạn cung quanh hỗ trợ"]):
        full_md_content += f"  * {cat}\n"

    full_md_content += f"""
### 2. Khi nào sập? (Kịch bản Rủi ro & Gãy nền):
- **Mốc Vi phạm Rủi ro (Failure Level):** **{fail_p:,.0f} VND** (Thủng mốc này thì toàn bộ thiết lập tăng bị hủy bỏ).
- **Khung thời gian nguy hiểm:** {crash.get('timing_window', 'Rủi ro rung lắc ở mức thấp')}
- **Cảnh báo cần theo dõi:**
"""
    for w in crash.get("warnings", ["Chưa phát hiện tín hiệu phân phối lớn hay phân kỳ âm"]):
        full_md_content += f"  * {w}\n"

    full_md_content += f"""
### 3. Thước Đo Kích Hoạt Giá (Price Ladder Gauge):
| Cột mốc | Mức Giá | Khoảng Cách so với Thị Giá ({current_price:,.0f} đ) | Trạng Thái & Hành Động |
| :--- | :---: | :---: | :--- |
| **Mục tiêu chốt lời 2 (TP2)** | `{trade_setup.get('take_profit_2', 0):,.0f} đ` | `+{trade_setup.get('take_profit_2_pct', 0)}%` | Chốt lời từng phần, nâng chặn lãi |
| **Mục tiêu chốt lời 1 (TP1)** | `{trade_setup.get('take_profit_1', 0):,.0f} đ` | `+{trade_setup.get('take_profit_1_pct', 0)}%` | Chốt lời 1/2 vị thế lướt sóng |
| **Điểm nổ Pivot kích hoạt** | `{pivot_p:,.0f} đ` | `{((pivot_p - current_price) / current_price * 100):+.1f}%` | Gia tăng tỷ trọng khi nổ Vol xác nhận |
| **THỊ GIÁ HIỆN TẠI** | `{current_price:,.0f} đ` | `0.0%` | Mức giá tham chiếu khớp lệnh phiên |
| **Ngưỡng gãy sóng (Failure)** | `{fail_p:,.0f} đ` | `{((fail_p - current_price) / current_price * 100):+.1f}%` | Kịch bản tăng mất hiệu lực |
| **Cắt lỗ kỷ luật (Stop Loss)** | `{trade_setup.get('stop_loss', 0):,.0f} đ` | `-{trade_setup.get('stop_loss_pct', 0)}%` | Kích hoạt bán hạ tỷ trọng bảo toàn vốn |

---

## 🔮 PHÂN HỆ 7: DỰ PHÓNG KỊCH BẢN & ĐIỀU KIỆN MẤT HIỆU LỰC
### 1. Dự phóng 3 Kịch bản Giá (Scenarios):
- **Kịch bản Cơ sở (Base - Xác suất 55%):** Giá vận động tích lũy trong biên độ `{trade_setup.get('buy_zone')}`, hấp thụ lượng cung kẹp hàng trước khi kiểm tra lại kháng cự `{pivot_p:,.0f} đ`. Hướng xử lý: Mua thăm dò tỷ trọng an toàn.
- **Kịch bản Tích cực (Bull - Xác suất 25%):** Dòng tiền lớn bùng nổ vượt dứt khoát mốc Pivot `{pivot_p:,.0f} đ` kèm Vol > 1.5x MA20, hướng về mục tiêu TP1 `{trade_setup.get('take_profit_1', 0):,.0f} đ`. Hướng xử lý: Gia tăng vị thế theo đà tăng.
- **Kịch bản Tiêu cực (Bear - Xác suất 20%):** Áp lực bán gia tăng, giá đóng cửa thủng mốc vi phạm `{fail_p:,.0f} đ` hoặc thủng hỗ trợ EMA50. Hướng xử lý: Kích hoạt kỷ luật cắt lỗ `{trade_setup.get('stop_loss', 0):,.0f} đ` để bảo vệ vốn tuyệt đối.

### 2. Điều kiện Mất hiệu lực (Invalidation Triggers):
Toàn bộ luận điểm phân tích và kế hoạch giao dịch phía trên lập tức **BỊ HỦY BỎ** nếu xảy ra một trong các điều kiện sau:
1. **Vi phạm Kỹ thuật:** Giá đóng cửa phiên xuyên thủng ngưỡng hỗ trợ cứng `{fail_p:,.0f} đ` kèm khối lượng bán đột biến > 1.3x MA20.
2. **Vi phạm Cơ bản:** BCTC quý kế tiếp công bố Dòng tiền HĐKD (CFO) âm nặng liên tiếp hoặc Nợ vay tăng đột biến vượt 2.0x Vốn chủ sở hữu.
3. **Biến cố Quản trị / Pháp lý:** Ban điều hành bán chui cổ phiếu, bị khởi tố điều tra hoặc xuất hiện giao dịch chuyển nhượng vốn lòng vòng mờ ám trong hệ sinh thái.

### 3. Báo cáo Dữ kiện Còn thiếu (Missing Data Audit):
- BCTC thuyết minh chi tiết tiến độ các dự án xây dựng dở dang cần đối chiếu với BCTC kiểm toán gần nhất.
- Tỷ lệ sở hữu chi tiết của các nhóm cổ đông liên quan đến Chủ tịch/CEO cần kiểm tra qua Báo cáo Quản trị định kỳ 6 tháng.

---
*Lưu ý miễn trừ trách nhiệm: Báo cáo này là sản phẩm tham mưu hỗ trợ quyết định từ Hệ thống Vietnam Stock Analyzer Terminal, không cấu thành lời mời chào hay khuyến nghị bảo đảm sinh lời. Nhà đầu tư tự chịu trách nhiệm về quyết định đặt lệnh.*
"""
    report_path.write_text(full_md_content, encoding="utf-8")
    console.print(f"\n[bold green]📁 Đã xuất bản báo cáo chi tiết chuẩn 7 Phân hệ tại:[/bold green] [underline cyan]{report_path}[/underline cyan]")


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


def _render_insider_whale_table(symbol: str, iw: dict):
    """Bảng Bóc tách Tạo Lập, Tay To Giữ Hàng & Radar Tin Tức Ban Lãnh Đạo"""
    if not iw:
        return
    holding = iw.get("holding_structure", {})
    mm = iw.get("market_maker_behavior", {})
    lead = iw.get("leadership_and_news_forensic", {})
    playbook = iw.get("actionable_playbook", {})

    w_table = Table(title=f"🦈 PHÂN HỆ: BÓC TÁCH TẠO LẬP, TAY TO & RADAR TIN TỨC LÃNH ĐẠO ({symbol})", header_style="bold magenta")
    w_table.add_column("Hạng mục Phân tích", style="cyan", width=25)
    w_table.add_column("Trạng thái & Thông số", style="bold white", width=26)
    w_table.add_column("Bóc tách Chuyên sâu & Cảnh báo", style="white")

    mm_status = mm.get("status", "CHƯA XÁC ĐỊNH")
    mm_col = "green" if "ĐẨY GIÁ" in mm_status else ("red" if "PHÂN PHỐI" in mm_status else ("cyan" if "GOM" in mm_status else "yellow"))
    sh_score = int(mm.get("shakeout_risk_score", 40))
    sh_col = "red" if sh_score >= 70 else ("yellow" if sh_score >= 45 else "green")

    w_table.add_row(
        "Trôi nổi & Độ cô đặc",
        f"Trôi nổi F0: {holding.get('true_free_float_pct', 0)}%",
        f"[bold yellow]{holding.get('concentration_grade', '')}[/bold yellow]\n{holding.get('whale_dominance', '')}"
    )
    w_table.add_row(
        "Hành vi Tạo lập / Tay to",
        f"[{mm_col}]{mm_status}[/{mm_col}]",
        f"{mm.get('whale_action_desc', '')}"
    )
    w_table.add_row(
        "Áp lực Rung lắc & Ép bán",
        f"[{sh_col}]{sh_score}/100 ({mm.get('shakeout_risk_level', '')})[/{sh_col}]",
        f"Khối ngoại phiên: {mm.get('foreign_flow_today', 'N/A')} | {'; '.join(mm.get('shakeout_evidence', [])[:2])}"
    )
    
    trap_diag = lead.get("news_trap_diagnosis", {})
    t_type = trap_diag.get("trap_type", "TRUNG TÍNH")
    t_col = "red" if "BẪY TIN TỐT" in t_type else ("cyan" if "TIN XẤU" in t_type else "green")
    w_table.add_row(
        "Radar Bẫy Tin Tức",
        f"[{t_col}]{t_type}[/{t_col}]",
        f"{trap_diag.get('explanation', '')}\n[bold red]⚠️ {trap_diag.get('warning', '')}[/bold red]"
    )
    w_table.add_row(
        "Uy tín Ban Lãnh đạo",
        f"{lead.get('leadership_credibility', '')}",
        f"{lead.get('leadership_behavior_desc', '')}"
    )
    console.print(w_table)


def _render_terminal_dashboard(symbol, quote, fa, ta, trade, council, timing=None, insider_whale=None):
    """In giao diện bảng Full (Cả FA, TA, Timing, Hội đồng & Tạo lập) chuẩn 360°"""

    current_price = trade.get("current_price", quote.get("price", 0))
    change_pct = quote.get("change_pct", 0)
    chg_color = "green" if change_pct > 0 else ("red" if change_pct < 0 else "yellow")

    # Header Thông tin thị trường
    console.print(Panel(
        f"[bold white]{symbol} - {quote.get('company_name', symbol)}[/bold white]\n"
        f"Giá hiện tại: [bold {chg_color}]{current_price:,.0f} VND[/bold {chg_color}] ({change_pct:+.2f}%) | "
        f"Khối lượng: [bold cyan]{quote.get('volume', 0):,.0f}[/bold cyan] CP | "
        f"Sàn: [bold yellow]{quote.get('exchange', 'HOSE')}[/bold yellow]",
        title="[bold yellow]🏛️ THÔNG TIN THỊ TRƯỜNG REALTIME[/bold yellow]",
        border_style="bright_blue"
    ))

    # PHÂN HỆ 1: GIẢI THÍCH CHO ĐỨA TRẺ LÊN 5 (ELI5)
    eli5 = generate_eli5_summary(symbol, quote, fa, ta, trade)
    console.print(Panel(
        f"[bold cyan]1. Công ty này bán gì kiếm tiền?[/bold cyan]\n{eli5['core_business']}\n\n"
        f"[bold cyan]2. Tiền thật hay tiền trên giấy?[/bold cyan]\n{eli5['real_vs_paper_money']}\n\n"
        f"[bold cyan]3. Món hời hay chiếc bẫy chuột?[/bold cyan]\n{eli5['bargain_or_trap']}\n\n"
        f"[bold cyan]4. Đội lái & Cá mập đang làm gì?[/bold cyan]\n{eli5['big_money_action']}\n\n"
        f"[bold yellow]🧒 Lời khuyên bỏ heo đất cho đứa trẻ 5 tuổi:[/bold yellow]\n[bold green]{eli5['piggy_bank_advice']}[/bold green]",
        title="[bold yellow]🧒 PHÂN HỆ 1: GIẢI THÍCH CHO ĐỨA TRẺ LÊN 5 (ELI5 — BẢN CHẤT CỐT LÕI)[/bold yellow]",
        border_style="yellow"
    ))

    # PHÂN HỆ 2: PHÁN QUYẾT HỘI ĐỒNG & KẾ HOẠCH GIAO DỊCH
    action_color = trade.get("action_color", "white")
    t_table = Table(title="🎯 PHÂN HỆ 2: KẾ HOẠCH GIAO DỊCH 2 TRƯỜNG PHÁI (CHIEF RISK OFFICER)", header_style="bold magenta")
    t_table.add_column("Trường phái / Hạng mục", style="cyan")
    t_table.add_column("Kế hoạch & Vùng mua", style="bold white")
    t_table.add_column("Lý do & Kỷ luật rủi ro", style="yellow")
    
    t_table.add_row(
        "Khuyến nghị tổng hợp",
        f"[{action_color}]{trade.get('action')}[/{action_color}]",
        f"Đồng thuận: {trade.get('consensus_score')}/100 | Tỷ trọng Max {trade.get('max_position_size_pct', 0):.1f}% NAV"
    )
    
    val_status_color = "red" if "ĐẮT" in trade.get("value_status", "") else ("green" if "RẺ" in trade.get("value_status", "") else "cyan")
    fair_p = trade.get('fair_price') or current_price
    fair_p_str = f"{float(fair_p):,.0f} đ" if fair_p else "N/A"
    t_table.add_row(
        "🏛️ Đầu tư Giá trị (Tích sản)",
        f"{trade.get('value_buy_zone')}\n(Giá trị thực: [bold]{fair_p_str}[/bold] | P/B: {fa.get('asset_valuation', {}).get('pb', 'N/A')}x)",
        f"[{val_status_color}]{trade.get('value_status')}[/{val_status_color}]: {trade.get('value_rationale', '')}"
    )
    
    t_table.add_row(
        "🏄 Lướt sóng Ngắn hạn (Swing)",
        f"Vùng mua: [bold green]{trade.get('swing_buy_zone')}[/bold green]\nCắt lỗ: [bold red]{trade.get('stop_loss', 0):,.0f} đ[/bold red] (-{trade.get('stop_loss_pct', 0)}%)\nChốt lời TP1: [bold cyan]{trade.get('take_profit_1', 0):,.0f} đ[/bold cyan] (+{trade.get('take_profit_1_pct', 0)}%)\nChốt lời TP2: [bold blue]{trade.get('take_profit_2', 0):,.0f} đ[/bold blue] (+{trade.get('take_profit_2_pct', 0)}%)",
        f"R:R = {trade.get('risk_reward_ratio')}:1 (SL <= 7%)\n{trade.get('swing_strategy_note', '')}"
    )
    console.print(t_table)

    # PHÂN HỆ 3: HỘI ĐỒNG 5 TRƯỜNG PHÁI & ĐIỂM XUNG ĐỘT (CONFLICT SPOTLIGHT)
    if council and isinstance(council, dict):
        members = council.get("members", [])
        if members:
            c_table = Table(title="🏛️ PHÂN HỆ 3: ĐÁNH GIÁ 5 TRƯỜNG PHÁI ĐẦU TƯ (COUNCIL MATRIX)", header_style="bold blue")
            c_table.add_column("Trường phái & Chuyên gia", style="cyan")
            c_table.add_column("Tín hiệu / Điểm", style="bold white", justify="center")
            c_table.add_column("Luận điểm & Góc nhìn độc lập", style="white")

            for m in members:
                stance = m.get("stance") or m.get("verdict") or "QUAN SÁT"
                v_col = "green" if "MUA" in stance else ("red" if "BÁN" in stance or "PHẢN ĐỐI" in stance else "yellow")
                role_str = m.get("role_title") or m.get("title") or ""
                arg_str = m.get("core_thesis") or (m.get("arguments", [""])[0] if m.get("arguments") else "")
                c_table.add_row(
                    f"{m.get('badge', '')} {m.get('name', '')}\n[dim]{role_str}[/dim]",
                    f"[{v_col}]{stance}[/{v_col}]\n({m.get('score', 0)}/100)",
                    arg_str
                )
            console.print(c_table)

        # Conflict Spotlight
        clashes = council.get("clash_of_perspectives", [])
        if clashes:
            clash = clashes[0]
            console.print(Panel(
                f"[bold red]⚡ Va chạm gay gắt nhất:[/bold red] {clash.get('topic')}\n\n"
                f"[bold yellow]Phe A ({clash.get('side_a', {}).get('speaker', '')}):[/bold yellow]\n{clash.get('side_a', {}).get('argument', '')}\n\n"
                f"[bold cyan]Phe B ({clash.get('side_b', {}).get('speaker', '')}):[/bold cyan]\n{clash.get('side_b', {}).get('argument', '')}\n\n"
                f"[bold green]Phán quyết Trung tài CRO:[/bold green]\n{clash.get('cro_synthesis', '')}",
                title="[bold red]⚡ ĐIỂM MÂU THUẪN LỚN NHẤT (CONFLICT SPOTLIGHT)[/bold red]",
                border_style="red"
            ))

    # PHÂN HỆ 4: FA DEEP-DIVE 360°
    # Vĩ mô & Chu kỳ Ngành
    macro = fa.get("macro", {})
    if macro:
        m_table = Table(title="🌐 VĨ MÔ & CHU KỲ NGÀNH (RAY DALIO & HOWARD MARKS)", header_style="bold blue")
        m_table.add_column("Chỉ tiêu Vĩ mô", style="cyan")
        m_table.add_column("Trạng thái", style="bold yellow")
        m_table.add_column("Nhận định & Tác động", style="white")

        t_color = "green" if macro.get("tailwind_score", 70) >= 80 else ("cyan" if macro.get("tailwind_score", 70) >= 70 else "yellow")
        m_table.add_row("Ngành & Pha chu kỳ", f"{macro.get('sector_name')}", f"Pha: {macro.get('cycle_phase')}")
        m_table.add_row("Gió xuôi Vĩ mô", f"[{t_color}]{macro.get('tailwind_score')}/100[/{t_color}]", f"[{t_color}]{macro.get('sentiment')}[/{t_color}]")
        drivers = macro.get('macro_drivers', [''])
        m_table.add_row("Động lực chính", "Catalysts", f"{drivers[0] if drivers else 'N/A'}")
        console.print(m_table)

        sw = macro.get("sector_wave", {})
        if sw and sw.get("has_wave"):
            w_table = Table(title=f"🌊 SÓNG NGÀNH TÂM ĐIỂM: {sw.get('wave_name')}", header_style="bold blue")
            w_table.add_column("Hạng mục Sóng", style="cyan", width=24)
            w_table.add_column("Thông số", style="bold white", width=22)
            w_table.add_column("Chi tiết Động lực & Kỷ luật", style="white")

            h_score = sw.get('heat_score', 50)
            h_col = "red" if h_score >= 80 else ("green" if h_score >= 63 else ("yellow" if h_score >= 45 else "white"))
            role_col = "yellow" if "LEADER" in sw.get("role", "") else "cyan"

            w_table.add_row("Độ nhiệt & Pha sóng", f"[{h_col}]{h_score}/100[/{h_col}]", f"[{h_col}]{sw.get('phase')}[/{h_col}]")
            w_table.add_row(f"Vai trò của {symbol}", f"[{role_col}]{sw.get('role')}[/{role_col}]", f"Leader: {', '.join(sw.get('leaders', []))} | Runner: {', '.join(sw.get('runners', []))}")
            cats = sw.get("catalysts", [])
            w_table.add_row("Xúc tác kích hoạt", f"{len(cats)} Catalysts", f"{cats[0] if cats else 'N/A'}")
            w_table.add_row("Kỷ luật giao dịch", "Chiến lược", f"{sw.get('trading_rule', '')}")
            console.print(w_table)

    # Dòng tiền thật & Altman Z-Score & Piotroski
    cf = fa.get("cash_flow", {})
    if cf:
        cf_table = Table(title="🔬 BÓC TÁCH DÒNG TIỀN THẬT & ALTMAN Z''-SCORE (CASH FLOW FORENSIC)", header_style="bold green")
        cf_table.add_column("Chỉ tiêu", style="cyan")
        cf_table.add_column("Giá trị", style="bold white")
        cf_table.add_column("Kiểm định Chất lượng", style="white")

        q_color = "green" if cf.get("quality_grade") in ["A", "B"] else "red"
        z_color = "green" if cf.get("z_zone") == "SAFE" else ("yellow" if cf.get("z_zone") == "GREY" else "red")
        eq_ratio = cf.get('earnings_quality_ratio')
        eq_str = f"{float(eq_ratio):.2f}x" if isinstance(eq_ratio, (int, float)) and eq_ratio is not None else "N/A"
        z_val = cf.get('altman_z')
        z_str = f"{float(z_val):.2f}" if isinstance(z_val, (int, float)) and z_val is not None else "N/A"

        cf_table.add_row("Chất lượng Lợi nhuận", f"[{q_color}]Hạng {cf.get('quality_grade')}[/{q_color}]", f"[{q_color}]{cf.get('quality_verdict')}[/{q_color}]")
        cf_table.add_row("Tiền HĐKD thật (CFO TTM)", f"{cf.get('cfo_ttm', 0):,.0f} đ", f"Tỷ lệ CFO/LNST: {eq_str}")
        cf_table.add_row("Dòng tiền tự do (FCF)", f"{cf.get('fcf_ttm', 0):,.0f} đ", f"CapEx: {cf.get('capex_ttm', 0):,.0f} đ")
        cf_table.add_row("Altman Z''-Score & F-Score", f"[{z_color}]Z'': {z_str} | F: {fa.get('f_score', 0)}/9[/{z_color}]", f"[{z_color}]{cf.get('z_verdict')}[/{z_color}]")
        console.print(cf_table)

    # DuPont 3 Nhân tố & ROIC
    dupont = fa.get("dupont", {})
    roic_val = fa.get("roic") if fa.get("roic") is not None else fa.get("ratios", {}).get("roic")
    if dupont or roic_val is not None:
        d_table = Table(title="📊 HIỆU QUẢ SỬ DỤNG VỐN DUPONT & ROIC", header_style="bold magenta")
        d_table.add_column("Chỉ tiêu Hiệu quả Vốn", style="cyan")
        d_table.add_column("Giá trị", style="bold white")
        d_table.add_column("Bản chất & Đóng góp tăng trưởng", style="white")

        d_table.add_row(
            "Biên Lợi nhuận ròng (Net Margin)",
            f"{dupont.get('net_margin_pct', 0.0):.2f}%",
            "Khả năng sinh lời trên mỗi đồng doanh thu thu về"
        )
        d_table.add_row(
            "Vòng quay Tổng tài sản (Asset Turnover)",
            f"{dupont.get('asset_turnover', 0.0):.2f}x",
            "Hiệu suất sử dụng tài sản để tạo ra doanh thu"
        )
        d_table.add_row(
            "Đòn bẩy Tài chính (Equity Multiplier)",
            f"{dupont.get('equity_multiplier', 0.0):.2f}x",
            f"Tài sản / Vốn CSH (Nợ/VCSH: {fa.get('ratios', {}).get('debt_to_equity', 'N/A')}x)"
        )
        roe_val = dupont.get('roe_dupont_pct') or fa.get('ratios', {}).get('roe', 0.0)
        d_table.add_row(
            "ROE DuPont (Tổng hợp 3 nhân tố)",
            f"[bold green]{float(roe_val):.2f}%[/bold green]",
            f"Động lực chính: {dupont.get('main_driver', 'Cân bằng')}"
        )
        if roic_val is not None:
            r_num = float(roic_val.get('roic_pct', 0.0)) if isinstance(roic_val, dict) else float(roic_val)
            r_verdict = "Suất sinh lời vượt trội (>15%)" if r_num >= 15 else ("Tích cực (>10%)" if r_num >= 10 else "Trung bình")
            d_table.add_row(
                "ROIC (Suất sinh lời vốn đầu tư)",
                f"[bold cyan]{r_num:.2f}%[/bold cyan]",
                f"{r_verdict} (Đo lường năng lực sinh tiền thực tế trên vốn vay + vốn chủ)"
            )
        console.print(d_table)

    # Định giá Bội số Tài sản & Rủi ro Pha loãng
    asset_val = fa.get("asset_valuation", {})
    if asset_val:
        a_table = Table(title="💎 ĐỊNH GIÁ BỘI SỐ TÀI SẢN & RỦI RO PHA LOÃNG", header_style="bold cyan")
        a_table.add_column("Chỉ tiêu", style="cyan")
        a_table.add_column("Thông số", style="bold yellow")
        a_table.add_column("Đánh giá An toàn vốn", style="white")

        risk_color = "green" if asset_val.get("manipulation_risk_level", 1) <= 2 else ("yellow" if asset_val.get("manipulation_risk_level") == 3 else "red")
        a_disc = asset_val.get('asset_discount_pct')
        a_disc_str = f"{float(a_disc):+.1f}%" if isinstance(a_disc, (int, float)) and a_disc is not None else "N/A"
        illiquid_str = f"{float(asset_val.get('illiquid_ratio') or 0.0):.1f}%"
        cash_str = f"{float(asset_val.get('cash_ratio') or 0.0):.1f}%"
        
        a_table.add_row("Giá trị sổ sách (BVPS)", f"{asset_val.get('bvps', 0):,.0f} đ", "Giá trị tài sản ròng thuộc về mỗi cổ phiếu")
        a_table.add_row("Hệ số Định giá P/B", f"{asset_val.get('pb', 'N/A')}x", f"Chiết khấu tài sản: {a_disc_str}")
        a_table.add_row("Rủi ro Thao túng / Pha loãng", f"[{risk_color}]Cấp {asset_val.get('manipulation_risk_level')}/5[/{risk_color}]", f"[{risk_color}]{asset_val.get('manipulation_verdict')}[/{risk_color}]")
        a_table.add_row("Chất lượng tài sản", f"{asset_val.get('asset_quality_verdict')}", f"Đọng vốn: {illiquid_str} | Tiền mặt: {cash_str}")
        
        console.print(a_table)

    # Bảng Bóc tách Mô hình kinh doanh cốt lõi (Segments)
    _render_segments_table(symbol, fa.get("segments", {}))

    # Bảng Quản trị Doanh nghiệp & Mạng lưới Công ty con
    _render_governance_table(fa.get("governance", {}))

    # Bảng Bóc tách Tạo Lập, Tay To Giữ Hàng & Radar Tin Tức Ban Lãnh Đạo
    _render_insider_whale_table(symbol, insider_whale)

    # PHÂN HỆ 5: TA DEEP-DIVE 360°

    ind = ta.get("indicators", {})
    adv_ta = ta.get("advanced_ta", {})
    vsa = ta.get("vsa", {})

    ta_table = Table(title="📈 PHÂN HỆ 5: BÓC TÁCH KỸ THUẬT & DÒNG TIỀN (TA DEEP-DIVE)", header_style="bold cyan")
    ta_table.add_column("Chỉ báo Kỹ thuật", style="cyan")
    ta_table.add_column("Giá trị", style="bold white")
    ta_table.add_column("Trạng thái & Tín hiệu", style="white")

    ema20 = float(ind.get('ema20', current_price))
    ema50 = float(ind.get('ema50', current_price))
    sma200 = float(ind.get('sma200', current_price))
    trend_desc = "Uptrend mạnh (Giá > EMA20 > EMA50)" if current_price >= ema20 >= ema50 else ("Downtrend / Chờ tích lũy" if current_price < ema50 else "Hồi phục / Giằng co")

    ta_table.add_row("Giá khớp & EMA20 / 50", f"{current_price:,.0f} đ (EMA20: {ema20:,.0f})", f"{trend_desc} (vs EMA20: {(current_price - ema20)/ema20*100:+.1f}%)")
    ta_table.add_row("Đường dài hạn SMA200", f"{sma200:,.0f} đ", "Xu thế năm: " + ("Trên SMA200" if current_price >= sma200 else "Dưới SMA200"))
    ta_table.add_row("Khung giá 52 Tuần (Range)", f"{float(ind.get('low_52w', current_price)):,.0f} - {float(ind.get('high_52w', current_price)):,.0f} đ", f"Khoảng cách đỉnh 52W: {(current_price - float(ind.get('high_52w', current_price))) / float(ind.get('high_52w', 1)) * 100:+.1f}%")
    
    rs_val = int(ind.get('rs_rating', 50))
    rs_col = "green" if rs_val >= 80 else ("yellow" if rs_val >= 60 else "white")
    ta_table.add_row("O'Neil RS Rating", f"[{rs_col}]{rs_val}/99 điểm[/{rs_col}]", f"[{rs_col}]{'Top 20% dẫn dắt thị trường' if rs_val >= 80 else 'Xung lực giá tích cực / trung bình'}[/{rs_col}]")

    rsi_val = float(ind.get('rsi14', 50))
    rsi_col = "red" if rsi_val >= 70 else ("green" if rsi_val <= 35 else "white")
    ta_table.add_row("Động lượng RSI 14", f"[{rsi_col}]{rsi_val:.1f}[/{rsi_col}]", "Quá mua" if rsi_val >= 70 else ("Quá bán" if rsi_val <= 35 else "Trung tính lành mạnh"))
    ta_table.add_row("Khối lượng vs MA20", f"{float(ind.get('vol_ratio', 1.0)):.2f}x MA20", f"Vol: {quote.get('volume', 0):,.0f} CP ({'Bùng nổ Vol' if float(ind.get('vol_ratio', 1.0)) >= 1.5 else 'Thanh khoản bình thường'})")
    ta_table.add_row("Mô hình VCP & Wyckoff", f"{adv_ta.get('pattern_name', 'Tích lũy')}", f"Pha VSA: {vsa.get('phase', 'Tích lũy')} | Nến: {adv_ta.get('vsa_signal', 'Bình thường')}")
    console.print(ta_table)

    # PHÂN HỆ 6: TIMING MATRIX & PRICE LADDER
    if timing and isinstance(timing, dict):
        tm_table = Table(title="⚡ PHÂN HỆ 6: ĐỘNG CƠ THỜI ĐIỂM (TIMING MATRIX & PRICE LADDER)", header_style="bold yellow")
        tm_table.add_column("Hạng mục Timing", style="cyan")
        tm_table.add_column("Thông số & Xác suất", style="bold white")
        tm_table.add_column("Mốc kích hoạt & Kỷ luật", style="white")

        up_prob = timing.get("up_probability_pct", 60)
        up_col = "green" if up_prob >= 65 else "yellow"
        tm_table.add_row("Dự báo Bùng nổ (Tăng)", f"[{up_col}]Xác suất {up_prob}% ({timing.get('timing_window_days', '3-7')} phiên)[/{up_col}]", f"Pivot nổ: {timing.get('pivot_price', current_price * 1.03):,.0f} đ kèm Vol > {timing.get('pivot_volume_ratio', 1.5):.1f}x MA20")
        
        down_prob = timing.get("down_probability_pct", 25)
        down_col = "red" if down_prob >= 40 else "green"
        tm_table.add_row("Rủi ro Điều chỉnh (Sập)", f"[{down_col}]Xác suất {down_prob}%[/{down_col}]", f"Mốc vi phạm gãy: {timing.get('breakdown_price', current_price * 0.95):,.0f} đ (Bán hạ tỷ trọng)")
        tm_table.add_row("Setup Quality Score", f"{timing.get('setup_quality_score', 70)}/100 điểm", f"Độ hoàn thiện mô hình & Dòng tiền hỗ trợ")
        console.print(tm_table)

    # Price Ladder Gauge
    pivot_p = float(timing.get("pivot_price", current_price * 1.03)) if timing else current_price * 1.03
    fail_p = float(timing.get("breakdown_price", current_price * 0.95)) if timing else current_price * 0.95
    ladder_table = Table(title="📐 THƯỚC ĐO KÍCH HOẠT GIÁ (PRICE LADDER GAUGE)", header_style="bold magenta")
    ladder_table.add_column("Mốc Giá Kích Hoạt", style="cyan")
    ladder_table.add_column("Mức Giá (VND)", style="bold white", justify="right")
    ladder_table.add_column("Khoảng cách (%)", style="bold yellow", justify="center")
    ladder_table.add_column("Hành động tương ứng", style="white")

    ladder_table.add_row("Mục tiêu chốt lời 2 (TP2)", f"{trade.get('take_profit_2', 0):,.0f} đ", f"+{trade.get('take_profit_2_pct', 0)}%", "Chốt lời từng phần, nâng chặn lãi")
    ladder_table.add_row("Mục tiêu chốt lời 1 (TP1)", f"{trade.get('take_profit_1', 0):,.0f} đ", f"+{trade.get('take_profit_1_pct', 0)}%", "Chốt lời 1/2 vị thế lướt sóng")
    ladder_table.add_row("Điểm nổ Pivot kích hoạt", f"{pivot_p:,.0f} đ", f"{((pivot_p - current_price) / current_price * 100):+.1f}%", "Gia tăng tỷ trọng khi nổ Vol xác nhận")
    ladder_table.add_row("THỊ GIÁ HIỆN TẠI", f"{current_price:,.0f} đ", "0.0%", "Mức giá tham chiếu khớp lệnh phiên")
    ladder_table.add_row("Ngưỡng gãy sóng (Failure)", f"{fail_p:,.0f} đ", f"{((fail_p - current_price) / current_price * 100):+.1f}%", "Kịch bản tăng mất hiệu lực")
    ladder_table.add_row("Cắt lỗ kỷ luật (Stop Loss)", f"{trade.get('stop_loss', 0):,.0f} đ", f"-{trade.get('stop_loss_pct', 0)}%", "Kích hoạt bán hạ tỷ trọng bảo toàn vốn")
    console.print(ladder_table)

    # PHÂN HỆ 7: DỰ PHÓNG KỊCH BẢN & ĐIỀU KIỆN MẤT HIỆU LỰC
    console.print(Panel(
        f"[bold white]1. Kịch bản Cơ sở (Base - 55%):[/bold white] Tích lũy trong biên độ [cyan]{trade.get('swing_buy_zone', trade.get('buy_zone'))}[/cyan], chờ xác nhận mốc Pivot [bold]{pivot_p:,.0f} đ[/bold].\n"
        f"[bold green]2. Kịch bản Tích cực (Bull - 25%):[/bold green] Vượt dứt khoát Pivot [bold]{pivot_p:,.0f} đ[/bold] kèm Vol > 1.5x MA20 -> Hướng tới TP1 [bold]{trade.get('take_profit_1', 0):,.0f} đ[/bold].\n"
        f"[bold red]3. Kịch bản Tiêu cực (Bear - 20%):[/bold red] Thủng ngưỡng [bold]{fail_p:,.0f} đ[/bold] -> Kích hoạt kỷ luật cắt lỗ tại [bold]{trade.get('stop_loss', 0):,.0f} đ[/bold].\n\n"
        f"[bold yellow]⚠️ Điều kiện Mất hiệu lực (Invalidation Triggers):[/bold yellow]\n"
        f"• Thủng hỗ trợ {fail_p:,.0f} đ với khối lượng bán đột biến > 1.3x MA20.\n"
        f"• BCTC quý tới có dòng tiền CFO âm nặng liên tiếp hoặc Nợ vay tăng vọt > 2.0x Vốn CSH.\n"
        f"• Xuất hiện biến cố lãnh đạo bán chui hoặc điều tra sai phạm.",
        title="[bold yellow]🔮 PHÂN HỆ 7: DỰ PHÓNG KỊCH BẢN & ĐIỀU KIỆN MẤT HIỆU LỰC[/bold yellow]",
        border_style="yellow"
    ))


def _render_terminal_fa(symbol, quote, fa):
    """Giao diện chỉ hiển thị Phân tích cơ bản (FA)"""
    fin = fa.get("ratios", {})
    asset_val = fa.get("asset_valuation", {})
    seg_data = fa.get("segments", {})
    dupont = fa.get("dupont", {})
    roic_data = fa.get("roic", {})

    console.print(f"\n[bold yellow]🏛️ CHUYÊN SÂU CƠ BẢN DOANH NGHIỆP: {symbol}[/bold yellow]")
    
    t = Table(show_header=True, header_style="bold cyan")
    t.add_column("Chỉ tiêu Cơ bản")
    t.add_column("Giá trị", justify="right")
    
    t.add_row("Piotroski F-Score", f"{fa.get('f_score')}/9")
    t.add_row("P/E Ratio", f"{fin.get('pe')}x" if fin.get('pe') else "N/A")
    t.add_row("P/B Ratio", f"{asset_val.get('pb', fin.get('pb'))}x" if asset_val.get('pb', fin.get('pb')) else "N/A")
    t.add_row("Giá trị sổ sách (BVPS)", f"{asset_val.get('bvps', 0):,.0f} đ" if asset_val.get('bvps') else "N/A")
    t.add_row("ROE (%)", f"{fin.get('roe')}%" if fin.get('roe') else "N/A")
    if dupont:
        t.add_row("DuPont 3 Nhân tố", f"Margin: {dupont.get('net_margin_pct', 0):.1f}% | Vòng quay: {dupont.get('asset_turnover', 0):.2f}x | Đòn bẩy: {dupont.get('equity_multiplier', 0):.2f}x")
    if roic_data:
        t.add_row("ROIC (%)", f"{roic_data.get('roic_pct', 0):.2f}% ({roic_data.get('verdict', 'N/A')})")
    t.add_row("Biên Lợi nhuận ròng", f"{fin.get('net_margin')}%" if fin.get('net_margin') else "N/A")
    t.add_row("Nợ vay / Vốn CSH", f"{fin.get('debt_to_equity')}x" if fin.get('debt_to_equity') else "N/A")
    t.add_row("Bội số Định giá & Rủi ro Pha loãng", f"{asset_val.get('manipulation_verdict', 'N/A')}")
    
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
    
    close_p = float(ind.get('close', 0))
    t.add_row("Giá hiện tại", f"{close_p:,.0f}")
    t.add_row("EMA 20 (Ngắn hạn)", f"{float(ind.get('ema20', 0)):,.0f}")
    t.add_row("EMA 50 (Trung hạn)", f"{float(ind.get('ema50', 0)):,.0f}")
    t.add_row("Khung giá 52 Tuần", f"{float(ind.get('low_52w', close_p)):,.0f} - {float(ind.get('high_52w', close_p)):,.0f}")
    t.add_row("O'Neil RS Rating", f"{int(ind.get('rs_rating', 50))}/99 điểm")
    t.add_row("Volume Ratio (so MA20)", f"{float(ind.get('vol_ratio', 1.0)):.2f}x")
    t.add_row("RSI 14", f"{float(ind.get('rsi14', 50)):.1f}")
    t.add_row("Vùng hỗ trợ", f"{float(ind.get('sup_20d', 0)):,.0f}")
    
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


def render_macro_terminal():
    """In bảng Vĩ mô và Hàng hóa quốc tế trên Terminal"""
    macro_data = get_global_macro_and_commodities()
    comm = macro_data.get("global_commodities", {})
    vn = macro_data.get("vietnam_macro", {})

    table = Table(title="📡 MA TRẬN VĨ MÔ QUỐC TẾ & HÀNG HÓA THẾ GIỚI", header_style="bold cyan")
    table.add_column("Hàng hóa / Chỉ số", style="bold white", width=30)
    table.add_column("Giá trị", justify="right", style="yellow", width=16)
    table.add_column("Biến động", justify="center", width=12)
    table.add_column("Xu hướng & Tác động", style="dim", width=42)

    for k, v in comm.items():
        chg = v.get("change_pct", 0)
        chg_str = f"+{chg}%" if chg > 0 else f"{chg}%"
        chg_col = "green" if chg > 0 else ("red" if chg < 0 else "white")
        val = f"{v.get('value'):,} {v.get('unit')}" if isinstance(v.get('value'), (int, float)) and v.get('value') > 1000 else f"{v.get('value')} {v.get('unit')}"
        table.add_row(
            v.get("name", k).split("(")[0].strip(),
            val,
            f"[{chg_col}]{chg_str}[/{chg_col}]",
            v.get("trend", "")[:40]
        )

    console.print(table)


def render_sector_wave_terminal():
    """Hiển thị Radar 10 Sóng Ngành lớn của TTCK Việt Nam (2020 - 2026+) trên Terminal"""
    waves = get_sector_waves_overview()

    table = Table(title="🌊 RADAR 10 SÓNG NGÀNH & ĐỘNG LỰC LUÂN CHUYỂN DÒNG TIỀN (2020 - 2026+)", header_style="bold cyan")
    table.add_column("#", justify="center", style="bold yellow", width=4)
    table.add_column("Sóng Ngành & Chủ Đề Vĩ Mô", style="bold white", width=34)
    table.add_column("Độ Nhiệt", justify="center", width=14)
    table.add_column("Pha Chu Kỳ Sóng", width=24)
    table.add_column("👑 Leaders / 🚀 Runners", style="cyan", width=30)
    table.add_column("Chất Xúc Tác Kích Hoạt (Catalysts)", style="dim", width=42)

    for idx, w in enumerate(waves, 1):
        heat = w.get("heat_score", 50)
        if heat >= 80:
            heat_str = f"[bold red]{heat}/100 🔥[/bold red]"
        elif heat >= 63:
            heat_str = f"[bold green]{heat}/100 🟢[/bold green]"
        elif heat >= 45:
            heat_str = f"[bold yellow]{heat}/100 🟡[/bold yellow]"
        else:
            heat_str = f"[dim white]{heat}/100 ⚪[/dim white]"

        phase_str = w.get("phase", "").split("(")[0].strip()
        leaders = ", ".join(w.get("leaders", [])[:3])
        runners = ", ".join(w.get("runners", [])[:3])
        ticker_str = f"[bold yellow]{leaders}[/bold yellow] | [cyan]{runners}[/cyan]"
        cats = w.get("catalysts", [])
        cat_str = cats[0] if cats else ""
        if len(cats) > 1:
            cat_str += f" (+{len(cats)-1} catalysts)"

        table.add_row(
            str(idx),
            w.get("wave_name", ""),
            heat_str,
            phase_str,
            ticker_str,
            cat_str[:55]
        )

    console.print(table)
    console.print(Panel(
        "[bold green]💡 KỶ LUẬT ĐÁNH THEO SÓNG NGÀNH (SECTOR ROTATION DISCIPLINE):[/bold green]\n"
        "• [bold yellow]Pha 1 (Tích lũy âm thầm):[/bold yellow] Smart Money gom hàng cạn kiệt Vol. Thăm dò 20-30% vị thế ở nền.\n"
        "• [bold green]Pha 2 (Bùng nổ & Đẩy sóng):[/bold green] Vùng đánh sóng NGON NHẤT! Gia tăng đủ tỷ trọng vào [bold yellow]Cổ phiếu Leader[/bold yellow] khi nổ Pivot.\n"
        "• [bold red]Pha 3 (Quá nhiệt / Phân phối):[/bold red] Báo chí ca ngợi, đám đông FOMO. CHỐT LỜI từng phần, nâng chặn lãi, TUYỆT ĐỐI KHÔNG MUA ĐUỔI.\n"
        "• [dim]Pha 4 (Hạ nhiệt / Thoái trào):[/dim] Dòng tiền rút sang nhóm ngành mới. ĐỨNG NGOÀI bảo toàn lợi nhuận.",
        title="🧭 NGUYÊN TẮC LUÂN CHUYỂN DÒNG TIỀN",
        border_style="cyan"
    ))


def list_experts():
    """Hiển thị danh mục 11 chuyên gia Hội đồng Tham mưu (prompts.chat)."""
    from ai.prompt_library import PromptLibrary
    personas = PromptLibrary.list_personas()
    table = Table(title="🏛️ DANH MỤC 11 CHUYÊN GIA HỘI ĐỒNG THAM MƯU (PROMPTS.CHAT)", header_style="bold cyan")
    table.add_column("Mã Alias (--expert)", style="bold yellow", width=18)
    table.add_column("Huy hiệu & Tên chuyên gia", style="cyan", width=30)
    table.add_column("Trường phái & Danh xưng", style="white", width=44)
    table.add_column("Nhóm", style="green", width=12)
    for p in personas:
        table.add_row(
            p["id"],
            f"{p['badge']} {p['name']}",
            p["title"],
            "Cốt lõi" if p["category"] == "core" else "Mở rộng"
        )
    console.print(table)


def ask_council(symbol: str, question: Optional[str] = None, expert_id: str = "all"):
    """
    Hỏi-đáp trực tiếp với 11 Chuyên gia Hội đồng Tham mưu (prompts.chat).
    """
    symbol = symbol.upper().strip()
    if not question:
        question = "Đánh giá toàn diện rủi ro, con hào kinh tế và cơ hội giải ngân vị thế tại vùng giá hiện tại?"

    console.print(f"\n[bold cyan]⏳ Đang tập hợp dữ liệu và kết nối Hội đồng Tham mưu cho mã [yellow]{symbol}[/yellow]...[/bold cyan]")
    from ai.interactive_advisor import CouncilAdvisor
    from core.stock_service import analyze_ticker_full

    context = {}
    try:
        res = analyze_ticker_full(symbol, save_report=False, send_alert=False)
        if "error" not in res:
            q = res.get("quote", {})
            fa = res.get("fa_result", {})
            ta = res.get("ta_result", {})
            ts = res.get("trade_setup", {})
            ratios = fa.get("ratios", {})
            p = float(q.get("price", 0))
            context = {
                "price": p,
                "fair_price": float(fa.get("fair_value", p)),
                "bvps": float(fa.get("bvps", 0)),
                "pb": float(ratios.get("pb", 1.0)),
                "stop_loss": float(ts.get("stop_loss", p * 0.93)),
                "stop_loss_pct": float(ts.get("stop_loss_pct", 7.0)),
                "take_profit_1": float(ts.get("take_profit_1", p * 1.12)),
                "take_profit_1_pct": float(ts.get("take_profit_1_pct", 12.0)),
                "take_profit_2": float(ts.get("take_profit_2", p * 1.25)),
                "take_profit_2_pct": float(ts.get("take_profit_2_pct", 25.0)),
                "trigger_pivot": float(ts.get("buy_zone_high", p * 1.03)),
                "risk_reward_ratio": float(ts.get("risk_reward_ratio", 2.0)),
                "max_position_size_pct": float(ts.get("position_size_pct", 10.0)),
                "foreign_net_vol": float(q.get("foreign_net_vol", 0)),
                "active_buy_pct": float(q.get("active_buy_pct", 50.0)),
                "sector": fa.get("sector_name", "Doanh nghiệp niêm yết"),
                "cfo_human": fa.get("cfo_quality", "Dương"),
                "fcf_human": fa.get("fcf_quality", "Dương"),
                "timing_verdict": ts.get("action", "Theo dõi")
            }
    except Exception:
        pass

    advisor = CouncilAdvisor()
    resp = advisor.answer_question(symbol=symbol, question=question, expert_id=expert_id, context=context)

    expert_name = resp.get("expert", "Hội đồng Tham mưu")
    answer = resp.get("answer", "")
    source = resp.get("source", "offline")

    console.print()
    console.print(Panel(
        f"[bold yellow]❓ Câu hỏi:[/bold yellow] {question}\n\n"
        f"[bold green]💬 Trả lời từ {expert_name}:[/bold green]\n\n"
        f"{answer}\n\n"
        f"[dim]Phương thức thẩm định: {source} | Dữ liệu mã: {symbol}[/dim]",
        title=f"🏛️ HỘI ĐỒNG THAM MƯU ĐẦU TƯ — {expert_name.upper()}",
        border_style="cyan"
    ))


def main():
    parser = argparse.ArgumentParser(
        description="Vietnam Stock Market Analyzer - Hệ thống Phân tích Chứng khoán Cục bộ Đa AI",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "ticker_pos",
        nargs="?",
        default=None,
        help="Mã cổ phiếu phân tích nhanh (ví dụ: python main.py HPG)"
    )
    parser.add_argument(
        "--mode", "-m",
        choices=["dashboard", "analyze", "scan", "macro", "wave", "fa", "ta", "track", "ask"],
        default=None,
        help="Chế độ hoạt động:\n  dashboard: Cập nhật & Mở Dashboard Offline trên Microsoft Edge\n  analyze: Soi sâu 1 mã (FA + TA + Timing Engine)\n  scan: Quét toàn bộ TTCK tìm top nổ vol\n  macro: Xem ma trận Vĩ mô & Hàng hóa thế giới\n  wave: Radar 10 Sóng Ngành & Động lực Luân chuyển Dòng tiền (2020-2026+)\n  fa: Chỉ phân tích Cơ bản (BCTC)\n  ta: Chỉ phân tích Kỹ thuật (Chart)\n  track: PDCA - Đánh giá hiệu suất khuyến nghị quá khứ\n  ask: Hỏi-đáp trực tiếp với 11 chuyên gia Hội đồng Tham mưu (prompts.chat)"
    )
    parser.add_argument(
        "--ticker", "-t",
        default=None,
        help="Mã cổ phiếu cần phân tích (ví dụ: HPG, PVD, GVR, FPT...)"
    )
    parser.add_argument(
        "--question", "-q",
        default=None,
        help="Câu hỏi dành cho chuyên gia Hội đồng (khi dùng --mode ask)"
    )
    parser.add_argument(
        "--expert", "-e",
        default="all",
        help="Chuyên gia trả lời (buffett, lynch, oneil, vsa, marks, cro, pe, audit, redteam, stresstest, unit... hoặc 'all')"
    )
    parser.add_argument(
        "--list-experts",
        action="store_true",
        help="Hiển thị danh mục 11 chuyên gia và vai trò thẩm định"
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
    parser.add_argument(
        "--no-alert",
        action="store_true",
        help="Tắt gửi thông báo qua Telegram"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Không tự động mở trình duyệt sau khi tạo Dashboard"
    )

    args = parser.parse_args()

    if args.list_experts:
        list_experts()
        return

    ticker = (args.ticker_pos or args.ticker or "HPG").upper().strip()
    send_alert = not args.no_alert

    if args.mode:
        mode = args.mode
    elif args.question or args.expert != "all":
        mode = "ask"
    elif args.ticker_pos or args.ticker:
        mode = "analyze"
    else:
        mode = "dashboard"

    if mode == "dashboard":
        console.print("[bold cyan]⏳ Đang cập nhật dữ liệu toàn diện và tạo file DASHBOARD.html...[/bold cyan]")
        p = generate_dashboard_html(auto_open=not args.no_browser)
        console.print(f"[bold green]🌐 Đã tạo thành công Dashboard tại:[/bold green] [underline cyan]{p}[/underline cyan]")
    elif mode == "macro":
        render_macro_terminal()
    elif mode == "wave":
        render_sector_wave_terminal()
    elif mode == "scan":
        run_market_screener(top_n=args.top, sector_filter=args.sector)
        if send_alert:
            from alerts.telegram_bot import send_telegram_radar
            send_telegram_radar(top_n=args.top, sector_filter=args.sector)
    elif mode == "track":
        from core.performance_tracker import evaluate_all_recommendations, render_performance_terminal_dashboard
        perf_data = evaluate_all_recommendations()
        render_performance_terminal_dashboard(perf_data)
    elif mode == "ask":
        ask_council(symbol=ticker, question=args.question, expert_id=args.expert)
    elif mode == "fa":
        analyze_single_ticker(symbol=ticker, mode="fa", send_alert=send_alert)
    elif mode == "ta":
        analyze_single_ticker(symbol=ticker, mode="ta", send_alert=send_alert)
    else:
        analyze_single_ticker(symbol=ticker, mode="full", send_alert=send_alert)


if __name__ == "__main__":
    main()


