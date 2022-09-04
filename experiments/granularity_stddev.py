import pandas
import matplotlib.pyplot as plt
import statistics

DATASET_PATH = '../datasets/crypto_dataset-365days-5m.csv'

counter = 0
change_map = {}

def fillmap(row):
    global counter
    global day_counter
    global change_map

    if counter == (24 * 60)/5:
        counter = 0

    direction = row['open'] - row['close']
    change_map[counter] = change_map.get(counter, []) + [direction]
    counter += 1

def process_slots(change_map):
    results = {}
    for slot, directions in change_map.items():
        mean = statistics.mean(directions)
        stddev = statistics.pstdev(directions)
        results[slot] = ((mean, stddev))
    
    return results

def main():
    df = pandas.read_csv(DATASET_PATH)
    df.apply(fillmap, axis=1)
  
    print('len of change_map: ' + str(len(change_map)))

    results = process_slots(change_map)
    stddev_sorted = sorted(results.items(), key=lambda item: item[1][1], reverse=True)
    mean_sorted = sorted(results.items(), key=lambda item: item[1][0], reverse=True)
    print("top/bottom 5 stddev:")
    stddev_top = stddev_sorted[:5]
    stddev_bot = stddev_sorted[-5:]
    print(stddev_top)
    print("...")
    print(stddev_bot)
    print()
    print("top/bottom 5 mean:")
    mean_top = mean_sorted[:5]
    mean_bot = mean_sorted[-5:]
    print(mean_top)
    print("...")
    print(mean_bot)

    # plot mean and stddev of price deltas of each 5m slot in a day, over a year 
    xvals = [i for i in range(0,288)]
    fig, axs = plt.subplots(2)
    # mean
    axs[0].plot(xvals, [result[0] for result in results.values()])
    axs[0].grid()
    axs[0].set_ylabel = 'mean ($)'
    axs[0].set_xlabel = '5m slot #'
    # stddev
    axs[1].plot(xvals, [result[1] for result in results.values()])
    axs[1].grid()
    axs[1].set_ylabel = 'stddev ($)'
    axs[1].set_xlabel = '5m slot #'
    plt.show()

if __name__ == "__main__":
    main()
