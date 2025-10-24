import numpy as np
from models.probabilities import local_probabilities


def backward_pricing(tree):
    """
    Pricing backward pour options européennes et américaines.
    Version avec mémoïsation locale des probabilités (i, k) pour rester rapide
    i : colonne temps
    k : index relatif du nœud dans cette colonne (k = j - i)
    """

    N, df, option = tree.N, tree.df, tree.option

    prob_cache = {}

    def get_prob_and_kprime(i, k, spot_here):
        """
        Retourne (p_down, p_mid, p_up, kprime) pour le nœud (i,k).
        Met en cache pour éviter de recalculer.
        """
        key = (i, k)
        if key in prob_cache:
            return prob_cache[key]

        pD, pM, pU, kprime = local_probabilities(
            tree.market,
            tree.dt,
            tree.alpha,
            tree.exp_sig2_dt,
            spot_here,           # le spot du noeud courant
            tree.trunk[i + 1],   # spot médian de la colonne suivante
            i,
            k
        )
        prob_cache[key] = (pD, pM, pU, kprime)
        return pD, pM, pU, kprime

    # -------------------------------------------------
    # 2. Valeur terminale : payoff à maturité
    # -------------------------------------------------
    last_level = tree.levels[-1]
    for node in last_level:
        if node:
            node.option_value = option.payoff(node.spot)

    # -------------------------------------------------
    # 3. Récurrence arrière colonne par colonne
    #    On part de N-1 et on remonte jusqu'à 0
    # -------------------------------------------------
    for i in range(N - 1, -1, -1):
        next_level = tree.levels[i + 1]

        for j, node in enumerate(tree.levels[i]):
            if node is None:
                continue

            # indice relatif k = j - i (définit la "hauteur" du noeud dans la colonne)
            k = j - i

            # Probabilités locales et décalage kprime pour localiser les enfants
            pD, pM, pU, kprime = get_prob_and_kprime(i, k, node.spot)

            # Le noeud "milieu" auquel ce noeud se connecte dans la colonne i+1
            base = kprime + (i + 1)

            # Indices enfants (down, mid, up)
            idxs = [base - 1, base, base + 1]

            # Récupération vectorisée des valeurs des enfants.
            # Si l'enfant n'existe pas (None ou hors range), on prend 0.0
            vals = np.array([
                next_level[idx].option_value
                if 0 <= idx < len(next_level) and next_level[idx] else 0.0
                for idx in idxs
            ])

            # Valeur "hold" = espérance sous mesure risque-neutre, actualisée
            hold = df * np.dot([pD, pM, pU], vals)

            # Valeur d'exercice immédiat
            exer = option.payoff(node.spot)

            # Américain : max(hold, exercice), Européen : juste hold
            node.option_value = max(hold, exer) if tree.exercise == "american" else hold

    # -------------------------------------------------
    # 4. Le prix final est la valeur au nœud racine
    # -------------------------------------------------
    return tree.levels[0][0].option_value
