from math import exp, sqrt, log
from scipy.stats import norm

def bs_price(S, K, r, sigma, T, is_call=True):
    """
    Calcul du prix de l’option par la formule de Black-Scholes
    """
    d_1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d_2 = d_1 - sigma * sqrt(T)

    df_r = exp(-r * T)

    if is_call:
        price = S * norm.cdf(d_1) - K * df_r * norm.cdf(d_2)
    else:
        price = K * df_r * norm.cdf(-d_2) - S * norm.cdf(-d_1)
    return price
    

def bs_greeks(S, K, r, sigma, T, is_call=True):
    """
    Grecs Black–Scholes 
    """
    d_1 = (log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * sqrt(T))
    d_2 = d_1 - sigma * sqrt(T)

    pdf_d1 = norm.pdf(d_1)
    Nd1, Nd2 = norm.cdf(d_1), norm.cdf(d_2)
    Nmd1, Nmd2 = norm.cdf(-d_1), norm.cdf(-d_2)

    df_r = exp(-r * T)

    price = bs_price(S, K, r, sigma, T, is_call=True)

    if is_call:
        delta = Nd1
        theta = -(S * pdf_d1 * sigma) / (2 * sqrt(T)) - r * K * df_r * Nd2
        rho_val = K * T * df_r * Nd2
    else:
        delta = -Nmd1
        theta = -(S * pdf_d1 * sigma) / (2 * sqrt(T)) + r * K * df_r * Nmd2
        rho_val = -K * T * df_r * Nmd2

    gamma = (pdf_d1 / (S * sigma * sqrt(T)))
    vega  = (S * pdf_d1 * sqrt(T))
    vomma = (vega * d_1 * d_2 / sigma)
    vanna = (vega * (1 - d_1 / (sigma * sqrt(T))) / S)

    return {
        "Price": price,
        "Delta": delta,
        "Gamma": gamma,
        "Vega": vega,
        "Theta": theta,
        "Rho": rho_val,
        "Vanna": vanna,
        "Vomma": vomma,
    }


