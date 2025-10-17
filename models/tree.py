import math
from models.node import Node
from models.option_trade import Option


class TrinomialTree:
    """
    Arbre trinomial pour le pricing d’options européennes et américaines.
    Compatible avec le Market utilisant datetime_to_years.
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

        # Paramètres du modèle trinomial
        self.alpha = math.exp(self.sigma * math.sqrt(3 * self.dt))
        self.exp_sig2_dt = math.exp(self.sigma**2 * self.dt)

        # Structure de l’arbre
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

    # =========================================================
    # CONSTRUCTION DE L’ARBRE DES PRIX
    # =========================================================
    def build_tree(self):
        """Construit l’arbre des prix du sous-jacent."""
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

        # Racine
        self.trunk[0] = self.market.S0
        self.tree.append([Node(0, self.trunk[0])])

        # Boucle de construction
        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i, t_ip1 = (i - 1) * self.dt, i * self.dt

            # Dividende éventuel sur ce pas
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)

            # Prix médian du niveau suivant
            mid_i = prev_mid * math.exp(self.r * self.dt) - div
            self.trunk[i] = mid_i

            # Niveau (2i + 1 nœuds)
            level = [Node(i, mid_i * (self.alpha ** k)) for k in range(-i, i + 1)]
            self.tree.append(level)

    # =========================================================
    # CALCUL DES PROBABILITÉS LOCALES
    # =========================================================
    def _probabilities(self, i, k, S_i_k):
        """Calcule les probabilités locales (p_down, p_mid, p_up)."""
        t_i, t_ip1 = i * self.dt, (i + 1) * self.dt
        div = self.market.dividend_on_step(t_i, t_ip1, S_i_k)

        # Espérance et variance du sous-jacent
        E = S_i_k * math.exp(self.r * self.dt) - div
        V = (S_i_k ** 2) * math.exp(2 * self.r * self.dt) * (self.exp_sig2_dt - 1)

        a = self.alpha
        a2 = a * a

        base_next = self.trunk[i + 1]
        kprime = int(round(math.log(E / base_next) / math.log(a)))
        S_mid = base_next * (a ** kprime)
        S_up, S_down = S_mid * a, S_mid / a

        # Cas sans dividendes
        if not self.market.has_dividend_between(t_i, t_ip1):
            p_down = (self.exp_sig2_dt - 1) / ((1 - a) * ((1 / a2) - 1))
            p_up = p_down / a
            p_mid = 1 - p_up - p_down
        else:
            # Cas général avec dividendes
            num = (1 / (S_mid ** 2)) * (V + E ** 2) - 1 - (a + 1) * ((E / S_mid) - 1)
            den = (1 - a) * ((1 / a2) - 1)
            p_down = num / den
            p_up = ((E / S_mid) - 1 - ((1 / a) - 1) * p_down) / (a - 1)
            p_mid = 1 - p_up - p_down

        # Ajustement si nécessaire
        lower, upper = 0.5 * (S_mid + S_down), 0.5 * (S_mid + S_up)
        if E > upper:
            kprime += 1
            S_mid *= a
        elif E < lower:
            kprime -= 1
            S_mid /= a

        return p_down, p_mid, p_up, int(kprime)

    # =========================================================
    # PROBABILITÉS D’ATTEINTE
    # =========================================================
    def compute_reach_probabilities(self):
        """Calcule la probabilité d’atteinte p_reach pour chaque nœud."""
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

        root = Node(0, self.market.S0)
        root.p_reach = 1.0
        self.tree.append([root])
        self.trunk[0] = self.market.S0

        for i in range(self.N):
            prev_level = self.tree[i]
            next_level = [None] * (2 * (i + 1) + 1)

            prev_mid = self.trunk[i]
            t_i, t_ip1 = i * self.dt, (i + 1) * self.dt
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)
            mid_next = prev_mid * math.exp(self.r * self.dt) - div
            self.trunk[i + 1] = mid_next

            for j, node in enumerate(prev_level):
                if node is None or node.p_reach == 0.0:
                    continue

                k = j - i
                pD, pM, pU, kprime = self._probabilities(i, k, node.stock_price)

                for dj, p in ((-1, pD), (0, pM), (+1, pU)):
                    if p <= 0:
                        continue
                    knext = k + dj
                    idx = knext + (i + 1)
                    if next_level[idx] is None:
                        S_next = mid_next * (self.alpha ** knext)
                        next_level[idx] = Node(i + 1, S_next)
                    next_level[idx].p_reach += node.p_reach * p

            self.tree.append(next_level)

    # =========================================================
    # ÉLAGAGE (PRUNING)
    # =========================================================
    def prune_tree(self, threshold=1e-7, inplace=True):
        """Supprime les nœuds peu probables pour accélérer le calcul."""
        pruned = []
        for level in self.tree:
            new_level = [node if node and node.p_reach >= threshold else None for node in level]
            pruned.append(new_level)

        if inplace:
            self.tree = pruned
        else:
            return pruned

    # =========================================================
    # PRICING BACKWARD
    # =========================================================
    def price_backward(self):
        """Prix de l’option par récurrence arrière."""
        # Payoff à maturité
        for node in self.tree[-1]:
            if node is not None:
                node.option_value = self.option.payoff(node.stock_price)

        # Remontée
        for i in range(self.N - 1, -1, -1):
            next_level = self.tree[i + 1]
            for j, node in enumerate(self.tree[i]):
                if node is None:
                    continue

                S = node.stock_price
                pD, pM, pU, kprime = self._probabilities(i, j - i, S)
                base = kprime + (i + 1)

                Vd = next_level[base - 1].option_value
                Vm = next_level[base].option_value
                Vu = next_level[base + 1].option_value

                hold = self.df * (pU * Vu + pM * Vm + pD * Vd)
                exer = self.option.payoff(S)
                node.option_value = max(hold, exer) if self.exercise == "american" else hold

        return self.tree[0][0].option_value

    # =========================================================
    # PRICING RÉCURSIF
    # =========================================================
    def price_recursive(self, i=0, k=0):
        """Calcul récursif du prix de l’option."""
        if i == self.N:
            return self.option.payoff(self.tree[i][k + i].stock_price)

        node = self.tree[i][k + i]
        S = node.stock_price
        pD, pM, pU, kprime = self._probabilities(i, k, S)

        Vd = self.price_recursive(i + 1, kprime - 1)
        Vm = self.price_recursive(i + 1, kprime)
        Vu = self.price_recursive(i + 1, kprime + 1)

        hold = self.df * (pU * Vu + pM * Vm + pD * Vd)
        exer = self.option.payoff(S)

        return max(hold, exer) if self.exercise == "american" else hold
