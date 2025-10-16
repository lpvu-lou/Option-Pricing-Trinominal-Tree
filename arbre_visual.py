import xlwings as xw
from market import Market
from option_trade import Option
from tree import TrinomialTree


def compare_and_display_in_excel(market, option, N):
    """Affiche les arbres sous forme triangulaire verticale dans Excel."""

    # --- Ouvrir le fichier Excel ---
    wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main/TrinomialAndBS_Pricer_V2.xlsm')
    sheet_prices = wb.sheets["Stock Prices"]
    sheet_reach = wb.sheets["Reach Probabilities"]
    sheet_eu = wb.sheets["European Option"]
    sheet_us = wb.sheets["American Option"]
    sheet_frontier = wb.sheets["Exercise Frontier"]

    # --- Nettoyage des feuilles ---
    for sh in [sheet_prices, sheet_reach, sheet_eu, sheet_us, sheet_frontier]:
        sh.clear_contents()
        for chart in sh.charts:
            chart.delete()

    # --- Construction des arbres ---
    tree_eu = TrinomialTree(market, option, N, exercise="european")
    tree_us = TrinomialTree(market, option, N, exercise="american")

    tree_us.compute_reach_probabilities()
    tree_us.price_backward()
    tree_eu.build_tree()
    tree_eu.price_backward()

    price_eu = tree_eu.tree[0][0].option_value
    price_us = tree_us.tree[0][0].option_value

    # --- Helper pour format vertical (colonne = step, ligne = état) ---
    def vertical_tree(tree, attr):
        """Transforme l’arbre pour affichage vertical dans Excel."""
        n = len(tree.tree)
        max_nodes = max(len(level) for level in tree.tree)
        matrix = [[""] * n for _ in range(2 * n + 1)]  # grille vide (plus grande pour centrer)
        center_row = n  # centre vertical

        for i, level in enumerate(tree.tree):  # i = colonne
            offset = len(level) // 2
            for j, node in enumerate(level):
                if node:
                    value = getattr(node, attr)
                    row = center_row - (j - offset)
                    matrix[row][i] = round(value, 6)
        return matrix

    # --- Arbre des prix du sous-jacent ---
    sheet_prices.range("A1").value = "Stock Price Tree"
    stock_matrix = vertical_tree(tree_us, "stock_price")
    sheet_prices.range("A2").value = stock_matrix

    # --- Arbre des probabilités d’atteinte ---
    sheet_reach.range("A1").value = "Reach Probability Tree"
    reach_matrix = vertical_tree(tree_us, "p_reach")
    sheet_reach.range("A2").value = reach_matrix

    # --- Arbres de valeurs EU et US ---
    sheet_eu.range("A1").value = f"European Option Tree (V₀={price_eu:.4f})"
    eu_matrix = vertical_tree(tree_eu, "option_value")
    sheet_eu.range("A2").value = eu_matrix

    sheet_us.range("A1").value = f"American Option Tree (V₀={price_us:.4f})"
    us_matrix = vertical_tree(tree_us, "option_value")
    sheet_us.range("A2").value = us_matrix

    # --- Frontière d’exercice ---
    frontier = []
    for i, level in enumerate(tree_us.tree):
        step_prices = [n.stock_price for n in level if n]
        step_values = [n.option_value for n in level if n]
        payoff_values = [option.payoff(s) for s in step_prices]
        exercised = [s for s, v, p in zip(step_prices, step_values, payoff_values) if abs(v - p) < 1e-8]
        if exercised:
            frontier.append((i, min(exercised)))
    sheet_frontier.range("A1").value = ["Step", "Exercise Boundary (S*)"]
    sheet_frontier.range("A2").value = frontier

    # --- Graphique de la frontière ---
    if frontier:
    # Create chart safely
        chart = sheet_frontier.charts.add(left=250, top=40, width=500, height=320)
        if isinstance(chart, tuple):  # macOS: xlwings sometimes returns (chart,)
                chart = chart[0]

    # Define the data range (A = Step, B = S*)
        data_range = sheet_frontier.range("A1").expand()

    # Set chart type explicitly (XY Scatter)
        chart.chart_type = "xy_scatter_lines"
        chart.set_source_data(data_range)
        chart.name = "Exercise Frontier"

    # --- macOS-friendly title + axis labels (in cells) ---
        sheet_frontier.range("D1").value = "Exercise Frontier (American Put)"
        sheet_frontier.range("D2").value = "X-axis: Step"
        sheet_frontier.range("D3").value = "Y-axis: Exercise Boundary S*"

    # --- Mise en forme basique ---
    for sh in [sheet_prices, sheet_reach, sheet_eu, sheet_us]:
        sh.range("A:ZZ").columns.autofit()
        sh.range("A:ZZ").api.HorizontalAlignment = -4108  # centré

    print("\n✅ Vertical trinomial trees exported successfully.")
    print(f"European price = {price_eu:.4f}")
    print(f"American price = {price_us:.4f}")
    print(f"Difference     = {price_us - price_eu:.4f}")


if __name__ == "__main__":
    S0 = 100
    K = 90
    r = 0.05
    sigma = 0.25
    T = 0.5
    N = 100

    market = Market(S0=S0, r=r, sigma=sigma, T=T, dividends=[])
    option = Option(K=K, is_call=False)
    compare_and_display_in_excel(market, option, N)
