from models.probabilities import local_probabilities

def price_backward(tree):
    """
    Calcul du prix de l’option par récurrence arrière.
    """
    last_level = tree.tree[-1]
    for node in last_level:
        if node is not None:
            node.option_value = tree.option.payoff(node.stock_price)

    def safe_val(level, idx):
        if 0 <= idx < len(level):
            child = level[idx]
            if child is not None and hasattr(child, "option_value"):
                return child.option_value
        return 0.0

    for i in range(tree.N - 1, -1, -1):
        next_level = tree.tree[i + 1]
        for j, node in enumerate(tree.tree[i]):
            if node is None:
                continue

            S = node.stock_price
            pD, pM, pU, kprime = local_probabilities(tree, i, j - i, S)
            base = kprime + (i + 1)

            Vd = safe_val(next_level, base - 1)
            Vm = safe_val(next_level, base)
            Vu = safe_val(next_level, base + 1)

            hold = tree.df * (pD * Vd + pM * Vm + pU * Vu)
            exer = tree.option.payoff(S)
            node.option_value = max(hold, exer) if tree.exercise == "american" else hold

    return tree.tree[0][0].option_value
