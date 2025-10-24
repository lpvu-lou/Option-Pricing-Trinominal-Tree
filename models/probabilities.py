import math
from utils.utils_constants import clip_and_normalize, EPS, MIN_PRICE

def local_probabilities(tree, i, k, S_i_k):
    """
    Calcule les probabilités locales (p_down, p_mid, p_up, kprime)
    """
    market = tree.market
    t_i, t_ip1 = i * tree.dt, (i + 1) * tree.dt
    div = market.dividend_on_step(t_i, t_ip1, S_i_k)

    # Espérance du prix futur sous la mesure risque-neutre
    E = S_i_k * math.exp(tree.r * tree.dt) - div
    a = tree.alpha
    a2 = a * a
    exp2r = math.exp(2 * tree.r * tree.dt)
    V = (S_i_k ** 2) * exp2r * (tree.exp_sig2_dt - 1.0)

    if V < 1e-18:
        base_next = max(MIN_PRICE, tree.trunk[i + 1])
        if base_next <= 0.0:
            base_next = max(MIN_PRICE, S_i_k * math.exp(tree.r * tree.dt))

        kprime = int(round(math.log(max(E, MIN_PRICE) / base_next) / max(EPS, math.log(a))))
        S_mid = base_next * (a ** kprime)
        dists = [(abs(E - S_mid / a), -1), (abs(E - S_mid), 0), (abs(E - S_mid * a), +1)]
        dj = min(dists, key=lambda x: x[0])[1]

        if dj == -1:
            return 1.0, 0.0, 0.0, kprime
        elif dj == 0:
            return 0.0, 1.0, 0.0, kprime
        else:
            return 0.0, 0.0, 1.0, kprime

    # Détermination du nœud médian de référence
    base_next = max(MIN_PRICE, tree.trunk[i + 1])
    denom = max(EPS, math.log(a))
    kprime = int(round(math.log(max(E, MIN_PRICE) / base_next) / denom))
    kprime = max(-(i + 1), min(i + 1, kprime))
    S_mid = base_next * (a ** kprime)

    S_up, S_down = S_mid * a, S_mid / a
    lower, upper = 0.5 * (S_mid + S_down), 0.5 * (S_mid + S_up)

    # Ajustement si l'espérance sort des bornes
    shifts = 0
    while (E > upper or E < lower) and shifts < 10:
        if E > upper:
            kprime += 1
            S_mid *= a
        elif E < lower:
            kprime -= 1
            S_mid /= a
        S_up, S_down = S_mid * a, S_mid / a
        lower, upper = 0.5 * (S_mid + S_down), 0.5 * (S_mid + S_up)
        shifts += 1

    m1 = E / S_mid
    m2 = (V + E * E) / (S_mid * S_mid)

    if not market.has_dividend_between(t_i, t_ip1):
        p_down = (tree.exp_sig2_dt - 1.0) / ((1.0 - a) * ((1.0 / a2) - 1.0))
        p_up = p_down / a
        p_mid = 1.0 - p_up - p_down
        return (*clip_and_normalize(p_down, p_mid, p_up), kprime)

    den = (1.0 - a) * ((1.0 / a2) - 1.0)
    if abs(den) < 1e-14:
        return 0.0, 1.0, 0.0, kprime

    num = (m2 - 1.0) - (a + 1.0) * (m1 - 1.0)
    p_down = num / den
    p_up = (m1 - 1.0 - ((1.0 / a) - 1.0) * p_down) / (a - 1.0)
    p_mid = 1.0 - p_up - p_down

    return (*clip_and_normalize(p_down, p_mid, p_up), kprime)
