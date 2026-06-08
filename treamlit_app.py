# treamlit_app.py
import streamlit as st
import pandas as pd
from analyzer import analyze_stock
from tickers import TICKERS

st.set_page_config(layout="wide")

st.title("🚀 AI Trading System Pro")
st.caption("顶级投行专供：动态书签记忆终端 | RSI动能追踪与推荐买点全自动化系统")

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
            st.sidebar.error(
                f"⚠️ 以下资产未成功拉取行情:\n`{', '.join(user_failed)}`"
            )

        if df.empty:
            st.warning("⚠️ 数据源暂时受限，请稍后再试。")
        else:
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            # 🔥 核心修正：优化列排布顺序，让高价值信息（推荐买价、RSI动态）一眼可见
            columns_order = [
                "Ticker", "Price", "Suggested Buy Price", "Trading Strategy", 
                "Trend", "Position Level", "Volume Status", "RSI Status & Advice",
                "9 EMA", "24 SMA", "Support", "Resistance"
            ]
            
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]

            st.subheader("📊 实时多维策略决策看板")
            
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
