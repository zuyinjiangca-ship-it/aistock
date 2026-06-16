# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf

# 📊 老板最新修正的45只全量精密常驻资产池（已剔除过载标的，校正代码）
TICKERS = [
    "COHU", "VECO", "ENTG", "UCTT", "ICHR", "AXTI", "WOLF", "POWI", 
    "AOSL", "MTSI", "AMAT", "KLAC", "CIFR", "WULF", "HUT", "FLNC", 
    "CIEN", "SMTC", "CRDO", "TXN", "ON", "MCHP", "GFS", "JBL", 
    "HIMX", "ALAB", "NOK", "TEL", "ENPH", "VPG", "NVTS", "AEHR", 
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
# 🛠️ 第一部分：核心纯量化数据引擎 (内存级数据切片)
# ==========================================

def get_secure_session():
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    return session

def analyze_stock_from_df(ticker, df):
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
    "title": "🚀 AI Trading System Pro",
    "caption": "顶级投行专供：常驻保险箱架构 | 0毫秒双语瞬切决策终端" if lang == "CN" else "Institutional Grade: Persistent Memory Terminal | 0-ms Multi-Asset Hot Swap Dashboard",
    "ctrl_panel": "⚙️ 控制台" if lang == "CN" else "⚙️ Console",
    "manage_pool": "➕ 管理监控池" if lang == "CN" else "➕ Watchlist",
    "input_label": "输入追加临时标的（逗号/空格隔开）:" if lang == "CN" else "Add Temporary Tickers:",
    "input_help": "临时追加美股(如SOXX); 加股加后缀(如VFV.TO)" if lang == "CN" else "e.g., SOXX, VFV.TO",
    "stat_text": "📊 监控数：" if lang == "CN" else "📊 Total: ",
    "stat_unit": " 只" if lang == "CN" else " symbols",
    "err_fetch": "⚠️ 失败标的（请检查代码或网络）:" if lang == "CN" else "⚠️ Failed Tickers:",
    "btn_scan": "开始扫描" if lang == "CN" else "Radar Scan",
    "spinner_text": "量化批量合并总线解算中..." if lang == "CN" else "Processing Batch Matrix...",
    "board_title": "📊 实时策略决策看板" if lang == "CN" else "📊 Quantitative Decision Dashboard",
    "top5_title": "🔥 强动能加仓标的 (TOP 5)" if lang == "CN" else "🔥 Top 5 High-Score Momentum Assets",
}

st.title(ui_meta["title"])
st.caption(ui_meta["caption"])

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
    session = get_secure_session()
    results = []
    failed = []
    
    try:
        # 🚀 降维打击核心：全量个股 45合1 单次打包下载，彻底碾碎雅虎频控限制
        all_data = yf.download(tickers_list, period="1y", progress=False, session=session)
    except:
        return pd.DataFrame(), tickers_list

    for t in tickers_list:
        try:
            # 在内存中执行高频交叉切片 (.xs)，0毫秒无缝提取个股历史矩阵
            if isinstance(all_data.columns, pd.MultiIndex):
                ticker_df = all_data.xs(t, level=1, axis=1)
            else:
                ticker_df = all_data if len(tickers_list) == 1 else pd.DataFrame()
            
            if ticker_df is not None and not ticker_df.empty:
                res = analyze_stock_from_df(t, ticker_df)
                if res:
                    results.append(res)
                else:
                    failed.append(t)
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

if st.session_state.failed_watchlist:
    st.sidebar.error(f"{ui_meta['err_fetch']} `{', '.join(st.session_state.failed_watchlist)}`")

if st.session_state.raw_scan_results is not None and not st.session_state.raw_scan_results.empty:
    df_raw = st.session_state.raw_scan_results.copy()

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

    st.subheader(ui_meta['board_title'])
    
    def style_strategy(val):
        val_str = str(val)
        if any(x in val_str for x in ["强力买入", "金叉", "黄金买点", "Strong Buy", "Golden Cross", "Golden Entry"]):
            return """background-color: #e6f4ea; color: #137333; font-weight: bold;"""
        if any(x in val_str for x in ["低吸", "分批", "左侧", "Pullback Buy", "Left-Side Entry"]):
            return """background-color: #f1f8e9; color: #558b2f; font-weight: bold;"""
        if any(x in val_str for x in ["假突破", "预警", "暂勿追", "Fake Out", "Avoid Chasing"]):
            return """background-color: #fffde7; color: #f57f17; font-weight: bold;"""
        if any(x in val_str for x in ["减仓", "止损", "Reduce", "Stop Loss"]):
            return """background-color: #fce8e6; color: #c5221f; font-weight: bold;"""
        return """"""
    
    styled_df = final_render_df.style.map(style_strategy, subset=[target_strategy_col])
    
    st.dataframe(styled_df, use_container_width=True, height=760)

    st.markdown("<br><br>", unsafe_allow_html=True)

    st.subheader(ui_meta['top5_title'])
    st.dataframe(final_render_df.head(5), use_container_width=True, height=210)

st.sidebar.markdown("---")
st.sidebar.info(ui_meta["title"] + " v5.0-TurboBatch")
