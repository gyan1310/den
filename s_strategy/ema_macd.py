import yfinance as yf
import pandas as pd

symbol = "btc-usd"
start = "2014-01-01"
end = "2024-02-16"
interval = "1d"
data = yf.download(symbol, start, end, interval)
print(data)
# Function to calculate SMA and MACD
def calculate_indicators(data, sma_s_period=20, sma_l_period=50, macd_short=12, macd_long=26, macd_signal=9):
    data['SMA_S'] = data['Close'].rolling(window=sma_s_period).mean()
    data['SMA_L'] = data['Close'].rolling(window=sma_l_period).mean()

    # Calculate MACD
    data['ShortEMA'] = data['Close'].ewm(span=macd_short, adjust=False).mean()
    data['LongEMA'] = data['Close'].ewm(span=macd_long, adjust=False).mean()
    data['MACD'] = data['ShortEMA'] - data['LongEMA']
    data['Signal_Line'] = data['MACD'].ewm(span=macd_signal, adjust=False).mean()
    data['MACD_Histogram'] = data['MACD'] - data['Signal_Line']

    return data

# Calculate SMA and MACD
data_with_indicators = calculate_indicators(data)

# Drop rows with NaN values
data_with_indicators = data_with_indicators.dropna()

# Long condition
def long_condition(row):
    return row['Close'] >= row['SMA_S'] and row['MACD_Histogram'] >= 0

# Long exit condition
def long_exit_condition(row, prev_position, prev_row):
    if prev_position == "LONG":
        return row['Close'] < row['SMA_S'] or row['MACD_Histogram'] < prev_row['MACD_Histogram']

# Short condition
def short_condition(row):
    return row['Close'] < row['SMA_S'] and row['MACD_Histogram'] < 0

# Short exit condition
def short_exit_condition(row, prev_position, prev_row):
    if prev_position == "SHORT":
        return row['Close'] > row['SMA_S'] or row['MACD_Histogram'] > prev_row['MACD_Histogram']

# Apply conditions to DataFrame
def apply_strategy(data):
    positions = ['na'] * len(data)
    in_position = False
    prev_position = 'not in trade'

    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        if not in_position and long_condition(row):
            positions[i] = 'LONG'
            in_position = True
            prev_position = 'LONG'
        elif in_position and long_exit_condition(row, prev_position, prev_row):
            positions[i] = 'EXIT LONG'
            in_position = False
            prev_position = 'not in trade'
        elif not in_position and short_condition(row):
            positions[i] = 'SHORT'
            in_position = True
            prev_position = 'SHORT'
        elif in_position and short_exit_condition(row, prev_position, prev_row):
            positions[i] = 'EXIT SHORT'
            in_position = False
            prev_position = 'not in trade'
        elif in_position:
            positions[i] = "HOLD"
 
    data['Position'] = positions
    return data

# Apply strategy
data_with_positions = apply_strategy(data_with_indicators)
print(data_with_positions)
# # Output the DataFrame with positions and indicators
data_with_positions = data_with_positions[["Close","SMA_S","SMA_L","MACD_Histogram","Position"]]
# Drop rows where 'Position' is 'na' or 'HOLD'
data_with_positions = data_with_positions[data_with_positions['Position'].isin(['LONG', 'SHORT', 'EXIT LONG', 'EXIT SHORT'])]
data_with_positions
# selected_columns = ['Close', 'SMA_S', 'SMA_L', 'MACD_Histogram', 'Position']
# data_with_positions[selected_columns]

# Function to calculate profit for each trade and drop rows with 'na' or 'HOLD' positions
def calculate_profit(data):
    profits = []

    for i in range(len(data)):
        row = data.iloc[i]

        if row['Position'] == 'LONG':
            # Assuming you buy at the 'Close' price
            entry_price = row['Close']
            exit_price = data.iloc[i + 1]['Close'] if i < len(data) - 1 else row['Close']
            profit = (((exit_price - entry_price) / entry_price) * 100) * 12
            profits.append(profit)

        elif row['Position'] == 'SHORT':
            # Assuming you short at the 'Close' price
            entry_price = row['Close']
            exit_price = data.iloc[i + 1]['Close'] if i < len(data) - 1 else row['Close']
            profit = (((entry_price - exit_price) / entry_price) * 100) * 12
            profits.append(profit)

        else:
            profits.append(0)  # For 'not in trade' or 'EXIT' positions

    data['Profit'] = profits
    return data

# Apply the profit calculation and drop rows
data_with_profit = calculate_profit(data_with_positions)
data_with_profit
# Function to calculate max profit and max loss
def calculate_max_profit_loss(data):
    max_profit = data['Profit'].max()
    max_loss = data['Profit'].min()
    return max_profit, max_loss

# Function to calculate total number of trades
def calculate_total_trades(data):
    total_trades = data[data['Position'].str.contains('EXIT')].shape[0]
    return total_trades * 2

# Function to calculate trading fees
def calculate_trading_fees(data, fee_per_trade):
    total_trades = calculate_total_trades(data)
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

# Example usage
max_profit, max_loss = calculate_max_profit_loss(data_with_positions)
total_trades = calculate_total_trades(data_with_positions)
trading_fees = calculate_trading_fees(data_with_positions, fee_per_trade= 0.05)  # Replace with your actual trading fee
net_profit = calculate_net_profit(data_with_positions)
roi = calculate_roi(data_with_positions, initial_balance=100)  # Replace with your initial balance

# Print the results
print(f"Max Profit: {max_profit}")
print(f"Max Loss: {max_loss}")
print(f"Total Number of Trades: {total_trades}")
# print(f"Leverage: {leverage}")
print(f"Trading Fees: {trading_fees}")
print(f"Net Profit: {net_profit}")
print(f"ROI: {roi}%")
