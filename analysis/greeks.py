import sys
import os
import copy
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_pricer import (
    input_parameters,
    run_backward_pricing,
    run_recursive_pricing,
)
from utils.utils_bs import bs_greeks
from utils.utils_grecs import OneDimDerivative

def get_price(market, option, N, exercise, optimize, threshold, method):
    """
    Retourne le prix de l’option selon la méthode choisie 
    """
    pricing_fn = run_backward_pricing if method.lower() == "backward" else run_recursive_pricing
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
    Calcule Vanna et Vomma avec stabilité numérique.
    - Vanna = ∂²V / ∂S∂σ
    - Vomma = ∂²V / ∂σ²
    """
    S0, sigma0 = market.S0, market.sigma

    # Choix de bumps stables
    hS = hS or max(1e-4, 0.01 * S0)      # 1% du sous-jacent
    hSigma = hSigma or max(1e-4, 0.005)  # 0.5% absolu sur sigma

    def price_shift(S_shift=0.0, sigma_shift=0.0):
        m = copy.deepcopy(market)
        m.S0 = S0 + S_shift
        m.sigma = max(1e-6, sigma0 + sigma_shift)  # éviter σ négative
        return float(get_price(m, option, N, exercise, optimize, threshold, method))

    # --- Vanna (∂²V / ∂S∂σ)
    p_up_up     = price_shift(+hS, +hSigma)
    p_up_down   = price_shift(+hS, -hSigma)
    p_down_up   = price_shift(-hS, +hSigma)
    p_down_down = price_shift(-hS, -hSigma)
    vanna = (p_up_up - p_up_down - p_down_up + p_down_down) / (4.0 * hS * hSigma)

    # --- Vomma (∂²V / ∂σ²)
    p_sig_up   = price_shift(0.0, +hSigma)
    p_sig_down = price_shift(0.0, -hSigma)
    vomma = (p_sig_up - 2.0 * base_price + p_sig_down) / (hSigma ** 2)

    # Protection contre les NaN / inf
    if not np.isfinite(vomma):
        vomma = 0.0
    if not np.isfinite(vanna):
        vanna = 0.0

    return float(vanna), float(vomma)

def compute_method_greeks(market, option, N, exercise, optimize, threshold, method):
    """
    Calcule les grecs pour une méthode donnée (Backward / Recursive)
    avec corrections Gamma/Vomma.
    """
    base_price = float(get_price(market, option, N, exercise, optimize, threshold, method))

    # Bumps
    hS = max(1e-4, 0.01 * market.S0)
    hSigma = max(1e-4, 0.005)
    hR = 1e-4
    hT = 1.0 / 365.0

    # Dérivées 1D
    dS = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "S0", method), shift=hS)
    dSigma = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "sigma", method), shift=hSigma)
    dRho = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "r", method), shift=hR)
    dTheta = OneDimDerivative(greek_wrapper, (market, option, N, exercise, optimize, threshold, "T", method), shift=hT)

    # Grecs primaires et secondaires
    Delta = dS.first(market.S0)
    Gamma = dS.second(market.S0)
    Vega  = dSigma.first(market.sigma)
    Rho   = dRho.first(market.r)
    Theta = -dTheta.first(market.T)

    Vanna, Vomma = finite_diff_2d(market, option, N, exercise, optimize, threshold, method,
                                  base_price, hS=hS, hSigma=hSigma)

    return {
        "Price": base_price,
        "Delta": float(Delta),
        "Gamma": float(Gamma),
        "Vega": float(Vega),
        "Theta": float(Theta),
        "Rho": float(Rho),
        "Vanna": float(Vanna),
        "Vomma": float(Vomma),
    }


def compute_greeks():
    """
    Fonction principale liée à Excel.
    Calcule les grecs via les deux méthodes 
    et les compare aux résultats Black-Scholes
    """

    (market, option, N, exercise, method, optimize, threshold, arbre_stock, arbre_proba, arbre_option, wb, sheet, S0, K, r, sigma, T, is_call, exdivdate, *_) = input_parameters()

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