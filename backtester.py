import pandas
import sys

# Import models to test
import models

DATASET_PATH = 'datasets/crypto_dataset-1m.csv'
INITIAL_FUNDS = 100000
MODEL = models.BuyOnceModel(funds=INITIAL_FUNDS)

def format_float(num, dp):
    format_str = "{:." + str(dp) + "f}"
    return format_str.format(num)

class Backtester:
    def __init__(self, dataset, model):
        self.dataset = dataset
        self.model = model
        # Uninvested cash (in $)
        self.funds = INITIAL_FUNDS
        # Invested equity (in asset units)
        self.equity = 0

    def evaluate(self, row):
        decision = self.model.evaluate_update(row)
        if decision[0] == "BUY":
            # Check amount makes sense
            amount = decision[1]
            if amount <= 0:
                sys.exit('ERROR: Model tried to BUY <= $0 worth of equity')
            elif amount > self.funds:
                sys.exit(f'ERROR: Model tried to BUY ${amount} with insufficient funds (${self.funds})')

            self.funds -= amount
            self.equity += amount/row['open']
        elif decision[0] == 'SELL':
            # Check amount makes sense
            amount = decision[1]
            if amount <= 0:
                sys.exit('ERROR: Model tried to SELL <= $0 worth of equity')
            elif amount > self.funds:
                sys.exit(f'ERROR: Model tried to SELL ${amount} with insufficient equity (${self.equity})')

            self.funds += amount
            self.equity -= amount/row['open']
        elif decision[0] == 'HOLD':
            pass
        else:
            sys.exit(f'ERROR: Unrecognized model action {decision[0]} ... Aborting')

    def run(self):
        print(f'Starting backtest using model {self.model} in dataset "{DATASET_PATH}" with ${self.funds} initial funds')
        # Run model over dataset
        self.dataset.apply(self.evaluate, axis=1)
        
        # Calculate statistics
        latest_close_price = self.dataset.iloc[-1]['close']
        equity_dollars = latest_close_price * self.equity
        net_worth = equity_dollars + self.funds
        gain = (net_worth/INITIAL_FUNDS) - 1
        if gain < 0:
            gain_string = "-" + format_float(gain * -1, 4) + "%"
        else:
            gain_string = "+" + format_float(gain, 4) + "%"

        # Print results
        print('\n=== Results ===')
        print(f'Uninvested: ${format_float(self.funds, 4)}')
        print(f'Equity:     {format_float(self.equity, 4)} units (${format_float(equity_dollars, 4)} on latest date)')
        print(f'Net:        ${format_float(net_worth, 4)}')
        print(f'% Gain:     {gain_string}')

def main():
    df = pandas.read_csv(DATASET_PATH)
    bt = Backtester(dataset=df, model=MODEL)
    bt.run()

if __name__ == "__main__":
    main()
