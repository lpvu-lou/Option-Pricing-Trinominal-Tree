# Objectif : stocker les paramètres du marché et fournir
# des méthodes simples pour calculer des valeurs dérivées,
# comme le prix forward ou les taux effectifs.

import math

# Modèle de dividende
class DividendPolicy:
    def __init__(self, rho: float, lam: float = 0.5, t0: float = 0.0):
        self.rho = rho      # Intensité du dividende
        self.lam = lam      # Vitesse de transition entre fixe et proportionnel
        self.t0 = t0        # Temps initial

    def amount(self, t: float, S: float, S0: float) -> float:
        return self.rho * (S0 * math.exp(-self.lam * (t - self.t0)) +
                           S * (1 - math.exp(-self.lam * (t - self.t0))))

class Market:
    """
    Classe représentant les paramètres du marché
    """

    def __init__(self, S0: float, r: float, sigma: float, T: float, dividends = None):
        self.S0 = S0                # Prix initial du sous-jacent
        self.r = r                  # Taux d'intérêt sans risque
        self.sigma = sigma          # Volatilité annualisée
        self.T = T                  # Maturité (en années)
        self.dividends = dividends if dividends else []

    # Calcul du prix forward du sous-jacent
    def prix_forward(self, dt: float) -> float:
        return self.S0 * math.exp(self.r * dt)

    def dividend_on_step(self, t_i: float, t_ip1: float, S: float) -> float:
        tol = (t_ip1 - t_i) / 1000
        total_div = 0.0
        for t_div, policy in self.dividends:
            if t_i < t_div <= t_ip1 + tol:  # le div tombe dans cet intervalle
                total_div += policy.amount(t_div, S, self.S0)
        return total_div

    def __repr__(self):
        return (
            f"Market(S0={self.S0}, r={self.r}, sigma={self.sigma}, "
            f"T={self.T}, dividends={self.dividends})"
        )


