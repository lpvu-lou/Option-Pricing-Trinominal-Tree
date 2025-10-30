import sys
import os
import xlwings as xw

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core_pricer import input_parameters, run_pricer as core_run_pricer

def display_trees(wb, tree, show_stock, show_reach, show_option, threshold=1e-7):
    """
    Affiche les différents arbres dans Excel :
    - Arbre des prix du sous-jacent
    - Arbre des probabilités d’atteinte
    - Arbre des valeurs d’option
    - Arbres des probabilités locales (p_up, p_mid, p_down) si demandé
    """

    def ensure_sheet(name):
        """Renvoie la feuille si elle existe, sinon la crée."""
        try:
            return wb.sheets[name]
        except Exception:
            return wb.sheets.add(name)

    def vertical_tree(levels, attr, decimals=6):
        """
        Convertit un arbre en matrice pour affichage dans Excel.
        - Colonnes = étapes de temps
        - Lignes = niveaux de nœuds
        - Masque les valeurs faibles si hide_small=True.
        """
        n = len(levels)
        matrix = [[""] * n for _ in range(2 * n + 1)]
        center_row = n

        for i, level in enumerate(levels):
            offset = len(level) // 2
            for j, node in enumerate(level):
                if not node:
                    continue
                value = getattr(node, attr, None)
                if value is None:
                    continue
                val = round(value, decimals)
                row = center_row - (j - offset)
                matrix[row][i] = val
        return matrix

    def write_tree(sheet, title, matrix):
        """Efface et écrit la matrice dans une feuille Excel."""
        sheet.clear_contents()
        sheet.range("A1").value = title
        sheet.range("A2").value = matrix
        sheet.range("A:ZZ").columns.autofit()

    levels = getattr(tree, "levels", getattr(tree, "tree", []))

    # Arbre du sous-jacent
    if show_stock:
        sht_stock = ensure_sheet("Arbre Stock")
        stock_matrix = vertical_tree(levels, "spot", decimals=4)
        write_tree(sht_stock, "Stock Price Tree", stock_matrix)

    # Arbre des valeurs d’option 
    if show_option:
        sht_option = ensure_sheet("Arbre Option")
        option_matrix = vertical_tree(levels, "option_value", decimals=6)
        write_tree(sht_option, "Option Value Tree", option_matrix)

    # Arbre des probabilités d’atteinte
    if show_reach:
        sht_reach = ensure_sheet("Arbre Proba")
        reach_matrix = vertical_tree(levels, "p_reach", decimals=10)
        write_tree(sht_reach, "Reach Probability Tree", reach_matrix)

        # Probabilités locales (p_up, p_mid, p_down)
        first_node = levels[0][0] if levels and levels[0] else None
        if first_node and hasattr(first_node, "p_up"):
            sht_pup = ensure_sheet("Arbre p_up")
            sht_pmid = ensure_sheet("Arbre p_mid")
            sht_pdown = ensure_sheet("Arbre p_down")

            p_up_matrix = vertical_tree(levels, "p_up", decimals=6)
            p_mid_matrix = vertical_tree(levels, "p_mid", decimals=6)
            p_down_matrix = vertical_tree(levels, "p_down", decimals=6)

            write_tree(sht_pup, "Local Probabilities (p_up)", p_up_matrix)
            write_tree(sht_pmid, "Local Probabilities (p_mid)", p_mid_matrix)
            write_tree(sht_pdown, "Local Probabilities (p_down)", p_down_matrix)


@xw.sub
def run_pricer():
    """
    Fonction principale appelée par le bouton 'PRICER' dans Excel :
    - Lit les paramètres
    - Calcule les prix
    - Affiche les résultats et les arbres
    """
    # Lecture des paramètres
    (market, option, N, exercise, method, optimize, threshold,
     arbre_stock, arbre_proba, arbre_option, wb, sheet,
     S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()

    # Calcul du prix
    results = core_run_pricer()

    # Écriture des résultats
    sheet.range('Prix_Tree').value = results['tree_price']
    sheet.range('Prix_Tree').number_format = '0.0000'

    sheet.range('Time_Tree').value = results['tree_time']
    sheet.range('Time_Tree').number_format = '0.000000'

    sheet.range('Prix_BS').value = results['bs_price']
    sheet.range('Prix_BS').number_format = '0.0000'

    sheet.range('Time_BS').value = results['bs_time']
    sheet.range('Time_BS').number_format = '0.000000'

    # Affichage des arbres
    display_trees(
        wb,
        results["tree"],
        show_stock=(arbre_stock == "Oui"),
        show_reach=(arbre_proba == "Oui"),
        show_option=(arbre_option == "Oui"),
        threshold=threshold
    )

    wb.save()

if __name__ == '__main__':
    run_pricer()