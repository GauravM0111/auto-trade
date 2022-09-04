import pandas
import matplotlib.pyplot as plt

DATASET_PATH = '../datasets/crypto_dataset-365days-5m.csv'

day_counter = 0
counter = 0
change_map = {}

def process_binary_change(row):
    global counter
    global day_counter
    global change_map

    if counter == (24 * 60)/5:
        counter = 0

    if counter == 0:
        day_counter += 1
        #print('Day ' + str(day_counter) + ': ')

    direction = row['open'] - row['close']
    if direction < 0:
        #print(' [-]', end='')
        change_map[counter] = change_map.get(counter, 0) - 1
    elif direction > 0:
        #print(' [+]', end='')
        change_map[counter] = change_map.get(counter, 0) + 1
    else:
        #print(' [0]', end='')
        pass

    counter += 1

def main():
    df = pandas.read_csv(DATASET_PATH)
    df.apply(process_binary_change, axis=1)
    print(dict(sorted(change_map.items(), key=lambda item: item[1], reverse=True)))
    plt.bar(*zip(*change_map.items()))
    plt.show()
    print("hello")

if __name__ == "__main__":
    main()
