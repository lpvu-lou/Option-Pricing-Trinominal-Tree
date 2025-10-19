import numpy as np
import xlwings as xw
import string
from models.market import Market
from models.option_trade import Option
from core_pricer import backward_pricing

def outil_am_vs_eu_excel():

    wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main 2/TrinomialAndBS_Pricer_V2.xlsm')
    sheet_name = "Am_vs_Eu_Test"
    sh = wb.sheets(sheet_name)

    # === PARAMETERS ===
    S0 = 100
    T = 1.0
    sigma = 0.2
    rates = [-0.01, 0.0, 0.01, 0.05]
    N = 200
    strikes = np.linspace(60, 140, 17)

    # === STORAGE ===
    results_call = {r: [] for r in rates}
    results_put = {r: [] for r in rates}

    for r in rates:
        for K in strikes:
            market = Market(S0=S0, r=r, sigma=sigma, T=T, dividends=[])
            # Call
            call_eu = Option(K=K, is_call=True)
            call_am = Option(K=K, is_call=True)
            price_eu, _, _ = backward_pricing(market, call_eu, N, exercise="european", optimize=False, threshold = 0)
            price_am, _, _ = backward_pricing(market, call_am, N, exercise="american", optimize=False, threshold = 0)
            results_call[r].append(price_am - price_eu)
            # Put
            put_eu = Option(K=K, is_call=False)
            put_am = Option(K=K, is_call=False)
            price_eu, _, _ = backward_pricing(market, put_eu, N, exercise="european", optimize=False, threshold = 0)
            price_am, _, _ = backward_pricing(market, put_am, N, exercise="american", optimize=False, threshold = 0)
            results_put[r].append(price_am - price_eu)

    # === WRITE RESULTS ===
    start_row = 2
    sh.range(f"A{start_row}").value = "Strike"
    sh.range(f"A{start_row+1}").options(transpose=True).value = strikes

    # Letter columns for Excel (B, C, D, ...)
    letters = list(string.ascii_uppercase)

    for idx, r in enumerate(rates):
        c1 = letters[1 + idx*2]  # e.g. B, D, F, H
        c2 = letters[2 + idx*2]  # e.g. C, E, G, I

        sh.range(f"{c1}1").value = f"r = {r*100:.0f}%"
        sh.range(f"{c1}{start_row}").value = "Call ΔV"
        sh.range(f"{c1}{start_row+1}").options(transpose=True).value = results_call[r]

        sh.range(f"{c2}{start_row}").value = "Put ΔV"
        sh.range(f"{c2}{start_row+1}").options(transpose=True).value = results_put[r]

    # === Summary Table ===
    summary_row = start_row + len(strikes) + 3
    sh.range(f"A{summary_row}").value = ["Type", "r(%)", "Mean Premium", "Max Premium"]
    row = summary_row + 1
    for r in rates:
        mean_call = np.mean(results_call[r])
        mean_put = np.mean(results_put[r])
        max_call = np.max(results_call[r])
        max_put = np.max(results_put[r])
        sh.range(f"A{row}").value = ["Call", r*100, mean_call, max_call]
        sh.range(f"A{row+1}").value = ["Put", r*100, mean_put, max_put]
        row += 2

    # === Simple charts ===
    call_chart = sh.charts.add(left=500, top=20, width=420, height=280)
    call_chart.set_source_data(
        sh.range(f"A{start_row}:{letters[len(rates)*2]}{start_row + len(strikes)}")
    )
    call_chart.name = "Call Premiums"
    call_chart.title = "American vs European Premium (Call)"

    put_chart = sh.charts.add(left=500, top=340, width=420, height=280)
    put_chart.set_source_data(
        sh.range(f"A{start_row}:{letters[len(rates)*2]}{start_row + len(strikes)}")
    )
    put_chart.name = "Put Premiums"
    put_chart.title = "American vs European Premium (Put)"

    sh.range("A1").value = "American vs European Test — No Dividends"
    sh.autofit()

if __name__ == "__main__":
    outil_am_vs_eu_excel()
