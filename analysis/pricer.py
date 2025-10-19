import sys
import os
import xlwings as xw
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_pricer import input_parameters, run_pricer as core_run_pricer


def display_trees(wb, tree, show_stock, show_reach, show_option, threshold=1e-7):
    """
    Affiche les différents arbres dans Excel : Arbre du stock, de la probabilité, et de la valeur d’option.
    """

    def ensure_sheet(name):
        """Renvoie la feuille si elle existe, sinon la crée."""
        try:
            return wb.sheets[name]
        except Exception:
            return wb.sheets.add(name)

    def vertical_tree(tree_obj, attr, decimals=8, hide_small=False):
        """
        Transforme un arbre en matrice pour affichage dans Excel :
        - Colonnes = étapes de temps
        - Lignes = niveaux de nœuds
        - Si hide_small=True : valeurs < threshold ou None → ""
        """
        n = len(tree_obj.tree)
        max_nodes = max(len(level) for level in tree_obj.tree)
        matrix = [[""] * n for _ in range(2 * n + 1)]
        center_row = n  # centre du tableau

        for i, level in enumerate(tree_obj.tree):
            offset = len(level) // 2
            for j, node in enumerate(level):
                if not node:
                    continue
                value = getattr(node, attr, "")
                if value is None:
                    continue

                # Masquer les petites valeurs si demandé
                if hide_small:
                    val = "" if abs(value) < threshold else round(value, decimals)
                else:
                    val = round(value, decimals)
                row = center_row - (j - offset)
                matrix[row][i] = val
        return matrix

    def write_tree(sheet, title, matrix):
        """
        Efface et écrit la matrice dans une feuille Excel
        """
        sheet.clear_contents()
        sheet.range("A1").value = title
        sheet.range("A2").value = matrix
        sheet.range("A:ZZ").columns.autofit()
        sheet.range("A1").select()

    # Arbre des prix du sous-jacent 
    if show_stock:
        sht_stock = ensure_sheet("Arbre Stock")
        stock_matrix = vertical_tree(tree, "stock_price", decimals=4, hide_small=False)
        write_tree(sht_stock, "Stock Price Tree", stock_matrix)

    # Arbre des valeurs d’option 
    if show_option:
        sht_option = ensure_sheet("Arbre Option")
        option_matrix = vertical_tree(tree, "option_value", decimals=6, hide_small=False)
        write_tree(sht_option, "Option Value Tree", option_matrix)

    # Arbre des probabilités de reach
    if show_reach:
        sht_reach = ensure_sheet("Arbre Proba")
        reach_matrix = vertical_tree(tree, "p_reach", decimals=10, hide_small=True)
        write_tree(sht_reach, "Reach Probability Tree", reach_matrix)

def display_exercise_frontier(wb, tree, option):
    """
    Trace la frontière d'exercice (S*) pour une option américaine dans Excel.
    """
    sheet = wb.sheets["Exercice Frontier"]
    
    # Détermination de la frontière
    frontier_data = []
    for i, level in enumerate(tree.tree):
        step_prices = [n.stock_price for n in level if n]
        step_values = [n.option_value for n in level if n]
        payoff_values = [option.payoff(s) for s in step_prices]

        # Identifier les nœuds où la valeur ≈ payoff (exercice optimal)
        exercised = [s for s, v, p in zip(step_prices, step_values, payoff_values)
                     if abs(v - p) < 1e-8]

        if exercised:
            frontier_data.append((i, min(exercised)))

    frontier_data = sorted(frontier_data, key=lambda x: x[0])

    # Écrire les données dans Excel
    sheet.range("A3").value = ["N", "Frontière (S*)"]
    sheet.range("A4").value = frontier_data
    last_row = sheet.range("A3").end("down").row

    # Création du graphique
    chart = sheet.charts.add(left=200, top=37, width=500, height=320)
    chart.chart_type = "xy_scatter_smooth_no_markers"
    chart.set_source_data(sheet.range(f"A3:B{last_row}"))
    chart.name = "Exercise Frontier"

@xw.sub
def run_pricer():
    """
    Fonction principale appelée par le bouton 'PRICER' dans Excel.
    Lit les paramètres, calcule les prix, et affiche les résultats.
    """
    # Lecture des paramètres depuis Excel
    (market, option, N, exercise, method, optimize, threshold,
        arbre_stock, arbre_proba, arbre_option, wb, sheet,
        S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()

    # Calcul du prix via le module core_pricer
    results = core_run_pricer()

    # Écriture des résultats dans la feuille Excel
    sheet.range('Prix_Tree').value = results['tree_price']
    sheet.range('Prix_Tree').number_format = '0.0000'

    sheet.range('Time_Tree').value = results['tree_time']
    sheet.range('Time_Tree').number_format = '0.000000'

    sheet.range('Prix_BS').value = results['bs_price']
    sheet.range('Prix_BS').number_format = '0.0000'

    sheet.range('Time_BS').value = results['bs_time']
    sheet.range('Time_BS').number_format = '0.000000'

    # Affichage des arbres selon les paramètres
    display_trees(
        wb,
        results["tree"],
        show_stock=(arbre_stock == "Oui"),
        show_reach=(arbre_proba == "Oui"),
        show_option=(arbre_option == "Oui"),
        threshold=threshold
    )

    # Affichage de la frontière d’exercice si applicable
    frontier_sheet = wb.sheets["Exercice Frontier"]
    for chart in frontier_sheet.charts:
        chart.delete()

    # Effacer toutes les cellules sauf A1
    used_range = frontier_sheet.used_range
    if used_range:
        last_row = used_range.last_cell.row
        last_col = used_range.last_cell.column

        if last_row > 1 or last_col > 1:
            frontier_sheet.range("A2:ZZ1048576").clear_contents()
            frontier_sheet.range("B1:ZZ1").clear_contents()

    if exercise == "american":
        display_exercise_frontier(wb, results["tree"], option)
    else:
        pass

    # Sauvegarde du fichier Excel
    wb.save()

if __name__ == '__main__':
    run_pricer()