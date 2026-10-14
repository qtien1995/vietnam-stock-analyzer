# -*- coding: utf-8 -*-
import sqlite3
import pytest
from pathlib import Path
from core.db_manager import (
    init_db,
    save_stock_master,
    get_stock_master,
    save_eod_quote,
    save_recommendation,
    backup_database,
)


def test_init_and_stock_master():
    init_db()
    save_stock_master("TEST_SYM", "Công ty Cổ phần Thử nghiệm", "HOSE", "STEEL", "Thép", 7.0)
    master = get_stock_master("TEST_SYM")
    assert master is not None
    assert master["symbol"] == "TEST_SYM"
    assert master["exchange"] == "HOSE"


def test_backup_database(tmp_path):
    dest = tmp_path / "test_market_backup.db"
    backup_path = backup_database(destination=dest)
    assert backup_path.exists()
    assert backup_path.stat().st_size > 0

    # Kiểm tra tính toàn vẹn của file backup
    conn = sqlite3.connect(backup_path)
    cur = conn.cursor()
    cur.execute("PRAGMA integrity_check;")
    check = cur.fetchone()[0]
    conn.close()
    assert check == "ok"
