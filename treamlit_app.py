# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
from tickers import TICKERS

# 强制开启全球量化大屏全宽布局
st.set_page_config(layout="wide")

# 🔥 核心空间榨汁：注入极限紧凑型 CSS，强行剥离页面多余留白与大间距
st.markdown("""
    <style>
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
    /* 让顶部的标题区域更加紧凑 */
    h1 {
        font-size: 1.8rem !important;
        margin-bottom: 0rem !important;
        padding-bottom: 0rem !important;
    }
    p {
        margin-bottom: 0.2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 🛠️ 第一部分：核心量化计算引擎
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

def analyze_stock(ticker, lang):
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

    if lang == "EN":
        t_cross_up, t_cross_down, t_bull, t_bear = "🎯 Golden Cross", "🚨 Death Cross", "📈 Bullish Trend", "📉 Bearish Momentum"
        l_breakout, l_breakdown, l_range = "🚀 Breakout", "⚠️ Breakdown", "Range Bound"
        v_up, v_down, v_low, v_norm = "🔥 Vol Surge", "💥 Vol Dump", "💤 Declining", "Normal"
        s_stop = "🚨 Reduce / Stop Loss"
        s_strong_buy = "🦅 Strong Buy / Add"
        s_fake = "👀 Fake Out / No Chase"
        s_golden = "👑 Golden Entry"
        s_scale_in = "📥 Scale In (Left)"
        s_tentative = "🏹 Open Long"
        s_pullback = "📥 Buy the Dip"
        s_hold = "👌 Trend Ok / Hold"
        s_wait = "⏳ Wait & See"
    else:
        t_cross_up, t_cross_down, t_bull, t_bear = "🎯 金叉启动", "🚨 死叉确立", "📈 多头趋势", "📉 空头动能"
        l_breakout, l_breakdown, l_range = "🚀 突破阻力", "⚠️ 跌破支撑", "区间震荡"
        v_up, v_down, v_low, v_norm = "🔥 放量上涨", "💥 放量下跌", "💤 缩量", "正常"
        s_stop = "🚨 坚决减仓 / 止损"
        s_strong_buy = "🦅 强力买入 / 加仓"
        s_fake = "👀 假突破 / 暂勿追"
        s_golden = "👑 黄金买点 / 左侧"
        s_scale_in = "📥 左侧潜伏 / 分批"
        s_tentative = "🏹 试探建仓 / 开多"
        s_pullback = "📥 缩量回踩 / 低吸"
        s_hold = "👌 趋势良好 / 持股"
        s_wait = "⏳ 震荡蓄势 / 观望"

    # 均线趋势
    df['EMA_9'] = close.ewm(span=9, adjust=False).mean()
    df['SMA_24'] = close.rolling(window=24).mean()
    ema_9_now = float(df['EMA_9'].iloc[-1])
    sma_24_now = float(df['SMA_24'].iloc[-1])
    ema_9_prev = float(df['EMA_9'].iloc[-2])
    sma_24_prev = float(df['SMA_24'].iloc[-2])

    if ema_9_prev < sma_24_prev and ema_9_now >= sma_24_now:
        trend_status_raw = "gold_cross"; trend_status = t_cross_up
    elif ema_9_prev > sma_24_prev and ema_9_now <= sma_24_now:
        trend_status_raw = "dead_cross"; trend_status = t_cross_down
    elif ema_9_now > sma_24_now:
        trend_status_raw = "bull"; trend_status = t_bull
    else:
        trend_status_raw = "bear"; trend_status = t_bear

    # RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_now = float(rsi.iloc[-1])
    rsi_prev = float(rsi.iloc[-2])
    rsi_change = rsi_now - rsi_prev
    
    rsi_trend = f"🔺+{round(rsi_change, 1)}" if rsi_change > 0 else f"🔻{round(rsi_change, 1)}"
    if rsi_now >= 70:
        rsi_advice = f"{round(rsi_now, 1)} | 🔥超买" if lang == "CN" else f"{round(rsi_now, 1)} | 🔥OB"
    elif rsi_now <= 30:
        rsi_advice = f"{round(rsi_now, 1)} | 🛡️超卖" if lang == "CN" else f"{round(rsi_now, 1)} | 🛡️OS"
    else:
        rsi_advice = f"{round(rsi_now, 1)} | ({rsi_trend})"

    # 布林带与斐波那契
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
        level_status_raw = "breakout"; level_status = l_breakout
    elif latest_close < support:
        level_status_raw = "breakdown"; level_status = l_breakdown
    else:
        level_status_raw = "range"; level_status = l_range

    suggested_buy_price = round(support * 1.015, 2)

    # 量价
    df['Vol_SMA20'] = volume.rolling(window=20).mean()
    avg_vol = float(df['Vol_SMA20'].iloc[-1])
    price_change = latest_close - float(close.iloc[-2])

    is_vol_dump = (latest_vol > avg_vol * 1.5 and price_change <= 0)
    is_vol_surge = (latest_vol > avg_vol * 1.5 and price_change > 0)

    if latest_vol > avg_vol * 1.5:
        vol_status = v_up if price_change > 0 else v_down
    elif latest_vol < avg_vol * 0.7:
        vol_status = v_low
    else:
        vol_status = v_norm

    # 评分
    score = 50
    if trend_status_raw == "gold_cross": score += 25
    elif trend_status_raw == "bull": score += 15
    elif trend_status_raw == "dead_cross": score -= 25
    elif trend_status_raw == "bear": score -= 15
    if level_status_raw == "breakout": score += 15
    if is_vol_surge: score += 10
    elif is_vol_dump: score -= 10
    score = max(10, min(95, score))

    # 策略执行
    if is_vol_dump and (trend_status_raw == "dead_cross" or level_status_raw == "breakdown"):
        strategy = s_stop
    elif level_status_raw == "breakout" and is_vol_surge and score >= 80:
        strategy = s_strong_buy
    elif level_status_raw == "breakout" and is_vol_dump:
        strategy = s_fake
    elif latest_close <= suggested_buy_price and not is_vol_dump:
        if trend_status_raw in ["gold_cross", "bull"]:
            strategy = s_golden
        else:
            strategy = s_scale_in
    elif trend_status_raw == "gold_cross" and not is_vol_dump:
        strategy = s_tentative
    elif trend_status_raw == "bull" and latest_close <= support * 1.04:
        strategy = "📥 Buy the Dip" if lang == "EN" else "📥 低吸买入"
    elif trend_status_raw == "bull" and vol_status == v_norm:
        strategy = s_hold
    else:
        strategy = s_wait

    return {
        "Ticker": ticker,
        "Price": round(latest_close, 2),
        "Suggested Buy Price": suggested_buy_price,
        "Score": int(score),
        "Trading Strategy": strategy,
        "Trend": trend_status,
        "Position Level": level_status,
        "Volume Status": vol_status,
        "RSI Status & Advice": rsi_advice,
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
    "caption": "顶级投行专供：一屏锁死高紧凑自适应版" if lang == "CN" else "Institutional Grade: Compact Screen Lock Edition",
    "ctrl_panel": "⚙️ 控制台" if lang == "CN" else "⚙️ Console",
    "manage_pool": "➕ 管理监控池" if lang == "CN" else "➕ Watchlist",
    "input_label": "输入追加标的（逗号/空格隔开）:" if lang == "CN" else "Add Tickers (use comma/space):",
    "input_help": "美股直输(如SOXX); 加股加后缀(如VFV.TO)" if lang == "CN" else "e.g., SOXX, VFV.TO",
    "stat_text": "📊 监控数：" if lang == "CN" else "📊 Total: ",
    "stat_unit": " 只" if lang == "CN" else " symbols",
    "err_fetch": "⚠️ 失败标的:" if lang == "CN" else "⚠️ Failed:",
    "btn_scan": "开始扫描" if lang == "CN" else "Radar Scan",
    "spinner_text": "量化矩阵解算中..." if lang == "CN" else "Processing Matrix...",
    "data_feed_err": "⚠️ 数据源受限。" if lang == "CN" else "⚠️ Data Restricted.",
    "board_title": "📊 实时策略决策看板 (内含布林与斐波那契)" if lang == "CN" else "📊 Quantitative Decision Dashboard",
    "top5_title": "🔥 强动能加仓标的 (TOP 5)" if lang == "CN" else "🔥 Top 5 High-Score Momentum Assets",
}

st.title(ui_meta["title"])
st.caption(ui_meta["caption"])

url_params = st.query_params.get_all("tickers")
default_text = url_params[0] if url_params else ""

st.sidebar.markdown("---")
st.sidebar.header(ui_meta["ctrl_panel"])
st.sidebar.subheader(ui_meta["manage_pool"])

user_input = st.sidebar.text_area(ui_meta["input_label"], value=default_text, help=ui_meta["input_help"], height=100)

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
def run_scan_with_feedback(tickers_list, lang_flag):
    results = []
    failed = []
    for t in tickers_list:
        try:
            res = analyze_stock(t, lang_flag)
            if res:
                results.append(res)
            else:
                failed.append(t)
        except:
            failed.append(t)
    return pd.DataFrame(results), failed

if st.button(ui_meta["btn_scan"], type="primary"):
    with st.spinner(ui_meta["spinner_text"]):
        df, failed_tickers = run_scan_with_feedback(combined_tickers, lang)

        user_failed = [f for f in failed_tickers if f in custom_tickers]
        if user_failed:
            st.sidebar.error(f"{ui_meta['err_fetch']} `{', '.join(user_failed)}`")

        if df.empty:
            st.warning(ui_meta["data_feed_err"])
        else:
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            columns_order = [
                "Ticker", "Price", "Suggested Buy Price", "Score", "Trading Strategy", 
                "Trend", "Position Level", "Volume Status", "RSI Status & Advice",
                "9 EMA", "24 SMA", "Support", "Resistance"
            ]
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]

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
            
            display_df = df.rename(columns=rename_dict)
            target_strategy_col = rename_dict["Trading Strategy"]

            # 使用 Markdown 小三级标题代替 st.subheader，腾出大量纵向像素
            st.markdown(f"##### {ui_meta['board_title']}")
            
            def style_strategy(val):
                val_str = str(val)
                if any(x in val_str for x in ["强力买入", "金叉", "黄金买点", "Strong Buy", "Golden Cross", "Golden Entry"]):
                    return 'background-color: #e6f4ea; color: #137333; font-weight: bold;'
                if any(x in val_str for x in ["低吸", "分批", "左侧", "Pullback Buy", "Left-Side Entry"]):
                    return 'background-color: #f1f8e9; color: #558b2f; font-weight: bold;'
                if any(x in val_str for x in ["假突破", "预警", "暂勿追", "Fake Out", "Avoid Chasing"]):
                    return 'background-color: #fffde7; color: #f57f17; font-weight: bold;'
                if "减仓" in val_str or "止损" in val_str or "Reduce" in val_str or "Stop Loss" in val_str:
                    return 'background-color: #fce8e6; color: #c5221f; font-weight: bold;'
                return ''
            
            styled_df = display_df.style.map(style_strategy, subset=[target_strategy_col])
            
            # 🔥 核心锁死：强行配置列宽（小尺寸列锁死），并将主表格高度限制在 380，杜绝全网页拖拽
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
                "9 EMA": st.column_config.NumberColumn(width="small"),
                "24 SMA": st.column_config.NumberColumn(width="small"),
                rename_dict["Support"]: st.column_config.NumberColumn(width="small"),
                rename_dict["Resistance"]: st.column_config.NumberColumn(width="small"),
            }
            
            st.dataframe(styled_df, width='stretch', height=380, column_config=col_config)

            st.markdown(f"##### {ui_meta['top5_title']}")
            st.dataframe(display_df.head(5), width='stretch', height=160, column_config=col_config)

st.sidebar.markdown("---")
st.sidebar.info(ui_meta["title"] + " v2.0")
