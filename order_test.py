import MetaTrader5 as mt5
import time

def close_position(position):
    # 获取最新的价格信息
    tick_info = mt5.symbol_info_tick(position.symbol)
    if tick_info is None:
        print(f"无法获取 {position.symbol} 的价格信息")
        return None

    # 检查是否有有效的报价
    if tick_info.bid == 0 or tick_info.ask == 0:
        print(f"{position.symbol} 没有有效的报价")
        return None

    price = tick_info.bid if position.type == mt5.ORDER_TYPE_SELL else tick_info.ask
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": position.symbol,
        "volume": position.volume,
        "type": mt5.ORDER_TYPE_BUY if position.type == mt5.ORDER_TYPE_SELL else mt5.ORDER_TYPE_SELL,
        "position": position.ticket,
        "price": price,
        "deviation": 10,
        "magic": 234000,
        "comment": "Close position",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_RETURN,
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Order close failed, retcode={result.retcode}")
        # 检查失败的原因
        result_dict = result._asdict()
        for field in result_dict.keys():
            print(f"  {field}={result_dict[field]}")
        return None
    print(f"Order close success, ticket={result.order}")
    return result

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

symbol = "EURUSD"

# 检查市场是否开放
symbol_info = mt5.symbol_info(symbol)
if symbol_info is None or not symbol_info.visible:
    print(f"{symbol} 不可交易")
    mt5.shutdown()

# 确保交易品种在市场报价中可见
if not mt5.symbol_select(symbol, True):
    print(f"选择交易品种失败: {symbol}")
    mt5.shutdown()

# 获取所有该符号下的头寸
positions = mt5.positions_get(symbol=symbol)

if positions:
    for position in positions:
        result = close_position(position)
        if result is not None:
            print(f"头寸 {position.ticket} 关闭成功")
        else:
            print(f"头寸 {position.ticket} 关闭失败")
else:
    print(f"没有找到符号 {symbol} 的头寸")

# 关闭MetaTrader 5连接
mt5.shutdown()
