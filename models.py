import sys

class Model:
    def __init__(self, funds):
        self.funds = funds

    def evaluate_update(self, metrics):
        """Evaluate an asset's metrics and return (signal, amount)
           where signal is one of 'BUY', 'SELL', 'HOLD' and amount
           is a float representing how much to buy/sell in $. Must
           be overriden by subclass model."""
        sys.exit('ERROR: Tried calling evaluate_update on Model base class')

# Invests all funds in the first data point and holds
class BuyOnceModel(Model):
    hasBought = False
    def evaluate_update(self, metrics):
        if not self.hasBought:
            self.hasBought = True
            return ('BUY', self.funds)
        else:
            return ('HOLD', 0)
       
