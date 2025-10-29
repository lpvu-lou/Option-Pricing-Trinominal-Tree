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
    """
    Builds and stores:
      - stock_tree:  nested list of stock prices per node
      - proba_tree:  nested list of (p_down, p_mid, p_up, kprime) per node
      - node_tree:   optional nested list of Node objects (if debug_nodes=True)
    """

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

        # Structures
        self.stock_tree = []   # list[list[float]]
        self.proba_tree = []   # list[list[(pD, pM, pU, kprime)]]
        self.trunk = [0.0] * (self.N + 1)
        from models.node import Node
        self.Node = Node

    # ----------------------------------------------------------
    # Build stock and probability trees (+ optional Node objects)
    # ----------------------------------------------------------
    def build_tree(self, debug_nodes: bool = False):
        """
        Builds both stock and probability trees.
        If debug_nodes=True, also builds a Node-based tree
        where each Node detects whether a dividend occurs in [t_i, t_{i+1}].
        """
        S0 = self.market.S0
        self.stock_tree = [[S0]]
        self.trunk[0] = S0

        # --- Stock prices per level ---
        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i, t_ip1 = (i - 1) * self.dt, i * self.dt
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)
            mid_i = max(prev_mid * math.exp(self.r * self.dt) - div, MIN_PRICE)
            self.trunk[i] = mid_i

            prices = [float(mid_i * (self.alpha ** k)) for k in range(-i, i + 1)]
            self.stock_tree.append(prices)

        # --- Probabilities per level ---
        self.proba_tree = []
        for i, level in enumerate(self.stock_tree[:-1]):
            level_proba = []
            for k, S in enumerate(level):
                pD, pM, pU, kprime = local_probabilities(self, i, k, S)
                level_proba.append((pD, pM, pU, kprime))
            self.proba_tree.append(level_proba)

    def compute_reach_probabilities(self):
        compute_reach_probabilities(self)

    def prune_tree(self, threshold=1e-7):
        prune_tree(self, threshold)

    def price_backward(self):
        return price_backward(self)

    def price_recursive(self):
        return price_recursive(self)
