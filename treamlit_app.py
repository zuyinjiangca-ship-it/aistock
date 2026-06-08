# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
from tickers import TICKERS

# 开启全宽布局
st.set_page_config(layout="wide", page_title="AI Trading Pro", page_icon="🚀")

# 🎨 视觉平衡：柔和舒适的浅色奶油白背景
st.markdown("""
    <style>
    .main, .stApp {
        background-color: #fcfaf0 !important;
        color: #333 !important;
    }
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 0.3rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #d1d1d1 !important;
    }
    [data-testid="stSidebar"] p {
        color: #333 !important;
    }
    .terminal-title {
        font-family: 'Courier New', Courier, monospace;
        font-weight: 900 !important;
        background: linear-gradient(45deg, #0047AB, #56d364);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 1.6rem !important;
        margin-bottom: 0rem !important;
        padding-bottom: 0rem !important;
    }
    .terminal-caption {
        color: #666 !important;
        font-size: 0.8rem !important;
        border-left: 3px solid #0047AB;
        padding-left: 8px;
        margin-bottom: 0.5rem !important;
    }
    .section-title {
        color: #0047AB !important;
        font-weight: bold !important;
        border-bottom: 1px solid #d1d1d1;
        padding-bottom: 2px;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        font-size: 1rem !important;
    }
    .kpi-container {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 0.2rem;
    }
    .kpi-card {
        flex: 1;
        background: #f1f1f1;
        border: 1px solid #d1d1d1;
        border-radius: 6px;
        padding: 0.4rem 0.8rem;
        box-shadow: 0 2px 6px rgba(0,0,0,0.1);
    }
    .kpi-label {
        font-size: 0.7rem;
        color: #666;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 1.4rem;
        font-weight: bold;
        color: #0047AB;
        margin-top: 0.1rem;
    }
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #6A1B9A 0%, #238636 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 2rem !important;
        font-size: 0.95rem !important;
        font-weight: bold !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    .stDataFrame {
        background-color: #ffffff !important;
        border: 1px solid #d1d1d1 !important;
        border-radius: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ 第一部分：核心纯量化数据引擎
# ==========================================

def get_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session

def get_data(ticker, session, retries=3):
    for _ in range(retries):
        try:
            df = yf.download(ticker, period="1y", progress=False, session=session)
            if not df.empty:
                if isinstance(df.columns, pd.MultiIndex):
                    df.columns = df.columns.get_level_values(0)
                return df
        except:
            time.sleep(0.5)
    return None

def analyze_stock_raw(ticker):
    session = get_secure_session()
    df = get_data(ticker, session)

    if df is None or df.empty:
        return None

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

    # 3. 布林带与斐波那契
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

    # 🔥 极限抗噪改动：把公式彻底做短，一行绝不超过5个字符，全面免疫任何高频截断
    sf = 1.015
    suggested_buy_price = round(support * sf, 2)

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

    # 5. 评分
    score = 50
    if trend_raw == "gold_cross": score += 25
    elif trend_raw == "bull": score += 15
    elif trend_raw == "dead_cross": score -= 25
    elif trend_raw == "bear": score -= 15
    if level_raw == "breakout": score += 15
    if is_vol_surge: score += 10
    elif is_vol_dump: score -= 10
    score = max(10, min(95, score))

    # 6. 策略决策
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
    elif trend_raw == "bull
