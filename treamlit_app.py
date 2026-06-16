# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
import concurrent.futures

# 📊 老板精简确认的45只全量精密常驻资产池
TICKERS = [
    "COHU", "VECO", "ENTG", "UCTT", "ICHR", "AXTI", "WOLF", "POWI", 
    "AOSL", "MTSI", "AMAT", "KLAC", "CIFR", "WULF", "HUT", "FLNC", 
    "CIEN", "SMTC", "CRDO", "TXN", "ON", "MCHP", "GFS", "JBL", 
    "HIMX", "ALAB", "NOK", "TE", "ENPH", "VPG", "NVTS", "AEHR", 
    "AMKR", "ASX", "PL", "ARM", "BE", "TSEM", "AMZN", "LRCX", 
    "AAOI", "COHR", "ETN", "VRT", "INTC"
]

# 开启全球量化大屏全宽布局
st.set_page_config(layout="wide")

# 🎨 视觉平衡样式表
st.markdown("""
    <style>
    .block-container {
        padding-top: 1.8rem !important;
        padding-bottom: 1.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 0.8rem !important;
    }
    h1 {
        font-size: 2.2rem !important;
        margin-bottom: 0.1rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ 第一部分：异步微线程引擎 (颗粒化高速解耦)
# ==========================================

@st.cache_data(ttl=300)
def get_clean_data_individually(ticker):
    """单兵颗粒化缓存舱：每只股票独立占用内存块，0毫秒极速响应"""
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    try:
        # 🛡️ 4秒硬熔断机制，超时直接切断，绝不拖累大盘总线
        df = yf.download(ticker, period="1y", progress=False, session=session, timeout=4)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        return df
    except:
        return None

def analyze_loaded_df(ticker, df):
    """纯内存量化算力矩阵 (耗时近乎0毫秒)"""
    df = df.dropna(subset=['Close'])
    if len(df) < 60:
        return None

    close = df['Close'].astype(float)
    volume = df['Volume'].astype(float)

    latest_close = float(close.iloc[-1])
    latest_vol = float(volume.iloc[-1])

    # 1. 均线趋势
    df['EMA_9'] = close.ewm(span=9, adjust=False).mean()
    df['SMA_24'] = close.rolling(window=24).mean()
    ema_9_now = float(df['EMA_9'].iloc[-1])
    sma_24_now = float(df['SMA_24'].iloc[-1])
    ema_9_prev = float(df['EMA_9'].iloc[-2])
    sma_24_prev = float(df['SMA_24'].iloc[-2])

    if ema_9_prev < sma_24_prev and ema_9_now >= sma_24_now:
        trend_raw = "gold_cross"
    elif ema_9_prev > sma_24_prev and ema_9_now <= sma_24_now:
        trend_raw = "dead_cross"
    elif ema_9_now > sma_24_now:
        trend_raw = "bull"
    else:
        trend_raw = "bear"

    # 2. RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_now = float(rsi.iloc[-1])
    rsi_prev = float(rsi.iloc[-2])
    rsi_change = rsi_now - rsi_prev

    # 3. 布林带与斐波那契融合支撑阻力
    df['BB_mid'] = close.rolling(window=20).mean()
    df['BB_std'] = close.rolling(window=20).std()
    df['BB_lower'] = df['BB_mid'] - (2 * df['BB_std'])
    
    recent_df = df.tail(60)
    high_p = float(recent_df['High'].max())
    low_p = float(recent_df['Low'].min())
    diff = high_p - low_p
    fib_382 = high_p - 0.382 * diff
    fib_618 = high_p - 0.618 * diff

    support = max(float(df['BB_lower'].iloc[-1]), fib_618)
    resistance = fib_382

    if latest_close > resistance:
        level_raw = "breakout"
    elif latest_close < support:
        level_raw = "breakdown"
    else:
        level_raw = "range"

    suggested_buy_price = round(support * 1.015, 2)

    # 4. 量价状态
    df['Vol_SMA20'] = volume.rolling(window=20).mean()
    avg_vol = float(df['Vol_SMA20'].iloc[-1])
    price_change = latest_close - float(close.iloc[-2])

    is_vol_dump = (latest_vol > avg_vol * 1.5 and price_change <= 0)
    is_vol_surge = (latest_vol > avg_vol * 1.5 and price_change > 0)

    if latest_vol > avg_vol * 1.5:
        vol_raw = "v_up" if price_change > 0 else "v_down"
    elif latest_vol < avg_vol * 0.7:
        vol_raw = "v_low"
    else:
        vol_raw = "v_norm"

    # 5. 评分系统
    score = 50
    if trend_raw == "gold_cross": score += 25
    elif trend_raw == "bull": score += 15
    elif trend_raw == "dead_cross": score -= 25
    elif trend_raw == "bear": score -= 15
    if level_raw == "breakout": score += 15
    if is_vol_surge: score += 10
    elif is_vol_dump: score -= 10
    score = max(10, min(95, score))

    # 6. 自动化决策状态元数据
    if is_vol_dump and (trend_raw == "dead_cross" or level_raw == "breakdown"):
        strat_raw = "stop"
    elif level_raw == "breakout" and is_vol_surge and score >= 80:
        strat_raw = "strong_buy"
    elif level_raw == "breakout" and is_vol_dump:
        strat_raw = "fake"
    elif latest_close <= suggested_buy_price and not is_vol_dump:
        if trend_raw in ["gold_cross", "bull"]:
            strat_raw = "golden"
        else:
            strat_raw = "scale_in"
    elif trend_raw == "gold_cross" and not is_vol_dump:
        strat_raw = "tentative"
    elif trend_raw == "bull" and latest_close <= support * 1.04:
        strat_raw = "pullback"
    elif trend_raw == "bull" and vol_raw == "v_norm":
        strat_raw = "hold"
    else:
        strat_raw = "wait"

    return {
        "Ticker": ticker, "Price": round(latest_close, 2), "Suggested Buy Price": suggested_buy_price, "Score": int(score),
        "trend_raw": trend_raw, "level_raw": level_raw, "vol_raw": vol_raw, "strat_raw": strat_raw,
        "rsi_now": rsi_now, "rsi_change": rsi_change, "9 EMA": round(ema_9_now, 2), "24 SMA": round(sma_24_now, 2),
        "Support": round(support, 2), "Resistance": round(resistance, 2)
    }

# ==========================================
# 🖥️ 第二部分：前端数据渲染交互主控
