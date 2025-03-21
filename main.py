import streamlit as st
import pandas as pd
import plotly.express as px
import calendar
import yfinance as yf

# --- Helper Functions ---
def load_data(symbol, start_date="1990-01-01"):
    """
    Downloads historical stock data from Yahoo Finance, selecting 'Open' and 'Close' columns.

    Parameters:
        symbol (str): Stock or index ticker symbol.
        start_date (str): Start date for data in 'YYYY-MM-DD' format.

    Returns:
        pd.DataFrame: DataFrame with 'Date' as datetime index, or stops execution on error.
    """
    try:
        df = yf.download(symbol, start=start_date)[['Open', 'Close']]
        if df.empty:
            st.error(f"Error: Unable to retrieve data for '{symbol}'. Check the ticker or network connection.")
            st.stop()
        return df
    except Exception as e:
        st.error(f"Error: Problem downloading '{symbol}' data - {str(e)}.")
        st.stop()

def calculate_monthly_returns(df):
    """
    Calculates monthly internal returns based on the first 'Open' and last 'Close' prices.

    Parameters:
        df (pd.DataFrame): DataFrame with 'Open', 'Close', and datetime index.

    Returns:
        pd.Series: Monthly internal returns as percentages.
    """
    monthly = df.resample("ME").agg({"Open": "first", "Close": "last"})
    monthly["Intra_Return"] = (monthly["Close"] / monthly["Open"]) - 1
    return monthly["Intra_Return"] * 100  # Convert to percentage

def get_average_monthly_returns(monthly_returns):
    """
    Computes average monthly internal returns for each calendar month.

    Parameters:
        monthly_returns (pd.Series): Monthly returns with datetime index.

    Returns:
        pd.Series: Average returns indexed by month abbreviations (Jan-Dec).
    """
    avg_returns = monthly_returns.groupby(monthly_returns.index.month).mean()
    month_names = [calendar.month_abbr[i] for i in range(1, 13)]
    return avg_returns.reindex(range(1, 13)).set_axis(month_names)

def create_avg_returns_chart(avg_returns, symbol_name, start_year):
    """
    Creates an interactive bar chart of average monthly returns.

    Parameters:
        avg_returns (pd.Series): Average returns per month.
        symbol_name (str): Name of the index.
        start_year (int): Starting year of the data range.

    Returns:
        plotly.graph_objs.Figure: Bar chart object for Streamlit display.
    """
    fig = px.bar(
        x=avg_returns.index,
        y=avg_returns.values,
        labels={"x": "Month", "y": "Average Return (%)"},
        title=f"{symbol_name} Average Monthly Returns",
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
    Creates a bar chart showing yearly returns for a specific month.

    Parameters:
        monthly_returns (pd.Series): All monthly returns data.
        month_name (str): Name of the selected month.
        month_num (int): Numeric representation of the month (1-12).
        symbol_name (str): Name of the index.
        start_year (int): Starting year of the data range.

    Returns:
        plotly.graph_objs.Figure: Bar chart with average line.
    """
    month_data = monthly_returns[monthly_returns.index.month == month_num]
    average_return = month_data.mean()
    
    fig = px.bar(
        x=month_data.index.year,
        y=month_data.values,
        labels={"x": "Year", "y": f"{month_name} Return (%)"},
        title=f"{symbol_name} {month_name} Returns",
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
        annotation_text=f"Average: {average_return:.2f}%",
        annotation_position="bottom right",
        annotation=dict(font=dict(color="black", size=14))
    )
    return fig

# --- Main Application ---
st.title("Index Monthly Returns Analysis Tool")
st.markdown("This tool provides historical monthly performance analysis for multiple indices, using interactive charts to help users understand data trends.")

# Sidebar: Index Selection
index_options = {
    "S&P 500 (^GSPC)": "^GSPC",
    "Hang Seng Index (HSI)": "^HSI",
    "FTSE 100 (^FTSE)": "^FTSE",
    "DAX (^GDAXI)": "^GDAXI"
}
selected_index_name = st.sidebar.selectbox(
    "Select Index",
    options=list(index_options.keys()),
    index=0,
    help="Choose an index to analyze from the dropdown list."
)
selected_symbol = index_options[selected_index_name]

# Load Historical Data
df = load_data(selected_symbol, start_date="1990-01-01")

# User Input: Select Starting Year
start_year = st.slider(
    "Select Starting Year",
    min_value=df.index.min().year,
    max_value=2025,
    value=2000,
    step=1,
    help="Choose the starting year to filter the data range."
)

# Filter Data Based on Starting Year
start_date = f"{start_year}-01-01"
df_filtered = df.loc[start_date:]

# Calculate Monthly Returns
monthly_returns = calculate_monthly_returns(df_filtered)

# Section 1: Average Monthly Returns Over the Years
st.subheader("Average Monthly Returns Over the Years")
avg_returns = get_average_monthly_returns(monthly_returns)
avg_chart = create_avg_returns_chart(avg_returns, selected_index_name, start_year)
st.plotly_chart(avg_chart, use_container_width=False)

# Section 2: Detailed Returns Analysis for a Specific Month
st.subheader("Detailed Returns Analysis for a Specific Month")
month_options = {calendar.month_name[i]: i for i in range(1, 13)}
selected_month_name = st.selectbox(
    "Select Month",
    options=list(month_options.keys()),
    index=0,
    help="Choose a month to view its historical returns and trends."
)
selected_month = month_options[selected_month_name]

# Filter and Display Data for the Selected Month
month_data = monthly_returns[monthly_returns.index.month == selected_month]
if month_data.empty:
    st.warning(f"No data available for {selected_month_name} in the selected range. Please adjust the starting year and try again.")
else:
    month_chart = create_monthly_detail_chart(monthly_returns, selected_month_name, selected_month, selected_index_name, start_year)
    st.plotly_chart(month_chart, use_container_width=False)

# Section 3: Half-Year Returns Comparison (May-Oct vs Nov-Apr)
st.subheader("Half-Year Returns Comparison (May-Oct vs Nov-Apr)")

# Compute half-year returns using 'Close' prices from the full dataset
half_year_df = df['Close'].resample("ME").last().pct_change(6).dropna()

# Filter for October (May-Oct) and April (Nov-Apr) periods
may_oct_df = half_year_df[half_year_df.index.month == 10]
nov_apr_df = half_year_df[half_year_df.index.month == 4]

# Convert to DataFrame and set index to year
may_oct_df = pd.DataFrame(may_oct_df, columns=["Close"])
may_oct_df.index = may_oct_df.index.year
may_oct_df.index.name = "Year"

nov_apr_df = pd.DataFrame(nov_apr_df, columns=["Close"])
nov_apr_df.index = nov_apr_df.index.year
nov_apr_df.index.name = "Year"

# Merge the two datasets on year
inner_joined_df = may_oct_df.merge(
    nov_apr_df,
    how="inner",
    left_index=True,
    right_index=True,
    suffixes=("_MayOct", "_NovApr")
)

# Filter to include only years from start_year onwards
inner_joined_df = inner_joined_df.loc[start_year:]

if inner_joined_df.empty:
    st.warning("No sufficient data available for half-year comparison after filtering. Try adjusting the starting year.")
else:
    # Compute mean returns for each period
    mean_mayoct = inner_joined_df["Close_MayOct"].mean()
    mean_novapr = inner_joined_df["Close_NovApr"].mean()

    # Prepare data for plotting
    df_plot = inner_joined_df.reset_index()
    df_melt = pd.melt(
        df_plot,
        id_vars="Year",
        value_vars=["Close_MayOct", "Close_NovApr"],
        var_name="Category",
        value_name="Return"
    )

    # Rename categories for readability
    df_melt["Category"] = df_melt["Category"].replace({
        "Close_MayOct": "May-Oct",
        "Close_NovApr": "Nov-Apr"
    })

    # Create grouped bar chart
    fig = px.bar(
        df_melt,
        x="Year",
        y="Return",
        color="Category",
        barmode="group",
        text="Return",
        labels={
            "Year": "Year",
            "Return": "Half-Year Return (%)",
            "Category": "Category"
        },
        title=f"{selected_index_name} Half-Year Returns Comparison (May-Oct vs Nov-Apr)"
    )

    # Customize the chart
    fig.update_traces(texttemplate='%{text:.3f}', textposition='outside')
    fig.update_layout(
        width=900,
        height=500,
        title_x=0.5,
        yaxis_tickformat=".2f"
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=False)

    # Display mean returns
    st.write(f"Mean May-Oct Return: {mean_mayoct:.4f}")
    st.write(f"Mean Nov-Apr Return: {mean_novapr:.4f}")

# Footer
st.markdown(
    '<div style="text-align: center; font-size: 1.8em;">'
    'APP developed by <a href="https://www.4mstrategy.com/" target="_blank" rel="noopener noreferrer">4M Strategy</a>'
    '</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# Disclaimer and Data Source
disclaimer_text = """
### Investment Disclaimer and Data Source Statement

The information provided on this platform, including but not limited to financial data, analysis, and tools, is for reference and educational purposes only and does not constitute financial, investment, or trading advice.  
Users should not rely solely on this information for investment decisions and are advised to consult a qualified financial advisor before engaging in any investment activities.

The financial data used on this platform is sourced from **Yahoo Finance**.  
While we strive to provide accurate and up-to-date information, we do not guarantee the accuracy, completeness, or timeliness of the data.  
The information may contain errors, omissions, or inaccuracies, and we are not liable for any losses or damages resulting from its use.

Users should independently verify the data and conduct their own research before making investment decisions.
"""
st.markdown(disclaimer_text)
