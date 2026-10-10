"""
Module Bóc tách Mô hình Kinh doanh Cốt lõi & Phân khúc Hoạt động (Core Business Segment Analyzer)
Chuyên trách:
- Nhận diện các mảng kinh doanh chính của doanh nghiệp (Xây lắp, BĐS, Năng lượng, Bán lẻ...).
- Thống kê tỷ trọng % Doanh thu và % Lợi nhuận gộp của từng mảng.
- Đánh giá biên lợi nhuận gộp từng mảng và xác định "Con bò sữa tạo tiền" (Cash Cow), "Trụ cột quy mô" (Revenue Base), "Ngòi nổ tăng trưởng" (Catalyst).
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
    Bóc tách mô hình kinh doanh cốt lõi (Core Business) và phân tích cơ cấu phân khúc (Segments)
    trả về thông tin chi tiết % Doanh thu, % Lợi nhuận gộp, biên lãi từng mảng và vai trò chiến lược.
    """
    sym = symbol.upper().strip()

    # 1. Nếu có trong hồ sơ chuyên sâu (được lưu tại data/segments/{symbol}.json)
    profile = load_segment_profile(sym)
    if profile:
        return {
            "has_detailed_segments": True,
            "symbol": sym,
            "company_name": profile.get("company_name", company_name),
            "business_model_summary": profile.get("business_model_summary", ""),
            "segments": profile.get("segments", []),
            "projects": profile.get("projects", [])
        }

    # 2. Suy luận thông minh theo nhóm ngành nếu chưa có profile riêng
    default_segments = []
    summary = f"Doanh nghiệp hoạt động chủ yếu trong phân khúc ngành {sector}."

    if sector == "BANK":
        summary = "Mô hình kinh doanh Ngân hàng thương mại: Thu nhập lãi thuần (NII) từ cho vay và huy động là cốt lõi, bổ trợ bởi thu nhập dịch vụ (phí, bảo hiểm) và kinh doanh ngoại hối/chứng khoán."
        default_segments = [
            {
                "name": "Thu nhập lãi thuần (Cho vay khách hàng)",
                "rev_share_pct": 75.0,
                "gross_profit_share_pct": 80.0,
                "gross_margin_pct": 3.5, # NIM tham chiếu
                "role": "Trụ cột cốt lõi (Core NII)",
                "strategic_role": "CASH_COW",
                "status": "Tăng trưởng tín dụng",
                "highlights": "Chiếm 70-80% tổng thu nhập hoạt động (TOI), động lực từ tăng trưởng tín dụng và chi phí vốn CASA.",
                "risks": "Rủi ro nợ xấu (NPL) và biên lãi thuần (NIM) co hẹp."
            },
            {
                "name": "Thu nhập ngoài lãi (Phí dịch vụ, Ngoại hối, Bancassurance)",
                "rev_share_pct": 25.0,
                "gross_profit_share_pct": 20.0,
                "gross_margin_pct": 70.0,
                "role": "Động lực đa dạng hóa",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Ổn định",
                "highlights": "Nguồn thu ít chịu rủi ro trích lập dự phòng, tăng chất lượng tài sản.",
                "risks": "Doanh thu bancassurance chịu sự kiểm soát chặt chẽ của pháp lý."
            }
        ]

    elif sector == "REAL_ESTATE":
        summary = "Mô hình kinh doanh Bất động sản: Doanh thu phụ thuộc vào chu kỳ bàn giao dự án nhà ở/thương mại, bổ trợ bởi hoạt động cho thuê và quản lý dịch vụ."
        default_segments = [
            {
                "name": "Chuyển nhượng Bất động sản (Bán căn hộ, thấp tầng, đất nền)",
                "rev_share_pct": 85.0,
                "gross_profit_share_pct": 90.0,
                "gross_margin_pct": 35.0,
                "role": "Động lực lợi nhuận chính",
                "strategic_role": "CORE_MOAT",
                "status": "Phụ thuộc chu kỳ pháp lý & mở bán",
                "highlights": "Ghi nhận doanh thu đột biến theo từng đợt bàn giao sổ và bàn giao nhà.",
                "risks": "Vướng mắc cấp phép pháp lý, tính tiền sử dụng đất và thanh khoản thị trường nhà đất."
            },
            {
                "name": "Cho thuê BĐS & Dịch vụ quản lý vận hành",
                "rev_share_pct": 15.0,
                "gross_profit_share_pct": 10.0,
                "gross_margin_pct": 25.0,
                "role": "Dòng tiền đều đặn duy trì",
                "strategic_role": "CASH_COW",
                "status": "Ổn định",
                "highlights": "Tạo dòng tiền mặt trang trải chi phí quản lý doanh nghiệp.",
                "risks": "Tỷ lệ lấp đầy mặt bằng thương mại sụt giảm trong giai đoạn khó khăn."
            }
        ]

    elif sector == "SECURITIES":
        summary = "Mô hình Công ty Chứng khoán: Hoạt động tự doanh đầu tư (FVTPL), Cho vay ký quỹ (Margin) và Môi giới chứng khoán (Brokerage)."
        default_segments = [
            {
                "name": "Lãi từ các tài sản tài chính (Tự doanh FVTPL / HTM)",
                "rev_share_pct": 45.0,
                "gross_profit_share_pct": 50.0,
                "gross_margin_pct": 50.0,
                "role": "Ngòi nổ tăng trưởng theo thị trường (Beta cao)",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Phụ thuộc VN-Index",
                "highlights": "Lợi nhuận bùng nổ khi thị trường vào sóng tăng mạnh.",
                "risks": "Trích lập giảm giá danh mục khi VN-Index điều chỉnh."
            },
            {
                "name": "Lãi cho vay giao dịch ký quỹ (Margin Lending)",
                "rev_share_pct": 35.0,
                "gross_profit_share_pct": 40.0,
                "gross_margin_pct": 60.0,
                "role": "Con bò sữa dòng tiền (Cash Cow)",
                "strategic_role": "CASH_COW",
                "status": "Rất ổn định",
                "highlights": "Dòng thu lãi vay cố định, biên lợi nhuận cao và an toàn vốn nhờ quản trị rủi ro call margin tự động.",
                "risks": "Thanh khoản toàn thị trường sụt giảm làm giảm dư nợ margin."
            },
            {
                "name": "Doanh thu Môi giới & Ngân hàng đầu tư (IB)",
                "rev_share_pct": 20.0,
                "gross_profit_share_pct": 10.0,
                "gross_margin_pct": 15.0,
                "role": "Nền tảng khách hàng",
                "strategic_role": "SCALE_BASE",
                "status": "Cạnh tranh gay gắt phí 0%",
                "highlights": "Kênh thu hút người dùng mở tài khoản.",
                "risks": "Cuộc chiến Zero-Fee làm xói mòn biên lợi nhuận môi giới thuần."
            }
        ]

    else:
        # Ngành thông thường
        summary = f"Doanh nghiệp sản xuất/thương mại tiêu chuẩn trong lĩnh vực {sector}."
        default_segments = [
            {
                "name": "Hoạt động kinh doanh cốt lõi (Sản xuất / Dịch vụ chính)",
                "rev_share_pct": 85.0,
                "gross_profit_share_pct": 85.0,
                "gross_margin_pct": 18.0,
                "role": "Hoạt động kinh doanh cốt lõi",
                "strategic_role": "CORE_MOAT",
                "status": "Đang vận hành",
                "highlights": "Sản phẩm chủ lực mang lại phần lớn doanh thu và lợi nhuận cho công ty.",
                "risks": "Biến động chi phí đầu vào và sức ép cạnh tranh thị phần."
            },
            {
                "name": "Hoạt động tài chính & Thu nhập phụ trợ",
                "rev_share_pct": 15.0,
                "gross_profit_share_pct": 15.0,
                "gross_margin_pct": 25.0,
                "role": "Hoạt động phụ trợ",
                "strategic_role": "CASH_COW",
                "status": "Ổn định",
                "highlights": "Lãi tiền gửi, cổ tức liên kết và thanh lý tài sản.",
                "risks": "Không mang tính bền vững dài hạn nếu hoạt động cốt lõi suy yếu."
            }
        ]

    return {
        "has_detailed_segments": False,
        "symbol": sym,
        "company_name": company_name or sym,
        "business_model_summary": summary,
        "segments": default_segments,
        "projects": [
            {
                "name": f"Dự án mở rộng hoạt động kinh doanh cốt lõi ({sym})",
                "location": "Theo địa bàn hoạt động chính",
                "scale": "Tối ưu hóa công suất hiện hữu",
                "status": "Đang vận hành",
                "profit_contribution": "Duy trì dòng tiền kinh doanh cốt lõi đều đặn.",
                "bottlenecks_and_risks": "Phụ thuộc vào chu kỳ kinh tế và sức mua thị trường chung."
            }
        ]
    }
