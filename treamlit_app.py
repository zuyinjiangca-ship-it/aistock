# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
from tickers import TICKERS

# 1. 开启全宽布局与尊享标题
st.set_page_config(
    layout="wide", 
    page_title="AI Trading Pro"
)

# 🎨 投行美学重构：高端大气的低标题、奶油色柔和清爽看盘皮肤
st.markdown("""
    <style>
    /* 全屏换装：高级柔和象牙奶油色，文字深度灰色，保护视力 */
    .main, .stApp {
        background-color: #f7f7f2 !important;
        color: #2c3e50 !important;
    }
    /* 极致控制内边距：标题高规格下移，留出呼吸感空间 */
    .block-container {
        padding-top: 2.5rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    /* 纯净白高级自营舱侧边栏 */
    [data-testid="stSidebar"] {
        background-color: #ffffff !important;
        border-right: 1px solid #e6e6e2 !important;
    }
    /* 表格背景与圆角美化 */
    .stDataFrame {
        background-color: #ffffff !important;
        border: 1px solid #e1e1db !important;
        border-radius: 8px !important;
    }
    /* 大牌渐变低位标题样式 */
    .terminal-title {
        font-family: 'Helvetica Neue', Arial, sans-serif;
        font-weight: 800 !important;
        color: #1a365d !important;
        font-size: 2.2rem !important;
        margin-bottom: 0.2rem !important;
    }
    .terminal-caption {
        color: #7f8c8d !important;
        font-size: 0.9rem !important;
        margin-bottom: 1.5rem !important;
    }
    .section-title {
        color: #2c3e50 !important;
        font-weight: 700 !important;
        border-bottom: 2px solid #e6e6e2;
        padding-bottom: 4px;
        margin-top: 1rem !important;
        margin-bottom: 0.6rem !important;
        font-size: 1.1rem !important;
    }
    /* 极客扫描主按钮视觉进化 */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #2c3e50 0%, #1a365d 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 2rem !important;
        font-size: 1rem !important;
        font-weight: bold !important;
        box-shadow: 0 4px 12px rgba(26, 54, 93, 0.15) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-1px) !important;
        box-shadow: 0 6px 15px rgba(26, 54, 93, 0.25) !important;
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

    # 6. 超短布林条件
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
        "Ticker": ticker, "Price": round(latest_close, 2), "Suggested Buy Price": suggested_buy_price, "Score": int(score),
        "trend_raw": trend_raw, "level_raw": level_raw, "vol_raw": vol_raw, "strat_raw": strat_raw,
        "rsi_now": rsi_now, "rsi_change": rsi_change, "9 EMA": round(ema_9_now, 2), "24 SMA": round(sma_24_now, 2),
        "Support": round(support, 2), "Resistance": round(resistance, 2)
    }

# ==========================================
# 🖥️ 第二部分：前端数据渲染交互主控
# ==========================================

# 🌐 极其安全的多语言判定舱
lang_choice = st.sidebar.radio(
    "Select Language / 语言切换", 
    ["中文", "English"]
)
lang = "EN" if lang_choice == "English" else "CN"

if lang == "EN":
    t_title, t_cap = "⚡ QUANT TRADING MATRIX", "Institutional Level Adaptive Technical Radar Terminal"
    t_ctrl, t_pool, t_lbl = "⚙️ Terminal Control", "➕ Watchlist Assets", "Insert Custom Tickers (Comma/Space):"
    t_scan, t_board, t_top5 = "⚡ RUN ASSET RADAR SCAN", "📊 Quantitative Strategy Decision Matrix", "🔥 Alpha Seekers: Top 5 High-Score"
else:
    t_title, t_cap = "⚡ 智能量化资产雷达", "顶级自营交易台专用：多维动能与强防御推荐买点自动化系统"
    t_ctrl, t_pool, t_lbl = "⚙️ 系统控制台", "➕ 动态自选股监控池", "在此输入想监控的资产代码（空格或逗号分隔）："
    t_scan, t_board, t_top5 = "⚡ 激活雷达全量扫描", "📊 实时策略量化决策看板", "🔥 强多头绝对加仓标的 (TOP 5)"

# 绘制下移的大牌标题区
st.markdown(f'<div class="terminal-title">{t_title}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="terminal-caption">{t_cap}</div>', unsafe_allow_html=True)

# 独立内存常驻风控险箱
if "raw_scan_results" not in st.session_state:
    st.session_state.raw_scan_results = None
if "failed_watchlist" not in st.session_state:
    st.session_state.failed_watchlist = []

# 🛡️ 绝杀防御：全版本安全兼容 Query Params 模块
default_text = ""
try:
    if hasattr(st, "query_params"):
        if hasattr(st.query_params, "get_all"):
            p_list = st.query_params.get_all("tickers")
            default_text = p_list[0] if p_list else ""
        else:
            default_text = st.query_params.get("tickers", "")
    else:
        old_qp = st.experimental_get_query_params()
        default_text = old_qp.get("tickers", [""])[0]
except:
    pass

st.sidebar.markdown("---")
st.sidebar.header(t_ctrl)
st.sidebar.subheader(t_pool)

user_input = st.sidebar.text_area(t_lbl, value=default_text, height=120)

try:
    if user_input != default_text:
        if user_input.strip():
            st.query_params["tickers"] = user_input.strip()
        else:
            if hasattr(st, "query_params") and hasattr(st.query_params, "clear"):
                st.query_params.clear()
            else:
                st.experimental_set_query_params()
except:
    pass

custom_tickers = []
if user_input:
    custom_tickers = [t.strip().upper() for t in user_input.replace("，", " ").replace(",", " ").split() if t.strip()]

combined_tickers = list(dict.fromkeys(TICKERS + custom_tickers))
st.sidebar.write(f"📊 Monitored Symbols: `{len(combined_tickers)}`")

@st.cache_data(ttl=600)
def run_full_heavy_scan(tickers_list):
    results, failed = [], []
    for t in tickers_list:
        try:
            res = analyze_stock_raw(t)
            if res: results.append(res)
            else: failed.append(t)
        except: failed.append(t)
    return pd.DataFrame(results), failed

if st.button(t_scan, type="primary"):
    with st.spinner("Processing Matrix..."):
        df, failed_tickers = run_full_heavy_scan(combined_tickers)
        st.session_state.raw_scan_results = df
        st.session_state.failed_watchlist = failed_tickers

user_failed = [f for f in st.session_state.failed_watchlist if f in custom_tickers]
if user_failed:
    st.sidebar.error(f"⚠️ Failed to fetch: `{', '.join(user_failed)}`")

# 渲染数据表格
if st.session_state.raw_scan_results is not None and not st.session_state.raw_scan_results.empty:
    df_raw = st.session_state.raw_scan_results.copy()

    high_alpha_count = len(df_raw[df_raw['Score'] >= 75])
    risk_count = len(df_raw[df_raw['strat_raw'] == 'stop'])
    
    # 纯原生组件 KPI 状态栏，杜绝 HTML 渲染问题
    k1, k2, k3 = st.columns(3)
    with k1: st.metric("监控总数 / TOTAL POOL", len(combined_tickers))
    with k2: st.metric("强多头 / BULL ALPHA", high_alpha_count)
    with k3: st.metric("风险提示 / RISK ALERTS", risk_count)

    if lang == "EN":
        trans_trend = {"gold_cross": "🎯 Golden Cross", "dead_cross": "🚨 Death Cross", "bull": "📈 Bullish Trend", "bear": "📉 Bearish Momentum"}
        trans_level = {"breakout": "🚀 Breakout", "breakdown": "⚠️ Breakdown", "range": "Range Bound"}
        trans_vol = {"v_up": "🔥 Vol Surge", "v_down": "💥 Vol Dump", "v_low": "💤 Declining", "v_norm": "Normal"}
        trans_strat = {
            "stop": "🚨 Reduce / Stop Loss", "strong_buy": "🦅 Strong Buy / Add", "fake": "👀 Fake Out / No Chase",
            "golden": "👑 Golden Entry", "scale_in": "📥 Scale In (Left)", "tentative": "🏹 Open Long",
            "pullback": "📥 Buy the Dip", "hold": "👌 Trend Ok / Hold", "wait": "⏳ Wait & See"
        }
    else:
        trans_trend = {"gold_cross": "🎯 金叉启动", "dead_cross": "🚨 死叉确立", "bull": "📈 多头趋势", "bear": "📉 空头动能"}
        trans_level = {"breakout": "🚀 突破阻力", "breakdown": "⚠️ 跌破支撑", "range": "区间震荡"}
        trans_vol = {"v_up": "🔥 放量上涨", "v_down": "💥 放量下跌", "v_low": "💤 缩量", "v_norm": "正常"}
        trans_strat = {
            "stop": "🚨 坚决减仓 / 止损", "strong_buy": "🦅 强力买入 / 加仓", "fake": "👀 假突破预警 / 暂勿追",
            "golden": "👑 黄金买点 / 左侧", "scale_in": "📥 左侧潜伏 / 分批", "tentative": "🏹 试探建仓 / 开多",
            "pullback": "📥 低吸买入", "hold": "👌 趋势良好 / 持股", "wait": "⏳ 震荡蓄势 / 观望"
        }

    processed_rows = []
    for _, row in df_raw.iterrows():
        r_chg = row['rsi_change']
        rsi_trend = f"🔺+{round(r_chg, 1)}" if r_chg > 0 else f"🔻{round(r_chg, 1)}"
        if row['rsi_now'] >= 70: rsi_advice = f"{round(row['rsi_now'], 1)} | 🔥超买" if lang == "CN" else f"{round(row['rsi_now'], 1)} | 🔥OB"
        elif row['rsi_now'] <= 30: rsi_advice = f"{round(row['rsi_now'], 1)} | 🛡️超卖" if lang == "CN" else f"{round(row['rsi_now'], 1)} | 🛡️OS"
        else: rsi_advice = f"{round(row['rsi_now'], 1)} | ({rsi_trend})"

        processed_rows.append({
            "Ticker": row["Ticker"], "Price": row["Price"], "Suggested Buy Price": row["Suggested Buy Price"], "Score": row["Score"],
            "Trading Strategy": trans_strat.get(row["strat_raw"], row["strat_raw"]),
            "Trend": trans_trend.get(row["trend_raw"], row["trend_raw"]),
            "Position Level": trans_level.get(row["level_raw"], row["level_raw"]),
            "Volume Status": trans_vol.get(row["vol_raw"], row["vol_raw"]),
            "RSI Status & Advice": rsi_advice, "9 EMA": row["9 EMA"], "24 SMA": row["24 SMA"], "Support": row["Support"], "Resistance": row["Resistance"]
        })
    
    display_df = pd.DataFrame(processed_rows)
    display_df = display_df.sort_values(by="Score", ascending=False).reset_index(drop=True)

    rename_dict = {
        "Ticker": "代码", "Price": "当前价", "Suggested Buy Price": "推荐买入价", "Score": "评分", "Trading Strategy": "交易策略",
        "Trend": "均线趋势", "Position Level": "关键位置", "Volume Status": "量态状态", "RSI Status & Advice": "RSI状态与建议",
        "9 EMA": "9 EMA", "24 SMA": "24 SMA", "Support": "核心支撑", "Resistance": "核心阻力"
    }
    final_render_df = display_df.rename(columns=rename_dict)
    target_strategy_col = rename_dict["Trading Strategy"]

    st.markdown(f'<div class="section-title">{t_board}</div>', unsafe_allow_html=True)
    
    def style_strategy(val):
        val_str = str(val)
        if any(x in val_str for x in ["强力买入", "金叉", "黄金买点", "Strong Buy", "Golden Cross"]): return "background-color: #e6f4ea; color: #137333; font-weight: bold;"
        if any(x in val_str for x in ["低吸", "分批", "左侧", "Pullback Buy"]): return "background-color: #f1f8e9; color: #558b2f; font-weight: bold;"
        if any(x in val_str for x in ["假突破", "预警", "暂勿追", "Fake Out"]): return "background-color: #fffde7; color: #f57f17; font-weight: bold;"
        if any(x in val_str for x in ["减仓", "止损", "Reduce", "Stop Loss"]): return "background-color: #fce8e6; color: #c5221f; font-weight: bold;"
        return ""
    
    styled_df = final_render_df.style.map(style_strategy, subset=[target_strategy_col])
    
    col_config = {
        rename_dict["Ticker"]: st.column_config.TextColumn(width="small"),
        rename_dict["Price"]: st.column_config.NumberColumn(width="small"),
        rename_dict["Suggested Buy Price"]: st.column_config.NumberColumn(width="small"),
        rename_dict["Score"]: st.column_config.NumberColumn(width="small"),
        rename_dict["Trading Strategy"]: st.column_config.TextColumn(width="medium"),
        rename_dict["Trend"]: st.column_config.TextColumn(width="small"),
        rename_dict["Position Level"]: st.column_config.TextColumn(width="small"),
        rename_dict["Volume Status"]: st.column_config.TextColumn(width="small"),
        rename_dict["RSI Status & Advice"]: st.column_config.TextColumn(width="medium"),
    }
    # 锁死一屏自适应宽高度
    st.dataframe(styled_df, use_container_width=True, height=380, column_config=col_config)

    st.markdown(f'<div class="section-title">{t_top5}</div>', unsafe_allow_html=True)
    st.dataframe(final_render_df.head(5), use_container_width=True, height=160, column_config=col_config)

st.sidebar.markdown("---")
st.sidebar.info("🤖 TERMINAL SECURED AT v4.1-IMMUNE")
