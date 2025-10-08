import math


class Node:
    def __init__(self, time_step, stock_price):
        self.time_index = time_step
        self.stock_price = stock_price
        self.option_value = None
        self.p_reach = 0.0

    def time(self, tree):
        return self.time_index * tree.dt

    def next_time(self, tree):
        return (self.time_index + 1) * tree.dt

    def dividend_next_amount(self, tree):
        mkt = tree.market
        t_i = self.time(tree)
        t_ip1 = self.next_time(tree)
        S = self.stock_price
        return mkt.dividend_on_step(t_i, t_ip1, S)

    def next_mid_price(self, tree):
        fwd = self.stock_price * math.exp(tree.market.r * tree.dt)
        div = self.dividend_next_amount(tree)
        s_mid = fwd - div
        if s_mid <= 0:
            raise ValueError(f"Prix milieu non positif : {s_mid}")
        return s_mid