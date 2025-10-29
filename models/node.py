import math

class Node:
    """
    Classe représentant un nœud de l’arbre trinomial.
    Chaque nœud connaît :
      - son indice temporel (i)
      - son prix de l’actif sous-jacent (S)
      - la probabilité d’atteindre ce nœud (p_reach)
      - la valeur de l’option à ce nœud (option_value)
    
    Cette classe permet également de vérifier automatiquement
    si un dividende intervient entre t_i et t_{i+1}.
    """

    def __init__(self, time_index: int, stock_price: float, tree=None):
        self.time_index = time_index         
        self.stock_price = stock_price        
        self.option_value = None            
        self.p_reach = 0.0                
        self.tree = tree

        self.is_div_in_next_period = False    # Indique s’il y a un dividende entre t_i et t_{i+1}
        self.div_amount_next = 0.0            # Montant du dividende prévu

        if tree is not None:
            self._check_dividend_timing()

    # Vérifie si deux temps sont presque égaux (pour éviter les erreurs d’arrondi)
    def _are_same_times(self, t1: float, t2: float) -> bool:
        """
        Compare deux instants t1 et t2 avec une tolérance numérique.
        """
        tol = self.tree.dt / 1000.0
        return abs(t1 - t2) < tol

    # Vérifie la présence d’un dividende entre t_i et t_{i+1}
    def _check_dividend_timing(self):
        """
        Détermine si une date ex-dividende t_div se situe
        strictement entre t_i et t_{i+1}.

        Si c’est le cas :
          - is_div_in_next_period = True
          - div_amount_next = montant du dividende correspondant
        """
        market = self.tree.market
        if not market.dividends:
            return 

        # Calcul des bornes temporelles 
        t_i = self.time_index * self.tree.dt
        t_ip1 = (self.time_index + 1) * self.tree.dt

        # Boucle sur les dividendes 
        for t_div, policy in market.dividends:
            # Si la date du dividende est strictement à l’intérieur de [t_i, t_{i+1})
            if t_i < t_div < t_ip1 and not self._are_same_times(t_div, t_ip1):
                self.is_div_in_next_period = True
                # Calcul du montant du dividende
                self.div_amount_next = policy.amount(t_div, self.stock_price, market.S0)
                break
