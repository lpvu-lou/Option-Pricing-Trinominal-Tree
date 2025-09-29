class Node:
    def __init__(self, time_index, stock_price):
        self.time_index = time_index
        self.stock_price = stock_price
        self.option_value = None

    def payoff(self, K, option_type="call"):
        if option_type == "call":
            return max(self.stock_price - K, 0)
        else:
            return max(K - self.stock_price, 0)
