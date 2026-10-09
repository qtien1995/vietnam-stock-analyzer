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


def analyze_technicals(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Tổng hợp phân tích kỹ thuật toàn diện từ chuỗi nến.
    """
    if df.empty or len(df) < 5:
        return {
            "ta_total_score": 50,
            "oneil": {"score": 50, "verdict": "THIẾU DỮ LIỆU", "reasons": []},
            "vsa": {"score": 50, "verdict": "THIẾU DỮ LIỆU", "reasons": []},
            "indicators": {}
        }

    df_ind = calculate_indicators(df)
    latest = df_ind.iloc[-1]
    prev = df_ind.iloc[-2] if len(df_ind) >= 2 else latest

    oneil = evaluate_oneil_momentum(latest, prev)
    vsa = evaluate_vsa_price_action(latest, prev)

    # Tổng điểm TA (50% O'Neil Breakout, 50% VSA / Price Action)
    ta_total_score = int(oneil["score"] * 0.5 + vsa["score"] * 0.5)

    return {
        "ta_total_score": ta_total_score,
        "oneil": oneil,
        "vsa": vsa,
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
