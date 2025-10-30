import sys
import os
import numpy as np
import matplotlib.pyplot as plt
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.utils_bs import bs_price
from core_pricer import (
    input_parameters,
    run_backward_pricing
)

def strike_test():
    # Lecture des paramètres depuis Excel
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()
    
    # Si la feuille n'existe pas, la créer
    if "Test Sur Param" not in [sh.name for sh in wb.sheets]:
        wb.sheets.add("Test Sur Param") 
    sheet_pr = wb.sheets["Test Sur Param"]

    # Nettoyage de la feuille
    for chart in sheet_pr.charts:
        chart.delete()
    sheet_pr.range("A4:M33").clear_contents()

    # Paramètres pour le test
    K_values = np.linspace(K-5, K+5, 30)
    bs_prices, tree_prices = [], []

    # Boucle principale
    for k in K_values:
        # Met à jour le strike
        option.K = k

        # Prix Black-Scholes
        bs_p = bs_price(S0, k, r, sigma, T, is_call)
        bs_prices.append(bs_p)

        # Prix par arbre trinomial
        price_tree, _, _ = run_backward_pricing(market, option, N, exercise, optimize=False, threshold=threshold)
        tree_prices.append(price_tree)

    bs_prices = np.array(bs_prices)
    tree_prices = np.array(tree_prices)
    diff = tree_prices - bs_prices

    for c in sheet_pr.charts:
        c.delete()
    sheet_pr.range("A5:M33").clear_contents()

    headers = ["Strike", "BS", "Tree", "Tree - BS"]
    data = np.column_stack((K_values, bs_prices, tree_prices, diff))
    start_row = 4
    sheet_pr.range(f"A{start_row}").value = headers
    sheet_pr.range(f"A{start_row+1}").value = data

    fig, ax1 = plt.subplots(figsize=(7, 4.5))

    ax1.plot(K_values, bs_prices, color="green", label="BS")
    ax1.plot(K_values, tree_prices, color="gold", label="Tree")
    ax1.set_xlabel("Strike (K)")
    ax1.set_ylabel("Option price")
    ax1.set_xlim(min(K_values) - 1, max(K_values) + 1)
    ax1.grid(True, alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(K_values, diff, color="red", label="Tree - BS")
    ax2.set_ylabel("Tree - BS")
    ax2.set_ylim(-0.8, 0.2)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    plt.title("Tree et Black-Scholes prix par rapport au strike")
    plt.tight_layout()

    sheet_pr.pictures.add(fig, name="Tree_vs_BS", update=True, left=300, top=60)

    plt.close(fig)

def run_strike_test():
    strike_test()

if __name__ == "__main__":
    run_strike_test()
    