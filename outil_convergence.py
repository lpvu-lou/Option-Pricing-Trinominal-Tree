import time
import warnings
import numpy as np
import xlwings as xw
from blackscholes import bs_price
from tree import TrinomialTree
from market import Market
from option_trade import Option

warnings.filterwarnings("ignore", category=RuntimeWarning)


def outil_convergence_excel(market: Market, option: Option, N_values, exercise="european"):
    wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main/TrinomialAndBS_Pricer_V2.xlsm')

    # si la feuille n'existe pas, la créer
    if "Convergence Python" not in [sh.name for sh in wb.sheets]:
        wb.sheets.add("Convergence Python")
    sheet = wb.sheets['Convergence Python']

    # Nettoyage de la feuille
    sheet.clear_contents()
    for chart in sheet.charts:
        chart.delete()

    # Titre 
    sheet.range("A1").value = "Convergence vers Black-Scholes (Arbre trinomial)"
    sheet.range("A1").font.bold = True
    sheet.range("A1").font.size = 18

    # Calcul des prix et erreurs
    bs = bs_price(market.S0, option.K, market.r, market.sigma,
                  market.T, is_call=option.is_call)
    tree_prices, times = [], []
    for N in N_values:
        tree = TrinomialTree(market, option, N, exercise)
        tree.build_tree()
        t0 = time.time()
        tree.price_backward()
        t1 = time.time()
        tree_prices.append(tree.tree[0][0].option_value)
        times.append(t1 - t0)

    errors = [abs(p - bs) for p in tree_prices]
    errors_N = [(p - bs) * N for p, N in zip(tree_prices, N_values)]

    # Remplissage des données dans Excel
    headers = ["N", "Prix Tree", "Prix BS", "|Tree - BS|",
               "Temps (s)", "(Tree - BS) × NbSteps"]
    data = list(zip(N_values, tree_prices, [bs]*len(N_values),
                    errors, times, errors_N))
    sheet.range("A3").value = headers
    sheet.range("A4").value = data
    sheet.range("A2").value = f"Prix BS de référence : {bs:.6f}"
    sheet.autofit()

    start_row, end_row = 4, 3 + len(N_values)

    width, height = 500, 300
    top_start = 45
    left_start = 850
    vertical_gap = height + 50
    horizontal_gap = width + 50

    # Chart 1: Tree vs BS 
    chart1 = sheet.charts.add(left=left_start, top=top_start, width=width, height=height)
    chart1.chart_type = "xy_scatter_smooth_no_markers"
    chart1.set_source_data(sheet.range(f"A3:C{end_row}"))
    chart1.title = "Tree vs BS"


    # Chart 2: Error vs N
    sheet.range("H3").value = ["N", "|Tree - BS|"]
    sheet.range("H4").value = list(zip(N_values, errors))
    chart2 = sheet.charts.add(left=left_start, top=top_start + vertical_gap, width=width, height=height)
    chart2.chart_type = "xy_scatter_smooth_no_markers"
    chart2.set_source_data(sheet.range(f"H3:I{end_row}"))
    chart2.title = "Erreur |Tree - BS| vs N"

    # Chart 3: Error * N vs N
    sheet.range("J3").value = ["N", "(Tree - BS) × NbSteps"]
    sheet.range("J4").value = list(zip(N_values, errors_N))
    chart3 = sheet.charts.add(left=left_start, top=top_start + 2 * vertical_gap, width=width, height=height)
    chart3.chart_type = "xy_scatter_smooth_no_markers"
    chart3.set_source_data(sheet.range(f"J3:K{end_row}"))
    chart3.title = "(Tree - BS) × NbSteps vs N"

    # Chart 4: Time vs N
    sheet.range("L3").value = ["N", "Temps (s)"]
    sheet.range("L4").value = list(zip(N_values, times))
    chart4 = sheet.charts.add(left=left_start, top=top_start + 3 * vertical_gap, width=width, height=height)
    chart4.chart_type = "xy_scatter_smooth_no_markers"
    chart4.set_source_data(sheet.range(f"L3:M{end_row}"))
    chart4.title = "Temps de calcul vs N"

    return tree_prices, bs, times

if __name__ == "__main__":
    market = Market(S0=100, r=0.05, sigma=0.25, T=0.5, dividends=None)
    option = Option(K=90, is_call=False)
    N_values = list(range(1, 201))
    outil_convergence_excel(market, option, N_values)
