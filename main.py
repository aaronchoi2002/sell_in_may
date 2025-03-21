import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import yfinance as yf

# --- 輔助函數 ---
def load_data(symbol, start_date="1990-01-01"):
    """
    從 Yahoo Finance 下載歷史股票數據，並選擇 'Open' 和 'Close' 列。
    
    參數:
        symbol (str): 股票或指數的代碼。
        start_date (str): 數據的起始日期，格式為 'YYYY-MM-DD'。
    
    返回:
        pd.DataFrame: 帶有 'Date' 作為 datetime 索引的 DataFrame，或在錯誤時停止執行。
    """
    try:
        df = yf.download(symbol, start=start_date)[['Open', 'Close']]
        if df.empty:
            st.error(f"錯誤：無法獲取 '{symbol}' 的數據，請檢查代碼或網絡連接。")
            st.stop()
        df.columns = df.columns.droplevel(1)  # 移除多層索引中的代碼層級
        return df
    except Exception as e:
        st.error(f"錯誤：下載 '{symbol}' 數據時發生問題 - {str(e)}。")
        st.stop()

def calculate_monthly_returns(df):
    """
    基於每月的第一個 'Open' 和最後一個 'Close' 價格計算月度內部回報。
    
    參數:
        df (pd.DataFrame): 包含 'Open' 和 'Close' 列及 datetime 索引的 DataFrame。
    
    返回:
        pd.Series: 月度內部回報（百分比）。
    """
    monthly = df.resample("ME").agg({"Open": "first", "Close": "last"})
    monthly["Intra_Return"] = (monthly["Close"] / monthly["Open"]) - 1
    return monthly["Intra_Return"] * 100  # 轉換為百分比

def get_average_monthly_returns(monthly_returns):
    """
    計算每個日曆月的平均月度內部回報。
    
    參數:
        monthly_returns (pd.Series): 帶有 datetime 索引的月度回報 Series。
    
    返回:
        pd.Series: 按月份縮寫（1月-12月）索引的平均回報。
    """
    avg_returns = monthly_returns.groupby(monthly_returns.index.month).mean()
    month_names = [calendar.month_abbr[i] for i in range(1, 13)]
    return avg_returns.reindex(range(1, 13)).set_axis(month_names)

def create_avg_returns_chart(avg_returns, symbol_name, start_year):
    """
    生成平均月度回報的互動式條形圖。
    
    參數:
        avg_returns (pd.Series): 每個月的平均回報。
        symbol_name (str): 指數名稱。
        start_year (int): 數據範圍的起始年份。
    
    返回:
        plotly.graph_objs.Figure: 用於 Streamlit 顯示的條形圖對象。
    """
    fig = px.bar(
        x=avg_returns.index,
        y=avg_returns.values,
        labels={"x": "月份", "y": "平均回報 (%)"},
        text=avg_returns.round(2).astype(str) + "%"
    )
    fig.update_traces(textposition="outside", marker_color="skyblue")
    fig.update_layout(
        width=900,
        height=500,
        title_font_size=20,
        title_x=0.5,
        yaxis_tickformat=".2f"
    )
    return fig

def create_monthly_detail_chart(monthly_returns, month_name, month_num, symbol_name, start_year):
    """
    創建顯示特定月份歷年回報的條形圖。
    
    參數:
        monthly_returns (pd.Series): 所有月度回報數據。
        month_name (str): 選定月份的名稱。
        month_num (int): 月份的數字表示（1-12）。
        symbol_name (str): 指數名稱。
        start_year (int): 數據範圍的起始年份。
    
    返回:
        plotly.graph_objs.Figure: 帶有平均線的條形圖。
    """
    month_data = monthly_returns[monthly_returns.index.month == month_num]
    average_return = month_data.mean()
    
    fig = px.bar(
        x=month_data.index.year,
        y=month_data.values,
        labels={"x": "年份", "y": f"{month_name} 回報 (%)"},
        text=month_data.round(2).astype(str) + "%"
    )
    fig.update_traces(textposition="outside", marker_color="skyblue")
    fig.update_layout(
        width=1200,
        height=600,
        title_font_size=20,
        title_x=0.5,
        yaxis_tickformat=".2f"
    )
    fig.add_hline(
        y=average_return,
        line_dash="dash",
        line_color="red",
        annotation_text=f"平均值: {average_return:.2f}%",
        annotation_position="bottom right",
        annotation=dict(font=dict(color="black", size=14))
    )
    return fig

# --- 主要應用程式 ---
st.title("指數月度回報分析工具")
st.markdown("此工具提供多個指數的歷史月度表現分析，通過互動式圖表幫助用戶深入了解數據趨勢。")

# 側邊欄：指數選擇
index_options = {
    "S&P 500 (^GSPC)": "^GSPC",
    "Hang Seng Index (HSI)": "^HSI",
    "FTSE 100 (^FTSE)": "^FTSE",
    "DAX (^GDAXI)": "^GDAXI"
}
selected_index_name = st.sidebar.selectbox(
    "選擇指數",
    options=list(index_options.keys()),
    index=0,
    help="請從下拉列表中選擇要分析的指數。"
)
selected_symbol = index_options[selected_index_name]

# 加載歷史數據
df = load_data(selected_symbol, start_date="1990-01-01")

# 用戶輸入：選擇起始年份
start_year = st.sidebar.slider(
    "選擇起始年份",
    min_value=df.index.min().year,
    max_value=2025,
    value=2000,
    step=1,
    help="請選擇分析的起始年份以過濾數據範圍。"
)

# 根據起始年份過濾數據
start_date = f"{start_year}-01-01"
df_filtered = df.loc[start_date:]

# 計算月度回報
monthly_returns = calculate_monthly_returns(df_filtered)

# 部分 1：歷年平均月度回報
st.subheader("歷年平均月度回報")
avg_returns = get_average_monthly_returns(monthly_returns)
avg_chart = create_avg_returns_chart(avg_returns, selected_index_name, start_year)
st.plotly_chart(avg_chart, use_container_width=False)

# 部分 2：特定月份的詳細回報分析
st.subheader("特定月份的詳細回報分析")
month_options = {calendar.month_name[i]: i for i in range(1, 13)}
selected_month_name = st.sidebar.selectbox(
    "選擇月份",
    options=list(month_options.keys()),
    index=0,
    help="請選擇一個月份以查看其歷年回報數據及趨勢。"
)
selected_month = month_options[selected_month_name]

# 過濾並顯示所選月份的數據
month_data = monthly_returns[monthly_returns.index.month == selected_month]
if month_data.empty:
    st.warning(f"所選範圍內 {selected_month_name} 無可用數據，請調整起始年份後重試。")
else:
    month_chart = create_monthly_detail_chart(monthly_returns, selected_month_name, selected_month, selected_index_name, start_year)
    st.plotly_chart(month_chart, use_container_width=False)

# 頁腳
st.markdown(
    '<div style="text-align: center; font-size: 1.8em;">'
    'APP developed by <a href="https://www.4mstrategy.com/" target="_blank" rel="noopener noreferrer">4M Strategy</a>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# 免責聲明及資料來源
disclaimer_text = """
### 投資免責聲明及資料來源聲明

本平台提供之資訊，包括但不限於財務數據、分析及工具，僅供參考及教育用途，並不構成財務、投資或交易建議。  
用戶不應僅依賴此資訊作出投資決定，建議在進行任何投資活動前諮詢合格的財務顧問。

本平台所使用的財務數據來自 **Yahoo Finance**。  
儘管我們致力於提供準確及最新的資訊，但我們不保證該數據的準確性、完整性或時效性。  
資訊可能存在錯誤、遺漏或不準確之處，對於因使用此資訊而導致的任何損失或損害，我們概不負責。

用戶應自行核實數據並進行獨立研究後再作出投資決定。
"""
st.markdown(disclaimer_text)
