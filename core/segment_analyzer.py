"""
Module Bóc tách Mô hình Kinh doanh Cốt lõi & Phân khúc Hoạt động (Core Business Segment Analyzer)
Chuyên trách:
- Nhận diện các mảng kinh doanh chính của doanh nghiệp (Xây lắp, BĐS, Năng lượng, Bán lẻ...).
- Thống kê tỷ trọng % Doanh thu và % Lợi nhuận gộp của từng mảng.
- Đánh giá biên lợi nhuận gộp từng mảng và xác định "Con bò sữa tạo tiền" (Cash Cow), "Trụ cột quy mô" (Revenue Base), "Ngòi nổ tăng trưởng" (Catalyst).
"""

from typing import Dict, Any, List


# Cơ sở dữ liệu phân tích mảng kinh doanh chuyên sâu cho các tập đoàn & doanh nghiệp tiêu biểu
KNOWN_SEGMENT_PROFILES: Dict[str, Dict[str, Any]] = {
    "DPG": {
        "company_name": "Công ty Cổ phần Tập đoàn Đạt Phương",
        "business_model_summary": "Mô hình 'Kiềng ba chân': Xây lắp hạ tầng làm nền tảng quy mô doanh thu, Thủy điện là 'máy in tiền' (biên lãi >60%) tài trợ chi phí vốn, và Bất động sản nghỉ dưỡng tạo lợi nhuận đột biến theo chu kỳ.",
        "segments": [
            {
                "name": "Xây lắp hạ tầng giao thông & Cầu đường",
                "rev_share_pct": 78.0,
                "gross_profit_share_pct": 26.0,
                "gross_margin_pct": 7.5,
                "role": "Trụ cột doanh thu & Dòng việc",
                "strategic_role": "SCALE_BASE",
                "status": "Ổn định",
                "highlights": "Top đầu nhà thầu cầu đường Việt Nam; Backlog đầu tư công lớn (>9.000 tỷ đồng) đảm bảo khối lượng công việc đến 2027.",
                "risks": "Biên lợi nhuận mỏng (7-8%), nhạy cảm với biến động giá nguyên vật liệu (cát, thép, đá) và tiến độ giải ngân vốn đầu tư công."
            },
            {
                "name": "Sản xuất & Bán điện thương phẩm (Thủy điện)",
                "rev_share_pct": 14.5,
                "gross_profit_share_pct": 52.0,
                "gross_margin_pct": 62.5,
                "role": "Con bò sữa tạo tiền mặt (Cash Cow)",
                "strategic_role": "CASH_COW",
                "status": "Rất tích cực",
                "highlights": "Cụm 4 nhà máy thủy điện (Sơn Trà 1A, 1B, 1C tổng 69MW và Sông Bung 6 30MW). Biên lãi gộp vượt trội (>60%), mang lại dòng tiền ròng 300-400 tỷ/năm ổn định.",
                "risks": "Phụ thuộc chu kỳ thủy văn (El Nino làm giảm lưu lượng nước về hồ)."
            },
            {
                "name": "Kinh doanh Bất động sản Khu đô thị",
                "rev_share_pct": 6.0,
                "gross_profit_share_pct": 19.5,
                "gross_margin_pct": 45.0,
                "role": "Ngòi nổ lợi nhuận đột biến (Catalyst)",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Chờ điểm rơi bàn giao",
                "highlights": "Quỹ đất giá vốn sạch tại Hội An: Casamia Võng Nhi, Casamia Calm, trọng điểm là Casamia Balanca Cồn Tiến (31ha, tổng mức đầu tư nghìn tỷ). Biên lãi gộp 40-50%.",
                "risks": "Tiến độ định giá tiền sử dụng đất bổ sung và sức mua thị trường BĐS nghỉ dưỡng miền Trung phục hồi chậm."
            },
            {
                "name": "Sản xuất Công nghiệp & Dịch vụ Khách sạn",
                "rev_share_pct": 1.5,
                "gross_profit_share_pct": 2.5,
                "gross_margin_pct": 25.0,
                "role": "Động lực tương lai (Future Horizon)",
                "strategic_role": "FUTURE_BET",
                "status": "Đang đầu tư",
                "highlights": "Dự án Nhà máy kính hoa siêu trắng Chu Lai (phục vụ pin năng lượng mặt trời) và quy hoạch quần thể nghỉ dưỡng Bình Dương (sân golf 18 lỗ).",
                "risks": "Đòi hỏi CapEx ban đầu lớn, cần thời gian chạy thử nghiệm và nghiệm thu thị trường."
            }
        ]
    },
    "HPG": {
        "company_name": "Công ty Cổ phần Tập đoàn Hòa Phát",
        "business_model_summary": "Tập đoàn công nghiệp sản xuất thép tích hợp khép kín từ thượng nguồn (quặng sắt, than mỡ) đến hạ nguồn (HRC, thép xây dựng, ống thép, tôn mạ), kết hợp nông nghiệp và BĐS KCN.",
        "segments": [
            {
                "name": "Thép & Sản phẩm gang thép (Thép XD, HRC, Ống, Tôn)",
                "rev_share_pct": 92.5,
                "gross_profit_share_pct": 91.0,
                "gross_margin_pct": 14.5,
                "role": "Trụ cột cốt lõi & Con hào kinh tế",
                "strategic_role": "CORE_MOAT",
                "status": "Phục hồi chu kỳ mạnh mẽ",
                "highlights": "Dung Quất 1 tối ưu công suất, Dung Quất 2 nâng công suất HRC thêm 5.6 triệu tấn, dẫn đầu thị phần thép Việt Nam.",
                "risks": "Biến động giá quặng sắt, giá than cốc và áp lực cạnh tranh từ thép cuộn cán nóng giá rẻ Trung Quốc."
            },
            {
                "name": "Nông nghiệp (Thức ăn chăn nuôi, Heo, Bò, Trứng gà)",
                "rev_share_pct": 5.0,
                "gross_profit_share_pct": 5.5,
                "gross_margin_pct": 15.0,
                "role": "Dòng tiền bổ trợ",
                "strategic_role": "CASH_COW",
                "status": "Tích cực",
                "highlights": "Thị phần bò Úc và trứng gà sạch dẫn đầu miền Bắc, biên lãi ổn định.",
                "risks": "Dịch bệnh chăn nuôi và giá nguyên liệu thức ăn nhập khẩu."
            },
            {
                "name": "Bất động sản & Điện máy gia dụng",
                "rev_share_pct": 2.5,
                "gross_profit_share_pct": 3.5,
                "gross_margin_pct": 20.0,
                "role": "Tiềm năng dài hạn",
                "strategic_role": "FUTURE_BET",
                "status": "Tích lũy",
                "highlights": "Hệ thống BĐS Khu công nghiệp (Yên Mỹ, Phố Nối A) tỷ lệ lấp đầy cao; mở rộng sản xuất container và điện lạnh.",
                "risks": "Quy mô đóng góp hiện tại còn nhỏ so với mảng thép."
            }
        ]
    },
    "FPT": {
        "company_name": "Công ty Cổ phần FPT",
        "business_model_summary": "Tập đoàn công nghệ hàng đầu Việt Nam hoạt động theo kiềng ba chân vững chắc: Xuất khẩu phần mềm toàn cầu, Hạ tầng viễn thông internet cáp quang, và Hệ sinh thái Giáo dục đào tạo.",
        "segments": [
            {
                "name": "Khối Công nghệ & Xuất khẩu phần mềm (Global IT)",
                "rev_share_pct": 60.5,
                "gross_profit_share_pct": 52.0,
                "gross_margin_pct": 22.0,
                "role": "Ngựa ô tăng trưởng toàn cầu",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Tăng trưởng cao (>25%/năm)",
                "highlights": "Doanh thu dịch vụ CNTT nước ngoài vượt 1 tỷ USD; mở rộng mạnh tại Nhật Bản, Mỹ, EU, APAC và mảng AI/bán dẫn.",
                "risks": "Biến động tỷ giá JPY (Yên Nhật) và cắt giảm ngân sách IT tại các tập đoàn phương Tây."
            },
            {
                "name": "Khối Viễn thông (FPT Telecom, PayTV, Data Center)",
                "rev_share_pct": 30.5,
                "gross_profit_share_pct": 33.0,
                "gross_margin_pct": 38.0,
                "role": "Con bò sữa dòng tiền (Cash Cow)",
                "strategic_role": "CASH_COW",
                "status": "Ổn định dòng tiền",
                "highlights": "Cung cấp internet băng rộng và trung tâm dữ liệu (Data Center), dòng tiền trả trước dồi dào, biên lợi nhuận cao.",
                "risks": "Thị trường băng rộng nội địa bão hòa, cạnh tranh khốc liệt với Viettel và VNPT."
            },
            {
                "name": "Khối Giáo dục & Đầu tư (Đại học, Cao đẳng FPT)",
                "rev_share_pct": 9.0,
                "gross_profit_share_pct": 15.0,
                "gross_margin_pct": 42.0,
                "role": "Nguồn nhân lực & Biên lợi nhuận cao",
                "strategic_role": "CORE_MOAT",
                "status": "Tăng trưởng vượt bậc",
                "highlights": "Số lượng người học tăng trưởng nhanh, biên lợi nhuận gộp trên 40%, tạo nguồn cung nhân lực kỹ sư CNTT trực tiếp cho tập đoàn.",
                "risks": "Chi phí đầu tư cơ sở hạ tầng trường học mới (CapEx)."
            }
        ]
    },
    "MWG": {
        "company_name": "Công ty Cổ phần Đầu tư Thế Giới Di Động",
        "business_model_summary": "Bán lẻ chuỗi đa mô hình: Thế Giới Di Động (ICT), Điện Máy Xanh (CE), Bách Hóa Xanh (thực phẩm thiết yếu), An Khang (dược phẩm) và EraBlue (Indonesia).",
        "segments": [
            {
                "name": "Thế Giới Di Động & Điện Máy Xanh",
                "rev_share_pct": 68.0,
                "gross_profit_share_pct": 78.0,
                "gross_margin_pct": 23.5,
                "role": "Trụ cột lợi nhuận & Dòng tiền",
                "strategic_role": "CASH_COW",
                "status": "Tái cấu trúc tối ưu hóa",
                "highlights": "Thị phần số 1 Việt Nam về điện thoại và điện máy; đóng các cửa hàng kém hiệu quả để tối đa hóa biên lãi ròng.",
                "risks": "Thị trường ICT bão hòa, chu kỳ đổi máy kéo dài."
            },
            {
                "name": "Chuỗi Bách Hóa Xanh (Bán lẻ thực phẩm & FMCG)",
                "rev_share_pct": 29.0,
                "gross_profit_share_pct": 20.0,
                "gross_margin_pct": 26.0,
                "role": "Ngôi sao tăng trưởng tương lai",
                "strategic_role": "GROWTH_CATALYST",
                "status": "Đã có lãi & Chuẩn bị mở rộng",
                "highlights": "Doanh thu/cửa hàng đạt trên 1.8 - 2.0 tỷ/tháng, chính thức đem lại lợi nhuận hoạt động dương từ 2024-2025.",
                "risks": "Quản lý hao hụt hàng tươi sống và chi phí logistics."
            },
            {
                "name": "Chuỗi Nhà thuốc An Khang & EraBlue (Indonesia)",
                "rev_share_pct": 3.0,
                "gross_profit_share_pct": 2.0,
                "gross_margin_pct": 18.0,
                "role": "Thử nghiệm tiềm năng",
                "strategic_role": "FUTURE_BET",
                "status": "Thu hẹp để tìm điểm hòa vốn",
                "highlights": "EraBlue tại Indonesia đang nhân rộng nhanh với mô hình hiệu quả.",
                "risks": "An Khang đang chịu cạnh tranh lớn từ Long Châu."
            }
        ]
    }
}


def analyze_company_segments(symbol: str, company_name: str = "", sector: str = "GENERAL") -> Dict[str, Any]:
    """
    Bóc tách mô hình kinh doanh cốt lõi (Core Business) và phân tích cơ cấu phân khúc (Segments)
    trả về thông tin chi tiết % Doanh thu, % Lợi nhuận gộp, biên lãi từng mảng và vai trò chiến lược.
    """
    sym = symbol.upper().strip()

    # 1. Nếu có trong hồ sơ chuyên sâu đã xác thực
    if sym in KNOWN_SEGMENT_PROFILES:
        profile = KNOWN_SEGMENT_PROFILES[sym]
        return {
            "has_detailed_segments": True,
            "symbol": sym,
            "company_name": profile.get("company_name", company_name),
            "business_model_summary": profile.get("business_model_summary", ""),
            "segments": profile.get("segments", [])
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
        "segments": default_segments
    }
