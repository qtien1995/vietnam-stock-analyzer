"""
Module Phân tích Vĩ mô & Chu kỳ Ngành Chuyên sâu (Macro & Sector Cycle Engine)
Phục vụ phân tích Top-Down từ Vĩ mô nền kinh tế -> Chu kỳ ngành -> Doanh nghiệp cụ thể.

Đặc tính:
1. Phân loại ngành linh hoạt cho TOÀN BỘ 1.500+ mã trên HOSE, HNX, UPCoM (không fix cứng danh sách mã).
2. Ma trận Vĩ mô & Động lực đặc thù theo từng nhóm ngành:
   - Bất động sản Khu công nghiệp (FDI, Giá thuê đất, Tỷ lệ lấp đầy, Của để dành doanh thu chưa thực hiện...)
   - Bán lẻ & Tiêu dùng (Tổng mức bán lẻ, SSSG, Sức mua nội địa, CPI, Chuỗi mở rộng...)
   - Ngân hàng (Hạn mức tín dụng NHNN, Lãi suất, NIM, CASA, Nợ xấu NPL...)
   - Bất động sản Dân dụng (Lãi suất cho vay, Tiến độ pháp lý, Hàng tồn kho dự án, Trái phiếu...)
   - Thép & Vật liệu xây dựng (Đầu tư công, Giá HRC thế giới, Thuế CBPG, Công suất...)
   - Xuất khẩu: Thủy sản, Dệt may (Tỷ giá USD/VND, Lạm phát thị trường xuất khẩu, Cước vận tải...)
   - Hóa chất & Phân bón (Giá Phốt pho vàng, Urê thế giới, Nhu cầu nông nghiệp...)
   - Dầu khí & Năng lượng (Giá dầu Brent, Quy hoạch Điện VIII, Thủy văn El Nino/La Nina, Lô B...)
   - Chứng khoán (Thanh khoản thị trường, Dư nợ Margin, Nâng hạng FTSE/KRX...)
   - Công nghệ (Chi tiêu IT toàn cầu, Chuyển đổi số, AI...)
3. Định vị Pha Chu kỳ Ngành (Đáy tích lũy, Tăng tốc mở rộng, Đỉnh chu kỳ, Suy thoái).
4. Tính toán Điểm số Hỗ trợ Vĩ mô (Macro Tailwind Score: 0 - 100).
"""

from typing import Dict, Any, List, Optional


# =====================================================================
# 1. HỆ THỐNG THÔNG SỐ VĨ MÔ VIỆT NAM HIỆN HÀNH (MACRO CONTEXT)
# =====================================================================
CURRENT_VIETNAM_MACRO = {
    "monetary_policy": "Nới lỏng thận trọng / Duy trì lãi suất thấp hỗ trợ tăng trưởng",
    "sbv_refinancing_rate_pct": 4.5,           # Lãi suất tái cấp vốn NHNN
    "avg_12m_deposit_rate_pct": 5.2,           # Lãi suất huy động 12T bình quân
    "credit_growth_target_pct": 15.0,          # Mục tiêu tăng trưởng tín dụng
    "usd_vnd_trend": "Áp lực tăng giá USD / VND mất giá nhẹ (Hỗ trợ Xuất khẩu, Bất lợi Nợ USD)",
    "public_investment_status": "Giải ngân quyết liệt các đại dự án cao tốc Bắc-Nam & Sân bay Long Thành",
    "fdi_trend": "Tăng trưởng tích cực, hưởng lợi làn sóng dịch chuyển chuỗi cung ứng toàn cầu (China+1)",
    "market_liquidity_state": "Trung bình - Sôi động (18.000 - 25.000 tỷ/phiên)",
    "krx_ftse_upgrade": "Đang hoàn thiện cơ chế Non-prefunding để đáp ứng tiêu chuẩn nâng hạng FTSE Russell"
}


# =====================================================================
# 2. MA TRẬN PHÂN LOẠI NGÀNH ĐỘNG CHO TOÀN BỘ CỔ PHIẾU
# =====================================================================
KNOWN_TICKER_SECTORS = {
    # BĐS Khu công nghiệp
    "IDC": "INDUSTRIAL_REAL_ESTATE", "KBC": "INDUSTRIAL_REAL_ESTATE", "SZC": "INDUSTRIAL_REAL_ESTATE",
    "BCM": "INDUSTRIAL_REAL_ESTATE", "SIP": "INDUSTRIAL_REAL_ESTATE", "VGC": "INDUSTRIAL_REAL_ESTATE",
    "NTC": "INDUSTRIAL_REAL_ESTATE", "TIP": "INDUSTRIAL_REAL_ESTATE", "LHG": "INDUSTRIAL_REAL_ESTATE",
    "D2D": "INDUSTRIAL_REAL_ESTATE", "SLS": "INDUSTRIAL_REAL_ESTATE", "PHR": "INDUSTRIAL_REAL_ESTATE",
    
    # Bán lẻ & Tiêu dùng
    "MWG": "RETAIL_CONSUMER", "FRT": "RETAIL_CONSUMER", "PNJ": "RETAIL_CONSUMER",
    "DGW": "RETAIL_CONSUMER", "MSN": "RETAIL_CONSUMER", "VNM": "RETAIL_CONSUMER",
    "SAB": "RETAIL_CONSUMER", "KDC": "RETAIL_CONSUMER", "MCH": "RETAIL_CONSUMER",
    "BAF": "RETAIL_CONSUMER", "DBC": "RETAIL_CONSUMER", "HAG": "RETAIL_CONSUMER",

    # Ngân hàng
    "VCB": "BANK", "BID": "BANK", "CTG": "BANK", "TCB": "BANK", "MBB": "BANK",
    "ACB": "BANK", "VPB": "BANK", "STB": "BANK", "HDB": "BANK", "LPB": "BANK",
    "SHB": "BANK", "VIB": "BANK", "TPB": "BANK", "MSB": "BANK", "OCB": "BANK",
    "EIB": "BANK", "NAB": "BANK", "BVB": "BANK", "BAB": "BANK", "SSB": "BANK",

    # Chứng khoán
    "SSI": "SECURITIES", "VND": "SECURITIES", "VCI": "SECURITIES", "HCM": "SECURITIES",
    "MBS": "SECURITIES", "SHS": "SECURITIES", "FTS": "SECURITIES", "BSI": "SECURITIES",
    "CTS": "SECURITIES", "AGR": "SECURITIES", "VDS": "SECURITIES", "ORS": "SECURITIES",
    
    # Thép & Vật liệu xây dựng
    "HPG": "STEEL_MATERIALS", "HSG": "STEEL_MATERIALS", "NKG": "STEEL_MATERIALS",
    "VGS": "STEEL_MATERIALS", "TLH": "STEEL_MATERIALS", "HT1": "STEEL_MATERIALS",
    "BCC": "STEEL_MATERIALS", "BMP": "STEEL_MATERIALS", "NTP": "STEEL_MATERIALS",

    # BĐS Dân dụng & Nhà ở
    "VHM": "RESIDENTIAL_REAL_ESTATE", "VIC": "RESIDENTIAL_REAL_ESTATE", "NVL": "RESIDENTIAL_REAL_ESTATE",
    "KDH": "RESIDENTIAL_REAL_ESTATE", "NLG": "RESIDENTIAL_REAL_ESTATE", "PDR": "RESIDENTIAL_REAL_ESTATE",
    "DXG": "RESIDENTIAL_REAL_ESTATE", "DIG": "RESIDENTIAL_REAL_ESTATE", "CEO": "RESIDENTIAL_REAL_ESTATE",
    "TCH": "RESIDENTIAL_REAL_ESTATE", "HDG": "RESIDENTIAL_REAL_ESTATE", "VRE": "RESIDENTIAL_REAL_ESTATE",

    # Xuất khẩu: Thủy sản, Dệt may
    "VHC": "EXPORT_SEAFOOD_TEXTILE", "ANV": "EXPORT_SEAFOOD_TEXTILE", "FMC": "EXPORT_SEAFOOD_TEXTILE",
    "IDI": "EXPORT_SEAFOOD_TEXTILE", "TNG": "EXPORT_SEAFOOD_TEXTILE", "MSH": "EXPORT_SEAFOOD_TEXTILE",
    "GIL": "EXPORT_SEAFOOD_TEXTILE", "TCM": "EXPORT_SEAFOOD_TEXTILE", "STK": "EXPORT_SEAFOOD_TEXTILE",

    # Hóa chất & Phân bón
    "DGC": "CHEMICAL_FERTILIZER", "DCM": "CHEMICAL_FERTILIZER", "DPM": "CHEMICAL_FERTILIZER",
    "BFC": "CHEMICAL_FERTILIZER", "CSV": "CHEMICAL_FERTILIZER", "LAS": "CHEMICAL_FERTILIZER",

    # Dầu khí & Năng lượng
    "GAS": "OIL_GAS_ENERGY", "PVD": "OIL_GAS_ENERGY", "PVS": "OIL_GAS_ENERGY",
    "BSR": "OIL_GAS_ENERGY", "PLX": "OIL_GAS_ENERGY", "PVB": "OIL_GAS_ENERGY",
    "PVC": "OIL_GAS_ENERGY", "POW": "OIL_GAS_ENERGY", "REE": "OIL_GAS_ENERGY",
    "NT2": "OIL_GAS_ENERGY", "GEG": "OIL_GAS_ENERGY", "PC1": "OIL_GAS_ENERGY",

    # Hạ tầng & Đầu tư công
    "DPG": "PUBLIC_INVEST_INFRA", "VCG": "PUBLIC_INVEST_INFRA", "HHV": "PUBLIC_INVEST_INFRA",
    "C4G": "PUBLIC_INVEST_INFRA", "LCG": "PUBLIC_INVEST_INFRA", "FCN": "PUBLIC_INVEST_INFRA",
    "CII": "PUBLIC_INVEST_INFRA", "CTD": "PUBLIC_INVEST_INFRA", "HBC": "PUBLIC_INVEST_INFRA",

    # Cảng biển & Logistics
    "GMD": "LOGISTICS_PORT", "HAH": "LOGISTICS_PORT", "VSC": "LOGISTICS_PORT",
    "PVT": "LOGISTICS_PORT", "VOS": "LOGISTICS_PORT", "DVP": "LOGISTICS_PORT",

    # Công nghệ
    "FPT": "TECH_TELECOM", "CMG": "TECH_TELECOM", "FOX": "TECH_TELECOM", "ELC": "TECH_TELECOM"
}


def classify_sector(symbol: str, overview_data: Optional[Dict[str, Any]] = None) -> str:
    """
    Phân loại ngành tự động cho BẤT KỲ cổ phiếu nào trên thị trường:
    1. Kiểm tra bảng tra cứu nhanh.
    2. Nếu không có, quét qua tên công ty, hồ sơ kinh doanh (company_profile) và sector từ vnstock.
    """
    sym = symbol.upper().strip()
    if sym in KNOWN_TICKER_SECTORS:
        return KNOWN_TICKER_SECTORS[sym]

    if not overview_data:
        return "GENERAL"

    text = (
        str(overview_data.get("organ_name", "")) + " " +
        str(overview_data.get("company_profile", "")) + " " +
        str(overview_data.get("sector", ""))
    ).lower()

    # Nhận diện BĐS KCN
    if any(k in text for k in ["khu công nghiệp", "kcn", "industrial park", "industrial zone", "hạ tầng khu công nghiệp"]):
        return "INDUSTRIAL_REAL_ESTATE"

    # Nhận diện Ngân hàng
    if any(k in text for k in ["ngân hàng", "bank", "banking"]):
        return "BANK"

    # Nhận diện Chứng khoán
    if any(k in text for k in ["chứng khoán", "securities", "môi giới chứng khoán"]):
        return "SECURITIES"

    # Nhận diện Bán lẻ & Tiêu dùng
    if any(k in text for k in ["bán lẻ", "siêu thị", "chuỗi cửa hàng", "tiêu dùng", "bánh kẹo", "sữa", "nước giải khát", "retail", "consumer"]):
        return "RETAIL_CONSUMER"

    # Nhận diện Thép & Kim loại
    if any(k in text for k in ["thép", "tôn mạ", "ống thép", "gang thép", "luyện kim", "steel"]):
        return "STEEL_MATERIALS"

    # Nhận diện BĐS Dân dụng
    if any(k in text for k in ["bất động sản", "đô thị", "nhà ở", "chung cư", "địa ốc", "real estate"]) and "khu công nghiệp" not in text:
        return "RESIDENTIAL_REAL_ESTATE"

    # Nhận diện Xuất khẩu Thủy sản, Dệt may
    if any(k in text for k in ["thủy sản", "cá tra", "tôm", "dệt may", "may mặc", "sợi", "garment", "seafood", "textile"]):
        return "EXPORT_SEAFOOD_TEXTILE"

    # Nhận diện Hóa chất, Phân bón
    if any(k in text for k in ["phân bón", "hóa chất", "đạm", "phốt pho", "fertilizer", "chemical"]):
        return "CHEMICAL_FERTILIZER"

    # Nhận diện Dầu khí, Điện
    if any(k in text for k in ["dầu khí", "khí đốt", "xăng dầu", "thủy điện", "nhiệt điện", "điện gió", "năng lượng"]):
        return "OIL_GAS_ENERGY"

    # Nhận diện Đầu tư công, Xây lắp
    if any(k in text for k in ["xây dựng", "xây lắp", "hạ tầng giao thông", "cầu đường", "nhà thầu", "construction"]):
        return "PUBLIC_INVEST_INFRA"

    # Nhận diện Cảng biển, Vận tải
    if any(k in text for k in ["cảng biển", "vận tải biển", "logistics", "kho bãi", "tàu biển", "port"]):
        return "LOGISTICS_PORT"

    # Nhận diện Công nghệ
    if any(k in text for k in ["công nghệ thông tin", "phần mềm", "viễn thông", "chuyển đổi số", "technology", "software"]):
        return "TECH_TELECOM"

    return "GENERAL"


# =====================================================================
# 3. KHO DỮ LIỆU ĐẶC THÙ NGÀNH & CHU KỲ (SECTOR DEEP-DIVE PROFILES)
# =====================================================================
SECTOR_PROFILES: Dict[str, Dict[str, Any]] = {
    "INDUSTRIAL_REAL_ESTATE": {
        "sector_name": "Bất động sản Khu công nghiệp",
        "cycle_phase": "Tăng tốc mở rộng (Mid-Cycle Expansion)",
        "phase_description": "Hưởng lợi từ dòng vốn FDI thế hệ mới dịch chuyển vào công nghệ bán dẫn & điện tử; giá thuê đất giữ đà tăng 8-12%/năm tại các thủ phủ công nghiệp.",
        "tailwind_score": 85,
        "sentiment": "RẤT TÍCH CỰC (STRONG TAILWIND)",
        "macro_drivers": [
            "Dòng vốn FDI giải ngân thực tế liên tục lập đỉnh mới tại Việt Nam.",
            "Nâng cấp quan hệ đối tác chiến lược toàn diện với Mỹ, Hàn Quốc, Nhật Bản thúc đẩy các đại bàng công nghệ (Nvidia, Foxconn, Amkor, Hana Micron) mở rộng nhà máy.",
            "Giá thuê đất KCN bình quân tăng trưởng bền vững: Miền Bắc ~135-145 USD/m2/chu kỳ, Miền Nam ~160-180 USD/m2/chu kỳ.",
            "Hạ tầng kết nối (các tuyến cao tốc và cảng nước sâu Cái Mép, Lạch Huyện) rút ngắn mạnh thời gian logistics."
        ],
        "key_metrics_to_watch": [
            "Quỹ đất thương phẩm sẵn sàng cho thuê (Net Leasable Land Bank) có pháp lý sạch.",
            "Tỷ lệ lấp đầy (Occupancy Rate) hiện hữu.",
            "Doanh thu chưa thực hiện dài hạn (Unearned Revenue) — thước đo 'Của để dành' thu tiền 1 lần từ khách thuê.",
            "Tiến độ đền bù giải phóng mặt bằng và chi phí tiền sử dụng đất mới theo Luật Đất đai."
        ],
        "key_risks": [
            "Rủi ro thiếu hụt nguồn cung điện ổn định vào mùa cao điểm nắng nóng.",
            "Thuế tối thiểu toàn cầu (Global Minimum Tax 15%) có thể làm giảm bớt tính hấp dẫn của các gói ưu đãi thuế truyền thống nếu không có chính sách hỗ trợ đầu tư bù đắp kịp thời."
        ]
    },

    "RETAIL_CONSUMER": {
        "sector_name": "Bán lẻ & Tiêu dùng Nội địa",
        "cycle_phase": "Phục hồi tăng tốc (Recovery to Expansion)",
        "phase_description": "Sức mua tiêu dùng hồi phục rõ nét; mô hình tái cấu trúc tinh gọn mạng lưới cửa hàng bắt đầu phát huy đòn bẩy hoạt động, biên lợi nhuận cải thiện mạnh.",
        "tailwind_score": 78,
        "sentiment": "TÍCH CỰC (TAILWIND)",
        "macro_drivers": [
            "Tổng mức bán lẻ hàng hóa và doanh thu dịch vụ tiêu dùng duy trì đà tăng trưởng 8.5 - 9.5% YoY.",
            "Chính sách hỗ trợ tài khóa tiếp tục giảm 2% thuế VAT kích thích sức mua người dân.",
            "Lãi suất cho vay duy trì thấp hỗ trợ tín dụng tiêu dùng hồi phục trở lại.",
            "Thu nhập khả dụng và tầng lớp trung lưu gia tăng thúc đẩy xu hướng tiêu dùng hiện đại (Modern Trade)."
        ],
        "key_metrics_to_watch": [
            "Tăng trưởng doanh số trên cùng một cửa hàng (Same-Store Sales Growth - SSSG).",
            "Biên lợi nhuận gộp từng chuỗi bán lẻ (ICT/CE, Bách hóa thực phẩm, Dược phẩm, Trang sức vàng).",
            "Tốc độ tối ưu hóa chi phí vận hành (SG&A / Doanh thu).",
            "Mùa vụ tiêu dùng cao điểm (Quý 3 tựu trường, Quý 4 lễ hội & Quý 1 Tết Nguyên Đán)."
        ],
        "key_risks": [
            "Cạnh tranh gay gắt từ thương mại điện tử (E-commerce / TikTok Shop).",
            "Lạm phát chi phí mặt bằng tại các vị trí đắc địa đô thị lớn."
        ]
    },

    "BANK": {
        "sector_name": "Ngân hàng Thương mại",
        "cycle_phase": "Phục hồi chất lượng tài sản (Quality Rebound)",
        "phase_description": "Tăng trưởng tín dụng bứt phá trong nửa cuối năm; biên lãi ròng (NIM) chạm đáy và bắt đầu hồi phục khi chi phí vốn huy động giá rẻ phát huy tác dụng.",
        "tailwind_score": 80,
        "sentiment": "TÍCH CỰC (TAILWIND)",
        "macro_drivers": [
            "Mục tiêu tăng trưởng tín dụng toàn ngành 15% được giao sớm và linh hoạt.",
            "Môi trường lãi suất thấp giúp giảm chi phí vốn đầu vào (COF), tiền gửi CASA tăng trưởng trở lại.",
            "Thị trường Bất động sản và hoạt động sản xuất kinh doanh ấm dần giúp giảm bớt áp lực nợ xấu phát sinh mới.",
            "Thông tư hỗ trợ cơ cấu nợ giữ vững bộ đệm thanh khoản cho hệ thống."
        ],
        "key_metrics_to_watch": [
            "Biên lãi thuần (NIM - Net Interest Margin).",
            "Tỷ lệ tiền gửi không kỳ hạn (CASA) — lợi thế vốn rẻ.",
            "Tỷ lệ nợ xấu nội bảng (NPL) và Tỷ lệ bao phủ nợ xấu (LLR).",
            "Hệ số an toàn vốn (CAR theo Basel II/III)."
        ],
        "key_risks": [
            "Áp lực trích lập dự phòng rủi ro tín dụng nếu nợ nhóm 2 và nợ tái cơ cấu chuyển nhóm.",
            "Thị trường trái phiếu doanh nghiệp xử lý chậm có thể gây tắc nghẽn dòng tiền ở một số ngân hàng liên kết."
        ]
    },

    "SECURITIES": {
        "sector_name": "Chứng khoán & Dịch vụ Tài chính",
        "cycle_phase": "Bùng nổ chu kỳ thanh khoản & Nâng hạng",
        "phase_description": "Hưởng lợi kép từ môi trường lãi suất tiền gửi thấp đẩy dòng tiền cá nhân vào kênh đầu tư, cùng kỳ vọng lịch sử về hệ thống KRX và nâng hạng thị trường FTSE Russell.",
        "tailwind_score": 82,
        "sentiment": "RẤT TÍCH CỰC (STRONG TAILWIND)",
        "macro_drivers": [
            "Lãi suất tiết kiệm thấp kỷ lục tạo hiệu ứng FOMO dịch chuyển dòng tiền sang thị trường chứng khoán.",
            "Thanh khoản bình quân toàn thị trường duy trì ở mức cao (tăng 25-40% so với cùng kỳ).",
            "Cơ chế giao dịch không ký quỹ 100% bằng tiền (Non-prefunding) cho nhà đầu tư ngoại mở đường cho quyết định nâng hạng lên thị trường Mới nổi thứ cấp (Secondary Emerging Market).",
            "Quy mô tài khoản mở mới cá nhân duy trì hàng trăm nghìn tài khoản mỗi tháng."
        ],
        "key_metrics_to_watch": [
            "Giá trị giao dịch bình quân phiên (ADTV - Average Daily Trading Value).",
            "Dư nợ cho vay ký quỹ (Margin Loans) và Tỷ lệ Dư nợ Margin / Vốn chủ sở hữu.",
            "Hiệu quả danh mục tự doanh (FVTPL / AFS) trong các nhịp sóng ngành.",
            "Thị phần môi giới HOSE/HNX."
        ],
        "key_risks": [
            "Biến động thị trường ngắn hạn điều chỉnh mạnh có thể gây giảm giá trị danh mục tự doanh.",
            "Cạnh tranh gay gắt về phí giao dịch (Zero-Fee Wars) ăn mòn biên lợi nhuận môi giới thuần."
        ]
    },

    "STEEL_MATERIALS": {
        "sector_name": "Thép & Vật liệu Xây dựng",
        "cycle_phase": "Vượt đáy phục hồi (Early to Mid-Cycle)",
        "phase_description": "Ngành thép đã vượt qua đáy xấu nhất của chu kỳ suy thoái; sản lượng tiêu thụ nội địa tăng trưởng nhờ đầu tư công và BĐS, giá bán HRC bước vào pha hồi phục.",
        "tailwind_score": 75,
        "sentiment": "TÍCH CỰC (TAILWIND)",
        "macro_drivers": [
            "Đẩy mạnh giải ngân vốn đầu tư công các dự án hạ tầng lớn tiêu thụ lượng thép khổng lồ.",
            "Việt Nam tiến hành điều tra áp thuế chống bán phá giá (AD) đối với thép cán nóng HRC nhập khẩu từ Trung Quốc/Ấn Độ, bảo hộ thị phần nội địa.",
            "Thị trường BĐS dân dụng phục hồi dần tháo gỡ thanh khoản cho thép xây dựng.",
            "Biên lợi nhuận gộp hồi phục nhờ giá nguyên liệu than cốc và quặng sắt hạ nhiệt."
        ],
        "key_metrics_to_watch": [
            "Chênh lệch giá bán HRC thành phẩm so với nguyên liệu quặng sắt & than cốc (Steel Crack Spread).",
            "Sản lượng bán hàng thép xây dựng, HRC và tôn mạ hàng tháng.",
            "Tiến độ giải ngân các đại dự án nâng công suất (như Khu liên hợp Dung Quất 2).",
            "Diễn biến thị trường bất động sản Trung Quốc tác động đến áp lực xuất khẩu thép giá rẻ."
        ],
        "key_risks": [
            "Nguồn cung thép giá rẻ từ Trung Quốc tràn vào nếu hàng rào phòng vệ thương mại chậm thực thi.",
            "Chi phí điện và các rào cản xanh (CBAM của châu Âu) trong xuất khẩu dài hạn."
        ]
    },

    "RESIDENTIAL_REAL_ESTATE": {
        "sector_name": "Bất động sản Dân dụng & Nhà ở",
        "cycle_phase": "Phân hóa gỡ khó (Tích lũy đáy chu kỳ)",
        "phase_description": "Bộ ba Luật Đất đai, Luật Nhà ở, Luật Kinh doanh BĐS mới có hiệu lực tạo hành lang pháp lý minh bạch; doanh nghiệp có quỹ đất sạch và dự án thực bước vào chu kỳ mở bán mới.",
        "tailwind_score": 68,
        "sentiment": "PHÂN HÓA (NEUTRAL TO SELECTIVE TAILWIND)",
        "macro_drivers": [
            "Lãi suất cho vay mua nhà đang ở mức cạnh tranh nhất trong nhiều năm (5-7%/năm ưu đãi).",
            "Nhu cầu ở thực tại các đô thị lớn (Hà Nội, TP.HCM) duy trì rất cao trong bối cảnh nguồn cung căn hộ khan hiếm.",
            "Hạ tầng giao thông kết nối các vùng vệ tinh mở rộng biên độ phát triển dự án mới.",
            "Chính phủ tích cực tháo gỡ điểm nghẽn pháp lý cho từng dự án cụ thể."
        ],
        "key_metrics_to_watch": [
            "Tiền người mua trả trước ngắn hạn (Khách hàng cọc tiền mua nhà) — chỉ báo doanh thu bàn giao tương lai.",
            "Hàng tồn kho dự án đã hoàn thành pháp lý vs Hàng tồn kho dự án dở dang chưa đền bù xong.",
            "Tỷ lệ Đòn bẩy nợ vay / Vốn CSH và áp lực đáo hạn trái phiếu doanh nghiệp riêng lẻ.",
            "Tiến độ tính tiền sử dụng đất tại các dự án trọng điểm."
        ],
        "key_risks": [
            "Chi phí tiền sử dụng đất tính theo bảng giá đất mới dự kiến tăng cao làm đội giá vốn dự án.",
            "Các doanh nghiệp từng phát hành trái phiếu dàn trải vẫn chịu áp lực tái cấu trúc tài chính lớn."
        ]
    },

    "EXPORT_SEAFOOD_TEXTILE": {
        "sector_name": "Xuất khẩu: Thủy sản, Dệt may & Gỗ",
        "cycle_phase": "Hồi phục đơn hàng (Cyclical Rebound)",
        "phase_description": "Tồn kho tại các thị trường tiêu thụ lớn (Mỹ, EU) đã về mức an toàn, đơn hàng ký mới quay trở lại; tỷ giá USD/VND neo cao mang lại lợi thế doanh thu quy đổi.",
        "tailwind_score": 74,
        "sentiment": "TÍCH CỰC (TAILWIND)",
        "macro_drivers": [
            "Đồng USD neo cao hỗ trợ gia tăng biên lợi nhuận ròng cho các doanh nghiệp thu ngoại tệ.",
            "Chu kỳ xả hàng tồn kho của các nhà bán lẻ quốc tế (Walmart, Target...) đã kết thúc, bắt đầu mùa đặt hàng mới.",
            "Các hiệp định thương mại tự do (CPTPP, EVFTA) duy trì thuế quan ưu đãi 0%.",
            "Lạm phát tại Mỹ và châu Âu hạ nhiệt kích thích sức mua người tiêu dùng."
        ],
        "key_metrics_to_watch": [
            "Giá xuất khẩu bình quân (Average Selling Price - ASP) cá tra, tôm, sợi may mặc.",
            "Giá cước vận tải biển container (Drewry World Container Index) — chi phí logistics xuất khẩu.",
            "Các phán quyết về thuế chống bán phá giá định kỳ (POR của Bộ Thương mại Mỹ - DOC).",
            "Tỷ lệ đáp ứng chứng chỉ xanh, truy xuất nguồn gốc (ESG, chứng chỉ cá ngừ, bông sạch)."
        ],
        "key_risks": [
            "Biến động cước tàu biển tăng cao do căng thẳng địa chính trị eo biển Biển Đỏ/Trung Đông.",
            "Rủi ro thẻ vàng IUU đối với hải sản khai thác tự nhiên."
        ]
    },

    "CHEMICAL_FERTILIZER": {
        "sector_name": "Hóa chất cơ bản & Phân bón",
        "cycle_phase": "Tích lũy ổn định (Mid-Cycle)",
        "phase_description": "Giá các loại hóa chất công nghiệp cốt lõi (Phốt pho vàng P4, Xút, Axit) và Phân bón Urê duy trì ở mức cân bằng; nhu cầu bán dẫn và nông nghiệp toàn cầu giữ vững đà tiêu thụ.",
        "tailwind_score": 72,
        "sentiment": "TÍCH CỰC (TAILWIND)",
        "macro_drivers": [
            "Làn sóng sản xuất chất bán dẫn và pin xe điện thế giới giữ nhu cầu Phốt pho vàng P4 tinh khiết ở mức cao.",
            "Chính sách hạn chế xuất khẩu phân bón từ Trung Quốc và Nga giúp giữ vững mặt bằng giá Urê, NPK khu vực.",
            "Luật Thuế GTGT sửa đổi dự kiến đưa phân bón vào diện chịu thuế VAT 5% giúp doanh nghiệp được hoàn thuế đầu vào lớn.",
            "Biên lợi nhuận gộp hưởng lợi nhờ chi phí năng lượng và nguyên liệu đầu vào ổn định."
        ],
        "key_metrics_to_watch": [
            "Giá bán Phốt pho vàng P4, Urê thế giới và giá Xút NaOH.",
            "Khối lượng tiền mặt ròng và tỷ lệ chi trả cổ tức tiền mặt cao.",
            "Tiến độ cấp phép mở rộng khai thác các mỏ quặng Apatit (với phân bón/hóa chất)."
        ],
        "key_risks": [
            "Trung Quốc nới lỏng hạn ngạch xuất khẩu phân bón có thể gây áp lực giảm giá ngắn hạn.",
            "Quy định nghiêm ngặt về khí thải và môi trường trong chế biến hóa chất."
        ]
    },

    "OIL_GAS_ENERGY": {
        "sector_name": "Dầu khí & Năng lượng",
        "cycle_phase": "Chu kỳ đại dự án & Mở rộng hạ tầng năng lượng",
        "phase_description": "Ngành Dầu khí bước vào chu kỳ đầu tư lớn nhất 10 năm qua nhờ chuỗi đại dự án Lô B - Ô Môn và Lạc Đà Vàng; ngành Điện hưởng lợi từ khung pháp lý Quy hoạch Điện VIII.",
        "tailwind_score": 80,
        "sentiment": "RẤT TÍCH CỰC (STRONG TAILWIND)",
        "macro_drivers": [
            "Chuỗi dự án khí điện Lô B - Ô Môn (quy mô gần 12 tỷ USD) liên tục trao các gói thầu EPCI lớn.",
            "Giá dầu thô Brent duy trì ổn định trên 70-80 USD/thùng đảm bảo biên lợi nhuận cho hoạt động khoan và khai thác thượng nguồn.",
            "Giá thuê giàn khoan tự nâng (Jack-up Dayrate) khu vực Đông Nam Á neo ở mức cao kỷ lục.",
            "Cơ chế mua bán điện trực tiếp (DPPA) và khung giá điện tái tạo mới khơi thông dòng vốn đầu tư năng lượng."
        ],
        "key_metrics_to_watch": [
            "Giá dầu thô Brent & Giá khí thiên nhiên.",
            "Khối lượng công việc tồn đọng (Backlog) dịch vụ dầu khí thượng nguồn (PVS, PVD).",
            "Đơn giá cho thuê giàn khoan và hiệu suất sử dụng giàn khoan (Rig Utilization).",
            "Pha thời tiết thủy văn (La Nina mang lại mưa lớn cho Thủy điện, El Nino có lợi cho Nhiệt điện khí/than)."
        ],
        "key_risks": [
            "Tiến độ giải ngân và phê duyệt FID (Quyết định đầu tư cuối cùng) tại một số dự án lớn có thể bị chậm trễ thủ tục.",
            "Rủi ro biến động giá dầu thế giới do suy thoái kinh tế toàn cầu hoặc quyết định sản lượng OPEC+."
        ]
    },

    "PUBLIC_INVEST_INFRA": {
        "sector_name": "Đầu tư công & Hạ tầng Xây lắp",
        "cycle_phase": "Bùng nổ khối lượng công việc (Scale Expansion)",
        "phase_description": "Khối lượng công việc xây lắp hạ tầng lớn nhất trong lịch sử khi cả nước đồng loạt thi công hơn 3.000 km cao tốc, các vành đai đô thị và sân bay Long Thành.",
        "tailwind_score": 82,
        "sentiment": "RẤT TÍCH CỰC (STRONG TAILWIND)",
        "macro_drivers": [
            "Chính phủ chỉ đạo quyết liệt giải ngân >95% kế hoạch vốn đầu tư công hàng năm.",
            "Giao thầu các dự án hạ tầng nghìn tỷ cho các liên danh nhà thầu đầu ngành có năng lực thiết bị.",
            "Cơ chế mỏ vật liệu đặc thù được tháo gỡ giúp giảm bớt tình trạng khan hiếm cát đắp nền.",
            "Hạ tầng giao thông hoàn thiện tạo động lực kéo theo các dự án BĐS khu đô thị vệ tinh của chính các tập đoàn xây lắp."
        ],
        "key_metrics_to_watch": [
            "Giá trị hợp đồng chưa thực hiện (Backlog xây lắp) so với doanh thu hàng năm.",
            "Vòng quay khoản phải thu và dòng tiền thanh toán từ chủ đầu tư Ban quản lý dự án nhà nước.",
            "Biến động giá nguyên vật liệu xây dựng (cát, đá, xi măng, nhựa đường).",
            "Sở hữu các mỏ đá xây dựng phục vụ trực tiếp công trình."
        ],
        "key_risks": [
            "Biên lợi nhuận gộp mảng xây lắp mỏng (thường chỉ 6-9%), dễ bị ăn mòn nếu giá vật liệu biến động mạnh.",
            "Chậm thanh quyết toán công trình đọng vốn lớn tại các khoản phải thu."
        ]
    },

    "LOGISTICS_PORT": {
        "sector_name": "Cảng biển & Logistics",
        "cycle_phase": "Tăng trưởng theo luồng hàng hóa XNK",
        "phase_description": "Sản lượng hàng hóa thông qua cảng biển tăng trưởng mạnh theo đà phục hồi xuất nhập khẩu; giá cước bốc dỡ dịch vụ cảng biển được điều chỉnh tăng.",
        "tailwind_score": 76,
        "sentiment": "TÍCH CỰC (TAILWIND)",
        "macro_drivers": [
            "Kim ngạch xuất nhập khẩu của Việt Nam duy trì đà tăng trưởng 2 con số.",
            "Thông tư mới điều chỉnh tăng giá sàn dịch vụ xếp dỡ container tại cảng biển thêm 10%.",
            "Cụm cảng nước sâu Cái Mép - Thị Vải và Lạch Huyện đón các tuyến tàu mẹ đi thẳng Mỹ/châu Âu.",
            "Hiệu ứng gián đoạn chuỗi cung ứng biển đỏ giữ giá cước vận tải biển ở mức có lợi cho đội tàu quốc tế."
        ],
        "key_metrics_to_watch": [
            "Sản lượng hàng hóa thông qua cảng (Teus container / Tấn hàng rời).",
            "Tỷ lệ lấp đầy công suất các cảng nước sâu mới.",
            "Đơn giá cước cho thuê tàu định hạn (Time Charter Rates).",
            "Chi phí nhiên liệu dầu FO/MGO của đội tàu vận tải."
        ],
        "key_risks": [
            "Cạnh tranh hạ tầng nếu các dự án cảng mới bổ sung công suất vượt tốc độ tăng trưởng hàng hóa.",
            "Kinh tế toàn cầu chững lại làm giảm nhu cầu vận chuyển xuyên đại dương."
        ]
    },

    "TECH_TELECOM": {
        "sector_name": "Công nghệ Thông tin & Chuyển đổi số",
        "cycle_phase": "Tăng trưởng cơ cấu dài hạn (Long-term Compounder)",
        "phase_description": "Không phụ thuộc chu kỳ kinh tế ngắn hạn; hưởng lợi từ xu thế số hóa toàn cầu, hợp đồng xuất khẩu phần mềm quy mô lớn và làn sóng ứng dụng Trí tuệ nhân tạo (AI) / Bán dẫn.",
        "tailwind_score": 88,
        "sentiment": "RẤT TÍCH CỰC (SUPER TAILWIND)",
        "macro_drivers": [
            "Chi tiêu công nghệ thông tin toàn cầu (IT Spending) duy trì tốc độ tăng trưởng cao.",
            "Lợi thế cạnh tranh vượt trội về chi phí và nguồn nhân lực kỹ sư công nghệ dồi dào tại Việt Nam so với Ấn Độ/Đông Âu.",
            "Làn sóng AI bùng nổ kéo theo nhu cầu đầu tư Data Center, Cloud Computing và dịch vụ tích hợp hệ thống.",
            "Tỷ giá USD và Yên Nhật ổn định giúp tối ưu hóa doanh thu xuất khẩu thị trường Mỹ, Nhật, EU."
        ],
        "key_metrics_to_watch": [
            "Giá trị hợp đồng ký mới (Signed Revenue) và Doanh thu xuất khẩu phần mềm.",
            "Tăng trưởng doanh thu mảng Dịch vụ chuyển đổi số (Digital Transformation - DX).",
            "Biên lợi nhuận ròng và Tỷ suất sinh lời trên vốn (ROE > 20% bền vững).",
            "Quy mô tuyển dụng và năng suất nhân sự công nghệ."
        ],
        "key_risks": [
            "Chi phí lương nhân sự công nghệ chất lượng cao tăng nhanh.",
            "Rủi ro suy thoái kinh tế tại các thị trường trọng điểm khiến doanh nghiệp quốc tế trì hoãn các dự án IT lớn."
        ]
    },

    "GENERAL": {
        "sector_name": "Sản xuất & Kinh doanh Tổng hợp",
        "cycle_phase": "Bình thường theo chu kỳ kinh tế vĩ mô",
        "phase_description": "Tăng trưởng cùng tốc độ GDP toàn nền kinh tế, hưởng lợi từ lãi suất duy trì ở mức thấp và chính sách kích cầu tiêu dùng nội địa.",
        "tailwind_score": 70,
        "sentiment": "TRUNG TÍNH ĐẾN TÍCH CỰC",
        "macro_drivers": [
            "Tăng trưởng GDP cả nước duy trì mục tiêu 6.5 - 7.0%.",
            "Lãi suất cho vay sản xuất kinh doanh duy trì ở mức hấp dẫn.",
            "Lạm phát trong tầm kiểm soát."
        ],
        "key_metrics_to_watch": [
            "Doanh thu và Lợi nhuận sau thuế.",
            "Tỷ lệ nợ vay trên vốn chủ sở hữu.",
            "Vòng quay vốn lưu động và dòng tiền thuần từ hoạt động kinh doanh."
        ],
        "key_risks": [
            "Sức ép cạnh tranh từ hàng hóa nhập khẩu giá rẻ.",
            "Biến động giá nguyên nhiên vật liệu đầu vào."
        ]
    }
}


# =====================================================================
# 4. HÀM PHÂN TÍCH VĨ MÔ & CHU KỲ TỔNG HỢP CHO MỘT CỔ PHIẾU
# =====================================================================
def analyze_macro_and_sector_cycle(symbol: str, overview_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Phân tích toàn diện Vĩ mô & Chu kỳ Ngành cho 1 mã cổ phiếu:
    - Xác định ngành chính xác bằng bộ lọc động (Dynamic Classifier).
    - Trích xuất ma trận vĩ mô và động lực chu kỳ đặc thù.
    - Chấm điểm Macro Tailwind Score (0 - 100).
    - Cung cấp nhận định theo phong cách Ray Dalio & Howard Marks.
    """
    sym = symbol.upper().strip()
    sector_key = classify_sector(sym, overview_data)
    profile = SECTOR_PROFILES.get(sector_key, SECTOR_PROFILES["GENERAL"])

    # Đánh giá tương quan vĩ mô
    dalio_verdict = f"Theo chu kỳ vĩ mô hiện tại, ngành {profile['sector_name']} đang ở pha '{profile['cycle_phase']}'. "
    if profile["tailwind_score"] >= 80:
        dalio_verdict += f"Doanh nghiệp đang nhận được 'Gió xuôi chiều cực mạnh' (Tailwind) từ các yếu tố vĩ mô và dòng vốn tổ chức. Phù hợp để gia tăng tỷ trọng theo xu hướng lớn."
    elif profile["tailwind_score"] >= 70:
        dalio_verdict += f"Môi trường vĩ mô nhìn chung thuận lợi, hỗ trợ hoạt động kinh doanh cốt lõi mở rộng ổn định."
    else:
        dalio_verdict += f"Ngành đang ở pha phân hóa hoặc đáy phục hồi chậm. Cần sàng lọc khắt khe chất lượng tài sản và dòng tiền thật của từng mã cụ thể, tránh các mã đòn bẩy tài chính cao."

    marks_verdict = f"Howard Marks (Tâm lý Chu kỳ & Định giá): Khi ngành ở pha {profile['cycle_phase']}, "
    if "Đỉnh" in profile["cycle_phase"]:
        marks_verdict += "cần đặc biệt cảnh giác với bẫy P/E thấp. Thị trường thường định giá rẻ một cổ phiếu ở đỉnh chu kỳ khi lợi nhuận đạt mức tối đa trước khi đảo chiều suy giảm."
    elif "Đáy" in profile["cycle_phase"] or "Hồi phục" in profile["cycle_phase"]:
        marks_verdict += "đây là thời điểm rủi ro thực tế thấp hơn nhiều so với rủi ro tâm lý đám đông lo sợ. P/E có thể cao do lợi nhuận vừa qua đáy, nhưng định giá P/B và tài sản ròng là tấm đệm bảo vệ vốn tuyệt vời."
    else:
        marks_verdict += "thị trường đang phản ánh đúng tốc độ mở rộng. Hãy tập trung vào việc liệu dòng tiền kinh doanh (CFO) có chuyển hóa tương xứng với tốc độ tăng trưởng doanh thu hay không."

    return {
        "symbol": sym,
        "sector_key": sector_key,
        "sector_name": profile["sector_name"],
        "cycle_phase": profile["cycle_phase"],
        "phase_description": profile["phase_description"],
        "tailwind_score": profile["tailwind_score"],
        "sentiment": profile["sentiment"],
        "macro_drivers": profile["macro_drivers"],
        "key_metrics_to_watch": profile["key_metrics_to_watch"],
        "key_risks": profile["key_risks"],
        "general_macro": CURRENT_VIETNAM_MACRO,
        "dalio_verdict": dalio_verdict,
        "marks_verdict": marks_verdict
    }
