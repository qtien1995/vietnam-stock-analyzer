"""
Module Nghiệm thu Hiệu suất Khuyến nghị & Vòng lặp PDCA (Performance Tracker)
Đảm nhiệm 2 mắt xích then chốt còn thiếu trong chu trình Quản lý Chất lượng:
- CHECK (Kiểm định): Đối chiếu khuyến nghị trong quá khứ với biến động nến EOD thực tế.
  Đánh giá chạm mốc: HIT_TP1 (+12%), HIT_TP2 (+20%), HIT_SL (-7%), HOLDING (Đang mở), EXPIRED.
- ACT (Tối ưu hóa): Thống kê Win Rate (%), Tỷ lệ Lãi/Lỗ thực tế (Realized Profit Factor),
  từ đó đề xuất tinh chỉnh ngưỡng kỷ luật và lọc bẫy giá trị.
"""

import sqlite3
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from config import PROJECT_ROOT
from core.data_loader import get_historical_ohlcv
from core.db_manager import DB_PATH, init_db

console = Console()


def evaluate_all_recommendations() -> Dict[str, Any]:
    """
    Quét toàn bộ bảng recommendations trong SQLite,
    lấy nến lịch sử thực tế từ ngày khuyến nghị đến hiện tại và đánh giá kết quả.
    Cập nhật dữ liệu vào bảng performance_tracking.
    """
    init_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT 
            r.id, r.symbol, r.trading_date, r.action, r.current_price,
            r.buy_zone, r.stop_loss, r.tp_short, r.tp_mid, r.tp_long,
            r.consensus_score,
            p.status, p.pnl_pct, p.days_held, p.max_reached_price, p.min_reached_price
        FROM recommendations r
        LEFT JOIN performance_tracking p ON r.id = p.rec_id
        ORDER BY r.id DESC
    """)
    rows = cursor.fetchall()

    if not rows:
        conn.close()
        return {
            "total": 0,
            "wins": 0,
            "losses": 0,
            "holding": 0,
            "win_rate_pct": 0.0,
            "profit_factor": 0.0,
            "avg_gain_pct": 0.0,
            "avg_loss_pct": 0.0,
            "records": [],
            "action_breakdown": {},
            "insights": ["Chưa có dữ liệu khuyến nghị nào trong cơ sở dữ liệu để nghiệm thu."]
        }

    records = []
    now = datetime.now()

    for row in rows:
        rec_id = row["id"]
        sym = row["symbol"]
        rec_date = row["trading_date"]
        action = row["action"] or "QUAN SÁT"
        entry_price = float(row["current_price"] or 0.0)
        stop_loss = float(row["stop_loss"] or 0.0)
        tp1 = float(row["tp_short"] or 0.0)
        tp2 = float(row["tp_mid"] or 0.0)
        consensus_score = int(row["consensus_score"] or 0)

        if entry_price <= 0:
            continue

        # Nạp nến lịch sử để kiểm tra đường đi của giá
        df = get_historical_ohlcv(sym, days=120)
        status = "OPEN"
        pnl_pct = 0.0
        days_held = 0
        max_reached = entry_price
        min_reached = entry_price
        hit_tp1_session = False

        if not df.empty and "time" in df.columns:
            df["time_str"] = df["time"].dt.strftime("%Y-%m-%d")
            # Lọc các phiên xảy ra tại hoặc sau ngày khuyến nghị
            sub_df = df[df["time_str"] >= rec_date].copy().sort_values("time").reset_index(drop=True)
            
            if len(sub_df) > 1:
                days_held = len(sub_df) - 1
                # Duyệt qua từng phiên sau ngày khuyến nghị
                for _, s_row in sub_df.iloc[1:].iterrows():
                    h = float(s_row["high"])
                    l = float(s_row["low"])
                    c = float(s_row["close"])

                    max_reached = max(max_reached, h)
                    min_reached = min(min_reached, l)

                    # Kiểm tra chạm mốc kỷ luật
                    if tp2 > 0 and h >= tp2:
                        status = "HIT_TP2"
                        pnl_pct = round(((tp2 - entry_price) / entry_price) * 100, 2)
                        break
                    elif stop_loss > 0 and l <= stop_loss:
                        status = "HIT_SL"
                        pnl_pct = round(((stop_loss - entry_price) / entry_price) * 100, 2)
                        break
                    elif tp1 > 0 and h >= tp1:
                        hit_tp1_session = True

                # Nếu hết chu kỳ nến mà chưa chạm TP2 hoặc SL
                if status not in ["HIT_TP2", "HIT_SL"]:
                    latest_close = float(sub_df.iloc[-1]["close"])
                    if hit_tp1_session:
                        status = "HIT_TP1"
                        pnl_pct = round(((tp1 - entry_price) / entry_price) * 100, 2)
                    elif days_held >= 45:
                        status = "EXPIRED"
                        pnl_pct = round(((latest_close - entry_price) / entry_price) * 100, 2)
                    else:
                        status = "HOLDING"
                        pnl_pct = round(((latest_close - entry_price) / entry_price) * 100, 2)

        # Cập nhật kết quả vào database
        cursor.execute("""
            INSERT OR REPLACE INTO performance_tracking
            (rec_id, status, max_reached_price, min_reached_price, days_held, pnl_pct, last_checked)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (rec_id, status, max_reached, min_reached, days_held, pnl_pct))

        records.append({
            "rec_id": rec_id,
            "symbol": sym,
            "trading_date": rec_date,
            "action": action,
            "entry_price": entry_price,
            "stop_loss": stop_loss,
            "tp1": tp1,
            "tp2": tp2,
            "consensus_score": consensus_score,
            "status": status,
            "pnl_pct": pnl_pct,
            "days_held": days_held,
            "max_reached": max_reached,
            "min_reached": min_reached
        })

    conn.commit()
    conn.close()

    # Tính toán thống kê hiệu suất
    total = len(records)
    wins = len([r for r in records if r["status"] in ["HIT_TP1", "HIT_TP2"] or (r["status"] in ["HOLDING", "EXPIRED"] and r["pnl_pct"] > 0)])
    losses = len([r for r in records if r["status"] == "HIT_SL" or (r["status"] in ["HOLDING", "EXPIRED"] and r["pnl_pct"] < 0)])
    holding = len([r for r in records if r["status"] == "HOLDING"])

    gain_list = [r["pnl_pct"] for r in records if r["pnl_pct"] > 0]
    loss_list = [abs(r["pnl_pct"]) for r in records if r["pnl_pct"] < 0]

    avg_gain = round(sum(gain_list) / len(gain_list), 2) if gain_list else 0.0
    avg_loss = round(sum(loss_list) / len(loss_list), 2) if loss_list else 0.0

    total_gain_sum = sum(gain_list)
    total_loss_sum = sum(loss_list)
    profit_factor = round(total_gain_sum / total_loss_sum, 2) if total_loss_sum > 0 else (9.9 if total_gain_sum > 0 else 1.0)
    win_rate = round((wins / (wins + losses)) * 100, 1) if (wins + losses) > 0 else 0.0

    # Phân rã theo loại khuyến nghị
    action_breakdown = {}
    for act in ["MUA MẠNH", "MUA THĂM DÒ", "THEO DÕI", "BÁN / TRÁNH XA"]:
        act_recs = [r for r in records if act in r["action"]]
        if act_recs:
            act_wins = len([r for r in act_recs if r["pnl_pct"] > 0])
            act_total = len(act_recs)
            action_breakdown[act] = {
                "count": act_total,
                "wins": act_wins,
                "win_rate": round(act_wins / act_total * 100, 1) if act_total > 0 else 0.0,
                "avg_pnl": round(sum(r["pnl_pct"] for r in act_recs) / act_total, 2)
            }

    # Bóc tách bài học kinh nghiệm (Act phase of PDCA)
    insights = []
    if win_rate >= 65.0:
        insights.append(f"✅ Tỷ lệ thắng xuất sắc ({win_rate}%): Mô hình Hybrid FA & TA đang vận hành đồng thuận rất tốt.")
    elif win_rate >= 50.0:
        insights.append(f"⚠️ Tỷ lệ thắng trung bình ({win_rate}%): Cần siết chặt điều kiện nổ Volume và biên an toàn MoS.")
    else:
        insights.append(f"🚨 Tỷ lệ thắng thấp ({win_rate}%): Thị trường đang trong pha điều chỉnh hoặc các điểm breakout bị bull trap, cần tăng trọng số Quản trị rủi ro.")

    if profit_factor >= 2.0:
        insights.append(f"💎 Tỷ lệ Profit Factor đạt {profit_factor}x: Lợi nhuận từ các lệnh thắng vượt trội rủi ro cắt lỗ.")
    else:
        insights.append(f"⚠️ Profit Factor chỉ đạt {profit_factor}x: Khuyến nghị nâng tỷ lệ chốt lời TP1 lên +12% và kiên quyết cắt lỗ dưới -7%.")

    return {
        "total": total,
        "wins": wins,
        "losses": losses,
        "holding": holding,
        "win_rate_pct": win_rate,
        "profit_factor": profit_factor,
        "avg_gain_pct": avg_gain,
        "avg_loss_pct": avg_loss,
        "records": records,
        "action_breakdown": action_breakdown,
        "insights": insights
    }


def render_performance_terminal_dashboard(stats: Dict[str, Any]):
    """Hiển thị giao diện Bảng Tổng kết PDCA Performance Tracker trên Terminal."""
    total = stats["total"]
    if total == 0:
        console.print("[yellow]Chưa có dữ liệu khuyến nghị nào được lưu trong Database.[/yellow]")
        return

    win_rate = stats["win_rate_pct"]
    wr_color = "green" if win_rate >= 60 else ("yellow" if win_rate >= 45 else "red")
    pf_color = "green" if stats["profit_factor"] >= 2.0 else "yellow"

    console.print(Panel(
        f"[bold white]TỔNG KHUYẾN NGHỊ: [cyan]{total}[/cyan] mã | "
        f"LỆNH THẮNG: [green]{stats['wins']}[/green] | LỆNH THUA: [red]{stats['losses']}[/red] | ĐANG MỞ: [yellow]{stats['holding']}[/yellow][/bold white]\n"
        f"TỶ LỆ THẮNG (WIN RATE): [bold {wr_color}]{win_rate}%[/bold {wr_color}] | "
        f"PROFIT FACTOR: [bold {pf_color}]{stats['profit_factor']}x[/bold {pf_color}] | "
        f"LÃI TB: [green]+{stats['avg_gain_pct']}%[/green] | LỖ TB: [red]-{stats['avg_loss_pct']}%[/red]",
        title="[bold yellow]🎯 BÁO CÁO NGHIỆM THU HIỆU SUẤT KHUYẾN NGHỊ (PDCA PERFORMANCE TRACKER)[/bold yellow]",
        border_style="bright_blue"
    ))

    # Bảng chi tiết từng khuyến nghị
    t = Table(title="📋 NHẬT KÝ CHI TIẾT KHUYẾN NGHỊ & KẾT QUẢ THỰC TẾ", header_style="bold magenta")
    t.add_column("Mã CP", style="bold yellow")
    t.add_column("Ngày Khuyến nghị", style="cyan")
    t.add_column("Khuyến nghị", style="bold white")
    t.add_column("Giá vào", justify="right")
    t.add_column("Mục tiêu (TP1 | TP2)", justify="right")
    t.add_column("Cắt lỗ", justify="right")
    t.add_column("Trạng thái", style="bold")
    t.add_column("Lãi / Lỗ (% PnL)", justify="right")
    t.add_column("Số phiên", justify="right")

    for r in stats["records"][:15]:
        st = r["status"]
        if st in ["HIT_TP1", "HIT_TP2"]:
            st_str = f"[green]✅ {st}[/green]"
        elif st == "HIT_SL":
            st_str = f"[red]❌ {st}[/red]"
        elif st == "HOLDING":
            st_str = f"[yellow]⏳ {st}[/yellow]"
        else:
            st_str = f"[white]{st}[/white]"

        pnl = r["pnl_pct"]
        pnl_str = f"[green]+{pnl:.1f}%[/green]" if pnl > 0 else (f"[red]{pnl:.1f}%[/red]" if pnl < 0 else "0.0%")

        t.add_row(
            r["symbol"],
            r["trading_date"],
            r["action"].split()[0],
            f"{r['entry_price']:,.0f}",
            f"{r['tp1']:,.0f} | {r['tp2']:,.0f}",
            f"{r['stop_loss']:,.0f}",
            st_str,
            pnl_str,
            f"{r['days_held']}T"
        )

    console.print(t)

    # Hiển thị bài học kinh nghiệm (Act phase)
    if stats.get("insights"):
        console.print("\n[bold cyan]💡 BÀI HỌC KINH NGHIỆM & ĐỀ XUẤT TỐI ƯU HÓA (ACT PHASE):[/bold cyan]")
        for ins in stats["insights"]:
            console.print(f"  {ins}")
    console.print("\n")


def get_performance_telegram_summary(stats: Dict[str, Any]) -> str:
    """Định dạng báo cáo nghiệm thu PDCA để gửi qua Telegram Bot."""
    total = stats.get("total", 0)
    if total == 0:
        return "📊 *HIỆU SUẤT ĐẦU TƯ (PDCA TRACKER):*\nChưa có khuyến nghị nào được lưu trong Database."

    win_rate = stats["win_rate_pct"]
    pf = stats["profit_factor"]
    wr_icon = "🟢" if win_rate >= 60 else ("🟡" if win_rate >= 45 else "🔴")

    msg = (
        "📈 *BÁO CÁO NGHIỆM THU HIỆU SUẤT KHUYẾN NGHỊ (PDCA)*\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *Tổng số khuyến nghị:* `{total} mã`\n"
        f"{wr_icon} *Tỷ lệ thắng (Win Rate):* `{win_rate}%`\n"
        f"💎 *Tỷ lệ Profit Factor:* `{pf}x`\n"
        f"• Lệnh Thắng: `{stats['wins']}` | Lệnh Thua: `{stats['losses']}` | Đang chạy: `{stats['holding']}`\n"
        f"• Lãi trung bình: `+{stats['avg_gain_pct']}%` | Lỗ trung bình: `-{stats['avg_loss_pct']}%`\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "📋 *TOP 5 MÃ GẦN NHẤT:*\n"
    )

    for r in stats.get("records", [])[:5]:
        pnl = r["pnl_pct"]
        sign = "+" if pnl > 0 else ""
        icon = "✅" if "HIT_TP" in r["status"] else ("❌" if "HIT_SL" in r["status"] else "⏳")
        msg += f"• *{r['symbol']}* ({r['trading_date']}): {icon} `{r['status']}` ({sign}{pnl:.1f}%)\n"

    msg += "\n💡 *Góc nhìn Tối ưu (PDCA Act):*\n"
    for ins in stats.get("insights", [])[:2]:
        msg += f"• _{ins}_\n"

    return msg
