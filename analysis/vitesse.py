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
from core_pricer import input_parameters, backward_pricing, recursive_pricing, black_scholes_price
warnings.filterwarnings("ignore", category=RuntimeWarning)

def outil_vitesse_excel():
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()
    
    # Si la feuille n'existe pas, la créer
    if "Test Vitesse" not in [sh.name for sh in wb.sheets]:
        wb.sheets.add("Test Vitesse") 
    sheet_vt = wb.sheets["Test Vitesse"]

    # Nettoyage de la feuille
    for chart in sheet_vt.charts:
        chart.delete()
    
    N_values = list(range(1, N+1))

    start_col_sp = "B"
    start_col_ap = "V"
    start_row = 5
    data_start_row = start_row + 1
    end_row = start_row + N

    width, height = 800, 400
    top_start = 100
    left_start = 450

    for n in N_values:
        _, temps_bp_s, _ = backward_pricing(market, option, n, exercise, False, threshold)
        _, temps_rec_s, _ = recursive_pricing(market, option, n, exercise, False, threshold)

        _, temps_bp_av, _ = backward_pricing(market, option, n, exercise, True, threshold)
        _, temps_rec_av, _ = recursive_pricing(market, option, n, exercise, True, threshold)

        sheet_vt.range(f"{start_col_sp}{start_row + n}").value = n
        sheet_vt.range(f"{start_col_ap}{start_row + n}").value = n

        sheet_vt.range(f"C{start_row + n}").value = temps_rec_s
        sheet_vt.range(f"W{start_row + n}").value = temps_rec_av

        sheet_vt.range(f"E{start_row + n}").value = temps_bp_s
        sheet_vt.range(f"Y{start_row + n}").value = temps_bp_av

    # Chart 1: Sans Pruning
    chart1 = sheet_vt.charts.add(left=left_start, top=top_start, width=width, height=height)
    chart1.chart_type = "xy_scatter_smooth_no_markers"
    chart1.set_source_data(sheet_vt.range(f"{start_col_sp}{start_row}:F{end_row}"))
    chart1.title = "Temps du calcul : Sans Pruning"

    # Chart 2: Avec Pruning
    chart2 = sheet_vt.charts.add(left=left_start + 1300, top=top_start, width=width, height=height)
    chart2.chart_type = "xy_scatter_smooth_no_markers"
    chart2.set_source_data(sheet_vt.range(f"{start_col_ap}{start_row}:Z{end_row}")) 
    chart2.title = "Temps du calcul : Avec Pruning"

    sheet_vt.autofit()

def run_vt():
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()
    
    outil_vitesse_excel()

if __name__ == "__main__":
    run_vt()