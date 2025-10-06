import math
import numpy as np
from node import Node
from option_trade import Option

### CLASSE PRINCIPALE : TrinominalTree

class TrinomialTree:
    """
    Arbre trinomial pour le pricing d’options EU et US
    - Construction de l’arbre des prix du sous-jacent (forward)
    - Calcul des probabilités locales de transition
    - Calcul des probabilités d’atteinte (p_reach) de chaque nœud
    - Pricing Options en 2 méthodes: backward et récursif
    """

    def __init__(self, market, option: Option, N: int, exercise="european"):
        # Paramètres du marché et de l'option
        self.market = market
        self.option = option
        self.N = N
        self.dt = market.T / N
        self.r = market.r
        self.sigma = market.sigma
        self.df = math.exp(-self.r * self.dt)
        self.exercise = exercise.lower()

        # Paramètres de l’arbre
        self.alpha = math.exp(self.sigma * math.sqrt(3.0 * self.dt))
        self.exp_sig2_dt = math.exp(self.sigma * self.sigma * self.dt)
        self.tree = []  # Arbre complet (liste de niveaux)
        self.trunk = []  #  Middle prix de chaque niveau

    ## Construction de l’arbre des prix du sous-jacent
    def build_tree(self):
        """
        Construit la structure de l’arbre des prix (sans probabilités d’atteinte).
        Chaque niveau contient les prix possibles du sous-jacent à cet instant.
        """
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)
        self.trunk[0] = self.market.S0
        self.tree.append([Node(0, self.trunk[0])])

        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i = (i - 1) * self.dt
            t_ip1 = i * self.dt

            # Vérifie si un dividende tombe sur cet intervalle
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)
            mid_i = prev_mid * math.exp(self.r * self.dt) - div

            self.trunk[i] = mid_i
            level = [Node(i, mid_i * (self.alpha ** k)) for k in range(-i, i + 1)]
            self.tree.append(level)

    ## Probabilités locales de transition

    def _probabilities(self, i, k, S_i_k):
        """
        Calcule les probabilités locales de transition à partir d’un nœud (i, k)
        vers les trois états possibles à l’étape suivante :
        - p_down, p_mid, p_up
        Ces probabilités sont calculées dynamiquement à partir des
        équations d’espérance et de variance.
        """
        t_i = i * self.dt
        t_ip1 = (i + 1) * self.dt
        div = self.market.dividend_on_step(t_i, t_ip1, S_i_k)

        E = S_i_k * math.exp(self.r * self.dt) - div
        Var = (S_i_k ** 2) * math.exp(2.0 * self.r * self.dt) * (self.exp_sig2_dt - 1.0)

        base_next = self.trunk[i + 1]
        raw_k = math.log(E / base_next) / math.log(self.alpha)
        kprime = int(round(raw_k))

        S_mid = base_next * (self.alpha ** kprime)
        S_up = S_mid * self.alpha
        S_down = S_mid / self.alpha

        # Cas stable (S_mid ≈ E)
        if abs(S_mid - E) <= 1e-12 * max(1.0, S_mid, E):
            p_down = (self.exp_sig2_dt - 1.0) / ((1 - self.alpha) * (1 / (self.alpha ** 2) - 1))
            p_up = p_down / self.alpha
            p_mid = 1.0 - p_up - p_down
        else:
            # Cas général : résolution du système linéaire 2x2
            a, a_inv = self.alpha, 1.0 / self.alpha
            Ehat = E / S_mid
            M2hat = (Var + E * E) / (S_mid * S_mid)
            b1, b2 = (a * a - a), (a_inv * a_inv - a_inv)
            d1, d2 = (a - 1.0), (a_inv - 1.0)
            c1, c2 = (M2hat - Ehat), (Ehat - 1.0)
            det = b1 * d2 - b2 * d1

            p_up = (c1 * d2 - b2 * c2) / det
            p_down = (b1 * c2 - c1 * d1) / det
            p_mid = 1.0 - (p_up + p_down)

        s = p_up + p_mid + p_down
        p_up, p_mid, p_down = p_up / s, p_mid / s, p_down / s
        return max(0, p_down), max(0, p_mid), max(0, p_up), kprime

    ## Calcul des probabilités d’atteinte (p_reach)

    def compute_reach_probabilities(self):
        """
        Calcule les probabilités d’atteinte de chaque nœud dans l’arbre,
        en utilisant les probabilités locales calculées dynamiquement
        pour chaque nœud (approche forward).
        """
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)
        self.trunk[0] = self.market.S0

        # Root
        root = Node(0, self.trunk[0])
        root.p_reach = 1.0
        self.tree.append([root])

        # Boucle sur les niveaux
        for i in range(self.N):
            prev_level = self.tree[i]
            level_next = [None] * (2 * (i + 1) + 1)

            prev_mid = self.trunk[i]
            mid_i = prev_mid * math.exp(self.r * self.dt)
            self.trunk[i + 1] = mid_i

            for j, node in enumerate(prev_level):
                if node is None or node.p_reach == 0.0:
                    continue
                k = j - i

                # Calcul des probabilités locales dynamiques
                pD, pM, pU, kprime = self._probabilities(i, k, node.stock_price)

                # Propagation des probabilités d’atteinte
                for dj, p in ((+1, pU), (0, pM), (-1, pD)):
                    jn = k + dj
                    idx = jn + (i + 1)
                    if level_next[idx] is None:
                        S_next = self.trunk[i + 1] * (self.alpha ** jn)
                        level_next[idx] = Node(i + 1, S_next)
                    level_next[idx].p_reach += node.p_reach * p

            self.tree.append(level_next)

    ## Tree pruning
    def prune_tree(self, threshold: float = 1e-7, inplace: bool = True):
        """
        Supprime (ou ignore) les nœuds dont la probabilité d’atteinte (p_reach)
        est inférieure à un seuil donné.

        threshold :
            Seuil de probabilité minimum. Les nœuds ayant p_reach < threshold
            seront supprimés ou marqués comme None.
        inplace : bool
            Si True (défaut), modifie self.tree directement.
            Si False, retourne une copie allégée de l’arbre sans modifier l’original.
        """
        pruned_tree = []

        for i, level in enumerate(self.tree):
            new_level = []
            for node in level:
                # Si le nœud existe et a une probabilité suffisante
                if node and node.p_reach >= threshold:
                    new_level.append(node)
                else:
                    new_level.append(None)
            pruned_tree.append(new_level)

        if inplace:
            self.tree = pruned_tree
            return None
        else:
            return pruned_tree

    ## Pricing backward

    def price(self):
        """
        Calcule le prix de l’option par induction inverse (méthode backward).
        """
        last = self.tree[-1]
        for node in last:
            node.option_value = self.option.payoff(node.stock_price)

        # Remontée backward
        for i in range(self.N - 1, -1, -1):
            next_level = self.tree[i + 1]
            for j, node in enumerate(self.tree[i]):
                if node is None:
                    continue

                k = j - i
                pD, pM, pU, kprime = self._probabilities(i, k, node.stock_price)
                base_idx = kprime + (i + 1)

                Vd = next_level[base_idx - 1].option_value
                Vm = next_level[base_idx].option_value
                Vu = next_level[base_idx + 1].option_value
                hold = self.df * (pU * Vu + pM * Vm + pD * Vd)

                # Option américaine : comparaison avec exercice anticipé
                if self.exercise == "american":
                    exer = self.option.payoff(node.stock_price)
                    node.option_value = max(hold, exer)
                else:
                    node.option_value = hold

        return self.tree[0][0].option_value

    ## Pricing récursif

    def recursive_price(self, i=0, k=0):
        """
        Calcule récursivement le prix de l’option à partir du nœud (i, k).
        Compatible avec un arbre élagué (nodes = None).
        """

        # Vérifie les limites de l’arbre
        if i > self.N or k + i < 0 or k + i >= len(self.tree[i]):
            return 0.0

        node = self.tree[i][k + i]
        if node is None:
            return 0.0

        S = node.stock_price

        # Payoff à maturité
        if i == self.N:
            return self.option.payoff(S)

        # Probabilités locales (dynamiques)
        pD, pM, pU, kprime = self._probabilities(i, k, S)

        # Valeurs des 3 nœuds enfants
        Vd = self.recursive_price(i + 1, kprime - 1)
        Vm = self.recursive_price(i + 1, kprime)
        Vu = self.recursive_price(i + 1, kprime + 1)

        # Valeur théorique du nœud
        hold = self.df * (pU * Vu + pM * Vm + pD * Vd)

        # Option américaine
        if self.exercise == "american":
            return max(hold, self.option.payoff(S))
        else:
            return hold



