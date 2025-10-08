import math

# Modèle de dividende
class DividendPolicy:
    def __init__(self, rho, lam, t0=0.0):
        self.rho = rho
        self.lam = lam
        self.t0 = t0

    def amount(self, t, S, S0):
        return self.rho * (S0 * math.exp(-self.lam * (t - self.t0)) +
                           S * (1 - math.exp(-self.lam * (t - self.t0))))


# Classe Market
class Market:
    def __init__(self, S0, r, sigma, T, dividends=None,
                 auto_freq=1.0,  # fréquence annuelle
                 auto_offset=0.0,  # décalage en années
                 rho=0.0,
                 lam=0.0
                 ):
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

    def prix_forward(self, dt):
        return self.S0 * math.exp(self.r * dt)

    def dividend_on_step(self, t_i, t_ip1, S):
        tol = (t_ip1 - t_i) / 1000 if t_ip1 > t_i else 1e-12
        total_div = 0
        for t_div, policy in self.dividends:
            if t_i < t_div <= t_ip1 + tol:
                total_div += policy.amount(t_div, S, self.S0)
        return total_div

    def has_dividend_between(self, t_i, t_ip1):
        tol = (t_ip1 - t_i) / 1000 if t_ip1 > t_i else 1e-12
        for t_div, _ in self.dividends:
            if t_i < t_div <= t_ip1 + tol:
                return True
        return False