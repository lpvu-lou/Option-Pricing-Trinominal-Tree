import sys
import os
import copy
import numpy as np
from math import exp, sqrt, log
from scipy.stats import norm
from typing import Dict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_pricer import (
    input_parameters,
    backward_pricing,
    recursive_pricing,
    black_scholes_price
)
from utils.utils_bs import bs_price
from utils.utils_grecs import OneDimDerivative

def get_price(market, option, N, exercise, optimize, threshold, method):
    """
    Retourne le prix de l’option selon la méthode choisie 
    """
    pricing_fn = backward_pricing if method.lower() == "backward" else recursive_pricing
    price, _, _ = pricing_fn(market, option, N, exercise, optimize, threshold)
    return price


def greek_wrapper(params, x: float) -> float:
    """
    Wrapper : modifie un paramètre de marché pour recalculer le prix.
    Permet d’utiliser des dérivées numériques de manière générique.
    """
    market, option, N, exercise, optimize, threshold, target, method = params
    m = copy.deepcopy(market)
    setattr(m, target, x)
    return get_price(m, option, N, exercise, optimize, threshold, method)


def finite_diff_2d(market, option, N, exercise, optimize, threshold, method, base_price,
                   hS=None, hSigma=None):
    """
    Calcule les grecs de second ordre croisés :
    - Vanna : dérivée croisée ∂²V/∂S∂σ
    - Vomma : dérivée seconde ∂²V/∂σ²
    """
    S0, sigma0 = market.S0, market.sigma

    # Définit les incréments 
    hS = hS or 0.01      # Bump de 1% du sous-jacent
    hSigma = hSigma      # Bump absolu de volatilité

    # Fonction interne pour recalculer le prix avec des shifts donnés
    def price_with_shifts(S_shift=0.0, sigma_shift=0.0):
        m = copy.deepcopy(market)
        m.S0 = S0 + S_shift
        m.sigma = sigma0 + sigma_shift
        return get_price(m, option, N, exercise, optimize, threshold, method)

    # Vanna
    p_up_up     = price_with_shifts(+hS, +hSigma)
    p_up_down   = price_with_shifts(+hS, -hSigma)
    p_down_up   = price_with_shifts(-hS, +hSigma)
    p_down_down = price_with_shifts(-hS, -hSigma)
    vanna = (p_up_up - p_up_down - p_down_up + p_down_down) / (4.0 * hS * hSigma)

    # Vomma
    p_sig_up   = price_with_shifts(0.0, +hSigma)
    p_sig_down = price_with_shifts(0.0, -hSigma)
    vomma = (p_sig_up - 2.0 * base_price + p_sig_down) / (hSigma ** 2)

    return vanna, vomma

def compute_method_greeks(market, option, N, exercise, optimize, threshold, method):
    """
    Calcule les grecs d’une méthode donnée (Backward / Recursive) via différences finies
    """
    base_price = get_price(market, option, N, exercise, optimize, threshold, method)

    # Définition des pas de variation (scale-aware)
    hS = max(1e-4, 0.01 * market.S0)   # 1% du sous-jacent
    hSigma = 1e-3                      # 0.1% de volatilité
    hR = 1e-4                          # 1 bp
    hT = 1.0 / 365.0                   # 1 jour

    dS = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "S0", method), shift=hS)
    dSigma = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "sigma", method), shift=hSigma)
    dRho = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "r", method), shift=hR)
    dTheta = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "T", method), shift=hT)

    # Calculs des dérivées
    Delta = dS.first(market.S0)
    Gamma = dS.second(market.S0)
    Vega  = dSigma.first(market.sigma)
    Rho   = dRho.first(market.r)
    Theta = -dTheta.first(market.T)
    Vanna, Vomma = finite_diff_2d(market, option, N, exercise, optimize, threshold, method, base_price, hS=hS, hSigma=hSigma)

    return {
        "Price": base_price,
        "Delta": Delta,
        "Gamma": Gamma,
        "Vega": Vega,
        "Theta": Theta,
        "Rho": Rho,
        "Vanna": Vanna,
        "Vomma": Vomma,
    }

def bs_greeks(S, K, r, sigma, T, is_call=True) -> Dict[str, float]:
    """
    Calcule les grecs selon Black-Scholes
    """
    if T <= 0 or sigma <= 0 or S <= 0:
        return {g: 0.0 for g in ["Price", "Delta", "Gamma", "Vega", "Theta", "Rho", "Vanna", "Vomma"]}

    d1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d2 = d1 - sigma * sqrt(T)

    pdf_d1 = norm.pdf(d1)
    Nd1, Nd2 = norm.cdf(d1), norm.cdf(d2)

    price = bs_price(S, K, r, sigma, T, is_call)

    if is_call:
        delta = Nd1
        theta = -(S * pdf_d1 * sigma) / (2 * sqrt(T)) - r * K * exp(-r * T) * Nd2
        rho = K * T * exp(-r * T) * Nd2
    else:
        Nmd1, Nmd2 = norm.cdf(-d1), norm.cdf(-d2)
        delta = -Nmd1
        theta = -(S * pdf_d1 * sigma) / (2 * sqrt(T)) + r * K * exp(-r * T) * Nmd2
        rho = -K * T * exp(-r * T) * Nmd2

    gamma = pdf_d1 / (S * sigma * sqrt(T))
    vega = S * pdf_d1 * sqrt(T)
    vomma = vega * d1 * d2 / sigma
    vanna = vega * (1.0 - d1 / (sigma * sqrt(T))) / S

    return {
        "Price": price,
        "Delta": delta,
        "Gamma": gamma,
        "Vega": vega,
        "Theta": theta,
        "Rho": rho,
        "Vanna": vanna,
        "Vomma": vomma,
    }

def compute_greeks():
    """
    Fonction principale liée à Excel.
    Calcule les grecs via les deux méthodes 
    et les compare aux résultats Black-Scholes
    """
    (market, option, N, exercise, method, optimize, threshold,
        arbre_stock, arbre_proba, arbre_option, wb, sheet,
        S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()

    ws = wb.sheets["Greeks"]

    # Nettoyage de la feuille
    for chart in ws.charts:
        chart.delete()
    ws.range("C6:ZZ1048576").clear_contents()

    # S'il y a dividend ou si l'option est US, on fait pas le calcul de grecs pour Black-Scholes
    can_use_bs = (not exdivdate) and (exercise == "european")
    bs_results = bs_greeks(S0, K, r, sigma, T, is_call) if can_use_bs else None

    # Calcul des grecs pour les deux méthodes de pricing
    results = {m: compute_method_greeks(market, option, N, exercise, optimize, threshold, m)
               for m in ["backward", "recursive"]}

    labels = ["Prix d'option", "Delta", "Gamma", "Vega", "Theta", "Rho", "Vanna", "Vomma"]
    start_row = 6
    col_bs, col_rec, col_bw = "C", "F", "I"

    for i, label in enumerate(labels):
        key = label.replace("Prix d'option", "Price")

        # Colonnes Recursive et Backward
        ws.range(f"{col_rec}{start_row + i}").value = results["recursive"].get(key)
        ws.range(f"{col_bw}{start_row + i}").value = results["backward"].get(key)
        ws.range(f"{col_rec}{start_row + i}").value = results["recursive"].get(key, None)
        ws.range(f"{col_bw}{start_row + i}").value = results["backward"].get(key, None)

        # Colonne C (BS) uniquement si condition remplie
        if can_use_bs:
            ws.range(f"{col_bs}{start_row + i}").value = bs_results.get(key)
        else:
            ws.range(f"{col_bs}{start_row + i}").value = None

        ws.range(f"{col_rec}{start_row + i}:{col_bs}{start_row + i}").number_format = "0.000000"

    return results

if __name__ == "__main__":
    compute_greeks()
