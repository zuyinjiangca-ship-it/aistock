# analyzer.py
import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time

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
    high_series = df['High'].astype(float)
    low_series = df['Low'].astype(float)

    latest_close = float(close.iloc[-1])
    latest_vol = float(volume.iloc[-1])

    # 1. 均线趋势判定 (Trend)
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

    # 2. RSI (14)
    delta = close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    latest_rsi = float(rsi.iloc[-1])

    # 3. 布林带与斐波那契定位支撑阻力 (Levels)
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

    # 4. 量价精准追踪模块 (Volume)
    df['Vol_SMA20'] = volume.rolling(window=20).mean()
    avg_vol = float(df['Vol_SMA20'].iloc[-1])
    price_change = latest_close - float(close.iloc[-2])

    if latest_vol > avg_vol * 1.5:
        vol_status = "🔥 放量上涨" if price_change > 0 else "💥 放量下跌"
    elif latest_vol < avg_vol * 0.7:
        vol_status = "💤 缩量"
    else:
        vol_status = "正常"

    # 5. 综合多空评分体系 (Score)
    score = 50
    if trend_status == "🎯 金叉启动": score += 25
    elif trend_status == "📈 多头趋势": score += 15
    elif trend_status == "🚨 死叉确立": score -= 25
    elif trend_status == "📉 空头动能": score -= 15
    if level_status == "🚀 突破阻力": score += 15
    if vol_status == "🔥 放量上涨": score += 10
    elif vol_status == "💥 放量下跌": score -= 10
    score = max(10, min(95, score))

    # 6. 🚨 核心新增：自动化投行策略建议引擎 (Strategy Advice)
    if vol_status == "💥 放量下跌" and (trend_status == "🚨 死叉确立" or level_status == "⚠️ 跌破支撑"):
        strategy = "🚨 坚决减仓 / 右侧止损"
    elif level_status == "🚀 突破阻力" and vol_status == "🔥 放量上涨" and score >= 80:
        strategy = "🦅 强力买入 / 主升浪加仓"
    elif level_status == "🚀 突破阻力" and vol_status == "💥 放量下跌":
        strategy = "👀 假突破预警 / 暂勿追高"
    elif trend_status == "🎯 金叉启动" and vol_status != "💥 放量下跌":
        strategy = "🏹 试探性建仓 / 开多"
    elif trend_status == "📈 多头趋势" and latest_close <= support * 1.04:
        strategy = "📥 缩量回踩 / 逢低分批买入"
    elif trend_status == "📈 多头趋势" and vol_status == "正常":
        strategy = "👌 趋势良好 / 坚定持股"
    elif trend_status == "📉 空头动能" and level_status == "🚀 突破阻力":
        strategy = " Foxes 超跌反弹 / 轻仓短线试探"
    else:
        strategy = "⏳ 震荡蓄势 / 观望为宜"

    return {
        "Ticker": ticker,
        "Price": round(latest_close, 2),
        "Score": int(score),
        "9 EMA": round(ema_9_now, 2),
        "24 SMA": round(sma_24_now, 2),
        "Support": round(support, 2),
        "Resistance": round(resistance, 2),
        "RSI": round(latest_rsi, 1),
        "Volume Status": vol_status,
        "Trend": trend_status,
        "Position Level": level_status,
        "Trading Strategy": strategy
    }
