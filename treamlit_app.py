# treamlit_app.py
import streamlit as st
import pandas as pd
import numpy as np
import requests
import time
import yfinance as yf
from tickers import TICKERS

st.set_page_config(layout="wide")

st.title("🚀 AI Trading System Pro")
st.caption("顶级投行专供：动态书签记忆终端 | 推荐买点决策矩阵智能化系统")

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

def analyze_stock(ticker):
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

    # 1. 均线趋势交叉 (Trend)
    df['EMA_9'] = close.ewm(span=9, adjust=False).mean()
    df['SMA_24'] = close.rolling(window=24).mean()
    
    ema_9_now = float(df['EMA_9'].iloc[-1])
    sma_24_now = float(df['SMA_24'].iloc[-1])
    ema_9_prev = float(df['EMA_9'].iloc[-2])
    sma_24_prev = float(df['SMA_24'].iloc[-2])

    if ema_9_prev < sma_24_prev and ema_9_now >= sma_24_now:
        trend_status = "🎯 金叉启动"
    elif ema_9_prev > sma_24_prev and ema_9_now <= sma_24_now:
        trend_status = "🚨 死叉确立"
    elif ema_9_now > sma_24_now:
        trend_status = "📈 多头趋势"
    else:
        trend_status = "📉 空头动能"

    # 2. RSI (14) 动态分析
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
        rsi_advice = f"{round(rsi_now, 1)} | 🔥超买预警"
    elif rsi_now <= 30:
        rsi_advice = f"{round(rsi_now, 1)} | 🛡️超卖洼地"
    else:
        rsi_advice = f"{round(rsi_now, 1)} | 🧭中性({rsi_trend})"

    # 3. 布林带与斐波那契融合算法
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
        level_status = "🚀 突破阻力"
    elif latest_close < support:
        level_status = "⚠️ 跌破支撑"
    else:
        level_status = "区间震荡"

    # 4. 🔥 机构安全垫推荐买入价（核心锚点）
    suggested_buy_price = round(support * 1.015, 2)

    # 5. 量价追踪
    df['Vol_SMA20'] = volume.rolling(window=20).mean()
    avg_vol = float(df['Vol_SMA20'].iloc[-1])
    price_change = latest_close - float(close.iloc[-2])

    if latest_vol > avg_vol * 1.5:
        vol_status = "🔥 放量上涨" if price_change > 0 else "💥 放量下跌"
    elif latest_vol < avg_vol * 0.7:
        vol_status = "💤 缩量"
    else:
        vol_status = "正常"

    # 6. 综合评分矩阵
    score = 50
    if trend_status == "🎯 金叉启动": score += 25
    elif trend_status == "📈 多头趋势": score += 15
    elif trend_status == "🚨 死叉确立": score -= 25
    elif trend_status == "📉 空头动能": score -= 15
    if level_status == "🚀 突破阻力": score += 15
    if vol_status == "🔥 放量上涨": score += 10
    elif vol_status == "💥 放量下跌": score -= 10
    score = max(10, min(95, score))

    # 7. 🔥 核心重构：自动化策略决策矩阵（买入价绝对优先判定，解决模糊）
    if vol_status == "💥 放量下跌" and (trend_status == "🚨 死叉确立" or level_status == "⚠️ 跌破支撑"):
        strategy = "🚨 坚决减仓 / 右侧止损"
    elif level_status == "🚀 突破阻力" and vol_status == "🔥 放量上涨" and score >= 80:
        strategy = "🦅 强力买入 / 主升浪加仓"
    elif level_status == "🚀 突破阻力" and vol_status == "💥 放量下跌":
        strategy = "👀 假突破预警 / 暂勿追高"
    # ✨ 新增核心卡位：只要价格跌进或低于推荐买入价，且没有恶性放量砸盘
    elif latest_close <= suggested_buy_price and vol_status != "💥 放量下跌":
        if trend_status in ["🎯 金叉启动", "📈 多头趋势"]:
            strategy = "👑 黄金买点 / 强力左侧布局"
        else:
            strategy = "📥 左侧潜伏区 / 步兵分批试探"
    elif trend_status == "🎯 金叉启动" and vol_status != "💥 放量下跌":
        strategy = "🏹 试探性建仓 / 开多"
    elif trend_status == "📈 多头趋势" and latest_close <= support * 1.04:
        strategy = "📥 缩量回踩 / 逢低分批买入"
    elif trend_status == "📈 多头趋势" and vol_status == "正常":
        strategy = "👌 趋势良好 / 坚定持股"
    else:
        strategy = "⏳ 震荡蓄势 / 观望为宜"

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

url_params = st.query_params.get_all("tickers")
default_text = url_params[0] if url_params else ""

st.sidebar.header("⚙️ 终端控制台")
st.sidebar.subheader("➕ 动态管理监控池")

user_input = st.sidebar.text_area(
    "在此输入想追加的股票或ETF（多个用逗号或空格隔开）:",
    value=default_text,
    help="美股ETF直接输(如SOXX)；加股资产请加后缀(如VFV.TO)"
)

if user_input != default_text:
    if user_input.strip():
        st.query_params["tickers"] = user_input.strip()
    else:
        st.query_params.clear()

custom_tickers = []
if user_input:
    custom_tickers = [t.strip().upper() for t in user_input.replace("，", " ").replace(",", " ").split() if t.strip()]

combined_tickers = list(dict.fromkeys(TICKERS + custom_tickers))
st.sidebar.write(f"📊 当前雷达监控总数：`{len(combined_tickers)}` 只核心资产")

@st.cache_data(ttl=600)
def run_scan_with_feedback(tickers_list):
    results = []
    failed = []
    for t in tickers_list:
        try:
            res = analyze_stock(t)
            if res:
                results.append(res)
            else:
                failed.append(t)
        except:
            failed.append(t)
    return pd.DataFrame(results), failed

if st.button("开始扫描", type="primary"):
    with st.spinner("高级多维决策引擎解算中..."):
        df, failed_tickers = run_scan_with_feedback(combined_tickers)

        user_failed = [f for f in failed_tickers if f in custom_tickers]
        if user_failed:
            st.sidebar.error(f"⚠️ 以下资产未成功拉取行情:\n`{', '.join(user_failed)}`")

        if df.empty:
            st.warning("⚠️ 数据源暂时受限，请稍后再试。")
        else:
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            columns_order = [
                "Ticker", "Price", "Suggested Buy Price", "Score", "Trading Strategy", 
                "Trend", "Position Level", "Volume Status", "RSI Status & Advice",
                "9 EMA", "24 SMA", "Support", "Resistance"
            ]
            
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]

            st.subheader("📊 实时多维策略决策看板")
            
            # 升级色彩学高亮渲染
            def style_strategy(val):
                if "强力买入" in str(val) or "金叉" in str(val) or "👑 黄金买点" in str(val):
                    return 'background-color: #e6f4ea; color: #137333; font-weight: bold;'
                if "逢低分批" in str(val) or "📥 左侧潜伏" in str(val):
                    return 'background-color: #f1f8e9; color: #558b2f; font-weight: bold;'
                if "假突破" in str(val) or "预警" in str(val) or "暂勿追高" in str(val):
                    return 'background-color: #fffde7; color: #f57f17; font-weight: bold;'
                if "减仓" in str(val) or "止损" in str(val):
                    return 'background-color: #fce8e6; color: #c5221f; font-weight: bold;'
                return ''
            
            if "Trading Strategy" in df.columns:
                styled_df = df.style.map(style_strategy, subset=['Trading Strategy'])
            else:
                styled_df = df
            
            st.dataframe(styled_df, width='stretch', height=620)

            st.subheader("🔥 今日高权值核心加仓标的 (TOP 5)")
            st.dataframe(df.head(5), width='stretch')

st.sidebar.markdown("---")
st.sidebar.subheader("💾 资产永久留存绝招")
st.sidebar.info(
    "输入您想追加的股票/ETF组合后，**直接将当前的浏览器网页收藏为书签**。下次从手机或电脑书签直接打开，即可实现免代码永久保留自选池！"
)
