import streamlit as st
import yfinance as yf
import pandas as pd


def get_data(symbol, start, end, interval):
    data = yf.download(symbol, start, end, interval)
    return data

# Function to calculate SMA and MACD
def calculate_indicators(data, sma_s, sma_l, macd_short, macd_long, macd_signal):
    data['SMA_S'] = data['Close'].rolling(window=sma_s).mean()
    data['SMA_L'] = data['Close'].rolling(window=sma_l).mean()

    # Calculate MACD
    data['ShortEMA'] = data['Close'].ewm(span=macd_short, adjust=False).mean()
    data['LongEMA'] = data['Close'].ewm(span=macd_long, adjust=False).mean()
    data['MACD'] = data['ShortEMA'] - data['LongEMA']
    data['Signal_Line'] = data['MACD'].ewm(span=macd_signal, adjust=False).mean()
    data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']

    return data

# Long condition
def long_condition(row):
    return row['Close'] >= row['SMA_S'] and row['MACD_Histogram'] >= 0

# Modify exit conditions to include TP and SL
def long_exit_condition(row, prev_position, prev_row, tp_percent, sl_percent):
    if prev_position == "LONG":
        tp_price = prev_row['Close'] * (1 + tp_percent)
        sl_price = prev_row['Close'] * (1 - sl_percent)
        
        return row['Close'] < row['SMA_S'] or row['MACD_Histogram'] < prev_row['MACD_Histogram'] or row['Close'] >= tp_price or row['Close'] <= sl_price

# Short condition
def short_condition(row):
    return row['Close'] < row['SMA_S'] and row['MACD_Histogram'] < 0

def short_exit_condition(row, prev_position, prev_row, tp_percent, sl_percent):
    if prev_position == "SHORT":
        tp_price = prev_row['Close'] * (1 - tp_percent)
        sl_price = prev_row['Close'] * (1 + sl_percent)
        
        return row['Close'] > row['SMA_S'] or row['MACD_Histogram'] > prev_row['MACD_Histogram'] or row['Close'] <= tp_price or row['Close'] >= sl_price

def apply_strategy(data, tp_percent, sl_percent):
    positions = ['na'] * len(data)
    in_position = False
    prev_position = 'not in trade'
    exit_conditions = {'Exit_Long_TP': 0, 'Exit_Long_SL': 0, 'Exit_Short_TP': 0, 'Exit_Short_SL': 0}

    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        if not in_position and long_condition(row):
            positions[i] = 'LONG'
            in_position = True
            prev_position = 'LONG'
        elif in_position and long_exit_condition(row, prev_position, prev_row, tp_percent, sl_percent):
            if row['Close'] >= prev_row['Close'] * (1 + tp_percent):
                positions[i] = 'EXIT LONG TP'
                exit_conditions['Exit_Long_TP'] += 1
            elif row['Close'] <= prev_row['Close'] * (1 - sl_percent):
                positions[i] = 'EXIT LONG SL'
                exit_conditions['Exit_Long_SL'] += 1
            else:
                positions[i] = 'EXIT LONG'
            in_position = False
            prev_position = 'not in trade'
        elif not in_position and short_condition(row):
            positions[i] = 'SHORT'
            in_position = True
            prev_position = 'SHORT'
        elif in_position and short_exit_condition(row, prev_position, prev_row, tp_percent, sl_percent):
            if row['Close'] <= prev_row['Close'] * (1 - tp_percent):
                positions[i] = 'EXIT SHORT TP'
                exit_conditions['Exit_Short_TP'] += 1
            elif row['Close'] >= prev_row['Close'] * (1 + sl_percent):
                positions[i] = 'EXIT SHORT SL'
                exit_conditions['Exit_Short_SL'] += 1
            else:
                positions[i] = 'EXIT SHORT'
            in_position = False
            prev_position = 'not in trade'
        elif in_position:
            positions[i] = "HOLD"
    
    data['Position'] = positions
    return data, exit_conditions

def calculate_profit(data, trade_value):
    profits = []

    for i in range(len(data)):
        row = data.iloc[i]

        if row['Position'] == 'LONG':
            entry_price = row['Close']
            exit_price = data.iloc[i + 1]['Close'] if i < len(data) - 1 else row['Close']
            profit_pct = ((exit_price - entry_price) / entry_price)
            profit = trade_value * profit_pct
            profits.append(profit)
        elif row['Position'] == 'SHORT':
            entry_price = row['Close']
            exit_price = data.iloc[i + 1]['Close'] if i < len(data) - 1 else row['Close']
            profit_pct = ((entry_price - exit_price) / entry_price)
            profit = trade_value * profit_pct
            profits.append(profit)
        else:
            profits.append(0)  # For 'not in trade' or 'EXIT' positions

    data['Profit'] = profits
    return data

def get_long_short_trades(df, trade_type):
    if trade_type == "long":
        trades = df[df['Position'] == 'LONG']
    elif trade_type == "short":
        trades = df[df['Position'] == 'SHORT']
    else:
        trades = df
    return trades
        

# Function to calculate max profit and max loss
def calculate_max_profit_loss(data):
    max_profit = data['Profit'].max()
    max_loss = data['Profit'].min()
    return max_profit, max_loss

# Function to calculate total number of trades
def calculate_total_trades(data, trade_type):
    if trade_type =="long" or trade_type == "short":
        total_trades = len(data)
    else:
        total_trades = (len(data))/2
    return total_trades

# Function to calculate trading fees
def calculate_trading_fees(data, fee_per_trade, trade_type):
    total_trades = calculate_total_trades(data, trade_type)
    trading_fees = total_trades * fee_per_trade
    return trading_fees

# Function to calculate net profit
def calculate_net_profit(data):
    net_profit = data['Profit'].sum()
    return net_profit

# Function to calculate ROI (Return on Investment)
def calculate_roi(data, initial_balance):
    net_profit = calculate_net_profit(data)
    roi = (net_profit / initial_balance) * 100
    return roi



def main():
    st.title("Trading Strategy Analysis")

    # Sidebar inputs
    symbol = st.sidebar.text_input("Enter symbol (e.g., 'btc-usd'):", "btc-usd")
    start_date = st.sidebar.text_input("Enter start date (YYYY-MM-DD):", "2014-01-01")
    end_date = st.sidebar.text_input("Enter end date (YYYY-MM-DD):", "2024-02-16")
    interval = st.sidebar.selectbox("Select interval:", ["1d", "1wk", "1mo"], index=0)
    trade_value = st.sidebar.number_input("enter trade value per trade")
    trade_type = st.sidebar.selectbox("Select trade direction:", ["long", "short", "both"], index=0)
    # Calculate indicators
    data = get_data(symbol, start_date, end_date, interval)
    data_with_indicators = calculate_indicators(data, sma_s=21, sma_l=50, macd_short=12, macd_long=26, macd_signal=9)

    # Strategy parameters
    tp_percent = st.sidebar.slider("Take Profit (%)", 0.01, 0.10, 0.01, 0.01)
    sl_percent = st.sidebar.slider("Stop Loss (%)", 0.01, 0.10, 0.03, 0.01)

    # Apply strategy
    data_with_positions, exit_conditions = apply_strategy(data_with_indicators, tp_percent, sl_percent)

    # Display results
    st.subheader("Results")
    st.dataframe(data_with_positions[["Close", "SMA_S", "SMA_L", "MACD_Histogram", "Position"]])

    word1 = 'na'
    word2 = 'HOLD'

    # Assuming 'A' is the column where you want to check for the words
    data_with_positions = data_with_positions[~(data_with_positions['Position'].str.contains(word1, case=False, na=False) | data_with_positions['Position'].str.contains(word2, case=False, na=False))]
    
    df = calculate_profit(data_with_positions, trade_value)
    data = get_long_short_trades(df, trade_type)


    max_profit, max_loss = calculate_max_profit_loss(data)
    total_trades = calculate_total_trades(data, trade_type)
    trading_fees = calculate_trading_fees(data,trade_type, fee_per_trade=0.05)
    net_profit = calculate_net_profit(data)
    roi = calculate_roi(data, initial_balance=100)

    st.write(f"Max Profit: {max_profit}")
    st.write(f"Max Loss: {max_loss}")
    st.write(f"Total Number of Trades: {total_trades}")
    st.write(f"Trading Fees: {trading_fees}")
    st.write(f"Net Profit: {net_profit}")
    st.write(f"ROI: {roi}%")

    # Display exit conditions
    st.subheader("Exit Conditions")
    for condition, count in exit_conditions.items():
        st.write(f"{condition}: {count}")

if __name__ == "__main__":
    main()
