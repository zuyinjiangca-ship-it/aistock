# treamlit_app.py
import streamlit as st
import pandas as pd
from analyzer import analyze_stock
from tickers import TICKERS

st.set_page_config(layout="wide")

st.title("🚀 AI Trading System Pro")
st.caption("顶级投行专供：多指标去模糊分流雷达 | 策略行动建议决策自动化系统")

# 🛠️ 核心新增：左侧控制台管理栏
st.sidebar.header("⚙️ 终端控制台")
st.sidebar.subheader("➕ 动态增加监控标的")
user_input = st.sidebar.text_area(
    "在此输入想临时查看的股票代码（多个请用逗号或空格隔开，例如: NVDA, AAPL, MSFT）:",
    value="",
    help="输入的代码会自动加入下方的扫描池，无需修改代码。"
)

# 解析用户输入的自定义股票代码
custom_tickers = []
if user_input:
    # 将中文逗号或英文逗号全部替换为空格，并切分成列表，自动转大写
    custom_tickers = [t.strip().upper() for t in user_input.replace("，", " ").replace(",", " ").split() if t.strip()]

# 合并默认名单与用户输入的名单，并保持原有顺序去重
combined_tickers = list(dict.fromkeys(TICKERS + custom_tickers))

st.sidebar.write(f"📊 当前雷达监控总数：`{len(combined_tickers)}` 只核心资产")
if custom_tickers:
    st.sidebar.success(f"已成功并入动态标的: {', '.join(custom_tickers)}")

# 核心安全缓存拦截（将标的名单作为参数传入，确保名单变化时缓存能自动识别刷新）
@st.cache_data(ttl=600)
def run_scan(tickers_list):
    results = []
    for t in tickers_list:
        try:
            res = analyze_stock(t)
            if res:
                results.append(res)
        except:
            continue
    return pd.DataFrame(results)

if st.button("开始扫描", type="primary"):
    with st.spinner("高级多维决策引擎解算中..."):
        # 传入合并后的动态自选池进行全量计算
        df = run_scan(combined_tickers)

        if df.empty:
            st.warning("⚠️ 数据源暂时受限，请稍后再试。")
        else:
            # 依评分排序
            df = df.sort_values(by="Score", ascending=False).reset_index(drop=True)

            columns_order = [
                "Ticker", "Price", "Score", "Trading Strategy", 
                "Trend", "Position Level", "Volume Status", 
                "9 EMA", "24 SMA", "Support", "Resistance", "RSI"
            ]
            
            # 动态安全过滤
            existing_columns = [col for col in columns_order if col in df.columns]
            df = df[existing_columns]

            st.subheader("📊 实时多维策略决策看板")
            
            # 高级表格样式渲染
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
