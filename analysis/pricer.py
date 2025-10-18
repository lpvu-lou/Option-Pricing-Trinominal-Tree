import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import xlwings as xw
import numpy as np
from core_pricer import input_parameters, run_pricer as core_run_pricer


def display_trees(wb, tree, show_stock, show_reach, show_option):
    """
    Affiche les arbres dans des feuilles séparées
    """

    def ensure_sheet(name):
        """
        Retourne la feuille si elle existe, sinon la crée
        """
        try:
            return wb.sheets[name]
        except Exception:
            return wb.sheets.add(name)

    def vertical_tree(tree_obj, attr):
        """
        Transforme un arbre en matrice rectangulaire :
        - Colonnes = étapes de temps
        - Lignes = niveaux du nœud
        """
        n = len(tree_obj.tree)
        max_nodes = max(len(level) for level in tree_obj.tree)
        matrix = [[""] * n for _ in range(2 * n + 1)]
        center_row = n

        for i, level in enumerate(tree_obj.tree):
            offset = len(level) // 2
            for j, node in enumerate(level):
                if node:
                    value = getattr(node, attr)
                    row = center_row - (j - offset)
                    matrix[row][i] = round(value, 6)
        return matrix

    def write_tree(sheet, title, matrix):
        sheet.clear_contents()
        sheet.range("A1").value = title
        sheet.range("A2").value = matrix
        sheet.range("A:ZZ").columns.autofit()
        sheet.range("A:ZZ").api.HorizontalAlignment = -4108  # centré
        sheet.range("A1").select()

    if show_stock:
        sht_stock = ensure_sheet("Arbre Stock")
        stock_matrix = vertical_tree(tree, "stock_price")
        write_tree(sht_stock, "Stock Price Tree", stock_matrix)

    if show_option:
        sht_option = ensure_sheet("Arbre Option")
        option_matrix = vertical_tree(tree, "option_value")
        write_tree(sht_option, "Option Value Tree", option_matrix)

    if show_reach:
        sht_reach = ensure_sheet("Arbre Proba")
        reach_matrix = vertical_tree(tree, "p_reach")
        write_tree(sht_reach, "Reach Probability Tree", reach_matrix)

@xw.sub
def run_pricer():
    """
    Fonction principale appelée par le bouton 'PRICER' dans Excel
    """

    # Lecture des paramètres dans Excel
    (market, option, N, exercise, method, optimize, threshold, arbre_stock, arbre_proba, arbre_option, wb, sheet, S0, K, r, sigma, T, is_call, exdivdate) = input_parameters()
    
    # Calcul des prix via core_pricer.run_pricer()
    results = core_run_pricer()

    sheet.range('Prix_Tree').value = results['tree_price']
    sheet.range('Prix_Tree').number_format = '0.0000'

    sheet.range('Time_Tree').value = results['tree_time']
    sheet.range('Time_Tree').number_format = '0.000000'

    sheet.range('Prix_BS').value = results['bs_price']
    sheet.range('Prix_BS').number_format = '0.0000'

    sheet.range('Time_BS').value = results['bs_time']
    sheet.range('Time_BS').number_format = '0.000000'

    # Affichage des arbres si demandé
    display_trees(
        wb,
        results["tree"],
        show_stock=(arbre_stock == "Oui"),
        show_reach=(arbre_proba == "Oui"),
        show_option=(arbre_option == "Oui")
    )

    # Sauvegarde du fichier Excel
    wb.save()

if __name__ == '__main__':
    run_pricer()