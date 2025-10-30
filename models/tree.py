import math
from models.node import Node
from models.option_trade import Option
from models.probabilities import local_probabilities
from models.pruning import compute_reach_probabilities, prune_tree
from models.backward_pricing import price_backward
from models.recursive_pricing import price_recursive
from utils.utils_dividends import get_dividend_on_step
from utils.utils_constants import MIN_PRICE


class TrinomialTree:
    """
    Classe principale pour la construction et le stockage d’un arbre trinomial.
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
        self.stock_tree = []    # Arbre des prix du sous-jacent
        self.proba_tree = []    # Arbre des prix du sous-jacent
        self.trunk = [0.0] * (self.N + 1)    # # Tronc central : prix médian par niveau
        self.Node = Node

    def build_tree(self):
        """
        Construction de l’arbre des prix du sous-jacent et des probabilités locales
        """
        S0 = self.market.S0
        self.stock_tree = [[S0]]
        self.trunk[0] = S0

        # L'arbre des prix
        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i, t_ip1 = (i - 1) * self.dt, i * self.dt

            div, _ = get_dividend_on_step(self.market, t_i, t_ip1, prev_mid)

            # Nouveau prix central (on soustrait le dividende s’il est versé)       
            mid_i = max(prev_mid * math.exp(self.r * self.dt) - div, MIN_PRICE)
            self.trunk[i] = mid_i 

            # Création des prix de chaque noeud du niveau i
            prices = [float(mid_i * (self.alpha ** k)) for k in range(-i, i + 1)]
            self.stock_tree.append(prices)

        # L'arbre des probabilités
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
