# treamlit_app.py
import streamlit as st
import pandas as pd
from analyzer import analyze_stock
from tickers import TICKERS

# 强制开启日线级别专业看盘全宽大屏布局
st.set_page_config(layout="wide")

st.title("🚀 AI Trading System Pro")
st.caption("顶级投行专供：9 EMA + 24 SMA 趋势交叉 | 布林斐波那契全量日线雷达扫描系统")

# 核心数据安全防护拦截：10分钟内直接秒读内存，防止 IP 被频繁叩门拉黑
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

# 渲染触发按钮
if st.button("开始扫描", type="primary"):
    with st.spinner("多维量化引擎正在线上安全通道解算全量指标..."):
        df = run_scan()

        if df.empty:
            st.warning("⚠️ 数据源暂时受限，请稍后1-2分钟再次尝试。")
        else:
            # 严格按照权值评分由高到低进行降序重排
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            st.subheader("📊 实时核心量化扫描结果")
            
            # 视觉样式增强函数：突破/金叉高亮经典机构绿，死叉/跌破高亮风控红
            def style_rows(val):
                if "金叉" in str(val) or "突破" in str(val):
                    return 'background-color: #e6f4ea; color: #137333; font-weight: bold;'
                if "死叉" in str(val) or "跌破" in str(val):
                    return 'background-color: #fce8e6; color: #c5221f; font-weight: bold;'
                return ''
                
            styled_df = df.style.map(style_rows, subset=['Signal & Breakout'])
            
            # 使用 2026 最新规范 width='stretch' 渲染扁平化看板
            st.dataframe(styled_df, width='stretch', height=600)

            # 单独切出最具动能优势的 TOP 5 核心标的进行重点盯盘
            st.subheader("🔥 今日 TOP 5 强动能核心资产")
            st.dataframe(df.head(5), width='stretch')
