# Recuperer des donnees dans un Excel et utiliser ces donnees pour faire des calculs en utilisant xlwings

import xlwings as xw
from market import Market
from option_trade import Option
from tree import TrinomialTree
import math
import numpy as np
from blackscholes import bs_price
from node import Node
import time
import datetime as dt

def input_parameters():
    """Fonction pour lire les paramètres depuis l’Excel"""
    wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main 2/TrinomialAndBS_Pricer_V2.xlsm')
    sheet = wb.sheets['Paramètres']
    
    # ======= Lire les paramètres =======
    # Paramètres du marché
    S0 = sheet.range('Spot').value
    r = sheet.range('Taux').value
    sigma = sheet.range('Volatilité').value

    # Paramètres de l’option
    K = sheet.range('Strike').value
    maturity_date = sheet.range('Maturité').value
    is_call = (sheet.range('Call_Put').value == "Call")
    exercise = ["european" if sheet.range('Exercice').value == "EU" else "american"][0]

    # Paramètres de l’arbre
    pricing_date = sheet.range('date_pricing').value
    N = int(sheet.range('N').value)

    # Methode de calcul
    method = sheet.range('Methode_Pricing').value  # Recursive ou Backward

    # Optimisation
    optimize = sheet.range('Pruning').value  
    threshold = sheet.range('seuil').value

    # Afficher les arbres
    arbre_stock = sheet.range('AffichageStock').value
    arbre_proba = sheet.range('AffichageReach').value
    arbre_option = sheet.range('AffichageOption').value

    # Calcul du temps à maturité
    if isinstance(maturity_date, dt.datetime) and isinstance(pricing_date, dt.datetime):
        T = (maturity_date - pricing_date).days / 365.0
        if T < 0:
            raise ValueError("La date de maturité doit être postérieure à la date de pricing.")
    else:
        raise ValueError("Les dates doivent être au format datetime.")

    market = Market(S0=S0, r=r, sigma=sigma, T=T, dividends=None)
    option = Option(K=K, is_call=is_call)
    
    return market, option, N, exercise, method, optimize, threshold, arbre_stock, arbre_proba, arbre_option, sheet, S0, K, r, sigma, T, is_call

# ======= Arbre Trinomial Pricing =======
def backward_pricing(market, option, N, exercise, optimize, threshold):
    """Prix de l’option par la méthode backward"""
    start_time = time.time()
    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()
    if optimize == "Oui":
        tree.prune(threshold)
    tree.compute_reach_probabilities()
    tree.price_backward()
    end_time = time.time()
    elapsed_time = end_time - start_time
    return tree.tree[0][0].option_value, elapsed_time, tree

def recursive_pricing(market, option, N, exercise):
    """Prix de l’option par la méthode récursive"""
    start_time = time.time()
    tree = TrinomialTree(market, option, N, exercise)
    tree.build_tree()
    price = tree.price_recursive()
    end_time = time.time()
    elapsed_time = end_time - start_time
    return price, elapsed_time, tree

# ======= Prix Black-Scholes =======
def black_scholes_price(S0, K, r, sigma, T, is_call):
    """Calcul du prix de l’option par la formule de Black-Scholes"""
    start_time = time.time()
    price = bs_price(S0, K, r, sigma, T, is_call)
    end_time = time.time()
    elapsed_time = end_time - start_time
    return price, elapsed_time

def run_pricer():
    market, option, N, exercise, method, optimize, threshold, arbre_stock, arbre_proba, arbre_option, sheet, S0, K, r, sigma, T, is_call = input_parameters()
    if method == "Backward":
        price, elapsed_time, tree = backward_pricing(market, option, N, exercise, optimize, threshold)
    else:
        price, elapsed_time, tree = recursive_pricing(market, option, N, exercise)
    bs_price, bs_time = black_scholes_price(S0, K, r, sigma, T, is_call)

    sheet.range('Prix_Tree').value = float(price)
    sheet.range('Prix_Tree').number_format = '0.0000'
    sheet.range('Time_Tree').value = elapsed_time
    sheet.range('Time_Tree').number_format = '0.000000'
    sheet.range('Prix_BS').value = float(bs_price)
    sheet.range('Prix_BS').number_format = '0.0000'
    sheet.range('Time_BS').value = bs_time
    sheet.range('Time_BS').number_format = '0.000000'

    return {
        "tree_price": price,
        "tree_time": elapsed_time,
        "bs_price": bs_price,
        "bs_time": bs_time,
        "tree": tree
    }
