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
    wb = xw.Book('/Users/lanphuongvu/Downloads/TrinomialAndBS_Pricer_V2-2.xlsm')
    sheet = wb.sheets['Convergence Python']

    # === Clear previous content ===
    try:
        for ch in sheet.charts:
            ch.delete()
    except Exception:
        pass
    sheet.cells.clear()

    # === Header ===
    sheet.range("A1").value = "Convergence vers Black-Scholes (Arbre trinomial)"
    sheet.range("A1").font.bold = True

    # === Compute ===
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

    # === Write data ===
    headers = ["N", "Prix Tree", "Prix BS", "|Tree - BS|",
               "Temps (s)", "(Tree - BS) × NbSteps"]
    data = list(zip(N_values, tree_prices, [bs]*len(N_values),
                    errors, times, errors_N))
    sheet.range("A3").value = headers
    sheet.range("A4").value = data
    sheet.range("A2").value = f"Prix BS de référence : {bs:.6f}"
    sheet.autofit()

    start_row, end_row = 4, 3 + len(N_values)

    left_pos = sheet.range("P3").left        # start around column P
    top_start = sheet.range(f"A{start_row}").top
    width, height = 500, 250
    vertical_gap = height + 30

    # === Helper to make charts ===
    def add_chart(title, top, src_range, chart_type="xy_scatter_smooth"):
        ch = sheet.charts.add(left=50, top=top,
                              width=width, height=height)
        ch.chart_type = chart_type
        ch.set_source_data(src_range)
        ch.title = title
        return ch

    # === Chart 1: Tree vs BS ===
    # build small 3-column spill to ensure both series are contiguous
    ch = sheet.charts.add(left=100, top=100, width=500, height=300)
    ch.chart_type = "xy_scatter_smooth"
    ch.set_source_data(sheet.range("A3:C103"))
    ch.title = "Convergence des prix (Tree vs BS)"  # ✅ high-level title property only


    # === Chart 2: |Tree - BS| ===
    sheet.range("K3").value = ["N", "|Tree - BS|"]
    sheet.range("K4").value = list(zip(N_values, errors))
    add_chart("Différence absolue |Tree – BS|",
              top_start + vertical_gap,
              sheet.range(f"K3:L{end_row}"))

    # === Chart 3: (Tree - BS) × NbSteps ===
    sheet.range("M3").value = ["N", "(Tree - BS) × NbSteps"]
    sheet.range("M4").value = list(zip(N_values, errors_N))
    add_chart("(Tree – BS) × NbSteps",
              top_start + 2 * vertical_gap,
              sheet.range(f"M3:N{end_row}"))

    print("✅ Graphiques créés (macOS-safe, sans .api)")
    return tree_prices, bs, times


if __name__ == "__main__":
    market = Market(S0=100, r=0.05, sigma=0.25, T=0.5, dividends=None)
    option = Option(K=90, is_call=False)
    N_values = list(range(1, 121))
    outil_convergence_excel(market, option, N_values)
