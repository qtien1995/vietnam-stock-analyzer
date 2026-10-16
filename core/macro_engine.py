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
    "usd_vnd_trend": "Áp lực tăng giá USD / VND dao động 25.200 - 25.450 (Hỗ trợ Xuất khẩu, Bất lợi Nợ USD)",
    "public_investment_status": "Giải ngân quyết liệt các đại dự án cao tốc Bắc-Nam & Sân bay Long Thành",
    "fdi_trend": "Tăng trưởng tích cực, hưởng lợi làn sóng dịch chuyển chuỗi cung ứng toàn cầu (China+1)",
    "market_liquidity_state": "Trung bình - Sôi động (18.000 - 25.000 tỷ/phiên)",
    "krx_ftse_upgrade": "Đang hoàn thiện cơ chế Non-prefunding để đáp ứng tiêu chuẩn nâng hạng FTSE Russell"
}

# =====================================================================
# 1B. MA TRẬN VĨ MÔ QUỐC TẾ & HÀNG HÓA THẾ GIỚI (GLOBAL MACRO & COMMODITIES)
# =====================================================================
GLOBAL_COMMODITIES_AND_MACRO = {
    "fed_funds_rate": {
        "name": "Lãi suất Điều hành FED (Fed Funds Rate)",
        "value": 4.88,
        "unit": "%",
        "trend": "Đang trong chu kỳ nới lỏng cắt giảm lãi suất (Dovish Pivot)",
        "change_pct": -0.50,
        "impact": "Giảm áp lực tỷ giá USD/VND, mở rộng dư địa nới lỏng cho NHNN, hỗ trợ định giá chứng khoán & BĐS",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "us_cpi": {
        "name": "Lạm phát Mỹ (US Core CPI YoY)",
        "value": 2.7,
        "unit": "%",
        "trend": "Hạ nhiệt dần về mục tiêu 2.0% của Fed",
        "change_pct": -0.2,
        "impact": "Củng cố kỳ vọng Fed tiếp tục hạ lãi suất các kỳ họp tới",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "dxy_index": {
        "name": "Chỉ số Sức mạnh Đồng USD (DXY)",
        "value": 102.4,
        "unit": "điểm",
        "trend": "Hạ nhiệt từ đỉnh 106, dao động tích lũy quanh 101 - 103",
        "change_pct": -1.2,
        "impact": "Giảm áp lực rút ròng của khối ngoại khỏi các thị trường mới nổi như Việt Nam",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "usd_vnd": {
        "name": "Tỷ giá USD/VND (Thương mại / VCB)",
        "value": 25380,
        "unit": "VND",
        "trend": "Căng thẳng nhẹ theo biến động đồng USD thế giới",
        "change_pct": +0.3,
        "impact": "Doanh nghiệp vay nợ USD lớn (BSR, PC1, HPG...) chịu lỗ tỷ giá; Doanh nghiệp xuất khẩu (VHC, TNG, FMC) hưởng lợi",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "crude_oil_brent": {
        "name": "Giá Dầu Thô Brent (Brent Crude)",
        "value": 78.5,
        "unit": "USD/thùng",
        "trend": "Biến động mạnh theo căng thẳng địa chính trị Trung Đông và OPEC+ hạn chế sản lượng",
        "change_pct": +2.8,
        "impact": "Trực tiếp kích hoạt sóng ngành Dầu khí (PVD, PVS, BSR, GAS); Tăng chi phí vận tải & đầu vào phân bón, nhựa",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "gold_world": {
        "name": "Giá Vàng Thế Giới (Gold Spot)",
        "value": 2650.0,
        "unit": "USD/oz",
        "trend": "Thiết lập đỉnh cao lịch sử do nhu cầu trú ẩn rủi ro địa chính trị & NHTW gom mua",
        "change_pct": +1.5,
        "impact": "Thúc đẩy giá vàng trong nước; Tác động tâm lý thị trường tài chính và cổ phiếu kinh doanh vàng PNJ",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "gold_sjc": {
        "name": "Giá Vàng Miếng SJC Trong Nước",
        "value": 84.5,
        "unit": "Triệu VND/lượng",
        "trend": "Bình ổn dưới sự can thiệp bán vàng trực tiếp từ NHNN qua 4 NHTM Nhà nước và SJC",
        "change_pct": +0.6,
        "impact": "Dòng tiền nhàn rỗi có xu hướng phân bổ đa dạng, cạnh tranh với tiền gửi ngân hàng",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "rubber_tsr20": {
        "name": "Giá Cao Su Tự Nhiên (TSR20 / TOCOM)",
        "value": 204.5,
        "unit": "US Cents/kg",
        "trend": "Tăng mạnh lên vùng đỉnh nhiều năm do mưa bão El Nino/La Nina gây thiếu hụt nguồn cung tại Thái Lan, Việt Nam",
        "change_pct": +4.2,
        "impact": "Đòn bẩy cực lớn cho các doanh nghiệp Cao su tự nhiên (GVR, DPR, DRI, PHR); Tăng chi phí đầu vào săm lốp (DRC, CSM)",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "steel_hrc": {
        "name": "Giá Thép Cuộn Cán Nóng (HRC Thế Giới)",
        "value": 545.0,
        "unit": "USD/tấn",
        "trend": "Phục hồi nhẹ từ đáy; Việt Nam đang áp thuế Chống bán phá giá bảo hộ ngành thép nội địa",
        "change_pct": +1.8,
        "impact": "Hỗ trợ biên lợi nhuận của Hòa Phát (HPG), Hoa Sen (HSG), Nam Kim (NKG); Kích thích giải ngân đầu tư công",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    },
    "urea_fertilizer": {
        "name": "Giá Phân Bón Urê Thế Giới",
        "value": 355.0,
        "unit": "USD/tấn",
        "trend": "Tích lũy ổn định, hỗ trợ nhu cầu mùa vụ nông nghiệp quý 4",
        "change_pct": +0.9,
        "impact": "Hỗ trợ doanh thu & biên lãi gộp của DCM, DPM; Nhu cầu hóa chất DGC duy trì tích cực",
        "source_type": "REFERENCE_BENCHMARK",
        "as_of_date": "2024-Q4"
    }
}



# =====================================================================
# 2. MA TRẬN PHÂN LOẠI NGÀNH ĐỘNG CHO TOÀN BỘ CỔ PHIẾU
# =====================================================================
KNOWN_TICKER_SECTORS = {
    # Cao su Tự nhiên & Bất động sản Khu công nghiệp (Chuyển đổi quỹ đất KCN)
    "GVR": "RUBBER_AND_INDUSTRIAL_PARK", "PHR": "RUBBER_AND_INDUSTRIAL_PARK",
    "DPR": "RUBBER_AND_INDUSTRIAL_PARK", "DRI": "RUBBER_AND_INDUSTRIAL_PARK",
    "TRC": "RUBBER_AND_INDUSTRIAL_PARK",

    # BĐS Khu công nghiệp
    "IDC": "INDUSTRIAL_REAL_ESTATE", "KBC": "INDUSTRIAL_REAL_ESTATE", "SZC": "INDUSTRIAL_REAL_ESTATE",
    "BCM": "INDUSTRIAL_REAL_ESTATE", "SIP": "INDUSTRIAL_REAL_ESTATE", "VGC": "INDUSTRIAL_REAL_ESTATE",
    "NTC": "INDUSTRIAL_REAL_ESTATE", "TIP": "INDUSTRIAL_REAL_ESTATE", "LHG": "INDUSTRIAL_REAL_ESTATE",
    "D2D": "INDUSTRIAL_REAL_ESTATE", "SLS": "INDUSTRIAL_REAL_ESTATE",
    
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
    "APS": "SECURITIES", "VIX": "SECURITIES", "TCBS": "SECURITIES", "DSC": "SECURITIES",
    "TCI": "SECURITIES", "WSS": "SECURITIES", "IVS": "SECURITIES", "BVS": "SECURITIES",
    "PSI": "SECURITIES", "APG": "SECURITIES", "VIG": "SECURITIES", "EVS": "SECURITIES",
    "TVB": "SECURITIES", "TVS": "SECURITIES", "HBS": "SECURITIES", "AAS": "SECURITIES",
    "BMS": "SECURITIES", "SBS": "SECURITIES",
    
    # Thép & Vật liệu xây dựng
    "HPG": "STEEL_MATERIALS", "HSG": "STEEL_MATERIALS", "NKG": "STEEL_MATERIALS",
    "VGS": "STEEL_MATERIALS", "TLH": "STEEL_MATERIALS", "HT1": "STEEL_MATERIALS",
    "BCC": "STEEL_MATERIALS", "BMP": "STEEL_MATERIALS", "NTP": "STEEL_MATERIALS",

    # BĐS Dân dụng & Nhà ở
    "VHM": "RESIDENTIAL_REAL_ESTATE", "VIC": "RESIDENTIAL_REAL_ESTATE", "NVL": "RESIDENTIAL_REAL_ESTATE",
    "KDH": "RESIDENTIAL_REAL_ESTATE", "NLG": "RESIDENTIAL_REAL_ESTATE", "PDR": "RESIDENTIAL_REAL_ESTATE",
    "DXG": "RESIDENTIAL_REAL_ESTATE", "DIG": "RESIDENTIAL_REAL_ESTATE", "CEO": "RESIDENTIAL_REAL_ESTATE",
    "TCH": "RESIDENTIAL_REAL_ESTATE", "HDG": "RESIDENTIAL_REAL_ESTATE", "VRE": "RESIDENTIAL_REAL_ESTATE",
    "BIG": "RESIDENTIAL_REAL_ESTATE", "IDJ": "RESIDENTIAL_REAL_ESTATE", "API": "RESIDENTIAL_REAL_ESTATE",

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
    1. Kiểm tra bảng tra cứu nhanh KNOWN_TICKER_SECTORS.
    2. Nếu không có overview, tự động nạp từ get_governance_data(symbol).
    3. Quét thông minh qua tên công ty (organ_name), hồ sơ kinh doanh và sector từ BCTC.
    """
    sym = symbol.upper().strip()
    if sym in KNOWN_TICKER_SECTORS:
        return KNOWN_TICKER_SECTORS[sym]

    if not overview_data:
        try:
            from core.data_loader import get_governance_data
            gov = get_governance_data(sym)
            if gov and gov.get("overview"):
                overview_data = gov.get("overview")
        except Exception:
            pass

    if not overview_data:
        return "GENERAL"

    organ_name = str(overview_data.get("organ_name", "")).lower()
    profile = str(overview_data.get("company_profile", "")).lower()
    raw_sector = str(overview_data.get("sector", "")).lower()
    text = f"{organ_name} {profile} {raw_sector}"

    clean_profile = profile.replace("sàn giao dịch chứng khoán", "").replace("sở giao dịch chứng khoán", "").replace("thị trường chứng khoán", "")
    text = f"{organ_name} {clean_profile} {raw_sector}"

    # Nhận diện Chứng khoán (ưu tiên cao khi đúng là CTCK)
    if "chứng khoán" in organ_name or "securities" in organ_name:
        return "SECURITIES"
    if any(k in clean_profile for k in ["môi giới chứng khoán", "tự doanh chứng khoán", "công ty chứng khoán"]) and "bất động sản" not in text:
        return "SECURITIES"

    # Nhận diện Ngân hàng
    if "ngân hàng" in organ_name or "bank" in organ_name:
        return "BANK"
    if any(k in text for k in ["ngân hàng", "bank", "banking"]):
        return "BANK"

    # Nhận diện Cao su Tự nhiên & BĐS KCN (Chuyển đổi quỹ đất)
    if any(k in text for k in ["cao su", "rubber", "mủ cao su", "chuyển đổi đất cao su"]):
        return "RUBBER_AND_INDUSTRIAL_PARK"

    # Nhận diện BĐS KCN
    if any(k in text for k in ["khu công nghiệp", "kcn", "industrial park", "industrial zone", "hạ tầng khu công nghiệp"]):
        return "INDUSTRIAL_REAL_ESTATE"

    # Nhận diện Bán lẻ & Tiêu dùng
    if any(k in text for k in ["bán lẻ", "siêu thị", "chuỗi cửa hàng", "tiêu dùng", "bánh kẹo", "sữa", "nước giải khát", "retail", "consumer"]):
        return "RETAIL_CONSUMER"

    # Nhận diện BĐS Dân dụng & Dịch vụ Cho thuê BĐS
    if any(k in text for k in ["bất động sản", "đô thị", "nhà ở", "chung cư", "địa ốc", "cho thuê văn phòng", "căn hộ", "khách sạn", "real estate"]) and "khu công nghiệp" not in text:
        return "RESIDENTIAL_REAL_ESTATE"

    # Nhận diện Thép & Kim loại (tránh nhận nhầm công ty thương mại/đa ngành)
    if any(k in organ_name for k in ["thép", "gang thép", "steel"]) or any(k in text for k in ["sản xuất thép", "luyện thép", "gang thép", "luyện kim", "phôi thép", "cán thép", "tôn mạ", "ống thép"]):
        return "STEEL_MATERIALS"
    if ("thép" in text or "steel" in text) and not any(k in text for k in ["bất động sản", "nông sản", "đầu tư", "thương mại"]):
        return "STEEL_MATERIALS"

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
    "RUBBER_AND_INDUSTRIAL_PARK": {
        "sector_name": "Cao su Tự nhiên & Bất động sản Khu công nghiệp",
        "cycle_phase": "Siêu chu kỳ Chuyển đổi Quỹ đất KCN & Hưởng lợi Giá mủ Cao su thế giới",
        "phase_description": "Hưởng lợi kép mang tính bước ngoặt: (1) Sóng chuyển đổi hàng chục nghìn hecta đất cao su sang đất Khu công nghiệp theo Quy hoạch tỉnh thời kỳ 2021-2030 đã được Thủ tướng Chính phủ phê duyệt; (2) Tiền đền bù giải phóng mặt bằng đất cao su theo Nghị định 102/2024/NĐ-CP và Luật Đất đai mới ước tính 1.0 - 1.5 tỷ đ/ha; (3) Giá cao su tự nhiên thế giới TSR20/TOCOM neo ở mức cao lịch sử và doanh nghiệp dẫn đầu chứng chỉ rừng bền vững PEFC/EUDR.",
        "tailwind_score": 88,
        "sentiment": "RẤT TÍCH CỰC (SUPER TAILWIND)",
        "macro_drivers": [
            "Thủ tướng Chính phủ đã phê duyệt Quy hoạch tỉnh thời kỳ 2021-2030 cho các thủ phủ công nghiệp (Bình Dương, Đồng Nai, Tây Ninh, Bình Phước), mở đường chuyển đổi từ 23.000 đến hơn 40.000 ha đất cao su thành các KCN thế hệ mới.",
            "Cơ chế đền bù thu hồi đất cao su theo Nghị định 102/2024/NĐ-CP và Luật Đất đai 2024: Đơn giá bồi thường chi phí đầu tư vào đất và thanh lý cây cao su đạt 1.0 - 1.5 tỷ đồng/ha, tạo nguồn tiền mặt và thặng dư lợi nhuận khổng lồ.",
            "Giá cao su tự nhiên thế giới (hợp đồng TSR20 Singapore, TOCOM Tokyo) tăng mạnh lên vùng đỉnh nhiều năm do nguồn cung toàn cầu thiếu hụt (thời tiết La Nina và bệnh rụng lá tại Thái Lan, Indonesia).",
            "Lợi thế vượt trội về rào cản xanh EUDR: Doanh nghiệp sở hữu diện tích rừng cao su đạt chứng chỉ VFCS/PEFC lớn nhất Việt Nam, đáp ứng tiêu chuẩn nghiêm ngặt của Liên minh châu Âu để xuất khẩu giá cao.",
            "Sở hữu hệ sinh thái nhà phát triển KCN hàng đầu phía Nam (NTC - Nam Tân Uyên, SIP - Sài Gòn VRG, Tân Bình, Rạch Bắp, Bắc Đồng Phú, Minh Hưng III...), đón đầu dòng vốn FDI công nghệ cao."
        ],
        "key_metrics_to_watch": [
            "Tiến độ chấp thuận chủ trương đầu tư KCN của Thủ tướng Chính phủ và Quyết định giao đất/chuyển mục đích sử dụng đất của UBND tỉnh.",
            "Diện tích đất KCN thương phẩm bàn giao và cho thuê mới hàng năm.",
            "Giá bán mủ cao su bình quân (ASP - USD/tấn) và biên lợi nhuận gộp mảng cao su tự nhiên.",
            "Doanh thu tài chính từ tiền bồi thường đất cao su và cổ tức được chia từ các công ty KCN liên kết.",
            "Tiến độ thoái vốn nhà nước và tái cơ cấu danh mục tài sản theo đề án được phê duyệt."
        ],
        "key_risks": [
            "Tiến độ hoàn thiện thủ tục pháp lý quy hoạch phân khu 1/2.000 tại một số địa phương có thể kéo dài hơn dự kiến.",
            "Biến động giá cao su tự nhiên thế giới theo chu kỳ ngành săm lốp và công nghiệp ô tô toàn cầu."
        ]
    },

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

    commodity_sensitivity = get_commodity_sensitivity(sym, sector_key)

    try:
        from core.sector_wave_engine import get_wave_context_for_ticker
        sector_wave = get_wave_context_for_ticker(sym, sector_key)
    except Exception:
        sector_wave = {}

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
        "global_commodities": GLOBAL_COMMODITIES_AND_MACRO,
        "commodity_sensitivity": commodity_sensitivity,
        "sector_wave": sector_wave,
        "dalio_verdict": dalio_verdict,
        "marks_verdict": marks_verdict
    }


def get_global_macro_summary() -> Dict[str, Any]:
    """Trả về tổng hợp toàn bộ ma trận Vĩ mô Quốc tế, Hàng hóa và Vĩ mô Việt Nam"""
    return {
        "global_commodities": GLOBAL_COMMODITIES_AND_MACRO,
        "vietnam_macro": CURRENT_VIETNAM_MACRO
    }


def get_commodity_sensitivity(symbol: str, sector_key: str) -> Dict[str, Any]:
    """
    Phân tích mức độ nhạy cảm của từng cổ phiếu với biến số Hàng hóa & Vĩ mô thế giới:
    - Loại hàng hóa chi phối (Primary Commodity)
    - Hệ số nhạy cảm (High / Medium / Low)
    - Độ trễ thẩm thấu (Macro Lag): Thời gian tin tức phản ánh vào giá cổ phiếu
    """
    sym = symbol.upper().strip()
    sec = sector_key.upper().strip()

    # 1. Dầu khí & Năng lượng
    if sec == "OIL_GAS_ENERGY" or sym in ["PVD", "PVS", "BSR", "GAS", "PLX", "PVB", "PVC"]:
        brent = GLOBAL_COMMODITIES_AND_MACRO["crude_oil_brent"]
        return {
            "commodity_key": "crude_oil_brent",
            "commodity_name": "Giá Dầu Thô Brent",
            "current_value": f"{brent['value']} {brent['unit']}",
            "trend_direction": "TĂNG (+2.8%)" if brent["change_pct"] > 0 else "GIẢM",
            "sensitivity_level": "RẤT CAO (Hệ số tương quan Beta > 0.8)",
            "transmission_lag": "1 - 3 phiên (Tâm lý đầu cơ ngắn hạn) & 1 - 2 quý (Giá thuê giàn / Hợp đồng EPCI)",
            "impact_summary": f"Giá dầu duy trì quanh mức {brent['value']} USD/thùng bảo đảm lợi nhuận hoạt động cho giàn khoan (PVD) và đẩy nhanh tiến độ đại dự án Lô B - Ô Môn (PVS, GAS)."
        }

    # 2. Cao su tự nhiên
    if sym in ["GVR", "DPR", "DRI", "PHR", "TNC"] or "cao su" in sym.lower():
        rubber = GLOBAL_COMMODITIES_AND_MACRO["rubber_tsr20"]
        return {
            "commodity_key": "rubber_tsr20",
            "commodity_name": "Giá Cao Su Tự Nhiên (TSR20 / TOCOM)",
            "current_value": f"{rubber['value']} {rubber['unit']}",
            "trend_direction": "TĂNG MẠNH (+4.2%)",
            "sensitivity_level": "RẤT CAO (Doanh thu & Biên lãi gộp trực tiếp)",
            "transmission_lag": "2 - 5 phiên (Dòng tiền đón đầu) & 1 quý (Biên lợi nhuận gộp bùng nổ)",
            "impact_summary": f"Giá cao su neo đỉnh nhiều năm tại {rubber['value']} Cents/kg do khan hiếm nguồn cung Đông Nam Á tạo cú hích lợi nhuận đột biến cho các doanh nghiệp sở hữu nông trường bạt ngàn."
        }

    # 3. Thép & Kim loại
    if sec == "STEEL_MATERIALS" or sym in ["HPG", "HSG", "NKG", "VGS", "TLH"]:
        steel = GLOBAL_COMMODITIES_AND_MACRO["steel_hrc"]
        return {
            "commodity_key": "steel_hrc",
            "commodity_name": "Giá Thép Cuộn Cán Nóng (HRC)",
            "current_value": f"{steel['value']} {steel['unit']}",
            "trend_direction": "PHỤC HỒI NHẸ (+1.8%)",
            "sensitivity_level": "CAO (Tồn kho & Biên lãi gộp)",
            "transmission_lag": "3 - 7 phiên (Kỳ vọng giá bán) & 1 tháng (Xuất khẩu & Tồn kho giá rẻ)",
            "impact_summary": f"Giá HRC phục hồi lên {steel['value']} USD/tấn kết hợp với hàng rào thuế Chống bán phá giá bảo hộ thị trường nội địa giúp các nhà sản xuất lớn (HPG, HSG) mở rộng biên lợi nhuận."
        }

    # 4. Vàng & Trang sức
    if sym in ["PNJ", "DOJI"] or sec == "RETAIL_CONSUMER" and sym == "PNJ":
        gold = GLOBAL_COMMODITIES_AND_MACRO["gold_sjc"]
        return {
            "commodity_key": "gold_sjc",
            "commodity_name": "Giá Vàng SJC & Giá Vàng Thế Giới",
            "current_value": f"{gold['value']} {gold['unit']}",
            "trend_direction": "ĐỈNH LỊCH SỬ (+1.5%)",
            "sensitivity_level": "TRUNG BÌNH - CAO (Biên lãi vàng trang sức)",
            "transmission_lag": "Ngay trong tuần (Tâm lý) & 1 quý (Chênh lệch biên chế tác)",
            "impact_summary": "Giá vàng neo cao giúp gia tăng giá trị tồn kho vàng của PNJ, nhưng mảng trang sức bán lẻ thời trang biên lãi cao mới là động lực tạo tiền cốt lõi."
        }

    # 5. Phân bón & Hóa chất
    if sec == "CHEMICAL_FERTILIZER" or sym in ["DGC", "DCM", "DPM", "BFC", "CSV", "LAS"]:
        urea = GLOBAL_COMMODITIES_AND_MACRO["urea_fertilizer"]
        return {
            "commodity_key": "urea_fertilizer",
            "commodity_name": "Giá Phân Bón Urê & Hóa Chất",
            "current_value": f"{urea['value']} {urea['unit']}",
            "trend_direction": "TÍCH LŨY TĂNG (+0.9%)",
            "sensitivity_level": "CAO (Biên lợi nhuận gộp & Xuất khẩu)",
            "transmission_lag": "3 - 5 phiên & 1 quý (Hợp đồng thầu quốc tế)",
            "impact_summary": f"Giá Urea duy trì trên {urea['value']} USD/tấn hỗ trợ mức cổ tức tiền mặt cao của DCM, DPM; DGC hưởng lợi từ chuỗi giá trị Phốt pho vàng toàn cầu."
        }

    # 6. Ngân hàng & Chứng khoán (Nhạy cảm Lãi suất & Tỷ giá)
    if sec in ["BANK", "SECURITIES"]:
        fed = GLOBAL_COMMODITIES_AND_MACRO["fed_funds_rate"]
        fx = GLOBAL_COMMODITIES_AND_MACRO["usd_vnd"]
        return {
            "commodity_key": "fed_funds_rate",
            "commodity_name": "Lãi Suất FED & Tỷ Giá USD/VND",
            "current_value": f"Fed Rate {fed['value']}% | USD/VND {fx['value']:,} đ",
            "trend_direction": "CHU KỲ NỚI LỎNG (Dovish Pivot)",
            "sensitivity_level": "RẤT CAO (Định giá P/E, P/B & Thanh khoản thị trường)",
            "transmission_lag": "1 - 2 tuần (Lan tỏa thanh khoản hệ thống) & 1 quý (NIM ngân hàng)",
            "impact_summary": "Fed bước vào chu kỳ giảm lãi suất gỡ bỏ áp lực tỷ giá cho NHNN, duy trì mặt bằng lãi suất VND thấp kích thích dòng tiền margin đổ mạnh vào thị trường chứng khoán."
        }

    # Mặc định
    fx = GLOBAL_COMMODITIES_AND_MACRO["usd_vnd"]
    return {
        "commodity_key": "usd_vnd",
        "commodity_name": "Tỷ Giá USD/VND & Lãi Suất Trong Nước",
        "current_value": f"{fx['value']:,} VND",
        "trend_direction": "ỔN ĐỊNH TRONG TẦM KIỂM SOÁT",
        "sensitivity_level": "TRUNG BÌNH (Chi phí vốn & Sức mua nội địa)",
        "transmission_lag": "1 - 2 quý",
        "impact_summary": "Môi trường vĩ mô ổn định, lãi suất cho vay thấp hỗ trợ doanh nghiệp duy trì dòng tiền kinh doanh lành mạnh."
    }

