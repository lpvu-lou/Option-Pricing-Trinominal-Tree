from models.probabilities import local_probabilities

def price_recursive(tree, i=0, k=0, _cache=None):
    if _cache is None:
        _cache = {}

    key = (i, k)
    if key in _cache:
        return _cache[key]

    if i >= tree.N:
        if 0 <= k + i < len(tree.tree[i]):
            node = tree.tree[i][k + i]
            val = 0.0 if node is None else tree.option.payoff(node.stock_price)
        else:
            val = 0.0
        _cache[key] = val
        return val

    if 0 <= k + i < len(tree.tree[i]):
        node = tree.tree[i][k + i]
        if node is None:
            _cache[key] = 0.0
            return 0.0
    else:
        _cache[key] = 0.0
        return 0.0

    S = node.stock_price
    pD, pM, pU, kprime = local_probabilities(tree, i, k, S)
    kprime = max(-(i + 1), min(i + 1, kprime))

    Vd = price_recursive(tree, i + 1, kprime - 1, _cache)
    Vm = price_recursive(tree, i + 1, kprime, _cache)
    Vu = price_recursive(tree, i + 1, kprime + 1, _cache)

    hold = tree.df * (pD * Vd + pM * Vm + pU * Vu)
    exer = tree.option.payoff(S)
    val = max(hold, exer) if tree.exercise == "american" else hold

    _cache[key] = val
    return val
