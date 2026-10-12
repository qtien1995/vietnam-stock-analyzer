# QUY TRÌNH PHỤC HỒI & HOÀN NGUYÊN HỆ THỐNG (ROLLBACK & RECOVERY GUIDE)

Tài liệu này cung cấp các hướng dẫn chi tiết từng bước để hoàn nguyên hệ thống về trạng thái ban đầu nếu phát sinh sự cố ngoài ý muốn.

---

## 1. Điểm Phục Hồi Đã Được Thiết Lập (Recovery Baseline Points)

Trước khi tiến hành bất kỳ thay đổi nào, hệ thống đã tạo 2 điểm chốt an toàn độc lập:

1. **Nhánh Git Cách ly:**
   - Base branch: `main` (commit SHA: `17b76a2`)
   - Working branch: `audit-rebuild`
2. **Bản Sao Lưu Cơ Sở Dữ Liệu SQLite Được Xác Thực:**
   - File gốc: `data/market.db`
   - File sao lưu: `data/market_backup_20261012_174222.db`
   - Dung lượng: ~108 KB, 5 bảng nguyên vẹn (`eod_quotes`, `financial_ratios`, `market_screener`, `recommendations`, `system_logs`).

---

## 2. Kịch bản 1: Hoàn nguyên Cơ sở Dữ liệu (`data/market.db`)

Nếu cơ sở dữ liệu gặp lỗi schema hoặc dữ liệu bị sai lệch, thực hiện hoàn nguyên qua PowerShell:

```powershell
# Bước 1: Dừng các tiến trình bot hoặc cron đang truy cập SQLite (nếu có)
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force

# Bước 2: Kiểm tra bản sao lưu
Test-Path data\market_backup_20261012_174222.db

# Bước 3: Khôi phục đè file gốc từ bản sao lưu an toàn
Copy-Item -Path data\market_backup_20261012_174222.db -Destination data\market.db -Force

# Bước 4: Kiểm tra tính toàn vẹn (Integrity Check)
python -c "import sqlite3; con = sqlite3.connect('data/market.db'); print(con.execute('PRAGMA integrity_check;').fetchall()); con.close()"
# Kết quả mong đợi: [('ok',)]
```

---

## 3. Kịch bản 2: Hoàn nguyên Toàn bộ Mã Nguồn Git về Base Commit

Nếu muốn hủy bỏ toàn bộ các thay đổi trong nhánh `audit-rebuild` và quay trở lại trạng thái ban đầu:

```powershell
# Bước 1: Lưu trạng thái làm việc hiện tại vào một nhánh tạm (đề phòng muốn xem lại)
git branch emergency-checkpoint

# Bước 2: Chuyển về nhánh main ban đầu
git checkout main

# Bước 3: Khôi phục hoàn toàn thư mục làm việc về commit 17b76a2
git reset --hard 17b76a2

# Bước 4: Xóa các file untracked mới sinh ra (nếu muốn làm sạch hoàn toàn)
# Lưu ý: Không dùng cờ -x để tránh xóa các file .env và data/market.db
git clean -fd -e data/ -e .env
```

---

## 4. Kịch bản 3: Chuyển đổi qua lại giữa Codex và Google Antigravity

Dự án đã được thiết kế hoàn toàn độc lập với công cụ AI:
- Không sử dụng file cấu hình hay API phụ thuộc riêng vào một IDE.
- Tất cả cấu hình chạy test được lưu tại `pytest.ini`.
- Nếu chuyển sang Codex hoặc ngược lại, chỉ cần:
  ```powershell
  # Kiểm tra môi trường test
  pytest -v
  ```
  Tất cả 19 bài kiểm thử sẽ chạy bình thường trên bất kỳ IDE nào hỗ trợ Python 3.11+.

---

## 5. Danh Sách Kiểm Tra Sau Hoàn Nguyên (Post-Rollback Verification Checklist)

- [ ] SQLite database mở được và trả về `[('ok',)]`.
- [ ] Không có file nào trong thư mục `reports/` hoặc `data/segments/` bị mất mát.
- [ ] Lệnh `python main.py` chạy thành công.
