# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
from tickers import TICKERS

# 开启全宽布局
st.set_page_config(
    layout="wide", 
    page_title="AI Trading Pro"
)

# 🎨 智能皮肤：柔和舒适的浅色奶油白看盘背景
st.markdown("""
    <style>
    .main, .stApp {
        background-color: #fcfaf0 !important;
        color: #333 !important;
    }
    .block-container {
        padding-top: 0.6rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
    }
    [data-testid="stVerticalBlock"] {
        gap: 0.4rem !important;
    }
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e1e1e1 !important;
    }
    .stDataFrame {
        background-color: #ffffff !important;
        border: 1px solid #d1d1d1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ 第一部分：核心纯量化数据引擎
# ==========================================

def get_secure_session():
    session = requests.Session()
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    session.headers.update({'User-Agent': ua})
    return session

def get_data(ticker, session, retries=3):
    for _ in range(retries):
        try:
            df = yf.download(
                ticker, 
                period="1y", 
                progress=False, 
                session=session
            )
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

    # 安全因子计算短句化
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

    # 6. 超短布林条件卡位
    c_dump = is_vol_dump
    c_dead = (trend_raw == "dead_cross")
    c_drop = (level_raw == "breakdown")
    c_out = (level_raw == "breakout")
    c_surge = is_vol_surge
    c_high = (score >= 80)
    c_buy_p = (latest_close <= suggested_buy_price)
    c_gold = (trend_raw == "gold_cross")
    c_bull = (trend_raw == "bull")
    c_norm = (vol_raw == "v_norm")
    c_dip = (latest_close <= support * 1.04)

    # 决策树
    if c_dump and (c_dead or c_drop):
        strat_raw = "stop"
    elif c_out and c_surge and c_high:
        strat_raw = "strong_buy"
    elif c_out and c_dump:
        strat_raw = "fake"
    elif c_buy_p and (not c_dump):
        if c_gold or c_bull:
            strat_raw = "golden"
        else:
            strat_raw = "scale_in"
    elif c_gold and (not c_dump):
        strat_raw = "tentative"
    elif c_bull and c_dip:
        strat_raw = "pullback"
    elif c_bull and c_norm:
        strat_raw = "hold"
    else:
        strat_raw = "wait"

    return {
        "Ticker": ticker,
        "Price": round(latest_close, 2),
        "Suggested Buy Price": suggested_buy_price,
        "Score": int(score),
        "trend_raw": trend_raw,
        "level_raw": level_raw,
        "vol_raw": vol_raw,
        "strat_raw": strat_raw,
        "rsi_now": rsi_now,
        "rsi_change": rsi_change,
        "9 EMA": round(ema_9_now, 2),
        "24 SMA": round(sma_24_now, 2),
        "Support": round(support, 2),
        "Resistance": round(resistance, 2)
    }

# ==========================================
# 🖥️ 第二部分：前端数据渲染交互主控
# ==========================================

# 🌐 彻底精简单选文案，斩断截断风险
l_lbl = "Select Language / 语言"
l_opts = ["Chinese", "English"]
lang_choice = st.sidebar.radio(l_lbl, l_opts)

if lang_choice == "English":
    lang = "EN"
else:
    lang = "CN"

if lang == "EN":
    t_title = "⚡ BLOOMBERG QUANT APP"
    t_cap = "Proprietary Desk Terminal Pro"
    t_ctrl = "⚙️ Console"
    t_pool = "监控池管理"
    t_lbl = "Add Tickers:"
    t_scan
