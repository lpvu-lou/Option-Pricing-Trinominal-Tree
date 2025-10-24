from typing import Optional
import math

class Node:
    """
    Représente un nœud d’un arbre trinomial
    """

    def __init__(self, time_index: int, stock_price: float):
        self.time_index = time_index      # indice de temps (0..N)
        self.stock_price = stock_price    # prix du sous-jacent à ce noeud
        self.option_value = None          # valeur de l'option (à calculer)
        self.p_reach = 0.0                # probabilité d'atteindre ce noeud
