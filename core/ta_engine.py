import pandas as pd
import numpy as np
from typing import Dict, Any


def calculate_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tính toán các chỉ báo kỹ thuật cốt lõi trên chuỗi nến OHLCV.
    """
    if df.empty or len(df) < 20:
        return df

    data = df.copy()

    # 1. Đường trung bình động (EMA & SMA)
    data["ema20"] = data["close"].ewm(span=20, adjust=False).mean()
    data["ema50"] = data["close"].ewm(span=50, adjust=False).mean()
    if len(data) >= 200:
        data["sma200"] = data["close"].rolling(window=200).mean()
    else:
        data["sma200"] = data["close"].rolling(window=len(data)).mean()

    # 2. Khối lượng trung bình 20 phiên
    data["vol_ma20"] = data["volume"].rolling(window=20).mean()

    # 3. RSI 14
    delta = data["close"].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    data["rsi14"] = 100 - (100 / (1 + rs))
    data["rsi14"] = data["rsi14"].fillna(50)

    # 4. MACD (12, 26, 9)
    ema12 = data["close"].ewm(span=12, adjust=False).mean()
    ema26 = data["close"].ewm(span=26, adjust=False).mean()
    data["macd"] = ema12 - ema26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["macd_hist"] = data["macd"] - data["macd_signal"]

    # 5. ATR 14 (Đo độ biến động thực tế)
    high_low = data["high"] - data["low"]
    high_close = (data["high"] - data["close"].shift()).abs()
    low_close = (data["low"] - data["close"].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    data["atr14"] = tr.rolling(window=14).mean()

    # 6. Hỗ trợ và Kháng cự 20 phiên gần nhất
    data["res_20d"] = data["high"].shift(1).rolling(window=20).max()
    data["sup_20d"] = data["low"].shift(1).rolling(window=20).min()

    return data


def evaluate_oneil_momentum(latest: pd.Series, prev: pd.Series) -> Dict[str, Any]:
    """
    Đánh giá theo phong cách CANSLIM / Mark Minervini:
    - Xu hướng mạnh (Trend Template)
    - Breakout kèm thanh khoản bùng nổ (Pocket Pivot / Base Breakout)
    """
    price = float(latest["close"])
    ema20 = float(latest["ema20"])
    ema50 = float(latest["ema50"])
    sma200 = float(latest.get("sma200", ema50))
    vol = float(latest["volume"])
    vol_ma20 = float(latest["vol_ma20"]) if float(latest["vol_ma20"]) > 0 else 1.0
    res_20d = float(latest["res_20d"])

    vol_ratio = round(vol / vol_ma20, 2)
    score = 0
    reasons = []

    # 1. Bộ lọc xu hướng (Trend Template)
    in_uptrend = price > ema20 and ema20 > ema50
    dist_ema20 = ((price - ema20) / ema20 * 100) if ema20 > 0 else 0

    if dist_ema20 > 10.0:
        score += 15
        reasons.append(f"Cảnh báo Overextended: Giá hiện tại cách xa nền ngắn hạn EMA20 ({dist_ema20:.1f}%), rủi ro điều chỉnh cao, hạn chế mua đuổi.")
    elif in_uptrend:
        score += 35
        reasons.append("Giá nằm trong xu hướng tăng mạnh: Giá > EMA20 > EMA50.")
    elif price > ema50:
        score += 20
        reasons.append("Giá đang giữ vững trên đường xu hướng trung hạn EMA50.")
    else:
        score += 5
        reasons.append("Giá đang dưới các đường xu hướng ngắn và trung hạn.")

    # 2. Bùng nổ khối lượng (Volume Spike)
    if vol_ratio >= 1.5:
        score += 35
        reasons.append(f"Khối lượng bùng nổ đột biến gấp {vol_ratio}x lần trung bình 20 phiên (Smart Money tham gia).")
    elif vol_ratio >= 1.2:
        score += 20
        reasons.append(f"Khối lượng giao dịch tăng tích cực ({vol_ratio}x lần MA20).")
    else:
        score += 5
        reasons.append(f"Thanh khoản duy trì ở mức bình thường ({vol_ratio}x MA20).")

    # 3. Điểm bứt phá (Breakout)
    is_breakout = price >= res_20d and vol_ratio >= 1.25
    if is_breakout:
        score += 30
        reasons.append(f"Tín hiệu BREAKOUT vượt đỉnh kháng cự ngắn hạn ({res_20d:,.0f}) kèm thanh khoản xác nhận.")
    elif price >= res_20d:
        score += 15
        reasons.append("Giá áp sát hoặc vượt đỉnh nhưng thanh khoản chưa thực sự bùng nổ.")
    else:
        reasons.append(f"Giá đang vận động tích lũy trong nền giá dưới kháng cự {res_20d:,.0f}.")

    verdict = "MUA BREAKOUT" if score >= 75 else ("CHỜ TÍCH LŨY THÊM" if score >= 50 else "YẾU / KHÔNG MUA")

    return {
        "score": score,
        "is_breakout": is_breakout,
        "vol_ratio": vol_ratio,
        "verdict": verdict,
        "reasons": reasons
    }


def evaluate_vsa_price_action(latest: pd.Series, prev: pd.Series) -> Dict[str, Any]:
    """
    Đánh giá theo phong cách Wyckoff / VSA (Volume Spread Analysis) & Price Action:
    - Nhận diện pha thị trường (Tích lũy, Đẩy giá, Phân phối, Đè giá)
    - Tương quan giữa độ biến động giá (Spread) và Khối lượng (Volume)
    """
    price = float(latest["close"])
    open_p = float(latest["open"])
    high = float(latest["high"])
    low = float(latest["low"])
    vol = float(latest["volume"])
    vol_ma20 = float(latest["vol_ma20"]) if float(latest["vol_ma20"]) > 0 else 1.0
    vol_ratio = vol / vol_ma20

    spread = high - low
    body = abs(price - open_p)
    is_bullish = price >= open_p
    rsi = float(latest.get("rsi14", 50))

    score = 50
    reasons = []

    # Nhận diện pha
    if price > float(latest["ema20"]) and vol_ratio >= 1.2 and is_bullish:
        phase = "Pha Markup (Đang đẩy giá mạnh)"
        score = 85
        reasons.append("Nến tăng thân dài kèm vol lớn xác nhận dòng tiền đẩy giá quyết liệt.")
    elif price >= float(latest["sup_20d"]) and vol_ratio < 0.8:
        phase = "Pha Tích lũy / Cạn cung (Accumulation / Dry Up)"
        score = 70
        reasons.append("Khối lượng sụt giảm kiệt quệ quanh vùng hỗ trợ - biểu hiện cạn cung của cá mập (No Supply).")
    elif not is_bullish and vol_ratio >= 1.5:
        phase = "Pha Phân phối (Distribution / Chốt lời)"
        score = 25
        reasons.append("Nến giảm kèm khối lượng đột biến - áp lực phân phối chốt lời mạnh của Smart Money.")
    else:
        phase = "Pha Dao động tích lũy (Consolidation)"
        score = 55
        reasons.append("Thị trường dao động hẹp, lực cung cầu đang trong trạng thái cân bằng.")

    if rsi >= 75:
        reasons.append(f"Chỉ số RSI ({rsi:.1f}) đang tiến sâu vào vùng quá mua, chú ý rủi ro rung lắc ngắn hạn.")
    elif rsi <= 35:
        reasons.append(f"Chỉ số RSI ({rsi:.1f}) tiệm cận vùng quá bán, áp lực bán đang cạn kiệt.")

    verdict = "DÒNG TIỀN VÀO (TÍCH CỰC)" if score >= 70 else ("DÒNG TIỀN THOÁT (TIÊU CỰC)" if score <= 35 else "TRUNG LẬP")

    return {
        "score": score,
        "phase": phase,
        "rsi": round(rsi, 1),
        "verdict": verdict,
        "reasons": reasons
    }


def detect_advanced_patterns_and_vsa(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Phân tích kỹ thuật nâng cao:
    1. Nhận diện Mô hình nền giá (Price Base Patterns: VCP Minervini, Nền phẳng Flat Base).
    2. Hành vi nến & khối lượng VSA nâng cao (No Supply Test, Spring/Shakeout, SOS).
    3. Các mốc Fibonacci Retracement then chốt (38.2%, 50%, 61.8%).
    4. Vùng Cung Treo Lơ Lửng (Overhead Supply & Đỉnh cũ kẹp hàng).
    """
    if len(df) < 25:
        return {
            "pattern_name": "Đang tích lũy",
            "pattern_verdict": "Cần thêm dữ liệu nến để xác định mẫu hình chuẩn.",
            "vsa_signal": "Bình thường",
            "vsa_signal_desc": "Cung cầu cân bằng tự nhiên.",
            "overhead_supply": 0.0,
            "fibo_382": 0.0,
            "fibo_500": 0.0,
            "fibo_618": 0.0
        }

    latest = df.iloc[-1]
    close = float(latest["close"])
    high = float(latest["high"])
    low = float(latest["low"])
    vol = float(latest["volume"])
    vol_ma20 = float(latest.get("vol_ma20", vol)) if float(latest.get("vol_ma20", vol)) > 0 else vol

    # 1. Fibonacci & Overhead Supply trong 60-120 phiên gần nhất
    lookback = min(len(df), 120)
    window = df.iloc[-lookback:]
    h_max = float(window["high"].max())
    l_min = float(window["low"].min())
    diff = h_max - l_min if h_max > l_min else close * 0.1

    fibo_382 = round(h_max - 0.382 * diff, 0)
    fibo_500 = round(h_max - 0.500 * diff, 0)
    fibo_618 = round(h_max - 0.618 * diff, 0)
    overhead_supply = round(h_max, 0)

    # 2. Nhận diện Mô hình nền giá (Base Pattern)
    w20 = df.iloc[-20:]
    h20 = float(w20["high"].max())
    l20 = float(w20["low"].min())
    range20_pct = round(((h20 - l20) / l20) * 100, 1) if l20 > 0 else 5.0

    pattern_name = "Nền dao động tích lũy"
    pattern_verdict = f"Giá dao động trong biên độ {range20_pct}% trong 20 phiên gần nhất."
    
    if len(df) >= 50:
        w40 = df.iloc[-40:-20]
        h40 = float(w40["high"].max())
        l40 = float(w40["low"].min())
        range40_pct = round(((h40 - l40) / l40) * 100, 1) if l40 > 0 else 10.0
        
        if range40_pct > range20_pct and range20_pct <= 9.0:
            pattern_name = "Mô hình Thu hẹp Biến động (VCP - Mark Minervini)"
            pattern_verdict = f"Độ biến động thu hẹp tích cực từ {range40_pct}% xuống {range20_pct}%, khối lượng cạn kiệt ở nhịp co thắt cuối trước điểm bùng nổ."
        elif range20_pct <= 6.5:
            pattern_name = "Nền giá phẳng siết chặt (Tight Flat Base)"
            pattern_verdict = f"Biên độ dao động cực kỳ chặt chẽ ({range20_pct}%), lực cung cạn kiệt, sẵn sàng bứt phá khi có dòng tiền mồi."
    elif range20_pct <= 6.5:
        pattern_name = "Nền giá phẳng siết chặt (Tight Flat Base)"
        pattern_verdict = f"Nền giá phẳng dao động hẹp ({range20_pct}%), lực cung bán suy giảm."

    # 3. Hành vi nến VSA chuyên sâu
    atr = float(latest.get("atr14", close * 0.025))
    spread = high - low
    is_up = close >= float(latest["open"])
    vol_ratio = vol / vol_ma20 if vol_ma20 > 0 else 1.0

    vsa_signal = "Thanh khoản ổn định"
    vsa_signal_desc = "Cung cầu vận động tự nhiên theo nhịp điệu thị trường."

    if spread <= atr * 0.85 and vol_ratio < 0.65:
        vsa_signal = "Phiên Test Cung Cạn Kiệt (No Supply Test)"
        vsa_signal_desc = "Biên độ nến hẹp kèm khối lượng teo tóp dưới 65% MA20, chứng minh nhỏ lẻ đã cạn lực bán, áp lực cung không còn."
    elif low < float(latest.get("sup_20d", low)) and close >= float(latest.get("sup_20d", low)) and (close - low) > (high - close):
        vsa_signal = "Phiên Rũ Bỏ Đáy Rút Chân (Spring / Shakeout)"
        vsa_signal_desc = "Giá bị đạp thủng hỗ trợ trong phiên để ép nhỏ lẻ bán ra, sau đó kéo ngược đóng cửa cao nhất phiên. Bẫy gấu rũ bỏ kinh điển!"
    elif is_up and vol_ratio >= 1.4:
        vsa_signal = "Phiên Bùng Nổ Dòng Tiền Lớn (SOS - Sign of Strength)"
        vsa_signal_desc = f"Nến xanh tăng dứt khoát kèm thanh khoản đột biến gấp {vol_ratio:.1f}x lần MA20 xác nhận Big Boys đạp ga vào tiền quyết liệt."

    lookback_window = lookback
    overhead_val = round(h_max, 0)
    range40_val = range40_pct if 'range40_pct' in locals() else round(range20_pct * 1.5, 1)

    return {
        "pattern_name": pattern_name,
        "pattern_verdict": pattern_verdict,
        "range_20d_pct": range20_pct,
        "vsa_signal": vsa_signal,
        "vsa_signal_desc": vsa_signal_desc,
        "swing_low": l_min,
        "swing_high": h_max,
        "overhead_supply": overhead_val,
        "fibo_382": fibo_382,
        "fibo_500": fibo_500,
        "fibo_618": fibo_618,
        "vcp": {
            "vcp_stage": pattern_name,
            "contractions": [f"Nhịp co thắt trước: ~{range40_val}%", f"Nhịp gần nhất: {range20_pct}%"],
            "vcp_verdict": pattern_verdict
        },
        "vsa_signals": {
            "signal_descriptions": [f"{vsa_signal}: {vsa_signal_desc}"],
            "smart_money_action": "Đang âm thầm gom hàng và kiểm tra cung" if "Test" in vsa_signal or "Spring" in vsa_signal else ("Chủ động kích hoạt đà tăng giá (SOS)" if "SOS" in vsa_signal else "Vận động cung cầu tự nhiên")
        },
        "fibonacci": {
            "swing_low": l_min,
            "swing_high": h_max,
            "fibo_382": fibo_382,
            "fibo_500": fibo_500,
            "fibo_618": fibo_618,
            "current_fibo_zone": "Nằm trên vùng Fibo 38.2% (Nhịp sóng tăng rất khỏe)" if close >= fibo_382 else ("Vùng cân bằng giữa Fibo 38.2% và 50.0%" if close >= fibo_500 else "Vùng hỗ trợ Fibo 61.8% (Ngưỡng phòng thủ quan trọng)")
        },
        "overhead_supply_detail": {
            "resistance_cluster": f"{overhead_val:,.0f} đ (Đỉnh cao nhất {lookback_window} phiên)",
            "supply_intensity": "Thấp (Đã bứt phá đỉnh)" if close >= overhead_val else ("Vừa phải" if (overhead_val - close) / close < 0.08 else "Đáng kể (Cách đỉnh >8%)"),
            "explanation": f"Vùng cản tâm lý của nhà đầu tư kẹp hàng đỉnh cũ quanh {overhead_val:,.0f} đ. {'Giá đã tiệm cận vùng đỉnh, lực cung chốt hòa vốn đang được hấp thụ tốt.' if close >= overhead_val * 0.95 else 'Cần theo dõi thêm thanh khoản khi giá tiến về kiểm tra vùng đỉnh này.'}"
        }
    }


def analyze_technicals(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Tổng hợp phân tích kỹ thuật toàn diện từ chuỗi nến.
    """
    if df.empty or len(df) < 5:
        return {
            "ta_total_score": 50,
            "oneil": {"score": 50, "verdict": "THIẾU DỮ LIỆU", "reasons": []},
            "vsa": {"score": 50, "verdict": "THIẾU DỮ LIỆU", "reasons": []},
            "advanced_ta": {},
            "indicators": {}
        }

    df_ind = calculate_indicators(df)
    latest = df_ind.iloc[-1]
    prev = df_ind.iloc[-2] if len(df_ind) >= 2 else latest

    oneil = evaluate_oneil_momentum(latest, prev)
    vsa = evaluate_vsa_price_action(latest, prev)
    advanced_ta = detect_advanced_patterns_and_vsa(df_ind)

    # Tổng điểm TA (50% O'Neil Breakout, 50% VSA / Price Action)
    ta_total_score = int(oneil["score"] * 0.5 + vsa["score"] * 0.5)

    return {
        "ta_total_score": ta_total_score,
        "oneil": oneil,
        "vsa": vsa,
        "advanced_ta": advanced_ta,
        "indicators": {
            "close": float(latest["close"]),
            "ema20": float(latest["ema20"]),
            "ema50": float(latest["ema50"]),
            "sma200": float(latest.get("sma200", 0.0)),
            "rsi14": float(latest.get("rsi14", 50.0)),
            "atr14": float(latest.get("atr14", 0.0)),
            "res_20d": float(latest.get("res_20d", float(latest["close"]))),
            "sup_20d": float(latest.get("sup_20d", float(latest["close"]))),
            "vol_ratio": float(oneil["vol_ratio"])
        }
    }
