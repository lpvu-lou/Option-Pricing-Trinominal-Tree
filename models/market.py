import math
import datetime as dt
from models.dividend import DividendPolicy

class Market:
    """
    Paramètres du marché et calendrier des dividendes.
    """

    def __init__(self, S0: float, r: float, sigma: float, T: float,
                 dividends=None,exdivdate=None,
                 pricing_date=None,rho=0.0, lam=0.0):
        
        self.S0 = S0
        self.r = r
        self.sigma = sigma
        self.T = T
        self.rho = rho
        self.lam = lam
        self.pricing_date = pricing_date
        self.dividends = []

        # Cas 1 : liste complète de dividendes fournie
        if dividends is not None:
            self.dividends = dividends

        # Cas 2 : création automatique à partir des dates ex-div déjà en années
        elif exdivdate is not None:
            if not isinstance(exdivdate, (list, tuple)):
                exdivdate = [exdivdate]
            for t in exdivdate:
                policy = DividendPolicy(rho, lam, t0=0.0)
                self.dividends.append((float(t), policy))

        # Cas 3 : aucun dividende
        else:
            self.dividends = []

    def dividend_on_step(self, t_i: float, t_ip1: float, S: float) -> float:
        """
        Somme des dividendes survenant entre t_i et t_{i+1}
        """
        if not self.dividends:
            return 0.0
        
        tol = (t_ip1 - t_i) / 1000.0
        total_div = 0.0

        for t_div, policy in self.dividends:
            if t_i < t_div <= t_ip1 + tol:
                total_div += policy.amount(t_div, S, self.S0)

        return total_div

    def has_dividend_between(self, t_i: float, t_ip1: float) -> bool:
        """
        Vérifie s’il y a un dividende entre t_i et t_{i+1}
        """
        tol = (t_ip1 - t_i) / 1000.0
        return any(t_i < t_div <= t_ip1 + tol for t_div, _ in self.dividends)


