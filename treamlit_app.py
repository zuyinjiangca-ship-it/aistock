# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
from tickers import TICKERS

# 开启全球量化大屏全宽布局
st.set_page_config(layout="wide", page_title="AI Trading Pro", page_icon="🚀")

# 🎨 投行专属：硬核注入“大气平衡、柔和背景”高级 CSS 样式表
st.markdown("""
    <style>
    /* 1. 恢复大气舒适的奶油白柔和全屏背景 */
    .main, .stApp {
        background-color: #fcfaf0 !important;
        color: #333 !important;
    }
    
    /* 极致压缩页面主容器四周的空白 */
    .block-container {
        padding-top: 0.5rem !important;
        padding-bottom: 0rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    /* 压缩Streamlit组件之间的默认间距 */
    [data-testid="stVerticalBlock"] {
        gap: 0.3rem !important;
    }
    
    /* 2. 纯白侧边栏彭博分流舱样式 */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #d1d1d1 !important;
    }
    [data-testid="stSidebar"] p {
        color: #333 !important;
    }
    
    /* 3. 🔥 极致空间榨汁：压缩顶部标题区域，强行下移标题 */
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
    
    /* 4. 压缩表格小标题 */
    .section-title {
        color: #0047AB !important;
        font-weight: bold !important;
        border-bottom: 1px solid #d1d1d1;
        padding-bottom: 2px;
        margin-top: 0.2rem !important;
        margin-bottom: 0.2rem !important;
        font-size: 1rem !important;
    }

    /* 5. 磨砂玻璃科技数据卡片 (KPI Blocks) */
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
        letter-spacing: 0.5px;
    }
    .kpi-value {
        font-size: 1.4rem;
        font-weight: bold;
        color: #0047AB;
        margin-top: 0.1rem;
    }

    /* 6. 极客微光律动扫描按钮 */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #6A1B9A 0%, #238636 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.4rem 2rem !important;
        font-size: 0.95rem !important;
        font-weight: bold !important;
        letter-spacing: 0.5px !important;
        box-shadow: 0 2px 8px rgba(35, 134, 54, 0.2) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 4px 12px rgba(88, 166, 255, 0.4) !important;
        background: linear-gradient(135deg, #7B1FA2 0%, #56d364 100%) !important;
    }
    
    /* 7. 让Streamlit表格自然横向平摊，杜绝左右滚动 */
    .stDataFrame {
        background-color: #ffffff !important;
        border: 1px solid #d1d1d1 !important;
        border-radius: 6px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ 第一部分：核心纯量化数据引擎 (计算与语言完全解耦)
# ==========================================

def get_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
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
    """只负责纯粹的数学指标测算，返回标准化多空信号元数据，不掺杂任何翻译语言，极大加快缓存速度"""
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

    # 🔥 机构防御推荐买入价
    suggested_buy_price = round(support *
