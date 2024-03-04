import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import yfinance as yf

# Example usage
symbol = "btc-usd"
start_date = "2024-01-10"
end_date = "2024-03-01"

df = yf.download(symbol, start_date, end_date, interval="15m")

# Calculate 21 EMA
df['EMA21'] = df['Close'].ewm(span=21, adjust=False).mean()

# Initialize position state
position = 'flat'
tp_pct = 0.01  # showa 1% tp 
sl_pct = 0.05   # shows 5% sl

# Initialize entry and exit points
entry_points = []
exit_points = []

# Initialize trading statistics
num_trades = 0
num_profitable_trades = 0
num_losing_trades = 0
total_profit = 0
total_loss = 0

# Trading strategy conditions
for i in range(2, len(df)):
    if position == 'flat':
        if (
            df['Close'][i] >= df['EMA21'][i] and
            df['Close'][i-1] > df['EMA21'][i-1] and
            df['Close'][i-2] > df['EMA21'][i-2] and
            df['Low'][i] <= df['EMA21'][i-1]
        ):
            df.loc[df.index[i], 'Trades'] = 'long'
            position = 'long'
            entry_price = df['EMA21'][i]
            entry_points.append((df.index[i], entry_price))
            num_trades += 1
        elif (
            df['Close'][i] <= df['EMA21'][i] and
            df['Close'][i-1] < df['EMA21'][i-1] and
            df['Close'][i-2] < df['EMA21'][i-2] and
            df['High'][i] >= df['EMA21'][i-1]
        ):
            df.loc[df.index[i], 'Trades'] = 'short'
            position = 'short'
            entry_price = df['EMA21'][i]
            entry_points.append((df.index[i], entry_price))
            num_trades += 1
    elif position == 'long':
        if df["High"][i] >= (entry_price * (1 + tp_pct)):   # 100 * (1+ 0.01) = 101 /// 100 --> 101 --> 1%
            df.loc[df.index[i], 'Trades'] = 'exit_long_tp'
            position = 'flat'
            exit_points.append((df.index[i], df["High"][i]))
            num_profitable_trades += 1
            total_profit += (df["High"][i] - entry_price)
        elif df["Low"][i] <= (entry_price * (1 - sl_pct)):
            df.loc[df.index[i], 'Trades'] = 'exit_long_sl'
            position = 'flat'
            exit_points.append((df.index[i], df["Low"][i]))
            num_losing_trades += 1
            total_loss += (entry_price - df["Low"][i])
        elif df['High'][i] < df['EMA21'][i-1]:
            df.loc[df.index[i], 'Trades'] = 'exit_long'
            position = 'flat'
            exit_points.append((df.index[i], df['EMA21'][i-1]))
    elif position == 'short':
        if df["Low"][i] <= (entry_price * (1 - tp_pct)):
            df.loc[df.index[i], 'Trades'] = 'exit_short_tp'
            position = 'flat'
            exit_points.append((df.index[i], df["Low"][i]))
            num_profitable_trades += 1
            total_profit += (entry_price - df["Low"][i])
        elif df["High"][i] >= (entry_price * (1 + sl_pct)):
            df.loc[df.index[i], 'Trades'] = 'exit_short_sl'
            position = 'flat'
            exit_points.append((df.index[i], df["High"][i]))
            num_losing_trades += 1
            total_loss += (df["High"][i] - entry_price)
        elif df['Low'][i] > df['EMA21'][i-1]:
            df.loc[df.index[i], 'Trades'] = 'exit_short'
            position = 'flat'
            exit_points.append((df.index[i], df['EMA21'][i-1]))

# Drop unnecessary columns
df.drop(["Open","Adj Close", "Volume"], axis=1, inplace=True)

# Display trading statistics
print("Number of trades:", num_trades)
print("Number of profitable trades:", num_profitable_trades)
print("Number of losing trades:", num_losing_trades)
print("Total profit:", total_profit)
print("Total loss:", total_loss)
df.head(60)
