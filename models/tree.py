import math
import numpy as np
import datetime as dt

from models.node import Node
from models.trunc_node import TruncNode
from models.probabilities import local_probabilities
from utils.utils_date import datetime_to_years, years_to_datetime  

EPS = 1e-14
MIN_PRICE = 1e-12

class TrinomialTree:
    """
    Arbre trinomial pour le pricing d’options européennes et américaines.
    Gère les dividendes discrets, dates ex-div et structure recombinante.
    """

    def __init__(self, market, option, N: int, exercise="european"):
        self.market = market
        self.option = option
        self.N = N
        self.exercise = exercise.lower()

        # Paramètres du marché
        self.dt = market.T / N
        self.r = market.r
        self.sigma = market.sigma
        self.df = math.exp(-self.r * self.dt)

        # Paramètres du modèle trinomial
        self.alpha = math.exp(self.sigma * math.sqrt(3 * self.dt))
        self.exp_sig2_dt = math.exp(self.sigma**2 * self.dt)

        # Structure du tree
        self.levels = []
        self.trunk = [0.0] * (self.N + 1)
        self.trunk[0] = self.market.S0

        # Date de départ du pricing
        self.start_date = (
            self.market.pricing_date if self.market.pricing_date is not None else dt.datetime.today()
        )

        # Conversion cohérente des dates de dividende en temps (float)
        if hasattr(self.market, "dividends") and self.market.dividends:
            for i, (t_div, policy) in enumerate(self.market.dividends):
                if isinstance(t_div, dt.datetime):
                    t_div = datetime_to_years(t_div, self.start_date)
                    self.market.dividends[i] = (t_div, policy)

    # ============== CONSTRUCTION DE L’ARBRE ==============
    def build_tree(self):
        """
        Construit l’arbre trinomial (recombining) avec gestion des dividendes.
        Chaque niveau contient des TruncNodes permettant de détecter un ex-dividend date.
        """
        S0 = self.market.S0
        self.levels.append([TruncNode(None, self.start_date, S0, self)])
        self.trunk[0] = S0

        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i, t_ip1 = (i - 1) * self.dt, i * self.dt
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)

            # Prix médian suivant (forward ajusté dividende)
            mid_i = prev_mid * math.exp(self.r * self.dt) - div
            mid_i = max(mid_i, MIN_PRICE)
            self.trunk[i] = mid_i

            # Conversion de t_ip1 (float) en datetime
            curr_date = years_to_datetime(t_ip1, self.start_date)

            # Calcul des prix possibles à ce niveau
            powers = np.arange(-i, i + 1)
            prices = mid_i * (self.alpha ** powers)

            # Création des nœuds du niveau i
            level = [
                TruncNode(self.levels[i - 1][len(self.levels[i - 1]) // 2], curr_date, float(S), self)
                for S in prices
            ]
            self.levels.append(level)

        # Liaison des nœuds avec les probabilités 
        for i in range(self.N):
            current = self.levels[i]
            next_level = self.levels[i + 1]

            for j, node in enumerate(current):
                if node is None:
                    continue

                k = j - i
                pD, pM, pU, kprime = local_probabilities(
                    self.market, self.dt, self.alpha, self.exp_sig2_dt,
                    node.spot, self.trunk[i + 1], i, k
                )
                node.p_down, node.p_mid, node.p_up = pD, pM, pU

                base = kprime + (i + 1)
                if 0 <= base - 1 < len(next_level):
                    node.next_down = next_level[base - 1]
                if 0 <= base < len(next_level):
                    node.next_mid = next_level[base]
                if 0 <= base + 1 < len(next_level):
                    node.next_up = next_level[base + 1]

     # ============== PROBABILITÉS D'ATTEINTE ==============
    def compute_reach_probabilities(self):
        """
        Calcule la probabilité d’atteinte (p_reach) de chaque nœud
        """
        self.levels[0][0].p_reach = 1.0

        for i in range(self.N):
            for node in self.levels[i]:
                if node is None or node.p_reach <= 0:
                    continue
                for child, p in (
                    (node.next_down, node.p_down),
                    (node.next_mid, node.p_mid),
                    (node.next_up, node.p_up),
                ):
                    if child:
                        child.p_reach += node.p_reach * p
    
    # ============== PRUNING ==============
    def pruned_tree(self, threshold=1e-7):
        """Supprime les nœuds ayant une probabilité d’atteinte trop faible (< threshold)"""
        for level in self.levels:
            for j, node in enumerate(level):
                if node is not None:
                    if node.p_reach < threshold:
                        level[j] = None



    
