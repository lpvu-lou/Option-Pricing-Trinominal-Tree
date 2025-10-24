import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import warnings
import numpy as np
import xlwings as xw
from utils.utils_bs import bs_price 
from models.tree import TrinomialTree
from models.market import Market
from models.option_trade import Option
from core_pricer import input_parameters, run_backward_pricing, run_recursive_pricing, run_black_scholes
warnings.filterwarnings("ignore", category=RuntimeWarning)


def outil_convergence_excel():
    """
    Crée un test de convergence entre le prix du modèle trinomial et le modèle Black-Scholes.
    Écrit les résultats dans la feuille Excel 'Test Convergence' et trace deux graphiques :
    1. Tree vs BS
    2. (Tree - BS) x NbSteps
    """
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()
    
    sheet_cv = wb.sheets("Test Convergence")

     # Prix de référence Black-Scholes
    bs_val, _ = run_black_scholes(S0, K, r, sigma, T, is_call)

    N_values = list(range(1, N + 1))

    # En-têtes et configuration
    headers = ["N", "Prix Tree", "Prix BS", "(Tree - BS) × NbSteps"]
    start_col = "V"
    start_row = 5
    data_start_row = start_row + 1
    end_row = start_row + N

    sheet_cv.range(f"{start_col}{start_row}:Y{start_row}").value = headers
    sheet_cv.range(f"{start_col}{start_row}:Y{start_row}").font.bold = True
    sheet_cv.range(f"{start_col}{data_start_row}:AB{end_row}").value = None

    # Calcul des prix Tree et erreurs
    data = []
    for n in N_values:
        if method == "Backward":
            price, _, _ = run_backward_pricing(market, option, n, exercise, optimize, threshold)
        else:
            price, _, _ = run_recursive_pricing(market, option, N, exercise, optimize, threshold)

        data.append([n, price, bs_val, (price - bs_val) * n])

    # Écriture des données
    sheet_cv.range(f"{start_col}{data_start_row}").value = data

    # Création des graphiques
    width, height = 600, 400
    top_start = 90
    left_start = 1700
    vertical_gap = height + 50
    horizontal_gap = width + 50

    # Chart 1: Tree vs BS
    chart1 = sheet_cv.charts.add(left=left_start, top=top_start, width=width, height=height)
    chart1.chart_type = "xy_scatter_smooth_no_markers"
    chart1.set_source_data(sheet_cv.range(f"{start_col}{start_row}:X{end_row}"))
    chart1.title = "Tree vs BS : Python"

    # Chart 2: (Tree - BS) x NbSteps
    helper_col = "AA"   
    helper_headers = ["N", "(Tree - BS) × NbSteps"]
    sheet_cv.range(f"{helper_col}{start_row}").value = helper_headers

    n_rng = sheet_cv.range(f"{start_col}{data_start_row}:{start_col}{end_row}").value
    err_rng = sheet_cv.range(f"Y{data_start_row}:Y{end_row}").value
    helper_data = [[n, e] for n, e in zip(n_rng, err_rng)]
    sheet_cv.range(f"{helper_col}{data_start_row}").value = helper_data

    chart2 = sheet_cv.charts.add(left=left_start, top=top_start + vertical_gap, width=width, height=height)
    chart2.chart_type = "xy_scatter_smooth_no_markers"
    chart2.set_source_data(sheet_cv.range(f"{helper_col}{start_row}:AB{end_row}")) 
    chart2.title = "(Tree - BS) × NbSteps vs N : Python"

    sheet_cv.range(f"AA{start_row}:AB{end_row}").font.color = (255, 255, 255)
    sheet_cv.autofit()

def run_cv():
    """
    Vérifie si les conditions permettent de lancer le test de convergence.
    """
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()
    
    sheet_cv = wb.sheets("Test Convergence")
    for chart in sheet_cv.charts:
        chart.delete()
    sheet_cv.range("A5:ZZ1048576").clear_contents()

    if (not exdivdate) and (exercise == "european"):
        outil_convergence_excel()
    else: 
        pass

if __name__ == "__main__":
    run_cv()