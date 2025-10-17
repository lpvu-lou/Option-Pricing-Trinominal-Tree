import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import math
import pytest
import numpy as np
from models.node import Node
from models.option_trade import Option
from models.tree import TrinomialTree

class DummyMarket:
    def __init__(self, S0=100, r=0.02, sigma=0.2, T=1.0):
        self.S0 = S0
        self.r = r
        self.sigma = sigma
        self.T = T

        self.rho = 0.02
        self.lam = 0.5
        self.t0 = 0.0

    def dividend_on_step(self, t_i, t_ip1, S):
        return 0.0

class DummyOption(Option):
    def __init__(self, K=100, type="call"):
        self.K = K
        self.type = type

    def payoff(self, S):
        if self.type == "call":
            return max(S - self.K, 0.0)
        else:
            return max(self.K - S, 0.0)

def test_probabilities_sum_to_one():
    market = DummyMarket()
    option = DummyOption()
    tree = TrinomialTree(market, option, N=10)
    tree.build_tree()

    for i in range(0, 5):
        level = tree.tree[i]
        for k, node in enumerate(level):
            if node is None:
                continue
            S_i_k = node.stock_price
            pD, pM, pU, _ = tree._probabilities(i, k - i, S_i_k)
            s = pD + pM + pU
            assert abs(s - 1) < 1e-10, f"Somme != 1 à l’étape {i}, k={k}"
            assert 0 <= pD <= 1 and 0 <= pM <= 1 and 0 <= pU <= 1, \
                f"Proba négative ou >1 à l’étape {i}, k={k}"

def test_backward_pricing_does_not_crash():
    market = DummyMarket()
    option = DummyOption()
    tree = TrinomialTree(market, option, N=100)
    tree.build_tree()
    tree.compute_reach_probabilities()

    try:
        price = tree.price_backward()
        assert math.isfinite(price), "Prix non fini"
        assert price >= 0.0, "Prix négatif"
    except IndexError as e:
        pytest.fail(f"Erreur d’index détectée pendant le pricing : {e}")
    except Exception as e:
        pytest.fail(f"Erreur inattendue pendant le pricing : {e}")

def test_recursive_pricing_matches_backward():
    market = DummyMarket()
    option = DummyOption()
    tree = TrinomialTree(market, option, N=50)
    tree.build_tree()
    tree.compute_reach_probabilities()

    price_bwd = tree.price_backward()
    price_rec = tree.price_recursive(0, 0)

    assert abs(price_bwd - price_rec) < 1e-8, \
        f"Incohérence entre backward ({price_bwd}) et récursif ({price_rec})"
