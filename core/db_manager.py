import sqlite3
import datetime
import os
from pathlib import Path

from config import PROJECT_ROOT

DB_PATH = PROJECT_ROOT / "data" / "market.db"


def init_db():
    """Khởi tạo cấu trúc Database nếu chưa tồn tại"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Bảng 0: Master Data Cổ phiếu (Sàn giao dịch, Tên công ty, Ngành nghề)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS stock_master (
            symbol TEXT PRIMARY KEY,
            company_name TEXT,
            exchange TEXT NOT NULL,       -- 'HOSE', 'HNX', 'UPCOM'
            sector_key TEXT,
            sector_name TEXT,
            price_limit_pct REAL DEFAULT 7.0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Bảng 1: Lưu giá đóng cửa hàng ngày
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eod_quotes (
            symbol TEXT,
            trading_date TEXT,
            exchange TEXT,
            open_price REAL,
            high_price REAL,
            low_price REAL,
            close_price REAL,
            volume REAL,
            foreign_net_vol REAL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (symbol, trading_date)
        )
    """)
    
    # Bổ sung cột exchange vào eod_quotes nếu bảng đã tồn tại trước đó
    try:
        cursor.execute("ALTER TABLE eod_quotes ADD COLUMN exchange TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Bảng 2: Lưu vết khuyến nghị của Hội đồng
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            trading_date TEXT,
            exchange TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            action TEXT,
            current_price REAL,
            buy_zone TEXT,
            stop_loss REAL,
            tp_short REAL,
            tp_mid REAL,
            tp_long REAL,
            consensus_score INTEGER
        )
    """)

    # Bổ sung cột exchange vào recommendations nếu bảng đã tồn tại trước đó
    try:
        cursor.execute("ALTER TABLE recommendations ADD COLUMN exchange TEXT")
    except sqlite3.OperationalError:
        pass
    
    # Bảng 3: Đánh giá hiệu suất khuyến nghị
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS performance_tracking (
            rec_id INTEGER PRIMARY KEY,
            status TEXT DEFAULT 'OPEN',
            max_reached_price REAL,
            min_reached_price REAL,
            days_held INTEGER DEFAULT 0,
            pnl_pct REAL DEFAULT 0,
            last_checked TIMESTAMP,
            FOREIGN KEY(rec_id) REFERENCES recommendations(id)
        )
    """)
    
    conn.commit()
    conn.close()


def save_stock_master(
    symbol: str,
    company_name: str,
    exchange: str,
    sector_key: str = "",
    sector_name: str = "",
    price_limit_pct: float = 7.0
):
    """Lưu hoặc cập nhật thông tin Master của cổ phiếu (Sàn, Tên, Ngành)."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    sym = symbol.upper().strip()
    ex = exchange.upper().strip()
    if not ex:
        ex = "HOSE"
    
    if price_limit_pct <= 0:
        if ex == "HNX":
            price_limit_pct = 10.0
        elif ex == "UPCOM":
            price_limit_pct = 15.0
        else:
            price_limit_pct = 7.0
            
    cursor.execute("""
        INSERT OR REPLACE INTO stock_master
        (symbol, company_name, exchange, sector_key, sector_name, price_limit_pct, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
    """, (sym, company_name, ex, sector_key, sector_name, price_limit_pct))
    
    conn.commit()
    conn.close()


def get_stock_master(symbol: str) -> dict:
    """Tra cứu Master Data của cổ phiếu từ DB."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    sym = symbol.upper().strip()
    cursor.execute("SELECT symbol, company_name, exchange, sector_key, sector_name, price_limit_pct FROM stock_master WHERE symbol = ?", (sym,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "symbol": row[0],
            "company_name": row[1] or sym,
            "exchange": row[2] or "HOSE",
            "sector_key": row[3] or "GENERAL",
            "sector_name": row[4] or "Sản xuất & Kinh doanh Tổng hợp",
            "price_limit_pct": float(row[5] or 7.0)
        }
    return {}


def save_eod_quote(quote: dict):
    """Lưu giá chốt phiên vào DB."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    trading_date = quote.get("trading_date", datetime.datetime.now().strftime("%Y-%m-%d"))
    exchange = quote.get("exchange", "").upper()
    
    cursor.execute("""
        INSERT OR REPLACE INTO eod_quotes 
        (symbol, trading_date, exchange, open_price, high_price, low_price, close_price, volume, foreign_net_vol)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        quote["symbol"],
        trading_date,
        exchange,
        quote.get("open", 0),
        quote.get("high", 0),
        quote.get("low", 0),
        quote.get("price", 0),
        quote.get("volume", 0),
        quote.get("foreign_net_vol", 0)
    ))
    
    conn.commit()
    conn.close()


def save_recommendation(trade_setup: dict, quote: dict) -> int:
    """Lưu khuyến nghị để theo dõi hiệu suất."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    trading_date = quote.get("trading_date", datetime.datetime.now().strftime("%Y-%m-%d"))
    exchange = quote.get("exchange") or trade_setup.get("exchange", "HOSE")
    
    cursor.execute("""
        INSERT INTO recommendations 
        (symbol, trading_date, exchange, action, current_price, buy_zone, stop_loss, tp_short, tp_mid, tp_long, consensus_score)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        quote["symbol"],
        trading_date,
        str(exchange).upper(),
        trade_setup.get("action", ""),
        trade_setup.get("current_price", 0),
        trade_setup.get("buy_zone", ""),
        trade_setup.get("stop_loss", 0),
        trade_setup.get("take_profit_1", 0),
        trade_setup.get("take_profit_2", 0),
        trade_setup.get("take_profit_3", 0),
        trade_setup.get("consensus_score", 0)
    ))
    
    rec_id = cursor.lastrowid
    
    # Tạo bản ghi performance tracking luôn
    cursor.execute("""
        INSERT INTO performance_tracking (rec_id, status, max_reached_price, min_reached_price)
        VALUES (?, 'OPEN', ?, ?)
    """, (rec_id, trade_setup.get("current_price", 0), trade_setup.get("current_price", 0)))
    
    conn.commit()
    conn.close()
    return rec_id
