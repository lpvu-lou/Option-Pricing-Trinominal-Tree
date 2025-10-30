def price_backward(tree):
    """
    Calcule le prix de l’option par récurrence arrière.
    """
    
    option = tree.option
    df = tree.df
    is_american = (tree.exercise == "american")

    # Valeur à maturité
    last_level = tree.tree[-1]
    for node in last_level:
        if node is not None:
            node.option_value = option.payoff(node.stock_price)

    # Sécurité d'accès pour les noeuds enfants
    def safe_val(level, idx):
        """
        Retourne la valeur de l’enfant si le nœud existe,
        sinon renvoie 0.0 (cas de pruning ou d’absence de noeud).
        """
        if 0 <= idx < len(level):
            child = level[idx]
            if child is not None and hasattr(child, "option_value"):
                return child.option_value
        return 0.0

    # Récurrence arrière
    for i in range(tree.N - 1, -1, -1):
        next_level = tree.tree[i + 1]
        level = tree.tree[i]
        level_proba = tree.proba_tree[i]  # noeud supprimé par pruning

        for j, node in enumerate(level):
            if node is None:
                continue

            # Probabilités déjà stockées
            try:
                pD, pM, pU, kprime = level_proba[j]
            except IndexError:
                continue  # cas rare : taille incohérente après pruning

            S = node.stock_price
            base = kprime + (i + 1)

            Vd = safe_val(next_level, base - 1)
            Vm = safe_val(next_level, base)
            Vu = safe_val(next_level, base + 1)

            hold = df * (pD * Vd + pM * Vm + pU * Vu)
            exer = option.payoff(S)

            node.option_value = max(hold, exer) if is_american else hold

    # Retourne la valeur à la racine
    root = tree.tree[0][0]
    return root.option_value
