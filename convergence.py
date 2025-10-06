import math
import csv
from market import Market
from option_trade import Option
from tree import TrinomialTree

# Fonction prix Black-Scholes (sans dividendes)
def _norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))

def bs_price(S: float, K: float, r: float, sigma: float, T: float, is_call: bool = True) -> float:
    if T <= 0 or sigma <= 0:
        return max(S - K, 0.0) if is_call else max(K - S, 0.0)

    d1 = (math.log(S / K) + (r + 0.5 * sigma * sigma) * T) / (sigma * math.sqrt(T))
    d2 = d1 - sigma * math.sqrt(T)

    if is_call:
        return S * _norm_cdf(d1) - K * math.exp(-r * T) * _norm_cdf(d2)
    else:
        return K * math.exp(-r * T) * _norm_cdf(-d2) - S * _norm_cdf(-d1)

# Convergence par rapport au nombre d'étapes (N)
def convergence_vs_steps(S0, K, r, sigma, T, is_call=True, exercise="european",
                         N_list=(5, 10, 25, 50, 100, 200), filename="convergence_vs_steps.csv"):

    bs = bs_price(S0, K, r, sigma, T, is_call=is_call)

    print("\n=== Convergence par rapport à N ===")
    print(f"{'N':>5} | {'Tree Price':>12} | {'BS Price':>10} | {'Gap(Tree-BS)':>12}")
    print("-" * 45)

    rows = []
    for N in N_list:
        market = Market(S0=S0, r=r, sigma=sigma, T=T)
        option = Option(K=K, T=T, is_call=is_call)
        tree = TrinomialTree(market, option, N=N, exercise=exercise)
        tree.build_tree()
        tree_price = tree.price()
        gap = tree_price - bs
        rows.append([N, tree_price, bs, gap])
        print(f"{N:5d} | {tree_price:12.6f} | {bs:10.6f} | {gap:12.6e}")

    # Export CSV
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["N", "TreePrice", "BSPrice", "Gap(Tree-BS)"])
        writer.writerows(rows)

    print(f"\n Résultats enregistrés dans {filename}")

# Convergence par rapport au strike (K)
def convergence_vs_strike(S0, r, sigma, T, N=50, is_call=True, exercise="european",
                          K_list=(80, 90, 100, 110, 120), filename="convergence_vs_strike.csv"):
    print("\n=== Convergence par rapport au strike K ===")
    print(f"{'K':>8} | {'Tree Price':>12} | {'BS Price':>10} | {'Gap(Tree-BS)':>12}")
    print("-" * 50)

    rows = []
    for K in K_list:
        market = Market(S0=S0, r=r, sigma=sigma, T=T)
        option = Option(K=K, T=T, is_call=is_call)
        tree = TrinomialTree(market, option, N=N, exercise=exercise)
        tree.build_tree()
        tree_price = tree.price()
        bs_val = bs_price(S0, K, r, sigma, T, is_call=is_call)
        gap = tree_price - bs_val
        rows.append([K, tree_price, bs_val, gap])
        print(f"{K:8.2f} | {tree_price:12.6f} | {bs_val:10.6f} | {gap:12.6e}")

    # Export CSV
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["K", "TreePrice", "BSPrice", "Gap(Tree-BS)"])
        writer.writerows(rows)

    print(f"\n Résultats enregistrés dans {filename}")
