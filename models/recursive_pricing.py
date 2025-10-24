from models.probabilities import local_probabilities

def recursive_pricing(tree, i=0, k=0, cache=None):
    """
    Pricing récursif avec mémoïsation.
    Calcule le prix de l’option depuis le nœud (i, k).
    """
    if cache is None:
        cache = {}

    key = (i, k)
    if key in cache:
        return cache[key]

    # Cas terminal
    if i >= tree.N:
        node = tree.levels[-1][k + i] if 0 <= k + i < len(tree.levels[-1]) else None
        val = 0.0 if node is None else tree.option.payoff(node.spot)
        cache[key] = val
        return val

    # Nœud courant
    node = tree.levels[i][k + i] if 0 <= k + i < len(tree.levels[i]) else None
    if node is None:
        cache[key] = 0.0
        return 0.0

    # Probabilités locales
    pD, pM, pU, kprime = local_probabilities(
        tree.market, tree.dt, tree.alpha, tree.exp_sig2_dt,
        node.spot, tree.trunk[i + 1], i, k
    )
    kprime = max(-(i + 1), min(i + 1, kprime))

    # Récursion
    Vd = recursive_pricing(tree, i + 1, kprime - 1, cache)
    Vm = recursive_pricing(tree, i + 1, kprime, cache)
    Vu = recursive_pricing(tree, i + 1, kprime + 1, cache)

    hold = tree.df * (pD * Vd + pM * Vm + pU * Vu)
    exer = tree.option.payoff(node.spot)
    val = max(hold, exer) if tree.exercise == "american" else hold

    cache[key] = val
    return val
