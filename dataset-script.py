from math import ceil
from eta import ETA
import bitfinex
import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt

# Query parameters
PAIR = 'btcusd'     # Currency pair of interest
BIN_SIZE = '1m'     # This will return minute data
GRANULARITY = 1     # BIN_SIZE in integer form
NUM_DAYS = 365    # number of days to query

LIMIT = 10000                   # We want the maximum of 10000 data points
TIME_STEP = GRANULARITY * 60000 * LIMIT   # Set step size
OFFSET = 20                      # number of days that are deleted before the start date during calculations
EMA_SMOOTHING = 2

 
def fetch_data(start, stop, symbol, interval, tick_limit, step):
    # Create api instance
    api_v2 = bitfinex.bitfinex_v2.api_v2()
    print('Downloading data...')
    data = []
    eta = ETA(ceil((stop - start)/step) + 1)

    while start < stop:
        end = min(start + step, stop)

        res = api_v2.candles(symbol=symbol, interval=interval,
                             limit=tick_limit, start=start,
                             end=end)
        
        for entry in res:
            struct_time = datetime.datetime.fromtimestamp(entry[0]/1000.0).timetuple()  # entry[0] = time

            entry.append(struct_time.tm_year)                                           # year
            entry.append(struct_time.tm_mon)                                            # month of year
            entry.append(struct_time.tm_mday)                                           # day of month
            entry.append(struct_time.tm_wday)                                           # day of week
            entry.append(int(struct_time.tm_wday >= 5))                                      # weekend or not
            entry.append(struct_time.tm_hour)                                           # hour of day
            entry.append(struct_time.tm_min)                                            # minute of hour
            entry.append(struct_time.tm_sec)                                            # second of minute

        data.extend(res)
        start = start + step

        eta.print_status()
        time.sleep(0.7)

    eta.done()
    return data


def get_data_df(num_days, pair, bin_size, limit, time_step):
    # Convert start and end dates to milliseconds
    time_stop = datetime.datetime.now()
    time_start = time_stop - datetime.timedelta(days=num_days)

    t_stop = time.mktime(time_stop.timetuple()) * 1000
    t_start = time.mktime(time_start.timetuple()) * 1000

    pair_data = fetch_data(start=t_start, stop=t_stop, symbol=pair, interval=bin_size, tick_limit=limit, step=time_step)

    # Create pandas data frame and clean/format data
    print('Compiling data...')
    names = ['time', 'open', 'close', 'high', 'low', 'volume', 'year', 'month', 'day', 'day_of_week', 'weekend', 'hour', 'minute', 'second']
    df = pd.DataFrame(pair_data, columns=names)
    df.drop_duplicates(inplace=True)
    df['time'] = pd.to_datetime(df['time'], unit='ms')
    df.set_index('time', inplace=True)
    df.sort_index(inplace=True)
    print('Done!')

    return df


def calculate_change(df):
    df = df.assign(change=lambda x: round(((x.close-x.open)/x.open)*100.0, 2))
    change_list = df['change'].tolist()

    next_change_list = change_list[1:]
    next_change_list.append(0.0)
    df['next_change'] = next_change_list

    return df.iloc[:-1, :]


def calculate_moving_average(df, price_list, days, granularity, ema_smoothing):
    num_data_points = ceil(1440 * days / granularity)

    data_point_list = price_list[:num_data_points]
    price_list = price_list[num_data_points:]

    first_sma = float(sum(data_point_list)/num_data_points)
    sma_list = []
    ema_list = [first_sma]

    for price in price_list:
        data_point_list.pop(0)
        data_point_list.append(price)
        sma = float(sum(data_point_list)/num_data_points)
        sma_list.append(sma)

        ema = (price * (ema_smoothing/(1 + num_data_points))) + (ema_list[-1] * (1 - (ema_smoothing/(1 + num_data_points))))
        ema_list.append(ema)

    ema_list.pop(0)
    df = df.iloc[num_data_points:]
    df['sma'] = sma_list
    df['ema'] = ema_list

    return df

def plot_data(df, granularity, fields):
    x = [x * granularity for x in range(df.shape[0])]

    for field in fields:
        if not field in df.columns:
            continue
        plt.plot(x, df[field].tolist(), label=field)
    
    plt.xlabel('time')
    plt.ylabel('price')
    plt.title('Price Chart')
    plt.legend()
    plt.show()


def main():
    df = get_data_df(num_days=NUM_DAYS+OFFSET, pair=PAIR, bin_size=BIN_SIZE, limit=LIMIT, time_step=TIME_STEP)
    
    print('Calculating values...')
    df = calculate_moving_average(df, df['close'].tolist(), OFFSET, GRANULARITY, EMA_SMOOTHING)
    df = calculate_change(df)
    print('Done!')

    print('Writing to file...')
    df.to_csv('datasets/crypto_dataset-1m.csv')
    print('Done!')

    print('Plotting to graph...')
    plot_data(df, GRANULARITY, ['close', 'sma', 'ema'])
    print('Done!')
    


if __name__ == "__main__":
    main()