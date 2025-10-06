import math
from market import Market, DividendPolicy
from option_trade import Option
from tree import TrinomialTree

if __name__ == "__main__":

    # ======================
    # 1️⃣ Paramètres du marché
    # ======================
    mkt = Market(
        S0=100,                 # Prix initial
        r=0.02,                 # Taux sans risque
        sigma=0.25,             # Volatilité
        T=1.0,                  # Maturité en années
        dividends=[(0.59, DividendPolicy(rho=0.03, lam=0.5))]  # ex-div à 3 mois
    )

    # ======================
    # 2️⃣ Option à pricer (exemple)
    # ======================
    opt = Option(K=100, T=1.0, is_call = True)

    # ======================
    # 3️⃣ Arbre trinomial
    # ======================
    tree = TrinomialTree(market=mkt, option=opt, N=5, exercise="european")

    # Construction de l’arbre (avec dividende)
    tree.build_tree()

    # ======================
    # 4️⃣ Vérification du comportement du dividende
    # ======================
    print("\n=== Vérification du dividende ===")
    for i, level in enumerate(tree.tree):
        prices = [round(n.stock_price, 2) for n in level if n is not None]
        print(f"Step {i:2d}: {prices}")

    # On devrait observer une baisse du prix moyen (trunk) autour du pas t=0.25
    print("\n=== Trunk (prix milieu) ===")
    for i, mid in enumerate(tree.trunk):
        print(f"t={i * tree.dt:.2f} → S_mid={mid:.4f}")

    # ======================
    # 5️⃣ Pricing de l’option
    # ======================
    price = tree.price()
    print(f"\nPrix de l’option ({tree.exercise.title()}): {price:.4f}")