import math
from node import Node

# -------------------------------------------------------------------
# Utils : gestion des dates avec tolérance (slides Dauphine)
# -------------------------------------------------------------------
def are_same_dates(d1, d2, N):
    """
    Retourne True si deux dates sont 'quasi égales' avec une tolérance.
    Tolérance = (1/N)/1000
    """
    tol = 1.0 / (N * 1000.0)
    return abs(d1 - d2) < tol


def is_div_in_following_period(col_date, next_date, ex_div_date, N):
    """
    Retourne True si le dividende est payé dans (col_date, next_date],
    avec tolérance.
    """
    return (not are_same_dates(col_date, ex_div_date, N)) \
        and (col_date < ex_div_date) \
        and (ex_div_date < next_date or are_same_dates(ex_div_date, next_date, N))


# -------------------------------------------------------------------
# TrinomialTree (forward construction + backward pricing)
# -------------------------------------------------------------------
class TrinomialTree:
    def __init__(self, market, K, N, option_type="call", exercise="european"):
        self.market = market
        self.K = K
        self.N = N
        self.dt = market.T / N
        self.r = market.r
        self.sigma = market.sigma
        self.df = math.exp(-self.r * self.dt)
        self.option_type = option_type.lower()
        self.exercise = exercise.lower()

        # α = exp(σ√(3Δt)) (slides)
        self.alpha = math.exp(self.sigma * math.sqrt(3.0 * self.dt))

        # conteneurs
        self.tree = []
        self.trunk = []

        # cache variance facteur
        self.exp_sig2_dt = math.exp(self.sigma * self.sigma * self.dt)

    # ---------- Construction de l’arbre (forward) ----------
    def build_tree(self):
        """
        Construit l’arbre des prix du sous-jacent :
        - le tronc (k=0) avance avec le forward − dividende
        - les autres nœuds sont une série géométrique (α^k)
        """
        self.tree = []
        self.trunk = [0.0] * (self.N + 1)

        # Niveau 0
        self.trunk[0] = self.market.S0
        self.tree.append([Node(0, self.trunk[0])])

        # Dates discrètes (utile pour dividendes)
        times = [i * self.dt for i in range(self.N + 1)]
        ex_div_date = getattr(self.market, "ex_div_date", None)

        for i in range(1, self.N + 1):
            prev_mid = self.trunk[i - 1]
            fwd_mid = prev_mid * math.exp(self.r * self.dt)

            # Application dividende si ex-div tombe entre t_{i-1} et t_i
            if ex_div_date is not None:
                if is_div_in_following_period(times[i - 1], times[i], ex_div_date, self.N):
                    fwd_mid -= self.market.dividend

            mid_i = max(fwd_mid, 1e-14)
            self.trunk[i] = mid_i

            # Niveau i : k=-i..i
            level = []
            for k in range(-i, i + 1):
                S_ik = mid_i * (self.alpha ** k)
                level.append(Node(i, S_ik))
            self.tree.append(level)

    # ---------- Probabilités pour un nœud ----------
    def _probabilities(self, i, k, S_i_k):
        """
        Calcule (p_down, p_mid, p_up, kprime) selon les slides.
        """
        # Espérance forward du nœud
        E = S_i_k * math.exp(self.r * self.dt)
        if hasattr(self.market, "ex_div_date"):
            # si dividende cash global
            E -= float(self.market.dividend)
        E = max(E, 1e-14)

        Var = (S_i_k ** 2) * math.exp(2.0 * self.r * self.dt) * (self.exp_sig2_dt - 1.0)

        # Choix du médian le plus proche (k’)
        base_next = self.trunk[i + 1]
        raw_k = math.log(E / base_next) / math.log(self.alpha)
        kprime = int(round(raw_k))
        kprime = max(-(i + 1) + 1, min((i + 1) - 1, kprime))  # garder voisins

        # prix des cibles
        S_mid = base_next * (self.alpha ** kprime)
        S_up = S_mid * self.alpha
        S_down = S_mid / self.alpha

        # Cas spécial stable : E ≈ S_mid
        if abs(S_mid - E) <= 1e-12 * max(1.0, S_mid, E):
            denom = (1.0 - self.alpha) * (1.0 / (self.alpha * self.alpha) - 1.0)
            if abs(denom) < 1e-18:
                return 0.0, 1.0, 0.0, kprime
            p_down = (self.exp_sig2_dt - 1.0) / denom
            p_up = p_down / self.alpha
            p_mid = 1.0 - p_up - p_down
        else:
            # système réduit
            a, a_inv = self.alpha, 1.0 / self.alpha
            Ehat = E / S_mid
            M2hat = (Var + E * E) / (S_mid * S_mid)
            b1, b2 = (a * a - a), (a_inv * a_inv - a_inv)
            d1, d2 = (a - 1.0), (a_inv - 1.0)
            c1, c2 = (M2hat - Ehat), (Ehat - 1.0)

            det = b1 * d2 - b2 * d1
            if abs(det) < 1e-18:
                return 0.0, 1.0, 0.0, kprime

            p_up = (c1 * d2 - b2 * c2) / det
            p_down = (b1 * c2 - c1 * d1) / det
            p_mid = 1.0 - (p_up + p_down)

        # Clamp + normalisation
        s = p_up + p_mid + p_down
        if s <= 1e-14:
            return 0.0, 1.0, 0.0, kprime
        p_up, p_mid, p_down = p_up / s, p_mid / s, p_down / s
        p_up = max(0.0, min(1.0, p_up))
        p_mid = max(0.0, min(1.0, p_mid))
        p_down = max(0.0, min(1.0, p_down))
        return p_down, p_mid, p_up, kprime

    # ---------- Pricing (rollback) ----------
    def price(self):
        # payoff terminal
        last = self.tree[-1]
        if self.option_type == "call":
            for nd in last:
                nd.option_value = max(nd.stock_price - self.K, 0.0)
        else:
            for nd in last:
                nd.option_value = max(self.K - nd.stock_price, 0.0)

        # rollback
        for i in range(self.N - 1, -1, -1):
            next_level = self.tree[i + 1]
            for j, node in enumerate(self.tree[i]):
                k = j - i
                pD, pM, pU, kprime = self._probabilities(i, k, node.stock_price)

                base_idx = kprime + (i + 1)
                V_down = next_level[base_idx - 1].option_value
                V_mid = next_level[base_idx].option_value
                V_up = next_level[base_idx + 1].option_value

                hold = self.df * (pU * V_up + pM * V_mid + pD * V_down)
                if self.exercise == "american":
                    exer = (node.stock_price - self.K) if self.option_type == "call" else (self.K - node.stock_price)
                    node.option_value = max(hold, exer)
                else:
                    node.option_value = hold

        return float(self.tree[0][0].option_value)
