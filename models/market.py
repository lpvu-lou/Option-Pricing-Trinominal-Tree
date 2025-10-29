import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import math
import datetime as dt
from models.dividend import DividendPolicy

class Market:
    """
    Paramètres du marché et calendrier des dividendes.
    - Gère les cas : aucun dividende, liste de dividendes, ou ex-div dates explicites.
    - Vérifie correctement les limites :
        * ex-div = pricing + 1 jour → appliqué au premier pas
        * ex-div = maturité         → ignoré
    """

    def __init__(self, S0: float, r: float, sigma: float, T: float,
                 dividends=None, exdivdate=None,
                 pricing_date=None, rho: float = 0.0, lam: float = 0.0):
        self.S0 = S0
        self.r = r
        self.sigma = sigma
        self.T = T
        self.rho = rho
        self.lam = lam
        self.pricing_date = pricing_date
        self.dividends = []

        # --- Cas 1 : liste complète de dividendes fournie
        if dividends is not None:
            self.dividends = dividends

        # --- Cas 2 : création automatique à partir d'une ou plusieurs ex-div dates
        elif exdivdate is not None:
            if not isinstance(exdivdate, (list, tuple)):
                exdivdate = [exdivdate]
            for t in exdivdate:
                policy = DividendPolicy(rho, lam, t0=0.0)
                self.dividends.append((float(t), policy))

        # --- Cas 3 : aucun dividende
        else:
            self.dividends = []

    # ---------------------------------------------------------------
    # 🧮 Dividend logic
    # ---------------------------------------------------------------
    def dividend_on_step(self, t_i: float, t_ip1: float, S: float) -> float:
        """
        Retourne la somme des dividendes survenant strictement entre t_i et t_{i+1}.
        (Le dividende à maturité n’est PAS pris en compte.)
        """
        if not self.dividends:
            return 0.0

        tol = (t_ip1 - t_i) / 1000.0
        total_div = 0.0

        for t_div, policy in self.dividends:
            # ✅ Déclenche uniquement si le dividende tombe AVANT la fin du pas
            if t_i < t_div < t_ip1 - tol:
                amount = policy.amount(t_div, S, self.S0)
                total_div += amount

        return total_div

    def has_dividend_between(self, t_i: float, t_ip1: float) -> bool:
        """
        Vérifie s’il y a un dividende entre t_i et t_{i+1}.
        (Le dividende à maturité n’est PAS pris en compte.)
        """
        if not self.dividends:
            return False

        tol = (t_ip1 - t_i) / 1000.0
        return any(t_i < t_div < t_ip1 - tol for t_div, _ in self.dividends)
