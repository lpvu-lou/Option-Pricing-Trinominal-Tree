from market import Market
from tree import TrinomialTree

class TrinomialTreeModel:
    def __init__(self, trade):
        self.trade = trade
        self.market = Market(trade.S0, trade.r, trade.sigma, trade.T, trade.dividend)
        self.tree = TrinomialTree(
            self.market,
            trade.K,
            trade.N,
            option_type=trade.option_type,
            exercise=trade.exercise
        )

    def price(self):
        self.tree.build_tree()
        return self.tree.price()
