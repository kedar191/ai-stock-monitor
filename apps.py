import streamlit as st
import pandas as pd
import plotly.express as px
import yfinance as yf

st.set_page_config(page_title="AI Stock Monitor & Shadow Portfolio", layout="wide", initial_sidebar_state="expanded")

# --- Load Portfolio Data ---
@st.cache_data
def load_portfolio():
    return pd.read_csv("portfolio2.csv", sep="\t")

portfolio = load_portfolio()

# --- Load AI Universe Data ---
@st.cache_data
def load_universe():
    return pd.read_csv("ai_universe.csv", sep="\t")

ai_universe = load_universe()

# ---- PAGE LAYOUT ----
st.title("🧠 AI Stock Monitor & Shadow Portfolio")
st.markdown("Track, analyze, and research the best AI investment opportunities (US + China).")

tab1, tab2, tab3 = st.tabs(["📊 Portfolio", "👀 AI Stock Monitor", "📝 Research & Insights"])

with tab1:
    st.header("Your Shadow AI Portfolio")
    kpi1, kpi2, kpi3 = st.columns(3)
    total_invested = portfolio['Investment (INR)'].sum()
    kpi1.metric("Total Invested (₹)", f"{total_invested:,.0f}")
    total_value = 0
    current_prices = []
    USDINR = 83.5  # Adjust as needed
    
    for i, row in portfolio.iterrows():
        try:
            ticker = row['Ticker']
            # Use ticker as-is for US stocks; for HK or SZ stocks, keep suffix
            ticker_mod = ticker
            data = yf.Ticker(ticker_mod)
            live_price_usd = data.history(period="1d")["Close"].values[-1]
            
            # Convert USD price to INR for consistency
            if ticker.endswith(".SZ") or ticker.endswith(".HK"):
                # Assume prices from yfinance for these markets are in local currency
                live_price_inr = live_price_usd
            else:
                live_price_inr = live_price_usd * USDINR
            
            current_prices.append(live_price_inr)
            total_value += live_price_inr * row['Units']
        except Exception:
            # Fallback: use Buy Price if live fetch fails
            current_prices.append(row['Buy Price (INR)'])
            total_value += row['Buy Price (INR)'] * row['Units']

    kpi2.metric("Current Value (est, ₹)", f"{int(total_value):,}")
    gain = total_value - total_invested
    gain_pct = (gain / total_invested * 100) if total_invested else 0
    kpi3.metric("Total Return", f"{gain:,.0f} ({gain_pct:+.2f}%)", delta_color="normal")

    # Show the table
    portfolio['Current Price (INR)'] = current_prices
    portfolio['Current Value'] = (portfolio['Current Price (INR)'] * portfolio['Units']).round(2)
    portfolio['Gain/Loss (₹)'] = (portfolio['Current Value'] - portfolio['Investment (INR)']).round(2)
    portfolio['Gain/Loss (%)'] = ((portfolio['Gain/Loss (₹)'] / portfolio['Investment (INR)']) * 100).round(2)
    st.dataframe(portfolio, use_container_width=True)

    # Pie chart by Barbell Type
    pie = px.pie(portfolio, names='Barbell Type', values='Investment (INR)', title="Allocation by Barbell Type")
    st.plotly_chart(pie, use_container_width=True)
    # Bar chart by Gain/Loss
    bar = px.bar(portfolio, x='Stock', y='Gain/Loss (₹)', color='Barbell Type', title="Gain/Loss by Stock", color_discrete_sequence=px.colors.qualitative.Dark24)
    st.plotly_chart(bar, use_container_width=True)

with tab2:
    st.header("AI Stock Universe: Watch & Screen")
    # Filter/search
    search = st.text_input("🔎 Search stocks (name or ticker)")
    filtered = ai_universe
    if search:
        search = search.lower()
        filtered = ai_universe[ai_universe.apply(lambda row: search in str(row['Stock']).lower() or search in str(row['Ticker']).lower(), axis=1)]
    # Add "Flag" columns
    def undervalued(row):
        try:
            return float(row['P/E']) < 20
        except: return False
    filtered['Undervalued'] = filtered.apply(undervalued, axis=1)
    filtered['High Momentum'] = filtered['YTD %'] > 30
    st.dataframe(filtered, use_container_width=True)
    # Pie by Region
    pie2 = px.pie(filtered, names='Region', title="Universe by Region")
    st.plotly_chart(pie2, use_container_width=True)

with tab3:
    st.header("Research & Insights")
    st.markdown("""
    - **News headlines:** Add manually or use an RSS feed/news API in the future.
    - **Stock notes:** Jot down research, triggers, or macro news per stock.
    - **GPT-style analysis:** (Add via OpenAI API for summaries in future versions.)
    """)
    # Simple note input
    note = st.text_area("Write a research note or paste key news here", "")
    if st.button("Save note"):
        st.success("Note saved (not persistent in demo)")

st.markdown("---")
st.caption("Built by Kedar + ChatGPT | v1.0")
