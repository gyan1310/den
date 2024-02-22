import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Function to calculate EMA
def calculate_ema(data, ema_period):
    ema = data['Close'].ewm(span=ema_period, adjust=False).mean()
    return ema

# Function to backtest trading strategy
def backtest_strategy(data, ema_period, tp_percent, sl_percent):
    data['EMA'] = calculate_ema(data, ema_period)

    positions = ['na'] * len(data)
    in_position = False
    prev_position = 'not in trade'
    exit_conditions = {'Exit_Long_TP': 0, 'Exit_Long_SL': 0, 'Exit_Short_TP': 0, 'Exit_Short_SL': 0}

    for i in range(1, len(data)):
        row = data.iloc[i]
        prev_row = data.iloc[i - 1]

        if not in_position and row['Close'] > row['EMA'] and prev_row['Low'] <= prev_row['EMA']:
            positions[i] = 'LONG'
            in_position = True
            prev_position = 'LONG'
            entry_price = row['Open']

        elif in_position and row['Close'] > row['EMA']:
            if (row['High'] >= entry_price * (1 + tp_percent)):
                positions[i] = 'EXIT LONG TP'
                exit_conditions['Exit_Long_TP'] += 1
            elif (row['Close'] <= entry_price * (1 - sl_percent)):
                positions[i] = 'EXIT LONG SL'
                exit_conditions['Exit_Long_SL'] += 1
            else:
                positions[i] = 'EXIT LONG'
            in_position = False
            prev_position = 'not in trade'

        elif not in_position and row['Close'] < row['EMA'] and prev_row['High'] >= prev_row['EMA']:
            positions[i] = 'SHORT'
            in_position = True
            prev_position = 'SHORT'
            entry_price = row['Close']

        elif in_position and row['Close'] < row['EMA']:
            if (row['Low'] < entry_price * (1 - tp_percent)):
                positions[i] = 'EXIT SHORT TP'
                exit_conditions['Exit_Short_TP'] += 1
            elif (row['Close'] >= entry_price * (1 + sl_percent)):
                positions[i] = 'EXIT SHORT SL'
                exit_conditions['Exit_Short_SL'] += 1
            else:
                positions[i] = 'EXIT SHORT'
            in_position = False
            prev_position = 'not in trade'
        else:
            positions[i] = "HOLD"

    data['Position'] = positions
    return data, exit_conditions

# Example usage
symbol = "btc-usd"
start_date = "2024-01-01"
end_date = "2024-02-16"
interval = "1d"
ema_period = 21
tp_percent = 0.005  # 0.5%
sl_percent = 0.01  # 1%

# Get data
data = yf.download(symbol, start_date, end_date, interval)

# Backtest strategy
backtest_data, exit_conditions = backtest_strategy(data, ema_period, tp_percent, sl_percent)

# Display results
print(backtest_data[['Close', 'EMA', 'Position']])
print("Exit Conditions:")
for condition, count in exit_conditions.items():
    print(f"{condition}: {count}")
# Plotting the closing prices
plt.figure(figsize=(10, 6))
plt.plot(backtest_data['Close'], label='Close Price', alpha=0.5)
plt.plot(backtest_data['EMA'], label=f'{ema_period}-day EMA', linestyle='--', alpha=0.8)

# Plotting entry and exit points
entry_long = backtest_data[backtest_data['Position'] == 'LONG'].index
exit_long = backtest_data[backtest_data['Position'] == 'EXIT LONG'].index
entry_short = backtest_data[backtest_data['Position'] == 'SHORT'].index
exit_short = backtest_data[backtest_data['Position'] == 'EXIT SHORT'].index

plt.scatter(entry_long, backtest_data['Close'][entry_long], marker='^', color='g', label='Long Entry')
plt.scatter(exit_long, backtest_data['Close'][exit_long], marker='v', color='y', label='Long Exit')
plt.scatter(entry_short, backtest_data['Close'][entry_short], marker='v', color='r', label='Short Entry')
plt.scatter(exit_short, backtest_data['Close'][exit_short], marker='^', color='b', label='Short Exit')

plt.title('Trading Strategy Entry and Exit Points')
plt.xlabel('Date')
plt.ylabel('Close Price')
plt.legend()
plt.show()
