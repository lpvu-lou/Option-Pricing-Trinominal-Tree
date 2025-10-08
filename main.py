import math
from market import Market, DividendPolicy
from option_trade import Option
from tree import TrinomialTree


def display_full_tree(tree):
    """
    Affiche l’arbre complet avec :
      - prix du sous-jacent (S)
      - valeur de l’option (V)
      - probabilité d’atteinte (p_reach)
    """
    print("\n" + "=" * 80)
    print("🌳 AFFICHAGE COMPLET DE L’ARBRE TRINOMIAL")
    print("=" * 80)

    for i, level in enumerate(tree.tree):
        print(f"\n--- Step {i}/{tree.N} ---")
        print(f"{'k':>3} | {'Stock Price (S)':>15} | {'Option Value (V)':>15} | {'p_reach':>10}")
        print("-" * 55)
        for j, node in enumerate(level):
            if node is None:
                continue
            s = f"{node.stock_price:,.4f}"
            v = f"{node.option_value:,.4f}" if node.option_value is not None else "-"
            p = f"{node.p_reach:.2e}"
            k = j - i
            print(f"{k:>3} | {s:>15} | {v:>15} | {p:>10}")
    print("=" * 80 + "\n")


def run_test(title, market, option, N=10, exercise="european", full_display=True):
    """
    Exécute un test complet de pricing et affiche l’arbre.
    """
    print(f"\n{'='*80}")
    print(f"🧩 {title}")
    print(f"{'='*80}")

    tree = TrinomialTree(market=market, option=option, N=N, exercise=exercise)
    tree.build_tree()
    tree.compute_reach_probabilities()
    price = tree.price_backward()

    print(f"\n📈 Prix de l’option ({exercise.title()}): {price:.4f}")

    if full_display:
        display_full_tree(tree)
    else:
        print("\n(Aperçu limité des 3 premiers niveaux)")
        for i, level in enumerate(tree.tree[:3]):
            prices = [round(node.stock_price, 2) for node in level if node]
            print(f"Step {i:2d}: {prices}")


# ====================================================
# MAIN PROGRAM
# ====================================================
if __name__ == "__main__":

    # ------------------------------------------------
    # 1️⃣ TEST SANS DIVIDENDE
    # ------------------------------------------------
    market1 = Market(S0=100, r=0.05, sigma=0.25, T=1.0, dividends=[])
    option1 = Option(K=110, T=1.0, is_call=True)
    run_test("Test 1 - Sans dividende", market1, option1, N=5, full_display=True)

    # ------------------------------------------------
    # 2️⃣ TEST AVEC UN DIVIDENDE UNIQUE
    # ------------------------------------------------
    div_policy = DividendPolicy(rho=0.02, lam=0.4)
    market2 = Market(
        S0=100, r=0.05, sigma=0.25, T=2.0,
        dividends=[(1.0, div_policy)]  # dividende à t = 1 an
    )
    option2 = Option(K=110, T=2.0, is_call=True)
    run_test("Test 2 - Un dividende à 1 an", market2, option2, N=6, full_display=True)

    # ------------------------------------------------
    # 3️⃣ TEST AVEC PLUSIEURS DIVIDENDES AUTOMATIQUES
    # ------------------------------------------------
    market3 = Market(
        S0=100, r=0.05, sigma=0.25, T=3.5,
        dividends=None,
        auto_freq=1.0, auto_offset=0.25,
        rho=0.02, lam=0.4
    )

    print("\n=== Dividendes automatiques générés ===")
    for t_div, policy in market3.dividends:
        print(f"Dividende à t={t_div:.2f} ans | rho={policy.rho:.3f}, lambda={policy.lam:.3f}")

    option3 = Option(K=110, T=3.5, is_call=True)
    run_test("Test 3 - Plusieurs dividendes (1.25, 2.25, 3.25 ans)", market3, option3, N=7, full_display=True)
