import sys
import pandas
import matplotlib.pyplot as plt

DATASET_PATH = '../datasets/crypto_dataset-365days-5m.csv'

SLOT_NUM = 175

day_counter = 0
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

def main():
    if len(sys.argv) >= 2:
        print("using arg as slot #")
        slot = int(sys.argv[1])
    else:
        slot = SLOT_NUM

    df = pandas.read_csv(DATASET_PATH)
    df.apply(fillmap, axis=1)
   
    slot_trend = change_map[slot]
    try:
        xvals = [i for i in range(0,365)]
        plt.bar(xvals, slot_trend)
    except (ValueError):
        print("slot_trend length mismatch, trying 364 days")
        xvals = [i for i in range(0,364)]
        print("xvals len: " + str(len(xvals)))
        plt.bar(xvals, slot_trend)

    plt.show()

if __name__ == "__main__":
    main()
