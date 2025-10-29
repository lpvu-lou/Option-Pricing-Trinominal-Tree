import math
from utils.utils_constants import MIN_PRICE


def compute_reach_probabilities(tree):
    """
    Calcule et stocke la probabilité d’atteinte de chaque noeud (p_reach)
    à partir des probabilités de transition déjà construites dans proba_tree.
    """

    # Réinitialisation de l’arbre et du tronc central
    tree.tree = []
    tree.trunk = [0.0] * (tree.N + 1)

    # Création du noeud racine 
    root = tree.Node(0, tree.market.S0)  
    root.p_reach = 1.0                   
    tree.tree.append([root])             
    tree.trunk[0] = tree.market.S0       

    # Propagation vers l’avant
    for i in range(tree.N):
        prev_level = tree.tree[i]                      
        next_level = [None] * (2 * (i + 1) + 1)       
        prev_mid = tree.trunk[i]                        

        # Calcul du nouveau prix central après un pas de temps 
        t_i, t_ip1 = i * tree.dt, (i + 1) * tree.dt
        div = tree.market.dividend_on_step(t_i, t_ip1, prev_mid)  
        mid_next = prev_mid * math.exp(tree.r * tree.dt) - div    
        tree.trunk[i + 1] = max(mid_next, MIN_PRICE)              

        # Récupération des probabilités locales pour ce niveau
        level_proba = tree.proba_tree[i]

        for j, node in enumerate(prev_level):
            if node is None or node.p_reach == 0.0:
                continue  # Noeud inexistant ou jamais atteint, alors on passe

            k = j - i  # Position relative du noeud par rapport au centre
            if j >= len(level_proba):
                continue  

            pD, pM, pU, kprime = level_proba[j]  # Probabilités locales

            # Propagation de la probabilité d’atteinte vers le niveau suivant
            for dj, p in ((-1, pD), (0, pM), (+1, pU)):
                if p <= 0:
                    continue  # Probabilité nulle : pas de propagation

                knext = k + dj
                idx = knext + (i + 1)  # Index du noeud dans la liste du prochain niveau

                if 0 <= idx < len(next_level):
                    # Si le noeud n’existe pas encore, on le crée
                    if next_level[idx] is None:
                        S_next = tree.trunk[i + 1] * (tree.alpha ** knext)
                        next_level[idx] = tree.Node(i + 1, S_next)

                    # On ajoute la contribution de probabilité depuis le noeud courant
                    next_level[idx].p_reach += node.p_reach * p

        # On ajoute le niveau calculé à l’arbre
        tree.tree.append(next_level)


def prune_tree(tree, threshold=1e-7):
    """
    Supprime (met à None) les nœuds dont la probabilité d’atteinte p_reach est inférieure à un seuil donné.
    """
    for i, level in enumerate(tree.tree):
        for j, node in enumerate(level):
            if node is not None and node.p_reach < threshold:
                level[j] = None 
