import math

def _norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def bs_price(S, K, r, sigma, T, is_call = True):
    if T <= 0 or sigma <= 0:
        return max(S - K, 0.0) if is_call else max(K - S, 0.0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if is_call:
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)