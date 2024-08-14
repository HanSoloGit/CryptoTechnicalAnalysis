import streamlit as st
import yfinance as yf
import ta
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# Function to fetch data
def fetch_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data

# Function to calculate indicators
def calculate_indicators(data, indicators):
    results = {}
    if 'SMA' in indicators:
        if len(data) >= 200:
            results['SMA_50'] = ta.trend.SMAIndicator(data['Close'], window=50).sma_indicator()
            results['SMA_200'] = ta.trend.SMAIndicator(data['Close'], window=200).sma_indicator()
        else:
            st.warning("Not enough data to calculate SMA 200")
    if 'EMA' in indicators:
        results['EMA_20'] = ta.trend.EMAIndicator(data['Close'], window=20).ema_indicator()
    if 'RSI' in indicators:
        results['RSI'] = ta.momentum.RSIIndicator(data['Close'], window=14).rsi()
    if 'MACD' in indicators:
        macd = ta.trend.MACD(data['Close'])
        results['MACD'] = macd.macd()
        results['MACD_signal'] = macd.macd_signal()
        results['MACD_hist'] = macd.macd_diff()
    if 'Bollinger Bands' in indicators:
        bb = ta.volatility.BollingerBands(data['Close'], window=20, window_dev=2)
        results['Upper_BB'] = bb.bollinger_hband()
        results['Middle_BB'] = bb.bollinger_mavg()
        results['Lower_BB'] = bb.bollinger_lband()
    if 'Sharpe Ratio' in indicators:
        daily_return = data['Close'].pct_change().mean()
        daily_volatility = data['Close'].pct_change().std()
        sharpe_ratio = daily_return / daily_volatility * np.sqrt(252)  # Annualized Sharpe Ratio
        results['Sharpe_Ratio'] = sharpe_ratio
    if 'Sortino Ratio' in indicators:
        daily_return = data['Close'].pct_change().mean()
        downside_risk = data['Close'].pct_change()[data['Close'].pct_change() < 0].std()
        sortino_ratio = daily_return / downside_risk * np.sqrt(252) if downside_risk != 0 else np.nan
        results['Sortino_Ratio'] = sortino_ratio
    return results

def plot_data(data, indicators, ticker, mode, x_range=None, y_range=None):
    fig = go.Figure()

    # Add Candlestick chart
    fig.add_trace(go.Candlestick(
        x=data.index,
        open=data['Open'],
        high=data['High'],
        low=data['Low'],
        close=data['Close'],
        name='Price (candlesticks)'
    ))

    # Plot SMA50 and SMA200 together
    if 'SMA_50' in indicators and 'SMA_200' in indicators:
        fig.add_trace(go.Scatter(x=data.index, y=indicators['SMA_50'], mode='lines', name='SMA 50', line=dict(dash='solid')))
        fig.add_trace(go.Scatter(x=data.index, y=indicators['SMA_200'], mode='lines', name='SMA 200', line=dict(dash='solid')))

    # Plot other indicators individually
    for name, values in indicators.items():
        if name not in ['SMA_50', 'SMA_200', 'MACD_hist', 'Sharpe_Ratio', 'Sortino_Ratio']:
            fig.add_trace(go.Scatter(x=data.index, y=values, mode='lines', name=name, line=dict(dash='solid')))

    # Plot MACD histogram with color coding
    if 'MACD_hist' in indicators:
        colors = ['green' if val >= 0 else 'red' for val in indicators['MACD_hist']]
        fig.add_trace(go.Bar(x=data.index, y=indicators['MACD_hist'], name='MACD Histogram', marker_color=colors))

    # Set the mode for interaction to 'drawline'
    fig.update_layout(
        dragmode='drawline',  # Always set to drawline
        xaxis_title='Date',
        yaxis_title='Price (USD)',
        hovermode='closest',
        showlegend=True,
        margin=dict(l=40, r=40, t=40, b=40),
        xaxis_range=x_range,  # Preserve the x-axis zoom range
        yaxis_range=y_range,  # Preserve the y-axis zoom range
        modebar_add=["drawline", "eraseshape"],  # Include modebar tools
    )

    # Re-add shapes from session state if they exist
    if 'shapes' in st.session_state:
        fig.update_layout(shapes=st.session_state['shapes'])

    st.plotly_chart(fig, use_container_width=True)
    return fig  # Return the figure object

# Function to display explanations
def display_explanations(indicators):
    st.write("### Explanation of Selected Indicators:")
    
    if 'SMA' in indicators:
        with st.expander("Simple Moving Average (SMA)"):
            st.write("""
            **Simple Moving Average (SMA):**  
            The SMA calculates the average of a selected range of prices, typically closing prices, over a specific number of periods.
            
            **Golden Cross:** When a short-term SMA crosses above a long-term SMA, it may signal a bullish trend.  
            **Death Cross:** Conversely, when a short-term SMA crosses below a long-term SMA, it may signal a bearish trend.

            **Finance Perspective:**  
            SMAs are used to smooth out price data to identify the direction of the trend. Traders often use SMAs to determine potential support and resistance levels. The simplicity of SMAs makes them popular, though they are often used in conjunction with other indicators to confirm trends and avoid false signals.
            """)
            
    if 'EMA' in indicators:
        with st.expander("Exponential Moving Average (EMA)"):
            st.write("""
            **Exponential Moving Average (EMA):**  
            The EMA is similar to the SMA but gives more weight to recent prices, making it more responsive to new information.
            
            **Usage:**  
            Traders use EMAs to spot trends earlier than they might with SMAs. The EMA reacts more quickly to price changes, which can be both an advantage and a disadvantage. If the price is consistently above the EMA, it typically indicates an uptrend. This suggests dat de markt bullish is, en prijzen mogelijk blijven stijgen.
            If the price is consistently below the EMA, it usually indicates a downtrend. This suggests dat de markt bearish is, en prijzen mogelijk blijven dalen.

            **Finance Perspective:**  
            EMAs are particularly useful for traders looking to catch early trends and reversals. They are widely used in combination with other indicators like the MACD. The sensitivity of the EMA to price changes can help traders act quickly, but it can also lead to more frequent false signals.
            """)
            
    if 'RSI' in indicators:
        with st.expander("Relative Strength Index (RSI)"):
            st.write("""
            **Relative Strength Index (RSI):**  
            RSI is a momentum oscillator that measures the speed and change of price movements. It ranges from 0 to 100.
            
            **Overbought/Oversold Levels:**  
            RSI values above 70 may indicate that an asset is overbought and due for a correction, while values below 30 suggest it may be oversold and ripe for a rally.

            **Finance Perspective:**  
            The RSI is a popular indicator for identifying potential buy and sell points based on momentum. It is often used to confirm price movements en gauge the strength of a trend. While effective, the RSI can produce false signals in volatile markets or during strong trends, where prices may remain overbought or oversold for extended periods.
            """)
            
    if 'MACD' in indicators:
        with st.expander("Moving Average Convergence Divergence (MACD)"):
            st.write("""
            **Moving Average Convergence Divergence (MACD):**  
            The MACD is a trend-following momentum indicator that shows the relationship between two moving averages of a security's price. It consists of the MACD line, the signal line, and the histogram.

            **Bullish/Bearish Signals:**  
            - **Bullish:** When the MACD line crosses above the signal line, it may indicate a bullish trend.
            - **Bearish:** When the MACD line crosses below the signal line, it may indicate a bearish trend.

            **Finance Perspective:**  
            The MACD is valued for its versatility, as it combines momentum and trend-following strategies. The histogram provides additional insight into the strength and duration of a trend, making the MACD a favored tool among traders. However, like all indicators, it should be used in conjunction with others to confirm signals.
            """)
            
    if 'Bollinger Bands' in indicators:
        with st.expander("Bollinger Bands"):
            st.write("""
            **Bollinger Bands:**  
            Bollinger Bands consist of a middle band (typically a 20-day SMA) and an upper and lower band (set at a distance of two standard deviations).

            **Overbought/Oversold Conditions:**  
            - **Overbought:** Price nearing the upper band may indicate overbought conditions.
            - **Oversold:** Price nearing the lower band may indicate oversold conditions.

            **Finance Perspective:**  
            Bollinger Bands are useful for measuring market volatility. When the bands contract, it suggests low volatility and the potential for a breakout. Conversely, when the bands widen, it indicates high volatility. Bollinger Bands are often used in combination with other indicators to confirm trends en potential reversal points.
            """)

    if 'Sharpe Ratio' in indicators:
        with st.expander("Sharpe Ratio"):
            st.write("""
            **Sharpe Ratio:**  
            The Sharpe Ratio is a measure of risk-adjusted return. It is calculated by dividing the average return earned in excess of the risk-free rate by the standard deviation of returns.

            **Interpretation:**  
            A higher Sharpe Ratio indicates better risk-adjusted performance, while a lower Sharpe Ratio may suggest that the returns are not compensating for the risks taken.

            **Finance Perspective:**  
            The Sharpe Ratio is widely used to compare the performance of assets or portfolios. It provides insight into whether the returns are due to smart investment decisions or excessive risk. A Sharpe Ratio greater than 1 is generally considered good, while a ratio below 1 suggests that the returns may not be worth the risks.
            """)

    if 'Sortino Ratio' in indicators:
        with st.expander("Sortino Ratio"):
            st.write("""
            **Sortino Ratio:**  
            The Sortino Ratio is similar to the Sharpe Ratio, but it differentiates harmful volatility from general volatility by using only downside deviation.

            **Interpretation:**  
            A higher Sortino Ratio indicates better risk-adjusted performance, focusing on downside risk. It provides a clearer picture of the return relative to the negative volatility, which is often of greater concern to investors.

            **Finance Perspective:**  
            The Sortino Ratio is particularly useful for risk-averse investors who are more concerned with avoiding losses than capturing gains. By focusing on the downside risk, it gives a more targeted view of the risk-adjusted return, making it a preferred measure for evaluating the performance of assets or portfolios where downside protection is critical.
            """)

# Streamlit dashboard
st.title("Crypto Technical Analysis")

# User inputs
default_cryptos = ['BTC-USD', 'ETH-USD', 'BNB-USD', 'ADA-USD', 'SOL-USD', 'XRP-USD', 'DOT-USD', 'DOGE-USD', 'UNI-USD', 'LINK-USD', 'LTC-USD', 'BCH-USD', 'XLM-USD', 'VET-USD', 'FIL-USD', 'TRX-USD', 'AVAX-USD', 'MATIC-USD', 'ATOM-USD', 'FTT-USD']
user_cryptos = st.text_input("Enter additional cryptocurrencies (comma separated, e.g., 'ADA-USD,DOT-USD')")

cryptos = default_cryptos + [crypto.strip() for crypto in user_cryptos.split(',')] if user_cryptos else default_cryptos
selected_crypto = st.selectbox("Select Cryptocurrency", cryptos)

analysis_options = ['SMA', 'EMA', 'RSI', 'MACD', 'Bollinger Bands', 'Sharpe Ratio', 'Sortino Ratio']
selected_analysis = st.multiselect("Select Analysis Type", analysis_options, default=['SMA', 'RSI'])

start_date = st.date_input("Start Date", pd.to_datetime("2020-01-01"))
end_date = st.date_input("End Date", pd.to_datetime(datetime.today()))

# Fetch data
data = fetch_data(selected_crypto, start_date, end_date)

# Calculate indicators
indicators = calculate_indicators(data, selected_analysis)

# Initialize session state for x_range, y_range, and shapes if not present
if 'x_range' not in st.session_state:
    st.session_state['x_range'] = None
if 'y_range' not in st.session_state:
    st.session_state['y_range'] = None
if 'shapes' not in st.session_state:
    st.session_state['shapes'] = []

# Plot data
fig = plot_data(data, indicators, selected_crypto, 'drawline', st.session_state['x_range'], st.session_state['y_range'])

# Update the session state with the current zoom/pan range and shapes
if fig.layout.xaxis.range:
    st.session_state['x_range'] = fig.layout.xaxis.range
if fig.layout.yaxis.range:
    st.session_state['y_range'] = fig.layout.yaxis.range

# Save shapes only if there are new shapes
if fig.layout.shapes:
    st.session_state['shapes'] = fig.layout.shapes

# Display explanations
display_explanations(selected_analysis)
