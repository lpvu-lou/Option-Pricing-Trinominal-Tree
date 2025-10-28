import math
import numpy as np
from models.node import Node
from models.option_trade import Option
from models.probabilities import local_probabilities
from models.pruning import compute_reach_probabilities, prune_tree
from models.backward_pricing import price_backward
from models.recursive_pricing import price_recursive
from utils.utils_constants import MIN_PRICE

class TrinomialTree:
    def __init__(self, market, option: Option, N: int, exercise="european"):
        self.market = market
        self.option = option
        self.N = N
        self.dt = market.T / N
        self.r = market.r
        self.sigma = market.sigma
        self.df = math.exp(-self.r * self.dt)
        self.exercise = exercise.lower()
        self.alpha = math.exp(self.sigma * math.sqrt(3 * self.dt))
        self.exp_sig2_dt = math.exp(self.sigma ** 2 * self.dt)
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)
        self.Node = Node

    def build_tree(self):
        S0 = self.market.S0
        self.tree.append([Node(0, S0)])
        self.trunk[0] = S0

        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i, t_ip1 = (i - 1) * self.dt, i * self.dt
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)
            mid_i = max(prev_mid * math.exp(self.r * self.dt) - div, MIN_PRICE)
            self.trunk[i] = mid_i
            prices = mid_i * (self.alpha ** np.arange(-i, i + 1))
            self.tree.append([Node(i, float(S)) for S in prices])
        
        for i, level in enumerate(self.tree[:-1]): 
            for k, node in enumerate(level):
                pD, pM, pU, kprime = local_probabilities(self, i, k, node.stock_price)
                node.p_down = pD
                node.p_mid = pM
                node.p_up = pU
                node.kprime = kprime

    def compute_reach_probabilities(self):
        compute_reach_probabilities(self)

    def prune_tree(self, threshold=1e-7):
        prune_tree(self, threshold)

    def price_backward(self):
        return price_backward(self)

    def price_recursive(self):
        return price_recursive(self)
