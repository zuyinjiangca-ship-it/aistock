# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
from tickers import TICKERS

# ==========================================
# 🛠️ 第一部分：核心量化计算引擎 (支持多语言自适应)
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

    # 1. 语言字典硬核注入
    if lang == "EN":
        t_cross_up, t_cross_down, t_bull, t_bear = "🎯 Golden Cross", "🚨 Death Cross", "📈 Bullish Trend", "📉 Bearish Momentum"
        l_breakout, l_breakdown, l_range = "🚀 Resistance Breakout", "⚠️ Support Breakdown", "Range Bound"
        v_up, v_down, v_low, v_norm = "🔥 High Vol Surge", "💥 High Vol Dump", "💤 Decreasing Vol", "Normal"
        s_stop = "🚨 Reduce Position / Stop Loss"
        s_strong_buy = "🦅 Strong Buy / Add on Breakout"
        s_fake = "👀 Fake Breakout / Avoid Chasing"
        s_golden = "👑 Golden Entry / Strong Accumulation"
        s_scale_in = "📥 Left-Side Entry / Scale In"
        s_tentative = "🏹 Tentative Entry / Open Long"
        s_pullback = "📥 Pullback Buy / Buy the Dip"
        s_hold = "👌 Good Trend / Hold Firm"
        s_wait = "⏳ Consolidation / Wait and See"
    else:
        t_cross_up, t_cross_down, t_bull, t_bear = "🎯 金叉启动", "🚨 死叉确立", "📈 多头趋势", "📉 空头动能"
        l_breakout, l_breakdown, l_range = "🚀 突破阻力", "⚠️ 跌破支撑", "区间震荡"
        v_up, v_down, v_low, v_norm = "🔥 放量上涨", "💥 放量下跌", "💤 缩量", "正常"
        s_stop = "🚨 坚决减仓 / 右侧止损"
        s_strong_buy = "🦅 强力买入 / 主升浪加仓"
        s_fake = "👀 假突破预警 / 暂勿追高"
        s_golden = "👑 黄金买点 / 强力左侧布局"
        s_scale_in = "📥 左侧潜伏区 / 步兵分批试探"
        s_tentative = "🏹 试探性建仓 / 开多"
        s_pullback = "📥 缩量回踩 / 逢低分批买入"
        s_hold = "👌 趋势良好 / 坚定持股"
        s_wait = "⏳ 震荡蓄势 / 观望为宜"

    # 2. 均线趋势交叉 (Trend)
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

    # 3. RSI (14) 动态分析
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
        rsi_advice = f"{round(rsi_now, 1)} | 🔥超买预警" if lang == "CN" else f"{round(rsi_now, 1)} | 🔥 Overbought"
    elif rsi_now <= 30:
        rsi_advice = f"{round(rsi_now, 1)} | 🛡️超卖洼地" if lang == "CN" else f"{round(rsi_now, 1)} | 🛡️ Oversold"
    else:
        rsi_advice = f"{round(rsi_now, 1)} | 🧭中性({rsi_trend})" if lang == "CN" else f"{round(rsi_now, 1)} | 🧭 Neutral({rsi_trend})"

    # 4. 布林带与斐波那契融合算法
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

    # 5. 机构防御推荐买入价
    suggested_buy_price = round(support * 1.015, 2)

    # 6. 量价追踪
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

    # 7. 综合评分
    score = 50
    if trend_status_raw == "gold_cross": score += 25
    elif trend_status_raw == "bull": score += 15
    elif trend_status_raw == "dead_cross": score -= 25
    elif trend_status_raw == "bear": score -= 15
    if level_status_raw == "breakout": score += 15
    if is_vol_surge: score += 10
    elif is_vol_dump: score -= 10
    score = max(10, min(95, score))

    # 8. 自动化策略决策矩阵（多语言解耦）
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
        strategy = "📥 Pullback Buy / Buy the Dip" if lang == "EN" else "📥 缩量回踩 / 逢低分批买入"
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
# 🖥️ 第二部分：前端数据渲染交互主控 (支持双语无缝切换)
# ==========================================

# 🌐 侧边栏高规格多语言切换按钮
lang_choice = st.sidebar.radio("🌐 Language / 语言切换", ["🇨🇳 中文", "🇺🇸 English"])
lang = "EN" if lang_choice == "🇺🇸 English" else "CN"

# 动态翻译前台文案字典
ui_meta = {
    "title": "🚀 AI Trading System Pro",
    "caption": "顶级投行专供：动态书签记忆终端 | RSI动能追踪与推荐买点全自动化系统" if lang == "CN" else "Institutional Grade: Dynamic Bookmarked Terminal | RSI Momentum Stream & Automated Buy Price Matrix",
    "ctrl_panel": "⚙️ 终端控制台" if lang == "CN" else "⚙️ Terminal Control",
    "manage_pool": "➕ 动态管理监控池" if lang == "CN" else "➕ Manage Watchlist",
    "input_label": "在此输入想追加的股票或ETF（多个用逗号或空格隔开）:" if lang == "CN" else "Add custom Tickers or ETFs (separate with commas or spaces):",
    "input_help": "美股ETF直接输(如SOXX)；加股资产请加后缀(如VFV.TO)" if lang == "CN" else "US ETFs type directly (e.g., SOXX); Canadian assets require suffix (e.g., VFV.TO)",
    "stat_text": "📊 当前雷达监控总数：" if lang == "CN" else "📊 Total Assets Monitored: ",
    "stat_unit": " 只核心资产" if lang == "CN" else " symbols",
    "err_fetch": "⚠️ 以下资产未成功拉取行情:" if lang == "CN" else "⚠️ Failed to fetch market data for:",
    "btn_scan": "开始扫描" if lang == "CN" else "Start Radar Scan",
    "spinner_text": "高级多维决策引擎解算中..." if lang == "CN" else "Decompressing multi-dimensional decision matrix...",
    "data_feed_err": "⚠️ 数据源暂时受限，请稍后再试。" if lang == "CN" else "⚠️ Market data feed restricted. Please retry shortly.",
    "board_title": "📊 实时多维策略决策看板" if lang == "CN" else "📊 Real-Time Quantitative Decision Dashboard",
    "top5_title": "🔥 今日高权值核心加仓标的 (TOP 5)" if lang == "CN" else "🔥 Top 5 High-Score Momentum Assets",
    "tip_title": "💾 资产永久留存绝招" if lang == "CN" else "💾 Permanent Bookmarking Tip",
    "tip_desc": "输入您想追加的股票/ETF组合后，**直接将当前的浏览器网页收藏为书签**。下次从手机或电脑书签直接打开，即可实现免代码永久保留自选池！" if lang == "CN" else "After adding your custom tickers, **bookmark this page directly in your browser**. Opening the bookmark from any device will instantly load your saved watchlists without code!"
}

# 渲染全局基础标题
st.title(ui_meta["title"])
st.caption(ui_meta["caption"])

# URL 记忆加载模块
url_params = st.query_params.get_all("tickers")
default_text = url_params[0] if url_params else ""

st.sidebar.markdown("---")
st.sidebar.header(ui_meta["ctrl_panel"])
st.sidebar.subheader(ui_meta["manage_pool"])

user_input = st.sidebar.text_area(ui_meta["input_label"], value=default_text, help=ui_meta["input_help"])

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

# 🛡️ 核心大坑修复：将 lang 参数并入缓存签名，确保切语言时瞬间爆破旧缓存
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
            st.sidebar.error(f"{ui_meta['err_fetch']}\n`{', '.join(user_failed)}`")

        if df.empty:
            st.warning(ui_meta["data_feed_err"])
        else:
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            # 顶级排盘规范顺序
            columns_order = [
                "Ticker", "Price", "Suggested Buy Price", "Score", "Trading Strategy", 
                "Trend", "Position Level", "Volume Status", "RSI Status & Advice",
                "9 EMA", "24 SMA", "Support", "Resistance"
            ]
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]

            # 🎯 核心高阶动作：动态将 DataFrame 英文列名一键转换为对应语言
            rename_dict = {
                "Ticker": "Ticker" if lang == "EN" else "代码",
                "Price": "Price" if lang == "EN" else "当前价",
                "Suggested Buy Price": "Suggested Buy Price" if lang == "EN" else "推荐买入价",
                "Score": "Score" if lang == "EN" else "综合评分",
                "Trading Strategy": "Trading Strategy" if lang == "EN" else "交易策略",
                "Trend": "Trend" if lang == "EN" else "均线趋势",
                "Position Level": "Position Level" if lang == "EN" else "关键位置",
                "Volume Status": "Volume Status" if lang == "EN" else "量态状态",
                "RSI Status & Advice": "RSI Status & Advice" if lang == "EN" else "RSI状态与建议",
                "9 EMA": "9 EMA", "24 SMA": "24 SMA",
                "Support": "Support" if lang == "EN" else "核心支撑",
                "Resistance": "Resistance" if lang == "EN" else "核心阻力"
            }
            
            display_df = df.rename(columns=rename_dict)
            target_strategy_col = rename_dict["Trading Strategy"]

            st.subheader(ui_meta["board_title"])
            
            # 双语通用高亮色彩逻辑
            def style_strategy(val):
                val_str = str(val)
                if any(x in val_str for x in ["强力买入", "金叉", "黄金买点", "Strong Buy", "Golden Cross", "Golden Entry"]):
                    return 'background-color: #e6f4ea; color: #137333; font-weight: bold;'
                if any(x in val_str for x in ["逢低分批", "左侧潜伏", "Pullback Buy", "Left-Side Entry"]):
                    return 'background-color: #f1f8e9; color: #558b2f; font-weight: bold;'
                if any(x in val_str for x in ["假突破", "预警", "暂勿追高", "Fake Breakout", "Avoid Chasing"]):
                    return 'background-color: #fffde7; color: #f57f17; font-weight: bold;'
                if "减仓" in val_str or "止损" in val_str or "Reduce" in val_str or "Stop Loss" in val_str:
                    return 'background-color: #fce8e6; color: #c5221f; font-weight: bold;'
                return ''
            
            styled_df = display_df.style.map(style_strategy, subset=[target_strategy_col])
            st.dataframe(styled_df, width='stretch', height=620)

            st.subheader(ui_meta["top5_title"])
            st.dataframe(display_df.head(5), width='stretch')

st.sidebar.markdown("---")
st.sidebar.subheader(ui_meta["tip_title"])
st.sidebar.info(ui_meta["tip_desc"])
