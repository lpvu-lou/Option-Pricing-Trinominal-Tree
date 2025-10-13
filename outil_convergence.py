# Outils de convergence vers le modèle de Black-Scholes
# Comparaison des prix obtenus par l’arbre trinomial avec le prix de Black-Scholes
# pour différentes valeurs de N (nombre de pas dans l’arbre)

import math
import matplotlib.pyplot as plt
import numpy as np
from blackscholes import bs_price
from tree import TrinomialTree
from market import Market
from option_trade import Option
from node import Node
import time
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning)

def outil_convergence(market: Market, option: Option, N_values, exercise="european", plot=True):
    bs = bs_price(market.S0, option.K, market.r, market.sigma, market.T, is_call=False)
    tree_prices = []
    times = []

    for N in N_values:
        tree = TrinomialTree(market, option, N, exercise)
        tree.build_tree()
        start_time = time.time()
        tree.price_backward()
        elapsed_time = time.time() - start_time
        times.append(elapsed_time)
        price = tree.tree[0][0].option_value
        tree_prices.append(price)
        print(f"N={N}: Tree Price={price:.4f}, BS Price={bs:.4f}, Time={elapsed_time:.4f}s")

    if plot:
        plt.figure(figsize=(10, 5))
        plt.plot(N_values, tree_prices, marker='o', label='Trinomial Tree Price')
        plt.axhline(y=bs, color='r', linestyle='--', label='Black-Scholes Price')
        plt.xscale('log')
        plt.xlabel('Number of Steps (N)')
        plt.ylabel('Option Price')
        plt.title('Convergence of Trinomial Tree to Black-Scholes Price')
        plt.legend()
        plt.grid(True)
        plt.show()

        plt.figure(figsize=(10, 5))
        plt.plot(N_values, times, marker='o', color='orange', label='Computation Time')
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Number of Steps (N)')
        plt.ylabel('Time (seconds)')
        plt.title('Computation Time vs Number of Steps in Trinomial Tree')
        plt.legend()
        plt.grid(True)
        plt.show()
        

        # Autre visualisation possible : erreur absolue
        errors = [abs(p - bs) for p in tree_prices]
        plt.figure(figsize=(10, 5))
        plt.plot(N_values, errors, marker='o', color='green', label='Absolute Error')
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Number of Steps (N)')
        plt.ylabel('Absolute Error')
        plt.title('Absolute Error of Trinomial Tree Price vs Black-Scholes Price')
        plt.legend()
        plt.grid(True)
        plt.show()

        # Autre visualisation possible : erreur * nombre de pas
        errors_N = [(p - bs) * N for p, N in zip(tree_prices, N_values)]
        plt.figure(figsize=(20, 10))
        plt.plot(N_values, errors_N, marker='o', color='purple', label='Error * N')
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Number of Steps (N)')
        plt.ylabel('Error * N')
        plt.title('Error * N of Trinomial Tree Price vs Black-Scholes Price')
        plt.legend()
        plt.grid(True)
        plt.show()

    return tree_prices, bs, times

if __name__ == "__main__":
    # Paramètres du marché et de l’option
    market = Market(S0=100, r=0.05, sigma=0.25, T=0.5, dividends=None)
    option = Option(K=90, is_call=False)

    # Valeurs de N à tester
    N_values = list(range(1, 201, 1))

    # Exécuter l’outil de convergence
    outil_convergence(market, option, N_values, exercise="european", plot=True)