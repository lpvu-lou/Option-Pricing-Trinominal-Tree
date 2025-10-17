import xlwings as xw
import numpy as np
from core_pricer import input_parameters, run_pricer as core_run_pricer


def display_trees(wb, tree, show_stock, show_reach, show_option):
    """
    Affiche les arbres dans des feuilles séparées
    """

    def ensure_sheet(name):
        """Retourne la feuille si elle existe, sinon la crée."""
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

    def write_tree(sheet, matrix):
        sheet.clear_contents()
        sheet.range("A2").value = matrix
        sheet.range("A:ZZ").columns.autofit()
        sheet.range("A:ZZ").api.HorizontalAlignment = -4108  # centré
        sheet.range("A1").select()

    if show_stock:
        sht_stock = ensure_sheet("Arbre Stock")
        stock_matrix = vertical_tree(tree, "stock_price")
        write_tree(sht_stock, "", stock_matrix)

    if show_option:
        sht_option = ensure_sheet("Arbre Option")
        option_matrix = vertical_tree(tree, "option_value")
        write_tree(sht_option, option_matrix)

    if show_reach:
        sht_reach = ensure_sheet("Arbre Proba")
        reach_matrix = vertical_tree(tree, "p_reach")
        write_tree(sht_reach, reach_matrix)

@xw.sub
def run_pricer():
    """Fonction principale appelée par le bouton 'PRICER' dans Excel."""
    wb = xw.Book('/Users/lanphuongvu/Downloads/Option-Pricing-main 2/TrinomialAndBS_Pricer_V2.xlsm')

    # Lecture des paramètres dans Excel
    (market, option, N, exercise, method, optimize, threshold, arbre_stock, arbre_proba, arbre_option, sheet, S0, K, r, sigma, T, is_call) = input_parameters()

    core_run_pricer()

    # Calcul des prix via core_pricer.run_pricer()
    results = core_run_pricer()

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
