import pandas as pd
import yfinance as yf
import plotly.express as px

# Step 1: Download S&P 500 ETF (SPY) data
symbol = "SPY"  # Correct ticker for SPDR S&P 500 ETF Trust
df = yf.download(symbol, start="2010-01-01")

# Step 2: Prepare half-year returns
half_year_df = df.resample("ME").last().pct_change(6)  # 6-month percentage change
half_year_df = half_year_df.dropna()  # Remove NaN values

# Step 3: Extract May-Oct (October) and Nov-Apr (April) periods
may_oct_df = half_year_df[half_year_df.index.month == 10]  # October represents May-Oct
nov_apr_df = half_year_df[half_year_df.index.month == 4]  # April represents Nov-Apr

# Step 4: Set index to year
may_oct_df.index = may_oct_df.index.year
may_oct_df.index.name = "Year"
nov_apr_df = nov_apr_df.index = nov_apr_df.index.year
nov_apr_df.index.name = "Year"

# Step 5: Keep only the 'Close' column
may_oct_df = pd.DataFrame(may_oct_df["Close"], columns=["Close"])
nov_apr_df = pd.DataFrame(nov_apr_df["Close"], columns=["Close"])

# Step 6: Merge the two DataFrames
inner_joined_df = may_oct_df.merge(
    nov_apr_df,
    how="inner",
    left_index=True,
    right_index=True,
    suffixes=("_MayOct", "_NovApr")
)

# Step 7: Calculate statistics for May-Oct
may_oct_returns = inner_joined_df["Close_MayOct"]
may_oct_wins = (may_oct_returns > 0).sum()  # Positive returns
may_oct_losses = (may_oct_returns < 0).sum()  # Negative returns
may_oct_total = len(may_oct_returns)
may_oct_win_rate = may_oct_wins / may_oct_total if may_oct_total > 0 else 0
may_oct_mean = may_oct_returns.mean() * 100  # Mean return in percentage
may_oct_std = may_oct_returns.std() * 100    # Standard deviation in percentage

# Step 8: Calculate statistics for Nov-Apr
nov_apr_returns = inner_joined_df["Close_NovApr"]
nov_apr_wins = (nov_apr_returns > 0).sum()  # Positive returns
nov_apr_losses = (nov_apr_returns < 0).sum()  # Negative returns
nov_apr_total = len(nov_apr_returns)
nov_apr_win_rate = nov_apr_wins / nov_apr_total if nov_apr_total > 0 else 0
nov_apr_mean = nov_apr_returns.mean() * 100  # Mean return in percentage
nov_apr_std = nov_apr_returns.std() * 100    # Standard deviation in percentage

# Step 9: Prepare data for plotting
df = inner_joined_df.reset_index()
df_melt = pd.melt(
    df,
    id_vars="Year",
    value_vars=["Close_MayOct", "Close_NovApr"],
    var_name="Category",
    value_name="Return"
)
df_melt["Return"] = df_melt["Return"] * 100  # Convert to percentage

# Step 10: Rename categories to Chinese labels
df_melt["Category"] = df_melt["Category"].map({
    "Close_MayOct": "5月至10月",
    "Close_NovApr": "11月至4月"
})

# Step 11: Create grouped bar chart
fig = px.bar(
    df_melt,
    x="Year",
    y="Return",
    color="Category",
    barmode="group",
    text="Return",
    labels={
        "Year": "年份",
        "Return": "半年回報率 (%)",
        "Category": "分類"
    },
    title="SPY 5月至10月 vs 11月至4月 半年回報率比較"
)
fig.update_traces(texttemplate="%{text:.2f}", textposition="outside")
fig.update_layout(
    width=1800,
    height=1000,
    title_x=0.5,
    yaxis_tickformat=".2f"
)

# Step 12: Display the chart
fig.show()

# Step 13: Print statistics
print("5月至10月 統計:")
print(f"平均回報率: {may_oct_mean:.2f}%")
print(f"標準差 (波幅率): {may_oct_std:.2f}%")
print(f"獲勝期數: {may_oct_wins}")
print(f"虧損期數: {may_oct_losses}")
print(f"勝率: {may_oct_win_rate:.2%}")

print("\n11月至4月 統計:")
print(f"平均回報率: {nov_apr_mean:.2f}%")
print(f"標準差 (波幅率): {nov_apr_std:.2f}%")
print(f"獲勝期數: {nov_apr_wins}")
print(f"虧損期數: {nov_apr_losses}")
print(f"勝率: {nov_apr_win_rate:.2%}")
