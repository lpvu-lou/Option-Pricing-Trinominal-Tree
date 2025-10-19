import sys
import os
import math
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.node import Node
from models.trunc_node import TruncNode
from models.option_trade import Option

# Constantes numériques pour éviter les instabilités ou divisions par zéro
EPS = 1e-14
MIN_PRICE = 1e-12

def _clip_and_normalize(pD, pM, pU):
    """
    Nettoie et renormalise les probabilités locales.
    """
    ps = [pD, pM, pU]
    ps = [0.0 if p < -1e-12 else max(0.0, p) for p in ps]
    s = sum(ps)
    if s < EPS:
        return 0.0, 1.0, 0.0
    return ps[0]/s, ps[1]/s, ps[2]/s

class TrinomialTree:
    """
    Arbre trinomial pour le pricing d’options européennes et américaines
     Cette classe permet :
    - de construire l’arbre des prix du sous-jacent
    - de calculer les probabilités de transition
    - de propager les valeurs de l’option (backward ou récursif)
    """
    def __init__(self, market, option: Option, N: int, exercise="european"):
        self.market = market
        self.option = option
        self.N = N                              # Nombre d’étapes de l’arbre
        self.dt = market.T / N                  # Durée d’un pas de temps
        self.r = market.r
        self.sigma = market.sigma
        self.df = math.exp(-self.r * self.dt)   # Facteur d'actualisation
        self.exercise = exercise.lower()

        # Paramètres du modèle trinomial
        self.alpha = math.exp(self.sigma * math.sqrt(3 * self.dt))
        self.exp_sig2_dt = math.exp(self.sigma**2 * self.dt)
        self.df = math.exp(-self.r * self.dt)

        # Structure de l’arbre
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)
    
    # ============== CONSTRUCTION DE L’ARBRE ==============
    def build_tree(self):
        """
        Construit l’arbre des prix du sous-jacent
        """

        S0 = self.market.S0
        self.tree.append([Node(0, S0)])  # Noeud racine
        self.trunk[0] = S0

        # Boucle sur les étapes temporelles
        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            t_i, t_ip1 = (i - 1) * self.dt, i * self.dt

            # Dividende sur ce pas
            div = self.market.dividend_on_step(t_i, t_ip1, prev_mid)

            # Calcul du nœud médian suivant (forward ajusté du dividende)
            mid_i = prev_mid * math.exp(self.r * self.dt) - div
            if mid_i < MIN_PRICE:
                mid_i = MIN_PRICE  # Empêche le prix de devenir nul ou négatif en cas de dividende important
            self.trunk[i] = mid_i

            # Calcul des prix de chaque nœud du niveau i 
            powers = np.arange(-i, i + 1)
            prices = mid_i * (self.alpha ** powers)

            # Construction du niveau avec des TruncNode
            level = [TruncNode(Node(i - 1, prev_mid), None, float(S), self) for S in prices]
            self.tree.append(level)


    # ============== CALCUL DES PROBABILITÉS DE TRANSITION ==============
    def _probabilities(self, i, k, S_i_k):
        """
        Calcule les probabilités locales (p_down, p_mid, p_up)
        """
        t_i, t_ip1 = i * self.dt, (i + 1) * self.dt
        div = self.market.dividend_on_step(t_i, t_ip1, S_i_k)

        # Espérance du prix futur sous la mesure risque-neutre
        E = S_i_k * math.exp(self.r * self.dt) - div

        # Paramètres du modèle
        a = self.alpha                  
        a2 = a * a
        exp2r = math.exp(2 * self.r * self.dt)

         # Variance du prix sur un pas de temps
        V = (S_i_k ** 2) * exp2r * (self.exp_sig2_dt - 1.0)

        if V < 1e-18:
            # Si la variance est négligeable, la trajectoire devient quasi déterministe.
            # On attribue donc toute la probabilité au nœud le plus proche de l’espérance E
            base_next = max(MIN_PRICE, self.trunk[i + 1])
            if base_next <= 0.0:
                base_next = max(MIN_PRICE, S_i_k * math.exp(self.r * self.dt))
            
            # Approximation de l’indice médian k′ (niveau central)
            kprime = int(round(math.log(max(E, MIN_PRICE) / base_next) / max(EPS, math.log(a))))
            S_mid = base_next * (a ** kprime)
            S_up, S_down = S_mid * a, S_mid / a

            # On choisit le nœud le plus proche de E
            dists = [(abs(E - S_down), -1), (abs(E - S_mid), 0), (abs(E - S_up), +1)]
            dj = min(dists, key=lambda x: x[0])[1]

            # On attribue la probabilité totale à ce nœud
            if dj == -1:
                return 1.0, 0.0, 0.0, kprime
            elif dj == 0:
                return 0.0, 1.0, 0.0, kprime
            else:
                return 0.0, 0.0, 1.0, kprime

        # Détermination du nœud médian de référence
        base_next = max(MIN_PRICE, self.trunk[i + 1])
        denom = max(EPS, math.log(a))
        kprime = int(round(math.log(max(E, MIN_PRICE) / base_next) / denom))
        kprime = max(-(i + 1), min(i + 1, kprime))
        S_mid = base_next * (a ** kprime)

        # Bornes de l’intervalle dans lequel doit se trouver E
        S_up, S_down = S_mid * a, S_mid / a
        lower = 0.5 * (S_mid + S_down)
        upper = 0.5 * (S_mid + S_up)

        # Si E est en dehors de l’intervalle, on ajuste k′
        max_shifts = 10
        shifts = 0
        while (E > upper or E < lower) and shifts < max_shifts:
            if E > upper:
                kprime += 1
                S_mid *= a
            elif E < lower:
                kprime -= 1
                S_mid /= a
            S_up, S_down = S_mid * a, S_mid / a
            lower = 0.5 * (S_mid + S_down)
            upper = 0.5 * (S_mid + S_up)
            shifts += 1

        # Calcul des moments normalisés
        m1 = E / S_mid                      # Moment d’ordre 1 (espérance relative)
        m2 = (V + E * E) / (S_mid * S_mid)  # Moment d’ordre 2 (variance relative)

        # Cas sans dividende
        if not self.market.has_dividend_between(t_i, t_ip1):
            p_down = (self.exp_sig2_dt - 1.0) / ((1.0 - a) * ((1.0 / a2) - 1.0))
            p_up = p_down / a
            p_mid = 1.0 - p_up - p_down
            return _clip_and_normalize(p_down, p_mid, p_up) + (kprime,)
        
        den = (1.0 - a) * ((1.0 / a2) - 1.0)
        if abs(den) < 1e-14:
            # Si le dénominateur est trop petit (a ≈ 1), on évite les instabilités numériques
            return 0.0, 1.0, 0.0, kprime

        # Calcul stable à partir des moments m1 et m2
        num = (m2 - 1.0) - (a + 1.0) * (m1 - 1.0)
        p_down = num / den

        # Probabilité p_up dérivée de la condition sur l’espérance
        p_up = (m1 - 1.0 - ((1.0 / a) - 1.0) * p_down) / (a - 1.0)
        p_mid = 1.0 - p_up - p_down

        # Nettoyage et normalisation
        p_down, p_mid, p_up = _clip_and_normalize(p_down, p_mid, p_up)
        
        return p_down, p_mid, p_up, kprime

    # ============== PROBABILITÉS D'ATTEINTE ==============
    def compute_reach_probabilities(self):
        """
        Calcule et stocke la probabilité d’atteinte (p_reach) de chaque nœud dans l’arbre trinomial
        """
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

        # Initialisation du nœud racine
        root = Node(0, self.market.S0)
        root.p_reach = 1.0
        self.tree.append([root])
        self.trunk[0] = self.market.S0

        # Propagation pas à pas
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

    # ============== PRUNING ==============
    def prune_tree(self, threshold=1e-7):
        """
        Supprime les nœuds ayant une probabilité d’atteinte trop faible (< threshold).
        """
        for i, level in enumerate(self.tree):
            for j, node in enumerate(level):
                if node is not None and node.p_reach < threshold:
                    level[j] = None

    # ============== PRICING BACKWARD ==============
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
            """Renvoie la valeur de l’enfant si elle existe, sinon 0"""
            if 0 <= idx < len(level):
                child = level[idx]
                if child is not None and hasattr(child, "option_value"):
                    return child.option_value
            return 0.0  # fallback quand node = None

        # Boucle backward
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

                # Prise en compte de l’exercice anticipé (option américaine)
                node.option_value = max(hold, exer) if self.exercise == "american" else hold

        return self.tree[0][0].option_value


     # ============== PRICING RECURSIF (AVEC MEMOISATION) ==============
    def price_recursive(self, i=0, k=0, _cache=None):
        """
        Calcul récursif du prix de l’option
        """
        if _cache is None:
            _cache = {}

        key = (i, k)
        if key in _cache:
            return _cache[key]

        # Noeud terminal
        if i >= self.N:
            # Vérifie que l’indice existe dans l’arbre
            if 0 <= k + i < len(self.tree[i]):
                node = self.tree[i][k + i]
                val = 0.0 if node is None else self.option.payoff(node.stock_price)
            else:
                val = 0.0
            _cache[key] = val
            return val

        # Noeud actuel
        if 0 <= k + i < len(self.tree[i]):
            node = self.tree[i][k + i]
            if node is None:
                _cache[key] = 0.0
                return 0.0
        else:
            _cache[key] = 0.0
            return 0.0

        S = node.stock_price

        # Calculer les probabilités de transition
        pD, pM, pU, kprime = self._probabilities(i, k, S)

        # Borner kprime dans l’intervalle autorisé du niveau i+1
        kprime = max(-(i + 1), min(i + 1, kprime))

        Vd = self.price_recursive(i + 1, kprime - 1, _cache)
        Vm = self.price_recursive(i + 1, kprime, _cache)
        Vu = self.price_recursive(i + 1, kprime + 1, _cache)

        hold = self.df * (pD * Vd + pM * Vm + pU * Vu)
        exer = self.option.payoff(S)
        val = max(hold, exer) if self.exercise == "american" else hold

        _cache[key] = val
        return val

