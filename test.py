import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import talib

# 连接到MetaTrader 5
if not mt5.initialize():
    print("初始化失败")
    mt5.shutdown()

# 获取历史数据函数
def get_data(symbol, timeframe, bars=1000):
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    data = pd.DataFrame(rates)
    data['time'] = pd.to_datetime(data['time'], unit='s')
    data.set_index('time', inplace=True)
    return data

# 计算EMA和布林带
def add_indicators(data, ema_periods, boll_period=20, boll_dev=2):
    for period in ema_periods:
        data[f'ema_{period}'] = data['close'].ewm(span=period, adjust=False).mean()
    data['upper_band'], data['middle_band'], data['lower_band'] = talib.BBANDS(data['close'], timeperiod=boll_period, nbdevup=boll_dev, nbdevdn=boll_dev, matype=0)
    return data

# 判断趋势
def check_trend(data, ema_periods):
    for i in range(len(ema_periods) - 1):
        if not (data[f'ema_{ema_periods[i]}'] < data[f'ema_{ema_periods[i+1]}']).all():
            return 0
    return 1 if data[f'ema_{ema_periods[-1]}'].iloc[-1] > data[f'ema_{ema_periods[0]}'].iloc[-1] else -1

# 判断布林带位置
def check_bollinger_position(data):
    if data['close'].iloc[-1] <= data['lower_band'].iloc[-1]:
        return 'near_lower_band'
    elif data['close'].iloc[-1] >= data['upper_band'].iloc[-1]:
        return 'near_upper_band'
    else:
        return 'within_bands'

# 生成交易信号
def generate_signals(data, ema_periods, timeframe='H4'):
    signals = []
    for i in range(len(data)):
        trend = check_trend(data.iloc[:i+1], ema_periods)
        bollinger_pos = check_bollinger_position(data.iloc[:i+1])
        signals.append(bollinger_pos)
        signals.append(trend)
        if trend == 1 and bollinger_pos == 'near_lower_band':
            signals.append('buy')
        elif trend == -1 and bollinger_pos == 'near_upper_band':
            signals.append('sell')
        else:
            signals.append('hold')
    data['signal'] = signals
    return data

# 获取数据并添加指标
symbol = "EURUSD"
timeframe_h4 = mt5.TIMEFRAME_H4
timeframe_daily = mt5.TIMEFRAME_D1
ema_periods = [10, 20, 30, 40, 50]

data_h4 = get_data(symbol, timeframe_h4)
data_daily = get_data(symbol, timeframe_daily)

data_h4 = add_indicators(data_h4, ema_periods)
data_daily = add_indicators(data_daily, ema_periods)

# 根据日线判断波段
daily_trend = check_trend(data_daily, ema_periods)

# 生成交易信号
data_h4 = generate_signals(data_h4, ema_periods)

data_h4.to_csv('trading_signals.csv')

# 打印交易信号
print(data_h4[['close', 'signal']].tail(500))

# 断开连接
mt5.shutdown()
