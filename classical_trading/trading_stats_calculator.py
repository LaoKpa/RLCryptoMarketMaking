
from time import *
import bitfinex_trade_wrapper as btw

SYMBOLS = ['ETPUSD', 'BTCUSD']

def profit_from_past_trades(past_trades):
    buy_amount = sell_amount = fee_amount = 0
    for trade in past_trades:
        if trade['type'] == 'Buy':
            buy_amount += float(trade['price']) * float(trade['amount'])
        if trade['type'] == 'Sell':
            sell_amount += float(trade['price']) * float(trade['amount'])
        fee_amount += float(trade['fee_amount'])
    profit = sell_amount - buy_amount + fee_amount
    return {'profit':profit, 'buy_volume':buy_amount, 'sell_volume':sell_amount, 'fee':fee_amount}

def generate_timestamps():
    current_local_time = localtime()
    day_start_time = struct_time([current_local_time.tm_year, current_local_time.tm_mon,\
        current_local_time.tm_mday,0,0,0,0,0,current_local_time.tm_isdst])
    day_ago_time = struct_time([current_local_time.tm_year, current_local_time.tm_mon,current_local_time.tm_mday - 1,\
        current_local_time.tm_hour,current_local_time.tm_min,current_local_time.tm_sec,0,0,current_local_time.tm_isdst])
    week_ago_time = struct_time([current_local_time.tm_year, current_local_time.tm_mon,current_local_time.tm_mday - 7,\
        current_local_time.tm_hour,current_local_time.tm_min,current_local_time.tm_sec,0,0,current_local_time.tm_isdst])
    month_ago_time = struct_time([current_local_time.tm_year, current_local_time.tm_mon - 1,current_local_time.tm_mday,\
        current_local_time.tm_hour,current_local_time.tm_min,current_local_time.tm_sec,0,0,current_local_time.tm_isdst])
    timestamp_dictionary = {'day_start_time':mktime(day_start_time), 'day_ago_time':mktime(day_ago_time),\
        'week_ago_time':mktime(week_ago_time), 'month_ago_time':mktime(month_ago_time)}
    return timestamp_dictionary

def get_trades_from_timestamp(past_trades, timestamp):
    reduced_past_trades = []
    for trade in past_trades:
        if float(trade['timestamp']) > timestamp:
            reduced_past_trades.append(trade)
    return reduced_past_trades

def generate_all_stats():
    profit_dictionary = {}
    past_trades_dict = {}
    b = btw.BitfinexTradeWrapper(btw.BITFINEX_KEY, btw.BITFINEX_SECRET)
    timestamp_dictionary = generate_timestamps()
    for symbol in SYMBOLS:
        timestamp_profit_dictionary = {}
        past_trades_dict[symbol] = b.bitfinex_object.past_trades(symbol)
        for k,v in list(timestamp_dictionary.items()):
            timestamp_profit_dictionary[k] = profit_from_past_trades(get_trades_from_timestamp(past_trades_dict[symbol], v))
        profit_dictionary[symbol] = timestamp_profit_dictionary
    return profit_dictionary

def main():
    b = btw.BitfinexTradeWrapper(btw.BITFINEX_KEY, btw.BITFINEX_SECRET)
    print(profit_from_past_trades(b.bitfinex_object.past_trades('ETPUSD')))

if __name__ == "__main__":
    main()
