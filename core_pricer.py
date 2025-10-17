import xlwings as xw
import time
import datetime as dt
import math
import numpy as np

from models.market import Market
from models.option_trade import Option
from models.tree import TrinomialTree
from utils.utils_bs import bs_price
from models.node import Node
from utils.utils_date import datetime_to_years 

def input_parameters():
    """Lit les paramètres du pricer depuis Excel."""
    
    # Ouvre le fichier Excel
    wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main 2/TrinomialAndBS_Pricer_V2.xlsm')
    sheet = wb.sheets['Paramètres']

    # ====== Paramètres du marché ======
    S0 = float(sheet.range('Spot').value)
    r = sheet.range('Taux').value
    sigma = sheet.range('Volatilité').value
    rho = sheet.range('Rho').value
    lam = sheet.range('Lambda').value
    exdiv_raw = sheet.range('ExDivDate_Dividende').value

    # ====== Paramètres de l’option ======
    K = sheet.range('Strike').value
    maturity_date = sheet.range('Maturité').value
    pricing_date = sheet.range('date_pricing').value
    is_call = (sheet.range('Call_Put').value == "Call")
    exercise = "european" if sheet.range('Exercice').value == "EU" else "american"

    # ====== Paramètres de l’arbre ======
    N = int(sheet.range('N').value)
    method = sheet.range('Methode_Pricing').value
    optimize = sheet.range('Pruning').value
    threshold = sheet.range('seuil').value

    # ====== Options d’affichage ======
    arbre_stock = sheet.range('AffichageStock').value
    arbre_proba = sheet.range('AffichageReach').value
    arbre_option = sheet.range('AffichageOption').value

    # ====== Conversion des dates ======
    # Convertir la maturité et les ex-div en temps (années)
    T = datetime_to_years(maturity_date, pricing_date)
    exdivdate = datetime_to_years(exdiv_raw, pricing_date)

    # ====== Création du marché et de l’option ======
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

def backward_pricing(market, option, N, exercise, optimize, threshold):
    """Prix de l’option par la méthode backward."""
    start = time.time()

    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()

    if optimize == "Oui":
        tree.prune_tree(threshold, inplace=True)

    tree.compute_reach_probabilities()
    tree.price_backward()

    elapsed = time.time() - start
    return tree.tree[0][0].option_value, elapsed, tree


def recursive_pricing(market, option, N, exercise, optimize, threshold):
    """Prix de l’option par la méthode récursive."""
    start = time.time()

    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()

    if optimize == "Oui":
        tree.prune_tree(threshold, inplace=True)

    price = tree.price_recursive()

    elapsed = time.time() - start
    return price, elapsed, tree


def black_scholes_price(S0, K, r, sigma, T, is_call):
    """Prix Black-Scholes (sans dividendes discrets)."""
    start = time.time()
    price = bs_price(S0, K, r, sigma, T, is_call)
    elapsed = time.time() - start
    return price, elapsed

def run_pricer():
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()

    # --- Sélection de la méthode ---
    if method == "Backward":
        price, elapsed, tree = backward_pricing(market, option, N, exercise, optimize, threshold)
    else:
        price, elapsed, tree = recursive_pricing(market, option, N, exercise, optimize, threshold)

    # --- Calcul du prix Black-Scholes ---
    if (not exdivdate) and (exercise == "european"):
        bs_val, bs_time = black_scholes_price(S0, K, r, sigma, T, is_call)
    else:
        bs_val, bs_time = None, None

    return {
        "tree_price": price,
        "tree_time": elapsed,
        "bs_price": bs_val,
        "bs_time": bs_time,
        "tree": tree
    }

run_pricer()