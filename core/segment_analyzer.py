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
    default_projects = []
    summary = f"Doanh nghiệp hoạt động chủ yếu trong phân khúc ngành {sector}."

    sec_upper = sector.upper()

    if "RUBBER" in sec_upper:
        summary = "Mô hình kinh doanh Cao su & BĐS Khu công nghiệp: Tận dụng quỹ đất cao su rộng lớn để chuyển đổi sang phát triển hạ tầng Khu công nghiệp (biên lãi gộp > 50-60%) và nhận tiền bồi thường đất theo quy định mới; kết hợp khai thác mủ cao su tự nhiên và chế biến gỗ cao su."
        default_segments = [
            {
                "name": "Khai thác, Chế biến & Xuất khẩu Mủ Cao su",
                "service_description": "Quản lý nông trường cao su, thu hoạch mủ và chế biến cao su kỹ thuật (SVR, Latex) cung ứng ngành săm lốp và xuất khẩu.",
                "rev_share_pct": 65.0,
                "gross_profit_share_pct": 50.0,
                "gross_margin_pct": 22.0,
                "role": "Con bò sữa dòng tiền cốt lõi (Cash Cow)",
                "strategic_role": "CASH_COW",
                "status": "Hưởng lợi giá cao su thế giới",
                "highlights": "Hưởng lợi từ chu kỳ giá cao su tự nhiên thế giới TSR20/TOCOM tăng cao và chứng chỉ rừng PEFC/EUDR.",
                "risks": "Biến động giá hàng hóa cao su quốc tế và thời tiết mưa bão."
            },
            {
                "name": "Phát triển Hạ tầng KCN & Bồi thường chuyển đổi đất",
                "service_description": "Chuyển đổi quỹ đất cao su sang đất công nghiệp, cho thuê hạ tầng KCN 50 năm và nhận tiền bồi thường hỗ trợ thu hồi đất theo Nghị định 102/2024/NĐ-CP.",
                "rev_share_pct": 20.0,
                "gross_profit_share_pct": 40.0,
                "gross_margin_pct": 60.0,
                "role": "Ngòi nổ lợi nhuận đột biến (Growth Catalyst)",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Tăng tốc chuyển đổi đất",
                "highlights": "Biên lãi gộp vượt 60%, tiền bồi thường đất cao su ước tính 1.0 - 1.5 tỷ đ/ha mang lại thặng dư dòng tiền mặt rất lớn.",
                "risks": "Tiến độ phê duyệt chủ trương đầu tư của cơ quan nhà nước có thẩm quyền."
            },
            {
                "name": "Chế biến Gỗ cao su & Hoạt động phụ trợ",
                "service_description": "Thanh lý gỗ cao su già cỗi hết chu kỳ khai thác mủ, chế biến gỗ xẻ, ván ghép thanh xuất khẩu.",
                "rev_share_pct": 15.0,
                "gross_profit_share_pct": 10.0,
                "gross_margin_pct": 18.0,
                "role": "Tận dụng giá trị gia tăng vườn cây",
                "strategic_role": "SCALE_BASE",
                "status": "Ổn định",
                "highlights": "Chi phí gỗ nguyên liệu thấp từ vườn cây tự quản lý.",
                "risks": "Nhu cầu thị trường đồ gỗ xuất khẩu."
            }
        ]
        default_projects = [
            {
                "name": f"Dự án Chuyển đổi Quỹ đất Cao su sang KCN ({sym})",
                "location": "Vùng kinh tế trọng điểm Đông Nam Bộ",
                "scale": "Hàng trăm đến hàng nghìn ha đất cao su thuộc quy hoạch tỉnh",
                "status": "Đang hoàn thiện thủ tục chấp thuận chủ trương đầu tư & GPMB",
                "profit_contribution": "Tạo dòng tiền cho thuê đất KCN và tiền đền bù bồi thường đất theo bảng giá đất mới.",
                "bottlenecks_and_risks": "Đất công ty trực tiếp quản lý nên giải phóng mặt bằng nhanh; cần phối hợp địa phương phê duyệt quy hoạch 1/2000.",
                "flag": "TÍCH CỰC"
            },
            {
                "name": "Đề án Quản lý Rừng Bền vững & Chứng chỉ EUDR",
                "location": "Toàn bộ diện tích nông trường cao su",
                "scale": "Hàng chục nghìn ha vườn cây cao su",
                "status": "Đang triển khai cấp chứng chỉ PEFC/VFCS",
                "profit_contribution": "Cho phép bán mủ cao su với giá premium và duy trì xuất khẩu sang các thị trường khó tính EU, Mỹ.",
                "bottlenecks_and_risks": "Tuân thủ nghiêm ngặt quy định chống phá rừng của Liên minh châu Âu.",
                "flag": "TÍCH CỰC"
            }
        ]

    elif "INDUSTRIAL_REAL_ESTATE" in sec_upper:
        summary = "Mô hình kinh doanh BĐS Khu công nghiệp: Cho thuê đất công nghiệp hoàn thiện hạ tầng kỹ thuật 50 năm cho các tập đoàn FDI thu tiền 1 lần; cung ứng dịch vụ điện, nước, xử lý nước thải và cho thuê nhà xưởng xây sẵn (RBF)."
        default_segments = [
            {
                "name": "Cho thuê đất Khu công nghiệp (50 năm)",
                "service_description": "Cho thuê đất sạch đã giải phóng mặt bằng và hoàn thiện hạ tầng kỹ thuật trong KCN, thu tiền 1 lần hoặc định kỳ.",
                "rev_share_pct": 55.0,
                "gross_profit_share_pct": 70.0,
                "gross_margin_pct": 55.0,
                "role": "Trụ cột lợi nhuận & Dòng tiền đột biến",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Hút dòng vốn FDI",
                "highlights": "Quỹ đất sạch tại các thủ phủ FDI mang lại thặng dư tiền mặt lớn; giá thuê đất duy trì đà tăng 8-12%/năm.",
                "risks": "Chu kỳ cấp phép giấy chứng nhận đầu tư (IRC) của khách thuê."
            },
            {
                "name": "Dịch vụ Tiện ích KCN (Điện, Nước, Xử lý nước thải)",
                "service_description": "Phân phối điện, cung cấp nước sạch công nghiệp và xử lý nước thải cho toàn bộ nhà máy hoạt động trong KCN.",
                "rev_share_pct": 30.0,
                "gross_profit_share_pct": 18.0,
                "gross_margin_pct": 20.0,
                "role": "Con bò sữa dòng tiền (Cash Cow) đều đặn hàng tháng",
                "strategic_role": "CASH_COW",
                "status": "Cực kỳ ổn định",
                "highlights": "Dòng thu tiền mặt đều đặn hàng tháng gắn liền với hoạt động sản xuất của các nhà máy.",
                "risks": "Chi phí mua điện/nước đầu vào từ các nhà cung cấp nhà nước."
            },
            {
                "name": "Cho thuê Nhà xưởng xây sẵn (RBF) & Kho bãi",
                "service_description": "Xây dựng cụm nhà xưởng tiêu chuẩn cho các doanh nghiệp phụ trợ vừa và nhỏ thuê linh hoạt 3-5 năm.",
                "rev_share_pct": 15.0,
                "gross_profit_share_pct": 12.0,
                "gross_margin_pct": 45.0,
                "role": "Dòng tiền cho thuê định kỳ gối đầu",
                "strategic_role": "CASH_COW",
                "status": "Mở rộng diện tích",
                "highlights": "Tỷ lệ lấp đầy cao >85-90%, biên lợi nhuận cho thuê ổn định.",
                "risks": "Cần vốn đầu tư xây dựng ban đầu."
            }
        ]
        default_projects = [
            {
                "name": f"Dự án Khu công nghiệp Thương phẩm Trọng điểm ({sym})",
                "location": "Vùng kinh tế trọng điểm",
                "scale": "200 - 500 ha",
                "status": "Đang hoàn thiện hạ tầng & Thu hút nhà đầu tư FDI",
                "profit_contribution": "Đóng góp phần lớn doanh thu cho thuê đất và tích lũy doanh thu chưa thực hiện dài hạn.",
                "bottlenecks_and_risks": "Đã có quy hoạch phân khu; cần giám sát tiến độ cấp phép đầu tư thực tế.",
                "flag": "TÍCH CỰC"
            }
        ]

    elif "BANK" in sec_upper:
        summary = "Mô hình kinh doanh Ngân hàng thương mại: Thu nhập lãi thuần (NII) từ cho vay và huy động là cốt lõi, bổ trợ bởi thu nhập dịch vụ (phí, thẻ, bảo hiểm) và kinh doanh ngoại hối/chứng khoán."
        default_segments = [
            {
                "name": "Thu nhập lãi thuần (Cho vay khách hàng - NII)",
                "service_description": "Huy động tiền gửi và phát hành giấy tờ có giá, sau đó cấp tín dụng cho khách hàng doanh nghiệp và cá nhân.",
                "rev_share_pct": 78.0,
                "gross_profit_share_pct": 80.0,
                "gross_margin_pct": 3.8, # NIM tham chiếu
                "role": "Trụ cột cốt lõi (Core NII)",
                "strategic_role": "CASH_COW",
                "status": "Tăng trưởng tín dụng",
                "highlights": "Động lực từ hạn mức tăng trưởng tín dụng NHNN và tối ưu chi phí vốn qua tỷ lệ tiền gửi không kỳ hạn CASA.",
                "risks": "Rủi ro nợ xấu (NPL) và biên lãi thuần NIM co hẹp."
            },
            {
                "name": "Thu nhập ngoài lãi (Phí dịch vụ, Ngoại hối & Chứng khoán)",
                "service_description": "Cung cấp dịch vụ thanh toán, thẻ, bảo lãnh, kinh doanh ngoại tệ và phân phối bảo hiểm liên kết.",
                "rev_share_pct": 22.0,
                "gross_profit_share_pct": 20.0,
                "gross_margin_pct": 70.0,
                "role": "Động lực đa dạng hóa chất lượng cao",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Tăng trưởng ổn định",
                "highlights": "Nguồn thu phí thuần không phải trích lập dự phòng rủi ro tín dụng.",
                "risks": "Hành lang pháp lý thắt chặt hoạt động bán chéo bảo hiểm."
            }
        ]
        default_projects = [
            {
                "name": f"Chương trình Chuyển đổi số & Tối ưu CASA ({sym})",
                "location": "Toàn hệ thống ngân hàng",
                "scale": "Hàng triệu khách hàng cá nhân & SME",
                "status": "Đang vận hành hiệu quả",
                "profit_contribution": "Gia tăng tỷ lệ CASA giúp hạ chi phí vốn đầu vào (COF), nới rộng biên NIM.",
                "bottlenecks_and_risks": "Cạnh tranh số hóa từ các đối thủ cùng ngành.",
                "flag": "TÍCH CỰC"
            }
        ]

    elif "SECURITIES" in sec_upper:
        summary = "Mô hình Công ty Chứng khoán: Kinh doanh danh mục tự doanh (FVTPL/AFS), Cho vay giao dịch ký quỹ (Margin Lending) và Môi giới/Tư vấn đầu tư tài chính."
        default_segments = [
            {
                "name": "Lãi từ Cho vay Giao dịch Ký quỹ (Margin)",
                "service_description": "Cung cấp đòn bẩy tài chính cho nhà đầu tư giao dịch chứng khoán quản trị rủi ro tự động.",
                "rev_share_pct": 40.0,
                "gross_profit_share_pct": 45.0,
                "gross_margin_pct": 65.0,
                "role": "Con bò sữa dòng tiền (Cash Cow) an toàn vốn",
                "strategic_role": "CASH_COW",
                "status": "Tăng trưởng theo thanh khoản",
                "highlights": "Dòng thu lãi ổn định từ quy mô dư nợ margin kỷ lục, rủi ro nợ xấu thấp nhờ hệ thống call margin tự động.",
                "risks": "Thanh khoản thị trường chung sụt giảm làm thu hẹp nhu cầu vay margin."
            },
            {
                "name": "Kinh doanh Tài sản Tài chính Tự doanh (FVTPL / HTM)",
                "service_description": "Đầu tư cổ phiếu niêm yết, trái phiếu doanh nghiệp chất lượng cao và giấy tờ có giá.",
                "rev_share_pct": 38.0,
                "gross_profit_share_pct": 42.0,
                "gross_margin_pct": 50.0,
                "role": "Ngòi nổ lợi nhuận bùng nổ theo con sóng thị trường (Beta cao)",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Phụ thuộc nhịp sóng VN-Index",
                "highlights": "Lợi nhuận tăng vọt khi các cổ phiếu cốt lõi trong danh mục vào sóng tăng giá lớn.",
                "risks": "Trích lập giảm giá danh mục khi thị trường điều chỉnh."
            },
            {
                "name": "Môi giới Chứng khoán & Tư vấn Tài chính Doanh nghiệp (IB)",
                "service_description": "Dịch vụ môi giới giao dịch cổ phiếu, phái sinh, quản lý tài khoản và tư vấn phát hành vốn.",
                "rev_share_pct": 22.0,
                "gross_profit_share_pct": 13.0,
                "gross_margin_pct": 20.0,
                "role": "Nền tảng khách hàng & Bệ đỡ thị phần",
                "strategic_role": "SCALE_BASE",
                "status": "Cạnh tranh phí 0%",
                "highlights": "Hưởng lợi từ làn sóng mở mới tài khoản và triển khai hệ thống giao dịch KRX, cơ chế Non-prefunding.",
                "risks": "Cuộc chiến miễn phí giao dịch (Zero-Fee) ăn mòn biên lợi nhuận thuần."
            }
        ]
        default_projects = [
            {
                "name": f"Hệ thống Nâng cấp Công nghệ Giao dịch & Đón sóng Nâng hạng ({sym})",
                "location": "Toàn hệ thống công ty chứng khoán",
                "scale": "Cơ chế Non-prefunding & Hệ thống giao dịch KRX",
                "status": "Sẵn sàng vận hành",
                "profit_contribution": "Thu hút dòng vốn ngoại giải ngân khi thị trường được nâng hạng lên Mới nổi (FTSE Emerging).",
                "bottlenecks_and_risks": "Tiến độ đánh giá thực tế của tổ chức xếp hạng quốc tế.",
                "flag": "TÍCH CỰC"
            }
        ]

    elif "OIL_GAS" in sec_upper or "ENERGY" in sec_upper:
        summary = "Mô hình kinh doanh Dầu khí & Năng lượng: Cung cấp dịch vụ kỹ thuật dầu khí (khoan, xây lắp giàn khoan EPCI, tàu dịch vụ), khai thác phân phối dầu khí và năng lượng điện."
        default_segments = [
            {
                "name": "Dịch vụ Khoan & Kỹ thuật Dầu khí Thượng nguồn",
                "service_description": "Cung cấp giàn khoan biển, dịch vụ kỹ thuật giếng khoan, bảo dưỡng cơ khí công trình dầu khí ngoài khơi.",
                "rev_share_pct": 60.0,
                "gross_profit_share_pct": 70.0,
                "gross_margin_pct": 32.0,
                "role": "Ngòi nổ tăng trưởng theo chu kỳ giá dầu",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Hiệu suất hoạt động giàn khoan 100%",
                "highlights": "Giá thuê giàn khoan tự nâng (Jack-up) neo cao kỷ lục (>110.000 - 130.000 USD/ngày), lịch trình khoan kín chỗ nhiều năm.",
                "risks": "Biến động giá dầu Brent thế giới tác động đến ngân sách thăm dò của các nhà điều hành dầu khí."
            },
            {
                "name": "Khai thác, Phân phối Khí & Sản phẩm Xăng dầu",
                "service_description": "Vận chuyển, phân phối khí thiên nhiên, khí hóa lỏng LPG/LNG và các sản phẩm lọc hóa dầu.",
                "rev_share_pct": 40.0,
                "gross_profit_share_pct": 30.0,
                "gross_margin_pct": 18.0,
                "role": "Dòng tiền tiêu thụ ổn định (Cash Cow)",
                "strategic_role": "CASH_COW",
                "status": "Ổn định",
                "highlights": "Nhu cầu tiêu thụ năng lượng phục vụ các khu công nghiệp và nhà máy nhiệt điện khí.",
                "risks": "Rủi ro chênh lệch giá nhập khẩu LNG và cơ chế giá bán điện."
            }
        ]
        default_projects = [
            {
                "name": f"Tham gia Chuỗi Đại Dự án Khí Điện Lô B - Ô Môn ({sym})",
                "location": "Bồn trũng Malay - Thổ Chu & Cần Thơ",
                "scale": "Đại dự án quy mô gần 12 tỷ USD",
                "status": "Đang triển khai các gói thầu EPCI & Chuẩn bị chiến dịch khoan",
                "profit_contribution": "Mang lại khối lượng công việc khổng lồ liên tục trong giai đoạn 2024-2028.",
                "bottlenecks_and_risks": "Tiến độ phê duyệt quyết định đầu tư cuối cùng (FID) và đàm phán hợp đồng mua bán khí (GSA/PPA).",
                "flag": "TÍCH CỰC"
            }
        ]

    elif "STEEL" in sec_upper:
        summary = "Mô hình kinh doanh Thép & Vật liệu xây dựng: Luyện cán thép xây dựng, thép cuộn cán nóng HRC, tôn mạ kẽm/màu và ống thép công nghiệp phục vụ đầu tư công và bất động sản."
        default_segments = [
            {
                "name": "Thép cuộn cán nóng (HRC) & Thép xây dựng chất lượng cao",
                "service_description": "Sản xuất HRC nguyên liệu và thép thanh, thép cuộn phục vụ các đại công trình hạ tầng và chế tạo cơ khí.",
                "rev_share_pct": 75.0,
                "gross_profit_share_pct": 82.0,
                "gross_margin_pct": 17.5,
                "role": "Trụ cột quy mô & Lợi thế kinh tế theo quy mô (Cost Leadership)",
                "strategic_role": "CORE_MOAT",
                "status": "Hồi phục sản lượng",
                "highlights": "Hưởng lợi từ giải ngân đầu tư công hạ tầng và biện pháp phòng vệ thương mại chống bán phá giá thép nhập khẩu.",
                "risks": "Áp lực thép giá rẻ dư thừa từ Trung Quốc."
            },
            {
                "name": "Ống thép, Tôn mạ & Sản phẩm sau thép",
                "service_description": "Gia công chế biến sâu ống thép hàn, tôn mạ kẽm/màu xuất khẩu sang các thị trường quốc tế.",
                "rev_share_pct": 25.0,
                "gross_profit_share_pct": 18.0,
                "gross_margin_pct": 12.0,
                "role": "Hoàn thiện chuỗi giá trị hạ nguồn",
                "strategic_role": "SCALE_BASE",
                "status": "Duy trì thị phần",
                "highlights": "Thị phần dẫn đầu nội địa, mạng lưới đại lý phân phối rộng khắp toàn quốc.",
                "risks": "Các vụ kiện chống lẩn tránh thuế phòng vệ thương mại tại thị trường xuất khẩu."
            }
        ]
        default_projects = [
            {
                "name": f"Đại dự án Nâng công suất Luyện Thép & HRC ({sym})",
                "location": "Khu kinh tế ven biển",
                "scale": "Quy mô hàng chục nghìn tỷ đồng",
                "status": "Đang thi công xây dựng & Lắp đặt thiết bị",
                "profit_contribution": "Tăng gấp đôi công suất HRC khi đi vào vận hành thương mại, tạo bước nhảy vọt doanh thu.",
                "bottlenecks_and_risks": "Tiến độ chạy thử nghiệm và khả năng hấp thụ của thị trường.",
                "flag": "TÍCH CỰC"
            }
        ]

    else:
        # Nhóm ngành BĐS Dân dụng hoặc Sản xuất Thương mại Tiêu chuẩn
        if "RESIDENTIAL" in sec_upper or "ESTATE" in sec_upper:
            summary = "Mô hình kinh doanh Bất động sản Dân dụng: Phát triển quỹ đất sạch, đầu tư xây dựng dự án khu đô thị/nhà ở thương mại, mở bán và bàn giao căn hộ/đất nền ghi nhận doanh thu đột biến."
            default_segments = [
                {
                    "name": "Chuyển nhượng Bất động sản (Bàn giao nhà ở, căn hộ)",
                    "service_description": "Mở bán và bàn giao các sản phẩm căn hộ cao tầng, nhà phố, biệt thự khu đô thị cho người mua nhà.",
                    "rev_share_pct": 85.0,
                    "gross_profit_share_pct": 90.0,
                    "gross_margin_pct": 38.0,
                    "role": "Động lực lợi nhuận chính theo chu kỳ bàn giao",
                    "strategic_role": "GROWTH_CATALYST",
                    "status": "Phụ thuộc chu kỳ mở bán & pháp lý",
                    "highlights": "Ghi nhận doanh thu lợi nhuận đột biến khi các dự án lớn hoàn thành cất nóc và bàn giao sổ hồng.",
                    "risks": "Vướng mắc tính tiền sử dụng đất theo bảng giá đất mới và tiến độ cấp giấy phép xây dựng."
                },
                {
                    "name": "Cho thuê BĐS Thương mại & Dịch vụ Quản lý",
                    "service_description": "Cho thuê mặt bằng trung tâm thương mại, văn phòng và cung ứng dịch vụ quản lý vận hành tòa nhà.",
                    "rev_share_pct": 15.0,
                    "gross_profit_share_pct": 10.0,
                    "gross_margin_pct": 30.0,
                    "role": "Dòng tiền mặt định kỳ duy trì bộ máy (Cash Cow)",
                    "strategic_role": "CASH_COW",
                    "status": "Ổn định",
                    "highlights": "Tạo dòng tiền mặt đều đặn trang trải chi phí lãi vay và quản trị doanh nghiệp.",
                    "risks": "Tỷ lệ lấp đầy sàn thương mại trong giai đoạn sức mua tiêu dùng chậm."
                }
            ]
            default_projects = [
                {
                    "name": f"Dự án Khu Đô thị Trọng điểm Đang Triển khai ({sym})",
                    "location": "Đô thị vệ tinh cửa ngõ",
                    "scale": "Hàng chục ha quỹ đất thương phẩm",
                    "status": "Đang hoàn thiện hạ tầng & Thủ tục mở bán",
                    "profit_contribution": "Là nguồn đóng góp doanh thu chính khi bàn giao cho khách hàng trong 1-2 năm tới.",
                    "bottlenecks_and_risks": "Tiến độ phê duyệt tiền sử dụng đất và cấp phép đủ điều kiện bán nhà hình thành trong tương lai.",
                    "flag": "TIẾN ĐỘ BÌNH THƯỜNG"
                }
            ]
        else:
            summary = f"Doanh nghiệp sản xuất, thương mại và dịch vụ chuyên ngành trong lĩnh vực {sector}."
            default_segments = [
                {
                    "name": "Hoạt động Sản xuất & Cung ứng Dịch vụ Cốt lõi",
                    "service_description": f"Sản xuất, chế biến và thương mại các dòng sản phẩm chủ lực trong ngành {sector}.",
                    "rev_share_pct": 85.0,
                    "gross_profit_share_pct": 85.0,
                    "gross_margin_pct": 20.0,
                    "role": "Hoạt động kinh doanh cốt lõi (Core Business)",
                    "strategic_role": "CORE_MOAT",
                    "status": "Đang vận hành",
                    "highlights": "Sản phẩm chủ lực mang lại phần lớn dòng tiền doanh thu và lợi nhuận cho công ty.",
                    "risks": "Biến động chi phí nguyên vật liệu đầu vào và sức ép cạnh tranh thị phần."
                },
                {
                    "name": "Hoạt động Tài chính & Thu nhập Phụ trợ",
                    "service_description": "Khai thác thặng dư vốn, lãi tiền gửi ngân hàng, cổ tức từ công ty liên kết và dịch vụ phụ trợ.",
                    "rev_share_pct": 15.0,
                    "gross_profit_share_pct": 15.0,
                    "gross_margin_pct": 30.0,
                    "role": "Hoạt động phụ trợ bảo toàn vốn",
                    "strategic_role": "CASH_COW",
                    "status": "Ổn định",
                    "highlights": "Tạo bộ đệm tài chính bổ trợ lợi nhuận khi chu kỳ ngành biến động.",
                    "risks": "Lãi suất tiền gửi biến động theo chu kỳ tiền tệ."
                }
            ]
            default_projects = [
                {
                    "name": f"Chương trình Tối ưu hóa Năng lực Sản xuất & Chuỗi Cung ứng ({sym})",
                    "location": "Theo cơ sở sản xuất chính của doanh nghiệp",
                    "scale": "Tối ưu hóa công suất hiện hữu",
                    "status": "Đang vận hành liên tục",
                    "profit_contribution": "Cắt giảm chi phí vận hành (SG&A), gia tăng biên lợi nhuận ròng cho cổ đông.",
                    "bottlenecks_and_risks": "Phụ thuộc vào sức mua và chu kỳ kinh tế chung.",
                    "flag": "TIẾN ĐỘ BÌNH THƯỜNG"
                }
            ]

    return {
        "has_detailed_segments": False,
        "symbol": sym,
        "company_name": company_name or sym,
        "business_model_summary": summary,
        "segments": default_segments,
        "projects": default_projects
    }
