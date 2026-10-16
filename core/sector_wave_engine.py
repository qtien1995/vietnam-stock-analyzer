# -*- coding: utf-8 -*-
"""
core/sector_wave_engine.py
Hệ Thống Phân Tích Sóng Ngành & Radar Luân Chuyển Dòng Tiền (Sector Wave & Rotation Engine).
Chuyên biệt cho Thị Trường Chứng Khoán Việt Nam (Giai đoạn 2020 - 2026+).

Chức năng:
1. Danh mục 10 Sóng Ngành Kinh Điển của TTCK Việt Nam:
   - Sóng Dầu khí & Địa chính trị (Căng thẳng Mỹ - Iran, Eo biển Hormuz, Nga - Ukraine, OPEC+)
   - Sóng Công nghệ, Bán dẫn & AI (Nvidia, Data Center, Chuyển đổi số toàn cầu)
   - Sóng Thép, Vật liệu & Thuế Chống bán phá giá (Đầu tư công, Bảo hộ HRC)
   - Sóng Chứng khoán & Tiền rẻ (Lãi suất thấp, Thanh khoản bùng nổ, KRX, Nâng hạng FTSE)
   - Sóng Bất động sản Dân dụng (Hạ lãi suất cho vay, Tháo gỡ pháp lý Luật Đất đai)
   - Sóng BĐS Khu công nghiệp (Dòng vốn FDI kỷ lục, Chuỗi cung ứng China+1, Đất cao su)
   - Sóng Hóa chất & Phân bón (Phốt pho vàng cho chip/pin, Giá Urê thế giới)
   - Sóng Đầu tư công & Xây dựng Hạ tầng (Mệnh lệnh giải ngân cao tốc, Sân bay Long Thành)
   - Sóng Xuất khẩu & Cước Vận tải biển (Tỷ giá USD/VND cao, Tái tích lũy tồn kho Mỹ/EU)
   - Sóng Bán lẻ & Kích cầu Tiêu dùng Nội địa (Giảm thuế VAT 2%, Tăng lương cơ sở, SSSG hồi phục)
2. Thuật toán đo Nhiệt độ Sóng (Wave Heat Score: 0 - 100) dựa trên Xúc tác Vĩ mô + Dòng tiền.
3. Phân loại 4 Pha Chu kỳ Sóng (Pha 1 Gom -> Pha 2 Bùng nổ -> Pha 3 Quá nhiệt -> Pha 4 Thoái trào).
4. Phân cấp Cổ phiếu Đón Sóng: Leaders (Đầu đàn) vs High-Beta Runners (Chạy sau / Phiêu).
5. Mapping vị thế Sóng Ngành cho từng mã cụ thể phục vụ Báo cáo 360°.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime


# =====================================================================
# 1. MA TRẬN 10 SÓNG NGÀNH KINH ĐIỂN TTCK VIỆT NAM (WAVE TAXONOMY)
# =====================================================================
SECTOR_WAVES_CATALOG = {
    "WAVE_OIL_GAS_GEOPOLITICS": {
        "wave_id": "WAVE_OIL_GAS_GEOPOLITICS",
        "name_vi": "Sóng Dầu Khí & Địa Chính Trị (Hormuz / Trung Đông)",
        "name_en": "Oil & Gas Geopolitical Wave",
        "icon": "🛢️",
        "sector_key": "OIL_GAS_ENERGY",
        "core_catalysts": [
            "Xung đột quân sự Mỹ - Iran tại Vùng Vịnh và Eo biển Hormuz đe dọa 20% lượng dầu mỏ vận chuyển toàn cầu.",
            "Căng thẳng địa chính trị Trung Đông và xung đột Nga - Ukraine kéo dài làm gián đoạn chuỗi logistics năng lượng.",
            "OPEC+ thắt chặt sản lượng duy trì giá dầu Brent trên 75 - 85 USD/thùng.",
            "Đại dự án Lô B - Ô Môn (12 tỷ USD) bước vào giai đoạn triển khai hợp đồng EPCI quy mô lớn."
        ],
        "macro_trigger_indicators": ["crude_oil_brent"],
        "historical_cases": "Sóng Dầu khí 2022 (Chiến sự Nga - Ukraine), Sóng Dầu khí 2024 (Căng thẳng Iran - Israel)",
        "leaders": ["PVD", "PVS", "BSR", "GAS"],
        "high_beta_runners": ["PVC", "PVB", "PVT", "PLX", "PSH"],
        "wave_characteristics": "Sóng có tính đầu cơ cực cao, phản ứng cực nhanh (1 - 2 phiên) theo tin tức chiến sự và giá dầu thế giới ban đêm. Mã PVD/PVS thường chạy đầu đàn.",
        "trading_rule": "Mua khi giá dầu Brent bứt phá qua kháng cự kỹ thuật hoặc khi xung đột quân sự chớm bùng nổ; Chốt lời dứt khoát khi tin tức hạ nhiệt, không ôm dài hạn nếu thiếu hợp đồng thực tế."
    },

    "WAVE_TECH_AI_SEMICONDUCTOR": {
        "wave_id": "WAVE_TECH_AI_SEMICONDUCTOR",
        "name_vi": "Sóng Công Nghệ, Bán Dẫn & Trí Tuệ Nhân Tạo (AI)",
        "name_en": "Tech, Semiconductor & AI Global Wave",
        "icon": "💻",
        "sector_key": "TECHNOLOGY_TELECOM",
        "core_catalysts": [
            "Cuộc cách mạng AI toàn cầu (Nvidia, Microsoft, OpenAI) thúc đẩy nhu cầu xây dựng Data Center và hạ tầng đám mây Cloud.",
            "Chính phủ ban hành Chiến lược Quốc gia về Công nghiệp Bán dẫn đến năm 2030, định vị VN là cứ điểm lắp ráp, kiểm thử và thiết kế chip.",
            "Làn sóng ký kết hợp đồng chuyển đổi số và AI thế hệ mới trị giá hàng trăm triệu USD từ thị trường Nhật Bản, Mỹ, EU.",
            "Thương mại hóa mạng 5G toàn quốc kích hoạt chu kỳ đầu tư hạ tầng viễn thông mới."
        ],
        "macro_trigger_indicators": ["dxy_index", "fed_funds_rate"],
        "historical_cases": "Siêu sóng Công nghệ thông tin 2023 - 2024 khi FPT vượt đỉnh mọi thời đại liên tục",
        "leaders": ["FPT", "CMG", "CTR", "FOX"],
        "high_beta_runners": ["ELC", "VGI", "ITD", "TTN"],
        "wave_characteristics": "Sóng tăng trưởng dài hạn vững chắc nhất thị trường; ít bị ảnh hưởng bởi chu kỳ kinh tế nội địa. Dẫn dắt bởi dòng tiền tổ chức và khối ngoại.",
        "trading_rule": "Chiến lược Mua và Nắm giữ (Buy & Hold) hoặc Gom khi điều chỉnh về EMA50. FPT là cổ phiếu neo giữ chỉ số uy tín bậc nhất."
    },

    "WAVE_STEEL_INFRA_TARIFF": {
        "wave_id": "WAVE_STEEL_INFRA_TARIFF",
        "name_vi": "Sóng Thép, Vật Liệu & Thuế Chống Bán Phá Giá",
        "name_en": "Steel, Anti-Dumping Tariffs & Infrastructure",
        "icon": "🏗️",
        "sector_key": "STEEL_MATERIALS",
        "core_catalysts": [
            "Bộ Công Thương tiến hành điều tra và áp thuế Chống bán phá giá (CBPG) bảo hộ thép cuộn cán nóng HRC nội địa khỏi làn sóng thép giá rẻ.",
            "Đại công trường Đầu tư công (Sân bay Long Thành, Cao tốc Bắc - Nam, Vành đai 3 & 4) tăng tốc tiêu thụ sản lượng thép xây dựng kỷ lục.",
            "Thị trường Bất động sản dân dụng bắt đầu phục hồi pháp lý và khởi công các đại đô thị mới.",
            "Dự án Đại liên hợp Gang thép Dung Quất 2 đi vào vận hành giúp nâng gấp đôi công suất HRC chất lượng cao."
        ],
        "macro_trigger_indicators": ["steel_hrc", "public_investment_status"],
        "historical_cases": "Đại sóng Siêu chu kỳ hàng hóa 2020 - 2021 (HPG nhân 3 lần tài khoản); Sóng hồi phục kỳ vọng thuế CBPG 2024",
        "leaders": ["HPG", "HSG", "NKG"],
        "high_beta_runners": ["VGS", "TLH", "SMC", "POM"],
        "wave_characteristics": "Sóng chu kỳ kinh điển của TTCK Việt Nam. Hòa Phát (HPG) là xe ủi dẫn dắt thanh khoản, HSG và NKG có độ phiêu biến động mạnh hơn (High Beta).",
        "trading_rule": "Mua ở chân chu kỳ phục hồi khi P/B quanh 1.0 - 1.2x và biên lãi gộp bắt đầu tạo đáy; Cảnh giác bẫy giá trị P/E rẻ ở đỉnh chu kỳ khi lợi nhuận đạt đỉnh."
    },

    "WAVE_SECURITIES_LIQUIDITY": {
        "wave_id": "WAVE_SECURITIES_LIQUIDITY",
        "name_vi": "Sóng Chứng Khoán & Thanh Khoản Tiền Rẻ",
        "name_en": "Securities Brokerage & Market Liquidity Boom",
        "icon": "📈",
        "sector_key": "SECURITIES",
        "core_catalysts": [
            "Môi trường lãi suất tiền gửi ngân hàng duy trì ở mức đáy lịch sử (4.5 - 5.5%), dòng tiền tiết kiệm khổng lồ tháo chạy vào TTCK.",
            "Thanh khoản bình quân toàn thị trường bùng nổ vượt 20.000 - 30.000 tỷ VNĐ/phiên, thúc đẩy doanh thu phí môi giới và lãi vay Margin.",
            "Tiến trình vận hành hệ thống công nghệ thông tin KRX và triển khai cơ chế Non-prefunding đáp ứng tiêu chuẩn Nâng hạng thị trường FTSE Russell.",
            "Danh mục tự doanh của các công ty chứng khoán hoàn nhập dự phòng và ghi nhận lợi nhuận đột biến."
        ],
        "macro_trigger_indicators": ["avg_12m_deposit_rate_pct", "market_liquidity_state", "krx_ftse_upgrade"],
        "historical_cases": "Đại sóng F0 thần thánh 2020 - 2021; Sóng giảm lãi suất điều hành 4 lần liên tiếp năm 2023",
        "leaders": ["SSI", "VCI", "HCM", "VND"],
        "high_beta_runners": ["FTS", "BSI", "CTS", "MBS", "VIX", "AGR", "ORS"],
        "wave_characteristics": "Là dòng chỉ báo sớm của toàn bộ thị trường chứng khoán (Market Proxy). Dòng chứng khoán tăng mạnh là chỉ báo thị trường bước vào pha Bull Market rõ rệt.",
        "trading_rule": "Đánh theo đà tăng (Momentum Trading) khi thanh khoản thị trường liên tục nổ Vol > 1.3x MA20. Khi thị trường xuất hiện dấu hiệu phân phối tạo đỉnh, dòng chứng khoán phải là nhóm chốt lời đầu tiên."
    },

    "WAVE_RESIDENTIAL_REAL_ESTATE": {
        "wave_id": "WAVE_RESIDENTIAL_REAL_ESTATE",
        "name_vi": "Sóng Bất Động Sản Dân Dụng & Tháo Gỡ Pháp Lý",
        "name_en": "Residential Real Estate & Policy Easing",
        "icon": "🏡",
        "sector_key": "RESIDENTIAL_REAL_ESTATE",
        "core_catalysts": [
            "Luật Đất đai (sửa đổi), Luật Nhà ở và Luật Kinh doanh BĐS chính thức có hiệu lực, gỡ vướng pháp lý cho hàng trăm dự án đóng băng.",
            "Lãi suất cho vay mua nhà hạ nhiệt xuống mức hấp dẫn (5.0 - 7.0%/năm trong thời gian ưu đãi), kích thích nhu cầu mua ở thực và đầu tư.",
            "Áp lực đáo hạn trái phiếu doanh nghiệp được giãn hoãn thành công, các chủ đầu tư đàm phán cơ cấu nợ và tái khởi động dự án.",
            "Dòng tiền đầu cơ cá nhân tìm kiếm tài sản trú ẩn trước rủi ro lạm phát và mất giá tiền tệ."
        ],
        "macro_trigger_indicators": ["sbv_refinancing_rate_pct", "credit_growth_target_pct"],
        "historical_cases": "Cơn sốt đất và siêu sóng BĐS cuối năm 2021 (DIG, CEO nhân 5 - 10 lần); Nhịp sóng hồi phục chính sách giữa năm 2023",
        "leaders": ["VHM", "KDH", "NLG", "PDR"],
        "high_beta_runners": ["DIG", "CEO", "DXG", "NVL", "HDC", "TCH"],
        "wave_characteristics": "Dòng có tính chất thu hút dòng tiền cá nhân (Retail FOMO) mạnh nhất sàn. Khi vào sóng thì tăng rất bốc bằng các cây trần liên tiếp, nhưng khi gãy thì giảm sàn mất thanh khoản.",
        "trading_rule": "Ưu tiên doanh nghiệp có quỹ đất sạch và pháp lý minh bạch (KDH, NLG) cho danh mục an toàn; Chỉ lướt sóng nhóm High-Beta (DIG, DXG) khi có dòng tiền mồi nổ Vol và tuân thủ kỷ luật cắt lỗ tuyệt đối &le; 7%."
    },

    "WAVE_INDUSTRIAL_PARK_FDI": {
        "wave_id": "WAVE_INDUSTRIAL_PARK_FDI",
        "name_vi": "Sóng BĐS Khu Công Nghiệp & Làn Sóng FDI (China+1)",
        "name_en": "Industrial Real Estate & FDI Supply Chain Shift",
        "icon": "🏭",
        "sector_key": "INDUSTRIAL_REAL_ESTATE",
        "core_catalysts": [
            "Dòng vốn đầu tư trực tiếp nước ngoài (FDI) giải ngân thực tế liên tục lập kỷ lục nhờ làn sóng dịch chuyển nhà máy khỏi Trung Quốc (China+1).",
            "Giá thuê đất khu công nghiệp tại cả hai miền Nam - Bắc duy trì đà tăng 10 - 15%/năm do nguồn cung đất sạch sẵn sàng cho thuê khan hiếm.",
            "Tập đoàn Công nghiệp Cao su Việt Nam (GVR) đẩy mạnh chiến lược chuyển đổi hàng chục nghìn hecta nông trường cao su sang đất KCN biên lãi cực cao.",
            "Của để dành khổng lồ từ khoản mục 'Doanh thu chưa thực hiện dài hạn' trên BCTC bảo đảm dòng tiền cổ tức tiền mặt đều đặn."
        ],
        "macro_trigger_indicators": ["fdi_trend", "rubber_tsr20"],
        "historical_cases": "Sóng tăng trưởng âm thầm bền bỉ xuyên suốt từ 2020 đến 2024",
        "leaders": ["GVR", "KBC", "IDC", "SZC", "PHR"],
        "high_beta_runners": ["DPR", "D2D", "NTC", "TIP", "BCM"],
        "wave_characteristics": "Sóng có nền tảng cơ bản và tiền mặt dồi dào nhất thị trường. Doanh nghiệp nợ vay thấp, trả cổ tức tiền mặt cao, sức chịu đựng suy thoái kinh tế vượt trội.",
        "trading_rule": "Rất thích hợp cho chiến lược Tích sản đầu tư giá trị khi thị trường điều chỉnh chung. Mua gom khi P/B chiết khấu và nắm giữ theo tiến độ bàn giao đất."
    },

    "WAVE_CHEMICAL_FERTILIZER": {
        "wave_id": "WAVE_CHEMICAL_FERTILIZER",
        "name_vi": "Sóng Hóa Chất, Phân Bón & An Ninh Lương Thực",
        "name_en": "Chemicals, Fertilizers & Supply Disruption",
        "icon": "🧪",
        "sector_key": "CHEMICAL_FERTILIZER",
        "core_catalysts": [
            "Giá Phốt pho vàng thế giới leo thang do nhu cầu bùng nổ từ ngành sản xuất chip bán dẫn, vi mạch điện tử và pin xe điện LFP.",
            "Trung Quốc tiếp tục siết chặt hạn ngạch xuất khẩu phân bón Urê và hóa chất cơ bản để bảo đảm nguồn cung trong nước.",
            "Chi phí nguyên liệu khí đầu vào biến động đẩy giá phân bón thế giới tăng cao, mở rộng biên lợi nhuận của các nhà sản xuất xuất khẩu.",
            "Cổ tức tiền mặt cực khủng từ lượng tiền gửi ròng hàng nghìn tỷ đồng trong két sắt doanh nghiệp."
        ],
        "macro_trigger_indicators": ["urea_fertilizer"],
        "historical_cases": "Siêu sóng Phân bón & Hóa chất 2021 - 2022 (DGC, DCM, DPM nhân 3 - 5 lần)",
        "leaders": ["DGC", "DCM", "DPM"],
        "high_beta_runners": ["BFC", "CSV", "LAS", "DDV"],
        "wave_characteristics": "Sóng hàng hóa xuất khẩu có tính chu kỳ ngắn hạn nhưng biên độ tăng rất sốc. DGC là siêu cổ phiếu công nghệ hóa chất, DCM/DPM là cỗ máy in tiền mặt cổ tức.",
        "trading_rule": "Bám sát diễn biến giá hàng hóa thế giới hàng tuần (Giá Urê, Giá Phốt pho vàng). Mua khi giá hàng hóa bước vào nhịp tăng mới; Bán ngay khi giá hàng hóa lập đỉnh phân phối."
    },

    "WAVE_PUBLIC_INFRASTRUCTURE": {
        "wave_id": "WAVE_PUBLIC_INFRASTRUCTURE",
        "name_vi": "Sóng Đầu Tư Công & Xây Dựng Hạ Tầng Giao Thông",
        "name_en": "Public Infrastructure & Construction Sprint",
        "icon": "🛣️",
        "sector_key": "PUBLIC_INVEST_INFRA",
        "core_catalysts": [
            "Chính phủ quyết liệt chỉ đạo giải ngân 95 - 100% kế hoạch vốn đầu tư công, coi đây là động lực then chốt để thúc đẩy tăng trưởng GDP > 7%.",
            "Hàng loạt đại dự án giao thông trọng điểm quốc gia bước vào cao điểm thi công 3 ca 4 kíp: Sân bay Long Thành, Cao tốc Bắc - Nam, Đường vành đai.",
            "Các doanh nghiệp nhà thầu tích lũy được khối lượng công việc tồn đọng (Backlog) trúng thầu kỷ lục, đảm bảo nguồn thu trong 3 - 5 năm tới.",
            "Giá nguyên vật liệu xây dựng (đá, cát, đất đắp) bình ổn dưới sự kiểm soát của cơ quan quản lý."
        ],
        "macro_trigger_indicators": ["public_investment_status"],
        "historical_cases": "Sóng Đầu tư công bùng nổ đầu năm 2023 dẫn dắt toàn thị trường hồi phục",
        "leaders": ["VCG", "HHV", "LCG", "C4G"],
        "high_beta_runners": ["FCN", "KSB", "DHA", "VLB", "CTI"],
        "wave_characteristics": "Sóng hưởng lợi trực tiếp từ chính sách tài khóa của Chính phủ. Nhóm cổ phiếu đá xây dựng (KSB, DHA) thường có biên lợi nhuận thực chất hơn nhóm nhà thầu xây lắp.",
        "trading_rule": "Sóng thường chạy mạnh vào quý 1 (khi công bố chỉ tiêu vốn đầu năm) và quý 4 (nước rút giải ngân cuối năm). Cần kiểm tra kỹ dòng tiền hoạt động (CFO) để tránh các nhà thầu bị chiếm dụng vốn."
    },

    "WAVE_EXPORT_SHIPPING": {
        "wave_id": "WAVE_EXPORT_SHIPPING",
        "name_vi": "Sóng Xuất Khẩu (Thủy Sản, Dệt May) & Cảng Biển",
        "name_en": "Export Recovery & Marine Shipping Wave",
        "icon": "🚢",
        "sector_key": "EXPORT_SEAFOOD_TEXTILE",
        "core_catalysts": [
            "Tỷ giá USD/VND neo ở mức cao hỗ trợ mạnh mẽ biên lợi nhuận của các doanh nghiệp xuất khẩu thu về ngoại tệ ròng.",
            "Chu kỳ xả hàng tồn kho của các thị trường tiêu thụ lớn (Mỹ, EU, Nhật Bản) kết thúc, các nhà bán lẻ đẩy mạnh ký kết đơn hàng mới.",
            "Căng thẳng an ninh hàng hải tại Biển Đỏ buộc các tuyến tàu container phải đi vòng qua Mũi Hảo Vọng, đẩy giá cước vận tải biển tăng cao.",
            "Cụm cảng nước sâu Cái Mép - Thị Vải và Lạch Huyện đón các tuyến tàu mẹ trực tiếp đi thẳng bờ Tây/bờ Đông nước Mỹ."
        ],
        "macro_trigger_indicators": ["usd_vnd"],
        "historical_cases": "Sóng Xuất khẩu thủy sản cá tra năm 2022 (VHC, ANV); Sóng cước biển HAH, GMD năm 2021 và 2024",
        "leaders": ["VHC", "ANV", "TNG", "GMD", "HAH"],
        "high_beta_runners": ["MSH", "FMC", "VSC", "PVT", "VOS"],
        "wave_characteristics": "Sóng có độ trễ thẩm thấu theo quý. Khi tỷ giá tăng nóng và kim ngạch xuất khẩu hàng tháng công bố tăng trưởng dương 2 con số, dòng tiền sẽ kích hoạt nhịp rít mạnh.",
        "trading_rule": "Đánh theo chu kỳ mùa vụ: Nhóm Thủy sản và Dệt may thường đạt đỉnh xuất khẩu vào Quý 3 để phục vụ mùa lễ hội Giáng sinh và Năm mới tại phương Tây."
    },

    "WAVE_RETAIL_DOMESTIC": {
        "wave_id": "WAVE_RETAIL_DOMESTIC",
        "name_vi": "Sóng Bán Lẻ & Kích Cầu Tiêu Dùng Nội Địa",
        "name_en": "Retail, Consumption & SSSG Expansion",
        "icon": "🛍️",
        "sector_key": "RETAIL_CONSUMER",
        "core_catalysts": [
            "Chính sách tài khóa giảm 2% thuế suất thuế GTGT (VAT) được duy trì để kích thích sức mua người tiêu dùng trong nước.",
            "Cải cách tiền lương khu vực công giúp gia tăng thu nhập khả dụng của hàng triệu hộ gia đình Việt Nam.",
            "Cuộc chiến tranh hạ giá bán giữa các chuỗi bán lẻ công nghệ kết thúc, các nhà bán lẻ tối ưu hóa chi phí và cải thiện biên lãi ròng.",
            "Các chuỗi bách hóa và chuỗi nhà thuốc bán lẻ vượt qua điểm hòa vốn (Breakeven Point) và bắt đầu đóng góp dòng tiền mặt dương."
        ],
        "macro_trigger_indicators": ["us_cpi", "avg_12m_deposit_rate_pct"],
        "historical_cases": "Sóng phục hồi bán lẻ cuối năm 2023 - 2024 (MWG, FRT tăng vượt trội so với VN-Index)",
        "leaders": ["MWG", "PNJ", "FRT", "MSN"],
        "high_beta_runners": ["DGW", "PET"],
        "wave_characteristics": "Dòng phản ánh trực tiếp sức khỏe của tầng lớp trung lưu và tiêu dùng nội địa. Thích hợp cho dòng vốn lớn vì thanh khoản cổ phiếu dồi dào và minh bạch.",
        "trading_rule": "Theo dõi sát sao chỉ số tăng trưởng doanh thu trên cùng một cửa hàng (SSSG) hàng tháng. Mua mạnh khi biên lợi nhuận ròng của chuỗi bắt đầu mở rộng."
    }
}


# =====================================================================
# 2. THUẬT TOÁN ĐO NHIỆT ĐỘ & XÁC ĐỊNH PHA SÓNG NGÀNH (WAVE RADAR ENGINE)
# =====================================================================

def evaluate_sector_wave_radar(macro_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Quét và tính toán Điểm Nhiệt Sóng Ngành (Wave Heat Score: 0 - 100) cho toàn bộ 10 Sóng:
    - Điểm Xúc tác Vĩ mô & Hàng hóa (Macro Catalyst Fit: 0 - 45đ)
    - Điểm Dòng tiền & Sức mạnh Kỹ thuật (Money Momentum: 0 - 35đ)
    - Điểm Tâm lý Truyền thông & Xung đột Địa chính trị (Buzz & Sentiment: 0 - 20đ)
    
    Phân loại thành 4 Pha Chu kỳ Sóng:
    - Pha 1: TÍCH LŨY ÂM THẦM (SMART MONEY GOM - CHƯA RẦM RỘ) [45 - 62đ]
    - Pha 2: BÙNG NỔ & ĐẨY SÓNG (SURGING / MOMENTUM - VÙNG ĐÁNH SÓNG NGON NHẤT) [63 - 82đ]
    - Pha 3: QUÁ NHIỆT / PHÂN PHỐI ĐỈNH (OVERHEATED / RỦI RO FOMO CAO) [> 82đ]
    - Pha 4: HẠ NHIỆT / THOÁI TRÀO (FADING / DÒNG TIỀN RÚT SANG NGÀNH KHÁC) [< 45đ]
    """
    from core.macro_engine import GLOBAL_COMMODITIES_AND_MACRO, CURRENT_VIETNAM_MACRO
    
    macro = macro_data or {}
    comm = macro.get("global_commodities") or GLOBAL_COMMODITIES_AND_MACRO
    vn = macro.get("vietnam_macro") or CURRENT_VIETNAM_MACRO

    radar_results = []

    for wave_id, wave in SECTOR_WAVES_CATALOG.items():
        base_catalyst_score = 25.0
        sentiment_score = 15.0
        momentum_score = 25.0
        active_triggers = []

        # 1. Đánh giá xúc tác Dầu khí & Địa chính trị (Hormuz)
        if wave_id == "WAVE_OIL_GAS_GEOPOLITICS":
            brent = comm.get("crude_oil_brent", {})
            b_val = float(brent.get("value") or 78.5)
            b_chg = float(brent.get("change_pct") or 0.0)
            if b_val >= 80.0:
                base_catalyst_score += 15.0
                active_triggers.append(f"Giá dầu Brent neo cao ({b_val} USD/thùng) bảo đảm biên lợi nhuận lọc hóa dầu và giàn khoan.")
            elif b_val >= 75.0:
                base_catalyst_score += 10.0
                active_triggers.append(f"Giá dầu Brent ở mức thuận lợi ({b_val} USD/thùng) cho hoạt động thăm dò khai thác.")
            if b_chg > 2.0:
                sentiment_score += 8.0
                active_triggers.append("Căng thẳng quân sự Vùng Vịnh / Eo biển Hormuz kích hoạt tâm lý đầu cơ giá dầu ngắn hạn.")
            momentum_score += 5.0

        # 2. Đánh giá xúc tác Công nghệ & Bán dẫn / AI
        elif wave_id == "WAVE_TECH_AI_SEMICONDUCTOR":
            fed = comm.get("fed_funds_rate", {})
            f_trend = fed.get("trend", "")
            if "nới lỏng" in f_trend.lower() or "dovish" in f_trend.lower():
                base_catalyst_score += 12.0
                active_triggers.append("Chu kỳ Fed hạ lãi suất mở rộng định giá (Multiple Expansion) cho nhóm cổ phiếu công nghệ P/E cao.")
            base_catalyst_score += 10.0
            sentiment_score += 7.0
            momentum_score += 8.0
            active_triggers.append("Làn sóng đầu tư hạ tầng AI toàn cầu và chiến lược bán dẫn quốc gia mở rộng đơn hàng gia công phần mềm.")

        # 3. Đánh giá xúc tác Thép & Vật liệu
        elif wave_id == "WAVE_STEEL_INFRA_TARIFF":
            steel = comm.get("steel_hrc", {})
            s_val = float(steel.get("value") or 545.0)
            if s_val >= 540.0:
                base_catalyst_score += 12.0
                active_triggers.append(f"Giá thép HRC thế giới ({s_val} USD/tấn) phục hồi củng cố biên lãi gộp nhà sản xuất nội địa.")
            base_catalyst_score += 8.0
            active_triggers.append("Đại công trường Đầu tư công tăng tốc giải ngân và kỳ vọng hàng rào thuế Chống bán phá giá HRC.")

        # 4. Đánh giá xúc tác Chứng khoán
        elif wave_id == "WAVE_SECURITIES_LIQUIDITY":
            liq_state = vn.get("market_liquidity_state", "")
            if "sôi động" in liq_state.lower() or "25.000" in liq_state:
                base_catalyst_score += 14.0
                active_triggers.append("Thanh khoản toàn thị trường sôi động kích hoạt doanh thu phí môi giới và margin tăng vọt.")
            if "ftse" in vn.get("krx_ftse_upgrade", "").lower():
                sentiment_score += 6.0
                active_triggers.append("Kỳ vọng nâng hạng FTSE Russell và gỡ bỏ ký quỹ Non-prefunding hỗ trợ tâm lý thị trường.")

        # 5. Đánh giá xúc tác BĐS Khu công nghiệp
        elif wave_id == "WAVE_INDUSTRIAL_PARK_FDI":
            if "tích cực" in vn.get("fdi_trend", "").lower() or "china+1" in vn.get("fdi_trend", "").lower():
                base_catalyst_score += 14.0
                active_triggers.append("Dòng vốn FDI giải ngân tăng trưởng tích cực và xu hướng dịch chuyển chuỗi cung ứng toàn cầu.")
            base_catalyst_score += 8.0
            active_triggers.append("Quỹ đất cao su chuyển đổi KCN và tỷ lệ lấp đầy cao bảo đảm dòng tiền cho thuê.")

        # 6. Đánh giá xúc tác BĐS Dân dụng
        elif wave_id == "WAVE_RESIDENTIAL_REAL_ESTATE":
            if "nới lỏng" in vn.get("monetary_policy", "").lower():
                base_catalyst_score += 10.0
                active_triggers.append("Chính sách tiền tệ nới lỏng và mặt bằng lãi suất cho vay mua nhà chạm đáy hỗ trợ cầu bất động sản.")
            sentiment_score += 5.0
            active_triggers.append("Các bộ luật Bất động sản mới có hiệu lực tháo gỡ điểm nghẽn pháp lý dự án tồn đọng.")

        # 7. Đánh giá xúc tác Hóa chất & Phân bón
        elif wave_id == "WAVE_CHEMICAL_FERTILIZER":
            urea = comm.get("urea_fertilizer", {})
            u_val = float(urea.get("value") or 355.0)
            if u_val >= 350.0:
                base_catalyst_score += 10.0
                active_triggers.append(f"Giá phân bón Urê ({u_val} USD/tấn) ổn định ở vùng có lãi cao; Phốt pho vàng duy trì nhu cầu chip điện tử.")

        # 8. Đánh giá xúc tác Xuất khẩu & Tỷ giá
        elif wave_id == "WAVE_EXPORT_SHIPPING":
            if "tăng giá usd" in vn.get("usd_vnd_trend", "").lower():
                base_catalyst_score += 12.0
                active_triggers.append("Tỷ giá USD/VND neo cao mang lại thặng dư lợi nhuận tỷ giá trực tiếp cho doanh nghiệp xuất khẩu cá tra, dệt may.")

        # 9. Đánh giá xúc tác Đầu tư công
        elif wave_id == "WAVE_PUBLIC_INFRASTRUCTURE":
            base_catalyst_score += 12.0
            active_triggers.append("Mệnh lệnh giải ngân quyết liệt các đại dự án cao tốc và Sân bay Long Thành vào cao điểm bàn giao.")

        # 10. Đánh giá xúc tác Bán lẻ
        elif wave_id == "WAVE_RETAIL_DOMESTIC":
            base_catalyst_score += 10.0
            active_triggers.append("Chính sách giảm thuế VAT 2% và tăng lương kích cầu tiêu dùng nội địa; Chuỗi bách hóa bắt đầu sinh lời ròng.")

        # Tổng hợp điểm nhiệt độ
        heat_score = round(min(95.0, max(35.0, base_catalyst_score + sentiment_score + momentum_score)), 0)

        # Phân loại pha sóng
        if heat_score >= 83.0:
            phase = "PHA 3: QUÁ NHIỆT / PHÂN PHỐI ĐỈNH"
            phase_badge = "🔴 QUÁ NHIỆT (OVERHEATED)"
            phase_color = "#ef4444"
            action_advice = "Sóng đã tăng quá nóng, báo đài nhắc tên liên tục. Khuyến nghị CHỐT LỜI DẦN theo đà tăng, tuyệt đối không mua mới theo FOMO."
        elif heat_score >= 65.0:
            phase = "PHA 2: BÙNG NỔ & ĐẨY SÓNG (MOMENTUM)"
            phase_badge = "🟢 BÙNG NỔ (SURGING)"
            phase_color = "#10b981"
            action_advice = "VÙNG ĐÁNH SÓNG HIỆU QUẢ NHẤT! Dòng tiền lớn xác nhận tham gia, ưu tiên mua gia tăng vị thế tại cổ phiếu Leader khi vượt nền giá."
        elif heat_score >= 50.0:
            phase = "PHA 1: TÍCH LŨY ÂM THẦM (SMART MONEY GOM)"
            phase_badge = "🟡 TÍCH LŨY (ACCUMULATING)"
            phase_color = "#f59e0b"
            action_advice = "Dòng tiền thông minh bắt đầu gom hàng trước khi truyền thông chú ý. Phù hợp mở vị thế thăm dò từng phần (Tích sản đón sóng)."
        else:
            phase = "PHA 4: HẠ NHIỆT / THOÁI TRÀO"
            phase_badge = "⚪ THOÁI TRÀO (FADING)"
            phase_color = "#94a3b8"
            action_advice = "Dòng tiền đã rút sang nhóm ngành khác. Đứng ngoài quan sát, không bắt đáy khi chưa có tín hiệu gom hàng tạo đáy mới."

        # Gộp triggers thời gian thực và catalysts cốt lõi
        combined_catalysts = list(active_triggers)
        for c in wave["core_catalysts"]:
            if c not in combined_catalysts:
                combined_catalysts.append(c)

        radar_results.append({
            "wave_id": wave_id,
            "wave_name": wave["name_vi"],
            "name_vi": wave["name_vi"],
            "name_en": wave["name_en"],
            "icon": wave["icon"],
            "sector_key": wave["sector_key"],
            "heat_score": int(heat_score),
            "phase": phase,
            "phase_badge": phase_badge,
            "phase_color": phase_color,
            "action_advice": action_advice,
            "active_triggers": active_triggers if active_triggers else wave["core_catalysts"][:2],
            "catalysts": combined_catalysts,
            "core_catalysts": wave["core_catalysts"],
            "leaders": wave["leaders"],
            "high_beta_runners": wave["high_beta_runners"],
            "runners": wave["high_beta_runners"],
            "wave_characteristics": wave["wave_characteristics"],
            "theme_macro": wave["wave_characteristics"],
            "historical_cases": wave.get("historical_cases", ""),
            "historical_reference": wave.get("historical_cases", ""),
            "trading_rule": wave["trading_rule"],
            "warning": action_advice
        })

    # Sắp xếp các sóng từ Nóng nhất đến Nguội nhất
    radar_results = sorted(radar_results, key=lambda x: x["heat_score"], reverse=True)
    return radar_results


# =====================================================================
# 3. HÀM TRUY VẤN VỊ THẾ SÓNG NGÀNH CHO MỘT MÃ CỤ THỂ
# =====================================================================

def get_wave_context_for_ticker(symbol: str, sector_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Xác định chính xác vị thế Sóng Ngành của một mã cổ phiếu:
    - Mã này thuộc Sóng Ngành nào?
    - Đóng vai trò là Cổ phiếu Đầu đàn (LEADER) hay Cổ phiếu Chạy theo (RUNNER)?
    - Sóng Ngành hiện tại đang ở Pha mấy? Nhiệt độ sóng là bao nhiêu?
    - Xúc tác vĩ mô/địa chính trị kích hoạt là gì?
    - Chiến lược đánh sóng tối ưu cho mã này.
    """
    sym = symbol.upper().strip()
    all_waves = evaluate_sector_wave_radar()

    matched_wave = None
    role = "MEMBER"  # LEADER, HIGH_BETA_RUNNER, MEMBER

    # 1. Quét theo danh sách Leader và Runner cụ thể
    for w in all_waves:
        if sym in w["leaders"]:
            matched_wave = w
            role = "👑 CỔ PHIẾU ĐẦU ĐÀN (LEADER)"
            break
        elif sym in w["high_beta_runners"]:
            matched_wave = w
            role = "🚀 CỔ PHIẾU CHẠY THEO BETA CAO (RUNNER)"
            break

    # 2. Nếu chưa khớp mã, quét theo sector_key
    if not matched_wave and sector_key:
        sec = sector_key.upper().strip()
        for w in all_waves:
            if w["sector_key"] == sec:
                matched_wave = w
                role = "🎯 THÀNH VIÊN TRONG SÓNG NGÀNH"
                break

    # 3. Fallback nếu không thuộc 10 sóng lớn
    if not matched_wave:
        return {
            "has_active_wave": False,
            "has_wave": False,
            "wave_id": "NONE",
            "wave_name": "Không thuộc 10 Sóng Ngành Lớn Hiện Hành",
            "wave_icon": "🏛️",
            "heat_score": 50,
            "phase": "Bình thường / Vận động độc lập",
            "phase_badge": "ĐỘC LẬP",
            "ticker_role": "Vận động theo nội tại doanh nghiệp riêng lẻ",
            "role": "Vận động độc lập",
            "active_triggers": ["Cổ phiếu vận động theo câu chuyện tăng trưởng hoặc tái cơ cấu tài chính riêng lẻ, không bị chi phối bởi sóng ngành."],
            "catalysts": ["Cổ phiếu vận động theo câu chuyện tăng trưởng hoặc tái cơ cấu tài chính riêng lẻ, không bị chi phối bởi sóng ngành."],
            "peer_leaders": [],
            "leaders": [],
            "peer_runners": [],
            "runners": [],
            "theme_macro": "Chưa có sóng ngành quy mô lớn bao phủ",
            "trading_rule": "Tập trung phân tích sâu vào Báo cáo tài chính và Dòng tiền CFO của riêng doanh nghiệp thay vì kỳ vọng sóng ngành kéo lên.",
            "historical_reference": "N/A",
            "warning": "Không kỳ vọng dòng tiền sóng ngành nâng đỡ.",
            "wave_advice": "Tập trung phân tích sâu vào Báo cáo tài chính và Dòng tiền CFO của riêng doanh nghiệp thay vì kỳ vọng sóng ngành kéo lên."
        }

    return {
        "has_active_wave": True,
        "has_wave": True,
        "wave_id": matched_wave["wave_id"],
        "wave_name": matched_wave["name_vi"],
        "wave_icon": matched_wave["icon"],
        "heat_score": matched_wave["heat_score"],
        "phase": matched_wave["phase"],
        "phase_badge": matched_wave["phase_badge"],
        "phase_color": matched_wave["phase_color"],
        "ticker_role": role,
        "role": role,
        "active_triggers": matched_wave["active_triggers"],
        "catalysts": matched_wave["catalysts"],
        "core_catalysts": matched_wave.get("core_catalysts", []),
        "leaders": matched_wave["leaders"],
        "peer_leaders": [m for m in matched_wave["leaders"] if m != sym],
        "runners": matched_wave["high_beta_runners"],
        "peer_runners": [m for m in matched_wave["high_beta_runners"] if m != sym],
        "action_advice": matched_wave["action_advice"],
        "trading_rule": matched_wave["trading_rule"],
        "wave_characteristics": matched_wave["wave_characteristics"],
        "theme_macro": matched_wave["wave_characteristics"],
        "historical_reference": matched_wave.get("historical_cases", ""),
        "warning": matched_wave.get("action_advice", "")
    }
