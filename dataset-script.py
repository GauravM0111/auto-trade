from math import ceil
from eta import ETA
import bitfinex
import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
import statistics

# Query parameters
PAIR = 'btcusd'     # Currency pair of interest
BIN_SIZE = '5m'     # This will return minute data
GRANULARITY = 5     # BIN_SIZE in integer form
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
    data_cache = data_point_list[:]
    price_list = price_list[num_data_points:]

    df = df.iloc[num_data_points:]
    
    def calc_sma(price):
        data_cache.pop(0)
        data_cache.append(price)
        return float(sum(data_cache)/len(data_cache))


    df['sma'] = list(map(calc_sma, price_list))
    
    data_cache = data_point_list[:]
    prev_ema = float(sum(data_cache)/num_data_points)

    def calc_ema(price):
        nonlocal prev_ema
        ema = float((price * (ema_smoothing/(1 + num_data_points))) + (prev_ema * (1 - (ema_smoothing/(1 + num_data_points)))))
        prev_ema = ema
        return ema
    
    df['ema'] = list(map(calc_ema, price_list))


    temp_data_point_list = data_point_list[:]
    change_perc_list = []
    annual_periods_sqrt = 252 ** 0.5
    for i in range(1, len(temp_data_point_list), ceil(1440 / granularity)):
        change_perc_list.append((temp_data_point_list[i]/temp_data_point_list[i-1]) - 1)

    def calc_volatility(price):
        nonlocal change_perc_list
        vol = statistics.stdev(change_perc_list) * annual_periods_sqrt

        temp_data_point_list.pop(0)
        temp_data_point_list.append(price)

        change_perc_list = []
        for i in range(1, len(temp_data_point_list), ceil(1440 / granularity)):
            change_perc_list.append((temp_data_point_list[i]/temp_data_point_list[i-1]) - 1)
        # change_perc_list.pop(0)
        # change_perc_list.append((price/change_perc_list[-1]) - 1)
        return vol

    df['volatility'] = list(map(calc_volatility, price_list))

    return df


def plot_data(df, granularity, fields, write_path):
    fig, (ax1, ax2) = plt.subplots(2)

    x = [x * granularity for x in range(df.shape[0])]

    for field in fields:
        if not field in df.columns or field=='volatility':
            continue
        ax1.plot(x, df[field].tolist(), label=field)
    ax1.set(xlabel='time', ylabel='price')
    ax1.set_title('Price Chart')
    ax1.legend()

    if 'volatility' in fields:
        ax2.plot(x, df['volatility'].tolist(), label='volatility')
    ax2.set(xlabel='time')
    ax2.set_title('Volatility Chart')

    plt.savefig(write_path)
    plt.show()


def main():
    df = get_data_df(num_days=NUM_DAYS+OFFSET, pair=PAIR, bin_size=BIN_SIZE, limit=LIMIT, time_step=TIME_STEP)
    
    print('Calculating values...')
    df = calculate_moving_average(df, df['close'].tolist(), OFFSET, GRANULARITY, EMA_SMOOTHING)
    df = calculate_change(df)
    print('Done!')

    file_extension = str(NUM_DAYS) + 'days-' + BIN_SIZE

    print('Writing to file...')
    df.to_csv('datasets/crypto_dataset-' + file_extension + '.csv')
    print('Done!')

    print('Plotting to graph...')
    plot_data(df, GRANULARITY, ['close', 'sma', 'ema', 'volatility'], 'plots/plot-' + file_extension + '.png')
    print('Done!')
    


if __name__ == "__main__":
    main()