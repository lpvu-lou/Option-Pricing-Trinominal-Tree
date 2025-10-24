EPS = 1e-14
MIN_PRICE = 1e-12

def clip_and_normalize(pD, pM, pU):
    """
    Nettoie et renormalise les probabilités locales.
    """
    ps = [pD, pM, pU]
    ps = [0.0 if p < -1e-12 else max(0.0, p) for p in ps]
    s = sum(ps)
    if s < EPS:
        return 0.0, 1.0, 0.0
    return ps[0]/s, ps[1]/s, ps[2]/s
