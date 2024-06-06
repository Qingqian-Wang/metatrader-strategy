import time
import MetaTrader5 as mt5
import pandas as pd
from take_order import *
from datetime import datetime

# 定义账号、服务器和密码
account = 82680726
password = "Wu@vWgF5"
server = "MetaQuotes-Demo"


# 初始化MetaTrader 5
if not mt5.initialize():
    print("初始化失败")
    mt5.shutdown()

# 登录到交易账户
if not mt5.login(account, password, server):
    print("登录失败")
    mt5.shutdown()

# 定义获取市场数据的函数
def get_market_data(symbol, timeframe, num_bars):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, num_bars)
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    return df

# 计算EMA
def calculate_ema(data, periods):
    return data['close'].ewm(span=periods, adjust=False).mean()

# 计算布林带
def calculate_bollinger_bands(data, period=20, deviation=2):
    data['MA'] = data['close'].rolling(window=period).mean()
    data['BB_up'] = data['MA'] + (data['close'].rolling(window=period).std() * deviation)
    data['BB_down'] = data['MA'] - (data['close'].rolling(window=period).std() * deviation)
    return data



# 定义检查并执行交易的函数
def check_and_trade(symbol, lot):
    data = get_market_data(symbol, mt5.TIMEFRAME_H4, 100)
    
    # 计算EMA和布林带
    data['EMA10'] = calculate_ema(data, 10)
    data['EMA20'] = calculate_ema(data, 20)
    data['EMA30'] = calculate_ema(data, 30)
    data['EMA40'] = calculate_ema(data, 40)
    data['EMA50'] = calculate_ema(data, 50)
    data = calculate_bollinger_bands(data)
    
    last_row = data.iloc[-1]
    
    positions = mt5.positions_get(symbol=symbol)
    if len(positions) > 0:
        current_position = positions[0]
    else:
        current_position = None

    action_taken = "No action"
    
    if last_row['EMA10'] > last_row['EMA20'] > last_row['EMA30'] > last_row['EMA40'] > last_row['EMA50']:
        if last_row['close'] <= last_row['BB_down']:
            if current_position and current_position.type == mt5.ORDER_TYPE_SELL:
                # 平仓并买入
                close_position(current_position)
                place_trade(mt5.ORDER_TYPE_BUY, symbol, lot, last_row['close'], last_row['BB_down'], last_row['BB_up'])
                action_taken = "Buy"
            elif not current_position:
                # 买入
                place_trade(mt5.ORDER_TYPE_BUY, symbol, lot, last_row['close'], last_row['BB_down'], last_row['BB_up'])
                action_taken = "Buy"
    
    elif last_row['EMA10'] < last_row['EMA20'] < last_row['EMA30'] < last_row['EMA40'] < last_row['EMA50']:
        if last_row['close'] >= last_row['BB_up']:
            if current_position and current_position.type == mt5.ORDER_TYPE_BUY:
                # 平仓并卖出
                close_position(current_position)
                place_trade(mt5.ORDER_TYPE_SELL, symbol, lot, last_row['close'], last_row['BB_up'], last_row['BB_down'])
                action_taken = "Sell"
            elif not current_position:
                # 卖出
                place_trade(mt5.ORDER_TYPE_SELL, symbol, lot, last_row['close'], last_row['BB_up'], last_row['BB_down'])
                action_taken = "Sell"
    
    # 检查止损
    if current_position:
        if current_position.type == mt5.ORDER_TYPE_BUY and last_row['close'] < current_position.price_open:
            close_position(current_position)
            action_taken = "Close Buy"
        elif current_position.type == mt5.ORDER_TYPE_SELL and last_row['close'] > current_position.price_open:
            close_position(current_position)
            action_taken = "Close Sell"

    print(f"Time: {datetime.now()}, Action: {action_taken}")



# 运行策略
symbol = "EURUSD"
lot = 0.1

try:
    while True:
        check_and_trade(symbol, lot)
        time.sleep(1)
finally:
    mt5.shutdown()
