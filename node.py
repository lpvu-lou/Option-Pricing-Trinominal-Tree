import math

class Node:
    """
    Noeud d’un arbre trinomial
    """

    def __init__(self, time_index: int, stock_price: float):
        self.time_index = time_index      # indice de temps (0..N)
        self.stock_price = stock_price    # prix du sous-jacent à ce noeud
        self.option_value = None          # valeur de l'option (à calculer)
        self.p_reach = 0.0                # probabilité d'atteindre ce noeud

    def time(self, tree) -> float:
        """
        Temps correspondant à ce noeud
        """
        return self.time_index * tree.dt

    def next_time(self, tree) -> float:
        """
        Temps correspondant au pas de temps suivant
        """
        return (self.time_index + 1) * tree.dt

    def dividend_next_amount(self, tree) -> float:
        """
        Montant du dividende versé au prochain pas de temps
        """
        market = tree.market
        t_i = self.time(tree)
        t_ip1 = self.next_time(tree)
        return market.dividend_on_step(t_i, t_ip1, self.stock_price)

    def next_mid_price(self, tree) -> float:
        """
        Prix moyen du sous-jacent au pas de temps suivant ajusté des dividendes
        """
        market = tree.market
        fwd_price = self.stock_price * math.exp(market.r * tree.dt)
        div = self.dividend_next_amount(tree)
        s_mid = fwd_price - div
        return s_mid
