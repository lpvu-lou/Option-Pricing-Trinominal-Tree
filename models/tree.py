import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import math
import numpy as np
from models.node import Node
from models.option_trade import Option
class TrinomialTree:
    """
    Arbre trinomial pour le pricing d’options européennes et américaines
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

         # Paramètres du modèle
        self.alpha = math.exp(self.sigma * math.sqrt(3 * self.dt))
        self.exp_sig2_dt = math.exp(self.sigma**2 * self.dt)
        self.df = math.exp(-self.r * self.dt)

        # Structure de l’arbre
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

    
    # Arbre Stock Price
    def build_tree(self):
        """
        Construit l’arbre des prix du sous-jacent
        """
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

        # Racine
        S0 = self.market.S0
        self.tree.append([Node(0, S0)])
        self.trunk[0] = S0

        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i, t_ip1 = (i - 1) * self.dt, i * self.dt

            # Dividende éventuel sur ce pas
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)

            # Prix central du niveau suivant
            mid_i = prev_mid * math.exp(self.r * self.dt) - div
            self.trunk[i] = mid_i

            powers = np.arange(-i, i + 1)
            prices = mid_i * (self.alpha ** powers)
            level = [Node(i, float(S)) for S in prices]
            self.tree.append(level)

    # Probabilités de transition
    def _probabilities(self, i, k, S_i_k):
        """
        Calcule les probabilités locales (p_down, p_mid, p_up)
        """
        t_i, t_ip1 = i * self.dt, (i + 1) * self.dt
        div = self.market.dividend_on_step(t_i, t_ip1, S_i_k)

        E = S_i_k * math.exp(self.r * self.dt) - div
        a = self.alpha
        a2 = a * a
        base_next = max(self.trunk[i + 1], 1e-12)

        ratio = max(E / base_next, 1e-12)
        denom = math.log(a)
        kprime = int(round(math.log(ratio) / denom)) if abs(denom) > 1e-16 else 0

        S_mid = base_next * (a ** kprime)
        S_up, S_down = S_mid * a, S_mid / a

        # Cas: sans dividendes
        if not self.market.has_dividend_between(t_i, t_ip1):
            p_down = (self.exp_sig2_dt - 1) / ((1 - a) * ((1 / a2) - 1))
            p_up = p_down / a
            p_mid = 1 - p_up - p_down
        else:
            # Cas général: avec dividendes
            V = (S_i_k**2) * math.exp(2 * self.r * self.dt) * (self.exp_sig2_dt - 1)
            num = (1 / (S_mid**2)) * (V + E**2) - 1 - (a + 1) * ((E / S_mid) - 1)
            den = (1 - a) * ((1 / a2) - 1)
            p_down = num / den
            p_up = ((E / S_mid) - 1 - ((1 / a) - 1) * p_down) / (a - 1)
            p_mid = 1 - p_up - p_down

        lower, upper = 0.5 * (S_mid + S_down), 0.5 * (S_mid + S_up)
        if E > upper:
            kprime += 1
            S_mid *= self.alpha
        elif E < lower:
            kprime -= 1
            S_mid /= self.alpha

        return p_down, p_mid, p_up, kprime

    # Probabilités d'atteint
    def compute_reach_probabilities(self):
        """
        Calcule et stocke la probabilité d’atteinte (p_reach) de chaque nœud dans l’arbre trinomial
        """
        # Réinitialisation de l’arbre
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

        # Racine
        root = Node(0, self.market.S0)
        root.p_reach = 1.0
        self.tree.append([root])
        self.trunk[0] = self.market.S0

        for i in range(self.N):
            prev_level = self.tree[i]
            next_level = [None] * (2 * (i + 1) + 1)

            # Prix médian du prochain niveau
            prev_mid = self.trunk[i]
            t_i, t_ip1 = i * self.dt, (i + 1) * self.dt
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)
            mid_next = prev_mid * math.exp(self.r * self.dt) - div
            self.trunk[i + 1] = mid_next

            # Parcours des nœuds du niveau courant
            for j, node in enumerate(prev_level):
                if node is None or node.p_reach == 0.0:
                    continue

                k = j - i
                pD, pM, pU, kprime = self._probabilities(i, k, node.stock_price)

                # Mise à jour des nœuds du niveau suivant
                for dj, p in ((-1, pD), (0, pM), (+1, pU)):
                    if p <= 0:
                        continue
                    knext = k + dj
                    idx = knext + (i + 1)
                    if 0 <= idx < len(next_level):
                        if next_level[idx] is None:
                            S_next = mid_next * (self.alpha ** knext)
                            next_level[idx] = Node(i + 1, S_next)
                        next_level[idx].p_reach += node.p_reach * p

            # Ajout du niveau à l’arbre
            self.tree.append(next_level)

    # Prunind
    def prune_tree(self, threshold=1e-7):
        """
        Enlever les noeuds avec la probabilité < threshold
        """
        for i, level in enumerate(self.tree):
            for j, node in enumerate(level):
                if node is not None and node.p_reach < threshold:
                    level[j] = None

    # Pricing Backward
    def price_backward(self):
        """
        Prix de l’option par récurrence arrière.
        """
        
        # Payoff à maturité
        last_level = self.tree[-1]
        for node in last_level:
            if node is not None:
                node.option_value = self.option.payoff(node.stock_price)

        def safe_val(level, idx):
            if 0 <= idx < len(level):
                child = level[idx]
                if child is not None and hasattr(child, "option_value"):
                    return child.option_value
            return 0.0  # fallback quand node = None

        # Boucle pour backward
        for i in range(self.N - 1, -1, -1):
            next_level = self.tree[i + 1]
            for j, node in enumerate(self.tree[i]):
                if node is None:
                    continue

                S = node.stock_price
                pD, pM, pU, kprime = self._probabilities(i, j - i, S)
                base = kprime + (i + 1)

                Vd = safe_val(next_level, base - 1)
                Vm = safe_val(next_level, base)
                Vu = safe_val(next_level, base + 1)

                hold = self.df * (pD * Vd + pM * Vm + pU * Vu)
                exer = self.option.payoff(S)

                # American vs European
                node.option_value = max(hold, exer) if self.exercise == "american" else hold

        return self.tree[0][0].option_value


    # Recursif Pricing
    def price_recursive(self, i=0, k=0):
        """
        Calcul récursif du prix de l’option
        """
        # Noeud terminal
        if i == self.N:
            node = self.tree[i][k + i]
            if node is None:
                return 0.0
            return self.option.payoff(node.stock_price)

         # Noeud actuel
        node = self.tree[i][k + i]
        if node is None:
            return 0.0

        S = node.stock_price

        # Calculer les probabilités de transition
        pD, pM, pU, kprime = self._probabilities(i, k, S)

        Vd = self.price_recursive(i + 1, kprime - 1)
        Vm = self.price_recursive(i + 1, kprime)
        Vu = self.price_recursive(i + 1, kprime + 1)

        hold = self.df * (pD * Vd + pM * Vm + pU * Vu)
        exer = self.option.payoff(S)

        # American vs European 
        return max(hold, exer) if self.exercise == "american" else hold

