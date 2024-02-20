import yfinance as yf
import pandas as pd

# parameters

symbol = "btc-usd"
start = "2014-01-01"
end = "2024-02-16"
interval = "1d"
sma_s = 21
sma_l = 50
macd_short =12
macd_long = 26
macd_signal = 9
trade_value = 100
trade_type = "long"
fee_per_trade= 0.05
initial_balance=100
tp_percent = 0.01 # 1% Take Profit
sl_percent = 0.03  # 3% Stop Loss

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

# # Apply conditions to DataFrae with TP and SL
# def apply_strategy(data, tp_percent, sl_percent):
#     positions = ['na'] * len(data)
#     in_position = False
#     prev_position = 'not in trade'


#     for i in range(1, len(data)):
#         row = data.iloc[i]
#         prev_row = data.iloc[i - 1]

#         if not in_position and long_condition(row):
#             positions[i] = 'LONG'
#             in_position = True
#             prev_position = 'LONG'
#         elif in_position and long_exit_condition(row, prev_position, prev_row, tp_percent, sl_percent):
#             positions[i] = 'EXIT LONG'
#             in_position = False
#             prev_position = 'not in trade'
#         elif not in_position and short_condition(row):
#             positions[i] = 'SHORT'
#             in_position = True
#             prev_position = 'SHORT'
#         elif in_position and short_exit_condition(row, prev_position, prev_row, tp_percent, sl_percent):
#             positions[i] = 'EXIT SHORT'
#             in_position = False
#             prev_position = 'not in trade'
#         elif in_position:
#             positions[i] = "HOLD"
 
#     data['Position'] = positions
#     return data

# # ...

# Apply conditions to DataFrame with TP and SL
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


# get data 
data = get_data(symbol, start, end , interval )

# Calculate SMA and MACD
data_with_indicators = calculate_indicators(data, sma_s, sma_l, macd_short, macd_long, macd_signal)

# Drop rows with NaN values
data_with_indicators = data_with_indicators.dropna()

# Apply strategy
data_with_positions, exit_conditions = apply_strategy(data_with_indicators, tp_percent, sl_percent)

# # Output the DataFrame with positions and indicators
data_with_positions = data_with_positions[["Close","SMA_S","SMA_L","MACD_Histogram","Position"]]

word1 = 'na'
word2 = 'HOLD'

# Assuming 'A' is the column where you want to check for the words
data_with_positions = data_with_positions[~(data_with_positions['Position'].str.contains(word1, case=False, na=False) | data_with_positions['Position'].str.contains(word2, case=False, na=False))]

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


# Apply the profit calculation
df = calculate_profit(data_with_positions, trade_value)

def get_long_short_trades(df, trade_type):
    if trade_type == "long":
        trades = df[df['Position'] == 'LONG']
    elif trade_type == "short":
        trades = df[df['Position'] == 'SHORT']
    else:
        trades = df
    return trades
        
data = get_long_short_trades(df, trade_type)
data

# Function to calculate max profit and max loss
def calculate_max_profit_loss(data):
    max_profit = data['Profit'].max()
    max_loss = data['Profit'].min()
    return max_profit, max_loss

# Function to calculate total number of trades
def calculate_total_trades(data):
    if trade_type =="long" or trade_type == "short":
        total_trades = len(data)
    else:
        total_trades = (len(data))/2
    return total_trades

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
max_profit, max_loss = calculate_max_profit_loss(data)
total_trades = calculate_total_trades(data)
trading_fees = calculate_trading_fees(data, fee_per_trade)  # Replace with your actual trading fee
net_profit = calculate_net_profit(data)
roi = calculate_roi(data, initial_balance)  # Replace with your initial balance

# Print the results
print(f"Max Profit: {max_profit}")
print(f"Max Loss: {max_loss}")
print(f"Total Number of Trades: {total_trades}")
# print(f"Leverage: {leverage}")
print(f"Trading Fees: {trading_fees}")
print(f"Net Profit: {net_profit}")
print(f"ROI: {roi}%")

# Print the exit conditions
print("Exit Conditions:")
for condition, count in exit_conditions.items():
    print(f"{condition}: {count}")
