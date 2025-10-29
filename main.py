from models.market import Market
from models.option_trade import Option
from models.tree import TrinomialTree
from utils.utils_bs import bs_price
from models.backward_pricing import price_backward

S0, K, r, sigma, T, D = 100, 102, 0.05, 0.5, 1.0, 3.0
N = 200

# Dividend +1 day
market_div = Market(S0, r, sigma, T, exdivdate=1/365, rho=0.03, lam=0)
option = Option(K=K, is_call=True)
tree = TrinomialTree(market_div, option, N, "european").build_tree()
price_div = price_backward(tree)

# No-dividend reference (S0 - D)
market_ref = Market(S0 - D, r, sigma, T)
tree_ref = TrinomialTree(market_ref, option, N, "european").build_tree()
price_ref = tree_ref.price_backward()

bs_ref = bs_price(S0 - D, K, r, sigma, T, True)

print("Tree with div:", price_div)
print("Tree no-div (S0-D):", price_ref)
print("BS (S0-D):", bs_ref)
