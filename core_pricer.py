import time
import numpy as np
import os
import xlwings as xw

from models.market import Market
from models.option_trade import Option
from models.tree import TrinomialTree
from utils.utils_bs import bs_price
from utils.utils_date import datetime_to_years
from models.backward_pricing import price_backward
from models.recursive_pricing import price_recursive, clear_recursive_cache  # 👈 added import


# -------------------------------------------------------------------------
# 1. Lecture des paramètres dans Excel
# -------------------------------------------------------------------------
def input_parameters():
    """
    Lit les paramètres du pricer depuis Excel.
    Retourne les objets nécessaires pour le pricing.
    """
    base_path = os.path.dirname(os.path.abspath(__file__))
    excel_path = os.path.join(base_path, "TrinomialAndBS_Pricer 2 (2).xlsm")
    wb = xw.Book(excel_path)
    sheet = wb.sheets['Param']

    # Paramètres de marché 
    S0 = float(sheet.range('Spot').value)
    r = sheet.range('Taux').value
    sigma = sheet.range('Vol').value
    rho = sheet.range('Rho').value
    lam = sheet.range('Lambda').value
    exdiv_raw = sheet.range('ExDivDate_Dividende').value

    # Paramètres de l’option
    K = sheet.range('Strike').value
    maturity_date = sheet.range('Maturity').value
    pricing_date = sheet.range('date_pricing').value
    is_call = (sheet.range('Call_Put').value == "Call")
    exercise = "european" if sheet.range('Exercice').value == "EU" else "american"

    # Paramètres de l’arbre 
    N = int(sheet.range('N').value)
    method = sheet.range('Methode_Pricing').value
    optimize = sheet.range('Pruning').value
    threshold = sheet.range('SeuilPruning').value

    # Options d’affichage 
    arbre_stock = sheet.range('AffichageStock').value
    arbre_proba = sheet.range('AffichageProba').value
    arbre_option = sheet.range('AffichageOption').value

    # Conversion des dates
    T = datetime_to_years(maturity_date, pricing_date)
    exdivdate = datetime_to_years(exdiv_raw, pricing_date)

    # Création des objets Market et Option
    market = Market(
        S0=S0,
        r=r,
        sigma=sigma,
        T=T,
        exdivdate=exdivdate,
        pricing_date=pricing_date,
        rho=rho,
        lam=lam
    )
    option = Option(K=K, is_call=is_call)

    return (market, option, N, exercise, method, optimize, threshold,
            arbre_stock, arbre_proba, arbre_option, wb, sheet,
            S0, K, r, sigma, T, rho, lam, is_call, exdivdate)


# -------------------------------------------------------------------------
# 2. Backward pricing
# -------------------------------------------------------------------------
def run_backward_pricing(market, option, N, exercise, optimize, threshold):
    """Calcule le prix de l’option via la méthode backward."""
    start = time.time()

    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()
    tree.compute_reach_probabilities()

    if optimize == "Oui":
        tree.prune_tree(threshold)

    price = price_backward(tree)
    elapsed = time.time() - start
    return price, elapsed, tree


# -------------------------------------------------------------------------
# 3. Recursive pricing (with cache clearing)
# -------------------------------------------------------------------------
def run_recursive_pricing(market, option, N, exercise, optimize, threshold):
    """
    Calcule le prix de l’option via la méthode récursive.
    Nettoie le cache après le pricing pour éviter les interférences
    avec les appels successifs (utilisés pour les Greeks).
    """
    start = time.time()

    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()
    tree.compute_reach_probabilities()

    if optimize == "Oui":
        tree.prune_tree(threshold)

    price = price_recursive(tree)
    elapsed = time.time() - start

    # ✅ Clear recursive cache for this tree
    clear_recursive_cache(tree)

    return price, elapsed, tree


# -------------------------------------------------------------------------
# 4. Black-Scholes reference
# -------------------------------------------------------------------------
def run_black_scholes(S0, K, r, sigma, T, is_call):
    """Calcule le prix Black-Scholes (sans dividende explicite ici)."""
    start = time.time()
    price = bs_price(S0, K, r, sigma, T, is_call)
    elapsed = time.time() - start
    return price, elapsed


# -------------------------------------------------------------------------
# 5. Main pricer
# -------------------------------------------------------------------------
def run_pricer():
    """
    Exécute le pricer complet selon la méthode choisie (Backward ou Recursive)
    et compare au modèle de Black-Scholes si applicable.
    """
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, rho, lam, is_call, exdivdate) = input_parameters()

    # Choix de la méthode d’arbre
    if method == "Backward":
        price, elapsed, tree = run_backward_pricing(market, option, N, exercise, optimize, threshold)
    else:
        price, elapsed, tree = run_recursive_pricing(market, option, N, exercise, optimize, threshold)

    # Black–Scholes
    if exercise == "european":
        bs_val, bs_time = run_black_scholes(S0, K, r, sigma, T, is_call)
    else:
        bs_val, bs_time = None, None

    return {
        "tree_price": price,
        "tree_time": elapsed,
        "bs_price": bs_val,
        "bs_time": bs_time,
        "tree": tree
    }
