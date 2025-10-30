import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.dividend import DividendPolicy
class Market:
    """
    Classe Market : paramètres de marché et gestion du dividende.

    On ne considère qu’une seule date ex-dividende.
    Si aucun dividende n’est renseigné, la valeur retournée est 0.
    """

    def __init__(self, S0: float, r: float, sigma: float, T: float,
                 exdivdate=None, pricing_date=None,
                 rho: float = 0.0, lam: float = 0.0):
        self.S0 = S0
        self.r = r
        self.sigma = sigma
        self.T = T
        self.rho = rho
        self.lam = lam
        self.pricing_date = pricing_date

        # Initialisation du dividende
        self.dividends = []
        if exdivdate is not None:
            policy = DividendPolicy(rho, lam, t0=0.0)
            self.dividends.append((float(exdivdate), policy))

    def has_dividend(self) -> bool:
        """Retourne True si un dividende est défini."""
        return bool(self.dividends)
