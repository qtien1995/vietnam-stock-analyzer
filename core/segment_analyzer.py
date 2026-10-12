"""
Module Bóc tách Mô hình Kinh doanh Cốt lõi & Phân khúc Hoạt động (Core Business Segment Analyzer)
Chuyên trách:
- Nạp hồ sơ phân khúc kinh doanh thực tế từ data/segments/{symbol}.json (nếu có).
- Thống kê tỷ trọng % Doanh thu, % Lợi nhuận gộp, biên lãi từng mảng từ thuyết minh BCTC thực tế.
- Tuyệt đối KHÔNG tự bịa ra cơ cấu phân khúc hay tên dự án giả định khi chưa có dữ liệu kiểm chứng.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional
from config import SEGMENTS_DIR

# Bộ nhớ đệm phân tích phân khúc đã tải từ JSON
_SEGMENT_CACHE: Dict[str, Dict[str, Any]] = {}


def load_segment_profile(symbol: str) -> Optional[Dict[str, Any]]:
    """
    Nạp hồ sơ phân khúc hoạt động từ data/segments/{symbol}.json nếu có.
    Hỗ trợ bổ sung thêm mã mới mà không cần chỉnh sửa code Python.
    """
    sym = symbol.upper().strip()
    if sym in _SEGMENT_CACHE:
        return _SEGMENT_CACHE[sym]

    file_path = SEGMENTS_DIR / f"{sym}.json"
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                _SEGMENT_CACHE[sym] = data
                return data
        except Exception:
            pass
    return None


def analyze_company_segments(symbol: str, company_name: str = "", sector: str = "GENERAL") -> Dict[str, Any]:
    """
    Bóc tách mô hình kinh doanh cốt lõi (Core Business) và phân tích cơ cấu phân khúc (Segments).
    Trả về thông tin chi tiết % Doanh thu, % Lợi nhuận gộp, biên lãi từng mảng và vai trò chiến lược
    CHỈ KHI có hồ sơ được xác minh trong data/segments/{symbol}.json.
    Khi chưa có dữ liệu kiểm chứng: Trả về trạng thái INSUFFICIENT_DATA minh bạch, không bịa số liệu.
    """
    sym = symbol.upper().strip()

    # 1. Nếu có trong hồ sơ chuyên sâu (được lưu tại data/segments/{symbol}.json)
    profile = load_segment_profile(sym)
    if profile:
        return {
            "has_detailed_segments": True,
            "source": "VERIFIED_FILE",
            "symbol": sym,
            "company_name": profile.get("company_name", company_name or sym),
            "business_model_summary": profile.get("business_model_summary", f"Mô hình kinh doanh của {sym}."),
            "segments": profile.get("segments", []),
            "projects": profile.get("projects", [])
        }

    # 2. Khi chưa có hồ sơ phân rã phân khúc được xác minh:
    # Trả về kết quả trung thực: Chưa có dữ liệu phân rã phân khúc từ BCTC kiểm toán
    summary = (
        f"Doanh nghiệp hoạt động trong lĩnh vực {sector}. "
        f"Hệ thống chưa có hồ sơ bóc tách phân khúc chi tiết từ thuyết minh BCTC được kiểm chứng cho mã {sym}. "
        f"Cần tra cứu phụ lục BCTC kiểm toán gần nhất để nắm cơ cấu doanh thu và lợi nhuận theo từng mảng kinh doanh."
    )

    return {
        "has_detailed_segments": False,
        "source": "UNVERIFIED",
        "symbol": sym,
        "company_name": company_name or sym,
        "business_model_summary": summary,
        "segments": [],
        "projects": []
    }
