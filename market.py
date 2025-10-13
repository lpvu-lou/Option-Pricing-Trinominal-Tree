import math

class DividendPolicy:
    """
    Modele de dividende : montant proportionnel au prix du sous-jacent avec un taux de décroissance exponentielle.
    """
    def __init__(self, rho: float, lam: float, t0: float = 0.0):
        self.rho = rho
        self.lam = lam
        self.t0 = t0

    def amount(self, t: float, S: float, S0: float) -> float:
        return self.rho * (S0 * math.exp(-self.lam * (t - self.t0)) + S * (1 - math.exp(-self.lam * (t - self.t0))))


class Market:
    """
    Paramètres du marché et calendrier des dividendes discrets
    """
    def __init__(self, S0, r, sigma, T,
                 dividends=None,
                 auto_freq=1.0,  # fréquence des dividendes annuels
                 auto_offset=0.0, # premier dividende automatique
                 rho=0.0, lam=0.0):
        self.S0 = S0
        self.r = r
        self.sigma = sigma
        self.T = T
        self.rho = rho
        self.lam = lam

        if dividends is not None:
            self.dividends = dividends
        else:
            self.dividends = []
            if T > 0 and auto_freq > 0:
                t = auto_offset
                eps = 1e-12
                while t <= T + eps:
                    if t > eps:
                        self.dividends.append((t, DividendPolicy(rho, lam, t0=0.0)))
                    t += auto_freq

    def forward_price(self, dt: float) -> float:
        """
        Prix à terme du sous-jacent à l’instant t+dt sachant S(t)
        """
        return self.S0 * math.exp(self.r * dt)

    def dividend_on_step(self, t_i: float, t_ip1: float, S: float) -> float:
        """Somme des dividendes survenant entre t_i et t_{i+1}"""
        tol = (t_ip1 - t_i) / 1000
        total_div = 0.0
        for t_div, policy in self.dividends:
            if t_i < t_div <= t_ip1 + tol:
                total_div += policy.amount(t_div, S, self.S0)
        return total_div

    def has_dividend_between(self, t_i: float, t_ip1: float) -> bool:
        """Indique s’il y a un dividende entre t_i et t_{i+1}"""
        tol = (t_ip1 - t_i) / 1000
        return any(t_i < t_div <= t_ip1 + tol for t_div, _ in self.dividends)

