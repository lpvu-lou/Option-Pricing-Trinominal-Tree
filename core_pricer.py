import os
import time
import xlwings as xw
import datetime as dt

from models.market import Market
from models.option_trade import Option
from models.tree import TrinomialTree
from models.pruning import compute_reach_probabilities, prune_tree
from utils.utils_bs import bs_price
from utils.utils_date import datetime_to_years

def input_parameters():
    """
    Lit les paramètres du pricer depuis le fichier Excel.
    Retourne les objets nécessaires pour le pricing.
    """
    # Ouvre le classeur Excel contenant les paramètres
    wb = xw.Book('/Users/lanphuongvu/Downloads/TrinomialAndBS_Pricer.xlsm')
    sheet = wb.sheets['Param']

    # Paramètres du marché 
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
    arbre_proba = sheet.range('AffichageReach').value
    arbre_option = sheet.range('AffichageOption').value

    # Conversion des dates
    T = datetime_to_years(maturity_date, pricing_date)
    exdivdate = datetime_to_years(exdiv_raw, pricing_date)

    market = Market(
        S0=S0,
        r=r,
        sigma=sigma,
        T=T,
        dividends=None,
        exdivdate=exdivdate,
        pricing_date=pricing_date,
        rho=rho,
        lam=lam
    )

    option = Option(K=K, is_call=is_call)

    return (market, option, N, exercise, method, optimize, threshold,
            arbre_stock, arbre_proba, arbre_option, wb, sheet,
            S0, K, r, sigma, T, is_call, exdivdate)

from models.probabilities import local_probabilities  # <-- we need this


def attach_local_probabilities(tree):
    """
    For every node that still exists in tree.tree (after pruning, etc),
    compute and store p_down, p_mid, p_up on that node.
    We skip the last time step because it has no outgoing transitions.
    """
    # get levels list (tree.tree in your class)
    levels = getattr(tree, "levels", getattr(tree, "tree", []))
    if not levels:
        return

    # iterate on all but last column
    for i, level in enumerate(levels[:-1]):
        for k, node in enumerate(level):
            # some pruned trees may have 'None' placeholders
            if node is None:
                continue
            # node.stock_price must exist; if it's named differently in Node, adjust here
            stock_attr = "stock_price"
            if not hasattr(node, stock_attr):
                # fallback to "spot" etc. if needed
                if hasattr(node, "spot"):
                    stock_attr = "spot"
                elif hasattr(node, "price"):
                    stock_attr = "price"
                else:
                    # can't compute probs for this node
                    continue

            S_i_k = getattr(node, stock_attr)

            pD, pM, pU, kprime = local_probabilities(tree, i, k, S_i_k)

            node.p_down = pD
            node.p_mid = pM
            node.p_up = pU
            node.kprime = kprime


def run_backward_pricing(market, option, N, exercise, optimize, threshold):
    """Calcule le prix de l’option via la méthode backward"""
    start = time.time()

    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()

    compute_reach_probabilities(tree)

    if optimize == "Oui":
        prune_tree(tree, threshold)
    
    attach_local_probabilities(tree)

    price = tree.price_backward()
    elapsed = time.time() - start
    return price, elapsed, tree


def run_recursive_pricing(market, option, N, exercise, optimize, threshold):
    """Calcule le prix de l’option via la méthode récursive"""
    start = time.time()

    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()
    compute_reach_probabilities(tree)

    if optimize == "Oui":
        prune_tree(tree, threshold)

    attach_local_probabilities(tree)
    
    price = tree.price_recursive()
    elapsed = time.time() - start
    return price, elapsed, tree


def run_black_scholes(S0, K, r, sigma, T, is_call):
    """Calcule le prix Black-Scholes sans dividendes"""
    start = time.time()
    price = bs_price(S0, K, r, sigma, T, is_call)
    elapsed = time.time() - start
    return price, elapsed


def run_pricer():
    """
    Exécute le pricer complet selon la méthode choisie (Backward ou Recursive)
    et compare au modèle de Black-Scholes si applicable.
    """
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()

    if method == "Backward":
        price, elapsed, tree = run_backward_pricing(market, option, N, exercise, optimize, threshold)
    else:
        price, elapsed, tree = run_recursive_pricing(market, option, N, exercise, optimize, threshold)

    if (not exdivdate) and (exercise == "european"):
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
