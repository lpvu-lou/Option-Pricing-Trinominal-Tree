from market import Market
from tree import TrinomialTree
import math

def black_scholes(S0, K, r, sigma, T, option_type="call"):
    if T <= 0: return max(S0-K, 0) if option_type=="call" else max(K-S0, 0)
    d1 = (math.log(S0/K) + (r + 0.5*sigma**2)*T) / (sigma*math.sqrt(T))
    d2 = d1 - sigma*math.sqrt(T)
    N = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    if option_type == "call":
        return S0*N(d1) - K*math.exp(-r*T)*N(d2)
    else:
        return K*math.exp(-r*T)*N(-d2) - S0*N(-d1)

if __name__ == "__main__":
    # Parameters
    S0, K, r, sigma, T = 100, 100, 0.05, 0.2, 1
    for N in range(1000, 10, -100):
        mkt = Market(S0, r, sigma, T)
        tree = TrinomialTree(mkt, K, N, option_type="call", exercise="european")
        tree.build_tree()
        price_tree = tree.price()
        price_bs = black_scholes(S0, K, r, sigma, T, "call")
        print(f"N={N:<3d} Tree={price_tree:.6f}  BS={price_bs:.6f}  Error={price_tree-price_bs:.2e}")

    # American vs European with dividend
    print("\nAmerican vs European (dividend=2.0):")
    mkt = Market(S0, r, sigma, T, dividend=2.0)
    tree = TrinomialTree(mkt, K, 100, option_type="put", exercise="american")
    tree.build_tree()
    amer_put = tree.price()
    tree = TrinomialTree(mkt, K, 100, option_type="put", exercise="european")
    tree.build_tree()
    euro_put = tree.price()
    print(f"European put: {euro_put:.6f}, American put: {amer_put:.6f}")