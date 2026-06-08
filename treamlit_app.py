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

# 🎨 投行专属：硬核注入华尔街自营台“暗黑彭博科技终端”高级 CSS 样式表
st.markdown("""
    <style>
    /* 1. 全局底色全包与无缝边距配置 */
    .main, .stApp {
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
    }
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* 2. 侧边栏彭博分流舱样式 */
    [data-testid="stSidebar"] {
        background-color: #161b22 !important;
        border-right: 1px solid #30363d !important;
    }
    
    /* 3. 投行级高级渐变流光文字标题 */
    .terminal-title {
        font-family: 'Courier New', Courier, monospace;
        font-weight: 900 !important;
        background: linear-gradient(45deg, #58a6ff, #56d364);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.6rem !important;
        margin-bottom: 0rem !important;
    }
    .terminal-caption {
        color: #8b949e !important;
        font-size: 0.95rem !important;
        border-left: 3px solid #58a6ff;
        padding-left: 8px;
        margin-bottom: 1.2rem !important;
    }
    
    /* 4. 霓虹科技感小标题 */
    .section-title {
        color: #58a6ff !important;
        font-weight: bold !important;
        border-bottom: 1px solid #21262d;
        padding-bottom: 4px;
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* 5. 磨砂玻璃科技数据卡片 (KPI Blocks) */
    .kpi-container {
        display: flex;
        gap: 1rem;
        margin-bottom: 0.5rem;
    }
    .kpi-card {
        flex: 1;
        background: #161b22;
        border: 1px solid #30363d;
        border-radius: 8px;
        padding: 0.7rem 1.2rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.3);
    }
    .kpi-label {
        font-size: 0.8rem;
        color: #8b949e;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .kpi-value {
        font-size: 1.8rem;
        font-weight: bold;
        color: #58a6ff;
        margin-top: 0.2rem;
    }

    /* 6. 极客微光律动扫描按钮 */
    div.stButton > button:first-child {
        background: linear-gradient(135deg, #1f6feb 0%, #238636 100%) !important;
        color: #ffffff !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 0.6rem 2.5rem !important;
        font-size: 1.1rem !important;
        font-weight: bold !important;
        letter-spacing: 1px !important;
        box-shadow: 0 4px 15px rgba(35, 134, 54, 0.3) !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    div.stButton > button:first-child:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(88, 166, 255, 0.5) !important;
        background: linear-gradient(135deg, #58a6ff 0%, #56d364 100%) !important;
    }
    
    /* 7. 强制优化 Streamlit 原生表格的暗黑契合度 */
    .stDataFrame {
        background-color: #161b22 !important;
        border: 1px solid #30363d !important;
        border-radius: 8px !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ 第一部分：核心纯量化数据引擎
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

lang_choice = st.sidebar.radio("🌐 Language / 语言切换", ["🇨🇳 中文", "🇺🇸 English"])
lang = "EN" if lang_choice == "🇺🇸 English" else "CN"

ui_meta = {
    "title": "⚡ BLOOMBERG QUANT APP",
    "caption": "顶级自营台专供：常驻独立内存 | 0毫秒双语瞬切暗黑科技终端" if lang == "CN" else "Proprietary Desk: Persistent Memory | 0-ms Multi-Asset Hot Swap Dashboard",
    "ctrl_panel": "⚙️ 控制中心" if lang == "CN" else "⚙️ Terminal Control",
    "manage_pool": "➕ 动态监控池管理" if lang == "CN" else "➕ Watchlist Assets",
    "input_label": "输入追加标的（逗号/空格隔开）:" if lang == "CN" else "Insert Custom Tickers:",
    "input_help": "美股直输(如SOXX); 加股加后缀(如VFV.TO)" if lang == "CN" else "e.g., SOXX, VFV.TO",
    "stat_text": "📊 监控数：" if lang == "CN" else "📊 Total Assets: ",
    "stat_unit": " 只" if lang == "CN" else " symbols",
    "err_fetch": "⚠️ 失败标的:" if lang == "CN" else "⚠️ Failed:",
    "btn_scan": "⚡ 激活雷达全量扫描" if lang == "CN" else "⚡ INITIALIZE RADAR SCAN",
    "spinner_text": "彭博决策核心计算中..." if lang == "CN" else "Decompressing Matrix...",
    "data_feed_err": "⚠️ 数据源受限。" if lang == "CN" else "⚠️ Data Restricted.",
    "board_title": "📊 实时策略决策核心看板" if lang == "CN" else "📊 Real-Time Quantitative Decision Radar",
    "top5_title": "🔥 高得分绝对主力加仓标的 (TOP 5)" if lang == "CN" else "🔥 Alpha Seekers: Top 5 High-Score Momentum",
}

st.markdown(f'<div class="terminal-title">{ui_meta["title"]}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="terminal-caption">{ui_meta["caption"]}</div>', unsafe_allow_html=True)

if "raw_scan_results" not in st.session_state:
    st.session_state.raw_scan_results = None
if "failed_watchlist" not in st.session_state:
    st.session_state.failed_watchlist = []

url_params = st.query_params.get_all("tickers")
default_text = url_params[0] if url_params else ""

st.sidebar.markdown("---")
st.sidebar.header(ui_meta["ctrl_panel"])
st.sidebar.subheader(ui_meta["manage_pool"])

user_input = st.sidebar.text_area(ui_meta["input_label"], value=default_text, help=ui_meta["input_help"], height=120)

if user_input != default_text:
    if user_input.strip():
        st.query_params["tickers"] = user_input.strip()
    else:
        st.query_params.clear()

custom_tickers = []
if user_input:
    custom_tickers = [t.strip().upper() for t in user_input.replace("，", " ").replace(",", " ").split() if t.strip()]

combined_tickers = list(dict.fromkeys(TICKERS + custom_tickers))
st.sidebar.write(f"{ui_meta['stat_text']}`{len(combined_tickers)}`{ui_meta['stat_unit']}")

@st.cache_data(ttl=600)
def run_full_heavy_scan(tickers_list):
    results = []
    failed = []
    for t in tickers_list:
        try:
            res = analyze_stock_raw(t)
            if res:
                results.append(res)
            else:
                failed.append(t)
        except:
            failed.append(t)
    return pd.DataFrame(results), failed

if st.button(ui_meta["btn_scan"], type="primary"):
    with st.spinner(ui_meta["spinner_text"]):
        df, failed_tickers = run_full_heavy_scan(combined_tickers)
        st.session_state.raw_scan_results = df
        st.session_state.failed_watchlist = failed_tickers

user_failed = [f for f in st.session_state.failed_watchlist if f in custom_tickers]
if user_failed:
    st.sidebar.error(f"{ui_meta['err_fetch']} `{', '.join(user_failed)}`")

# ==========================================
# 🖥️ 第三部分：数据卡片与多行防截断染色逻辑
# ==========================================

if st.session_state.raw_scan_results is not None and not st.session_state.raw_scan_results.empty:
    df_raw = st.session_state.raw_scan_results.copy()

    high_alpha_count = len(df_raw[df_raw['Score'] >= 75])
    risk_count = len(df_raw[df_raw['strat_raw'] == 'stop'])
    
    kpi_html = f"""
    <div class="kpi-container">
        <div class="kpi-card">
            <div class="kpi-label">{"MONITORED POOL / 资产池总数" if lang=="CN" else "MONITORED POOL"}</div>
            <div class="kpi-value" style="color: #58a6ff;">{len(combined_tickers)}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-label">{"BULL ALPHA / 强多头标的" if lang=="CN" else "BULL ALPHA"}</div>
            <div class="kpi-value" style="color: #56d364;">{high_alpha_count}</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-card-inner">
                <div class="kpi-label">{"RISK ALERT / 抛压清仓预警" if lang=="CN" else "RISK ALERT"}</div>
                <div class="kpi-value" style="color: #ff7b72;">{risk_count}</div>
            </div>
        </div>
    </div>
    """
    st.markdown(kpi_html, unsafe_allow_html=True)

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
            "stop": "🚨 坚决减仓 / 止损", "strong_buy": "🦅 强力买入 / 加仓", "fake": "👀 假突破 / 暂勿追",
            "golden": "👑 黄金买点 / 左侧", "scale_in": "📥 左侧潜伏 / 分批", "tentative": "🏹 试探建仓 / 开多",
            "pullback": "📥 低吸买入", "hold": "👌 趋势良好 / 持股", "wait": "⏳ 震荡蓄势 / 观望"
        }

    processed_rows = []
    for _, row in df_raw.iterrows():
        rsi_trend = f"🔺+{round(row['rsi_change'], 1)}" if row['rsi_change'] > 0 else f"🔻{round(row['rsi_change'], 1)}"
        if row['rsi_now'] >= 70:
            rsi_advice = f"{round(row['rsi_now'], 1)} | 🔥超买" if lang == "CN" else f"{round(row['rsi_now'], 1)} | 🔥OB"
        elif row['rsi_now'] <= 30:
            rsi_advice = f"{round(row['rsi_now'], 1)} | 🛡️超卖" if lang == "CN" else f"{round(row['rsi_now'], 1)} | 🛡️OS"
        else:
            rsi_advice = f"{round(row['rsi_now'], 1)} | ({rsi_trend})"

        processed_rows.append({
            "Ticker": row["Ticker"],
            "Price": row["Price"],
            "Suggested Buy Price": row["Suggested Buy Price"],
            "Score": row["Score"],
            "Trading Strategy": trans_strat.get(row["strat_raw"], row["strat_raw"]),
            "Trend": trans_trend.get(row["trend_raw"], row["trend_raw"]),
            "Position Level": trans_level.get(row["level_raw"], row["level_raw"]),
            "Volume Status": trans_vol.get(row["vol_raw"], row["vol_raw"]),
            "RSI Status & Advice": rsi_advice,
            "9 EMA": row["9 EMA"],
            "24 SMA": row["24 SMA"],
            "Support": row["Support"],
            "Resistance": row["Resistance"]
        })
    
    display_df = pd.DataFrame(processed_rows)
    display_df = display_df.sort_values(by="Score", ascending=False).reset_index(drop=True)

    rename_dict = {
        "Ticker": "Ticker" if lang == "EN" else "代码",
        "Price": "Price" if lang == "EN" else "当前价",
        "Suggested Buy Price": "Suggested Buy" if lang == "EN" else "推荐买入价",
        "Score": "Score" if lang == "EN" else "评分",
        "Trading Strategy": "Strategy" if lang == "EN" else "交易策略",
        "Trend": "Trend" if lang == "EN" else "均线趋势",
        "Position Level": "Level" if lang == "EN" else "关键位置",
        "Volume Status": "Volume" if lang == "EN" else "量态状态",
        "RSI Status & Advice": "RSI Status" if lang == "EN" else "RSI状态与建议",
        "9 EMA": "9 EMA", "24 SMA": "24 SMA",
        "Support": "Support" if lang == "EN" else "核心支撑",
        "Resistance": "Resistance" if lang == "EN" else "核心阻力"
    }
    
    final_render_df = display_df.rename(columns=rename_dict)
    target_strategy_col = rename_dict["Trading Strategy"]

    st.markdown(f'<div class="section-title">{ui_meta["board_title"]}</div>', unsafe_allow_html=True)
    
    # 🛡️ 绝杀防御：将原先的长行列表推导式完全分行拆解，100% 避开任何复制截断 Bug！
    def style_strategy(val):
        val_str = str(val)
        
        # 绿色高亮组
        g_list = ["强力买入", "金叉", "黄金买点", "Strong Buy", "Golden Cross", "Golden Entry"]
        if any(x in val_str for x in g_list):
            return "background-color: #1f3a22; color: #56d364; font-weight: bold; border: 1px solid #238636;"
            
        # 浅绿低吸组
        lg_list = ["低吸", "分批", "左侧", "Pullback Buy", "Left-Side Entry"]
        if any(x in val_str for x in lg_list):
            return "background-color: #1b2f1c; color: #7fe98a; font-weight: bold;"
            
        # 黄色预警组
        y_list = ["假突破", "预警", "暂勿追", "Fake Out", "Avoid Chasing"]
        if any(x in val_str for x in y_list):
            return "background-color: #382e13; color: #e3b341; font-weight: bold;"
            
        # 红色清仓组
        r_list = ["减仓", "止损", "Reduce", "Stop Loss"]
        if any(x in val_str for x in r_list):
            return "background-color: #3c1e1e; color: #ff7b72; font-weight: bold; border: 1px solid #f85149;"
            
        return ""
    
    styled_df = final_render_df.style.map(style_strategy, subset=[target_strategy_col])
    
    st.dataframe(styled_df, use_container_width=True, height=480)

    st.markdown(f'<div class="section-title">{ui_meta["top5_title"]}</div>', unsafe_allow_html=True)
    st.dataframe(final_render_df.head(5), use_container_width=True, height=210)

st.sidebar.markdown("---")
st.sidebar.info("🤖 SYSTEM RUNNING AT EXTRACTION ALPHA v3.6")
