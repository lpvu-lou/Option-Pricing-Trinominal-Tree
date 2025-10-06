# Objectif :
# Représenter un nœud dans l’arbre trinomial.
# Chaque nœud correspond à un état possible du sous-jacent
# à une date donnée (time_step) avec :
#   - le prix du sous-jacent (stock_price)
#   - la valeur de l’option (option_value)
#   - la probabilité d’atteinte (p_reach)

class Node:
    """
    Représente un nœud dans l’arbre trinomial :
    - time_index : indice temporel (étape i)
    - stock_price : prix du sous-jacent au nœud
    - option_value : valeur de l’option associée à ce nœud
    - p_reach : probabilité d’atteindre ce nœud (calculée via compute_reach_probabilities)
    """

    def __init__(self, time_step: int, stock_price: float):
        self.time_index = time_step          # Étape temporelle (i)
        self.stock_price = stock_price       # Prix du sous-jacent au nœud
        self.option_value = None             # Valeur de l’option à ce nœud
        self.p_reach = 0.0                   # Probabilité d’atteindre ce nœud

    def has_dividend_next(self, tree) -> float:
        """
        Détecte s’il existe un dividende entre ce nœud et le prochain.
        Renvoie le montant du dividende si présent, sinon 0.
        """
        mkt = tree.market
        t_i = self.time_index * tree.dt
        t_ip1 = (self.time_index + 1) * tree.dt
        S = self.stock_price
        return mkt.dividend_on_step(t_i, t_ip1, S)

    def next_mid_price(self, tree) -> float:
        """
        Calcule le prix du nœud central à l’étape suivante,
        en tenant compte du dividende discret éventuel.
        """
        r = tree.market.r
        dt = tree.dt
        fwd = self.stock_price * math.exp(r * dt)
        div = self.has_dividend_next(tree)
        return fwd - div

    def __repr__(self):
        return (f"Node(i={self.time_index}, "
                f"S={self.stock_price:.4f}, "
                f"V={self.option_value if self.option_value is not None else 'None'}, "
                f"p_reach={self.p_reach:.5f})")


