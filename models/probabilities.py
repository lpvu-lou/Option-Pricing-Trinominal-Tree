import math

EPS = 1e-14
MIN_PRICE = 1e-12


def _clip_and_normalize(pD, pM, pU):
    """
    Nettoie et renormalise les probabilités locales.
    S'assure que les probabilités sont dans [0,1] et leur somme = 1.
    """
    ps = [pD, pM, pU]
    ps = [0.0 if p < -1e-12 else max(0.0, p) for p in ps]
    s = sum(ps)
    if s < EPS:
        return 0.0, 1.0, 0.0
    return ps[0] / s, ps[1] / s, ps[2] / s


def local_probabilities(market, dt, alpha, exp_sig2_dt, S_i_k, trunk_next, i, k):
    """
    Calcule les probabilités locales (p_down, p_mid, p_up, kprime)

    Parameters
    ----------
    market : Market
        Objet Market (contient r, sigma, dividend_on_step, etc.)
    dt : float
        Durée d’un pas de temps
    alpha : float
        Facteur multiplicatif entre les nœuds (S_up = alpha * S_mid)
    exp_sig2_dt : float
        exp(sigma² * dt)
    S_i_k : float
        Prix du sous-jacent au nœud courant
    trunk_next : float
        Prix du nœud central du niveau suivant (Smid_{i+1})
    i : int
        Indice de l’étape courante
    k : int
        Indice relatif du nœud dans l’étape courante

    Returns
    -------
    tuple : (p_down, p_mid, p_up, kprime)
    """

    # Étape temporelle courante
    t_i, t_ip1 = i * dt, (i + 1) * dt
    div = market.dividend_on_step(t_i, t_ip1, S_i_k)

    # Espérance du prix futur sous la mesure risque-neutre
    E = S_i_k * math.exp(market.r * dt) - div

    # Paramètres du modèle
    a = alpha
    a2 = a * a
    exp2r = math.exp(2 * market.r * dt)

    # Variance du prix sur un pas de temps
    V = (S_i_k ** 2) * exp2r * (exp_sig2_dt - 1.0)

    # Si la variance est négligeable, la trajectoire devient quasi déterministe.
    # On attribue donc toute la probabilité au nœud le plus proche de l’espérance E
    if V < 1e-18:
        base_next = max(MIN_PRICE, trunk_next)
        if base_next <= 0.0:
            base_next = max(MIN_PRICE, S_i_k * math.exp(market.r * dt))

        # Approximation de l’indice médian k′ (niveau central)
        kprime = int(round(math.log(max(E, MIN_PRICE) / base_next) / max(EPS, math.log(a))))
        S_mid = base_next * (a ** kprime)
        S_up, S_down = S_mid * a, S_mid / a

        # On choisit le nœud le plus proche de E
        dists = [(abs(E - S_down), -1), (abs(E - S_mid), 0), (abs(E - S_up), +1)]
        dj = min(dists, key=lambda x: x[0])[1]

        # On attribue la probabilité totale à ce nœud
        if dj == -1:
            return 1.0, 0.0, 0.0, kprime
        elif dj == 0:
            return 0.0, 1.0, 0.0, kprime
        else:
            return 0.0, 0.0, 1.0, kprime

    # Détermination du nœud médian de référence-
    base_next = max(MIN_PRICE, trunk_next)
    denom = max(EPS, math.log(a))
    kprime = int(round(math.log(max(E, MIN_PRICE) / base_next) / denom))
    kprime = max(-(i + 1), min(i + 1, kprime))
    S_mid = base_next * (a ** kprime)

    # Ajustement de k′ si E est en dehors de l’intervalle [S_down, S_up]
    S_up, S_down = S_mid * a, S_mid / a
    lower = 0.5 * (S_mid + S_down)
    upper = 0.5 * (S_mid + S_up)
    shifts = 0
    while (E > upper or E < lower) and shifts < 10:
        if E > upper:
            kprime += 1
            S_mid *= a
        elif E < lower:
            kprime -= 1
            S_mid /= a
        S_up, S_down = S_mid * a, S_mid / a
        lower = 0.5 * (S_mid + S_down)
        upper = 0.5 * (S_mid + S_up)
        shifts += 1

    # Moments normalisés
    m1 = E / S_mid                      # espérance relative
    m2 = (V + E * E) / (S_mid * S_mid)  # variance relative

    # Cas sans dividende
    if not market.has_dividend_between(t_i, t_ip1):
        p_down = (exp_sig2_dt - 1.0) / ((1.0 - a) * ((1.0 / a2) - 1.0))
        p_up = p_down / a
        p_mid = 1.0 - p_up - p_down
        return _clip_and_normalize(p_down, p_mid, p_up) + (kprime,)
    
    # Cas avec dividende
    # Si le dénominateur est trop petit (a ≈ 1), on évite les instabilités numériques
    den = (1.0 - a) * ((1.0 / a2) - 1.0)
    if abs(den) < 1e-14:
        return 0.0, 1.0, 0.0, kprime

    # Calcul stable à partir des moments m1 et m2
    num = (m2 - 1.0) - (a + 1.0) * (m1 - 1.0)
    p_down = num / den
    p_up = (m1 - 1.0 - ((1.0 / a) - 1.0) * p_down) / (a - 1.0)
    p_mid = 1.0 - p_up - p_down

    # Nettoyage et normalisation
    p_down, p_mid, p_up = _clip_and_normalize(p_down, p_mid, p_up)
    return p_down, p_mid, p_up, kprime
