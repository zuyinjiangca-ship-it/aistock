# treamlit_app.py
import streamlit as st
import pandas as pd
from analyzer import analyze_stock
from tickers import TICKERS

st.set_page_config(layout="wide")

st.title("🚀 AI Trading System Pro")
st.caption("顶级投行专供：多指标去模糊分流雷达 | 策略行动建议决策自动化系统")

@st.cache_data(ttl=600)
def run_scan():
    results = []
    for t in TICKERS:
        try:
            res = analyze_stock(t)
            if res:
                results.append(res)
        except:
            continue
    return pd.DataFrame(results)

if st.button("开始扫描", type="primary"):
    with st.spinner("高级多维决策引擎解算中..."):
        df = run_scan()

        if df.empty:
            st.warning("⚠️ 数据源暂时受限，请稍后再试。")
        else:
            # 依评分排序
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            # 调整列顺序，使看盘体验极其顺畅
            columns_order = [
                "Ticker", "Price", "Score", "Trading Strategy", 
                "Trend", "Position Level", "Volume Status", 
                "9 EMA", "24 SMA", "Support", "Resistance", "RSI"
            ]
            df = df[columns_order]

            st.subheader("📊 实时多维策略决策看板")
            
            # 高级表格样式渲染：买入类高亮绿，风险/假突破/跌破类高亮黄红
            def style_strategy(val):
                if "强力买入" in str(val) or "金叉" in str(val):
                    return 'background-color: #e6f4ea; color: #137333; font-weight: bold;'
                if "逢低分批" in str(val):
                    return 'background-color: #f1f8e9; color: #558b2f; font-weight: bold;'
                if "假突破" in str(val) or "预警" in str(val):
                    return 'background-color: #fffde7; color: #f57f17; font-weight: bold;'
                if "减仓" in str(val) or "止损" in str(val):
                    return 'background-color: #fce8e6; color: #c5221f; font-weight: bold;'
                return ''
                
            styled_df = df.style.map(style_strategy, subset=['Trading Strategy'])
            
            st.dataframe(styled_df, width='stretch', height=620)

            # 顶级核心推荐
            st.subheader("🔥 今日高权值核心加仓标的 (TOP 5)")
            st.dataframe(df.head(5), width='stretch')
