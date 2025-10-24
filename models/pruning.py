import math
from models.probabilities import local_probabilities
from utils.utils_constants import MIN_PRICE

def compute_reach_probabilities(tree):
    """
    Calcule et stocke la probabilité d’atteinte (p_reach)
    """
    tree.tree = []
    tree.trunk = [0.0] * (tree.N + 1)

    root = tree.Node(0, tree.market.S0)
    root.p_reach = 1.0
    tree.tree.append([root])
    tree.trunk[0] = tree.market.S0

    for i in range(tree.N):
        prev_level = tree.tree[i]
        next_level = [None] * (2 * (i + 1) + 1)

        prev_mid = tree.trunk[i]
        t_i, t_ip1 = i * tree.dt, (i + 1) * tree.dt
        div = tree.market.dividend_on_step(t_i, t_ip1, prev_mid)
        mid_next = prev_mid * math.exp(tree.r * tree.dt) - div
        tree.trunk[i + 1] = max(mid_next, MIN_PRICE)

        for j, node in enumerate(prev_level):
            if node is None or node.p_reach == 0.0:
                continue

            k = j - i
            pD, pM, pU, kprime = local_probabilities(tree, i, k, node.stock_price)

            for dj, p in ((-1, pD), (0, pM), (+1, pU)):
                if p <= 0:
                    continue
                knext = k + dj
                idx = knext + (i + 1)
                if 0 <= idx < len(next_level):
                    if next_level[idx] is None:
                        S_next = tree.trunk[i + 1] * (tree.alpha ** knext)
                        next_level[idx] = tree.Node(i + 1, S_next)
                    next_level[idx].p_reach += node.p_reach * p

        tree.tree.append(next_level)


def prune_tree(tree, threshold=1e-7):
    for i, level in enumerate(tree.tree):
        for j, node in enumerate(level):
            if node is not None and node.p_reach < threshold:
                level[j] = None
