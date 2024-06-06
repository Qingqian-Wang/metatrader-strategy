import MetaTrader5 as mt5
import pandas as pd
import numpy as np
import talib
from scipy.stats import linregress


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
    slopes = []
    for period in ema_periods:
        ema = data[f'ema_{period}'].dropna()  # 移除NaN值
        if len(ema) > 1:  # 确保有足够的数据点计算斜率
            slope, intercept, r_value, p_value, std_err = linregress(range(len(ema)), ema)
            slopes.append(slope)
        else:
            slopes.append(0)  # 数据点不足时设为0
    if all(slope > 0 for slope in slopes):
        return 1  # 上升趋势
    elif all(slope < 0 for slope in slopes):
        return -1  # 下降趋势
    else:
        return 0  # 无明显趋势

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
    bolling_poses = []
    trends = []
    for i in range(len(data)):
        trend = check_trend(data.iloc[:i+1], ema_periods)
        bollinger_pos = check_bollinger_position(data.iloc[:i+1])
        bolling_poses.append(bollinger_pos)
        trends.append(trend)
        if trend == 1 and bollinger_pos == 'near_lower_band':
            signals.append('buy')
        elif trend == -1 and bollinger_pos == 'near_upper_band':
            signals.append('sell')
        else:
            signals.append('hold')
    data['signal'] = signals
    data['bolling_pos'] = bolling_poses
    data['trend'] = trends
    return data



def signal_gen():
    # 连接到MetaTrader 5
    if not mt5.initialize():
        print("初始化失败")
        mt5.shutdown()

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
