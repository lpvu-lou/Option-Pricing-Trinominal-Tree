import math
from utils.utils_constants import MIN_PRICE
from utils.utils_dividends import get_dividend_on_step


def compute_reach_probabilities(tree):
    """
    Calcule et stocke la probabilité d’atteinte (p_reach) de chaque nœud de l’arbre.
    """

    # Réinitialisation de l’arbre et du tronc central
    tree.tree = []

    # Création du noeud racine 
    root = tree.Node(0, tree.market.S0, tree)
    root.p_reach = 1.0
    tree.tree.append([root])

    # Propagation vers l’avant
    for i in range(tree.N):
        prev_level = tree.tree[i]                         # Niveau courant
        next_level = [None] * (2 * (i + 1) + 1)           # Niveau suivant 
        mid_next = tree.trunk[i + 1]                      # Prix médian déjà stocké  

        # Récupération des probabilités locales déjà calculées
        level_proba = tree.proba_tree[i]

        for j, node in enumerate(prev_level):
            if node is None or node.p_reach == 0.0:
                continue  # Noeud inexistant ou jamais atteint, alors on passe

            if j >= len(level_proba):
                continue  

            # Récupération des probabilités locales pour ce noeud
            pD, pM, pU, kprime = level_proba[j] 

            # Propagation de la probabilité d’atteinte vers le niveau suivant
            k = j - i  # position relative par rapport au centre
            for dj, p in ((-1, pD), (0, pM), (+1, pU)):
                if p <= 0:
                    continue  # pas de propagation si probabilité nulle

                knext = k + dj
                idx = knext + (i + 1)  # position dans le prochain niveau

                if 0 <= idx < len(next_level):
                    # Création du nœud enfant si non existant
                    if next_level[idx] is None:
                        S_next = tree.trunk[i + 1] * (tree.alpha ** knext)
                        next_level[idx] = tree.Node(i + 1, S_next)

                    # Mise à jour de la probabilité d’atteinte cumulée
                    next_level[idx].p_reach += node.p_reach * p

        # Ajout du niveau complet à l’arbre
        tree.tree.append(next_level)


def prune_tree(tree, threshold=1e-7):
    """
    Supprime (met à None) les nœuds dont la probabilité d’atteinte p_reach est inférieure à un seuil donné.
    """
    for i, level in enumerate(tree.tree):
        for j, node in enumerate(level):
            if node is not None and node.p_reach < threshold:
                level[j] = None 
