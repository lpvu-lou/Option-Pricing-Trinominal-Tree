import datetime as dt
from models.node import Node


class TruncNode(Node):
    """
    Nœud spécialisé utilisé pour détecter si un dividende (ex-dividend date) 
    se situe entre deux pas de temps dans le modèle trinomial.
    """

    def __init__(self, precNode, colDate, price, tree):
        """
        Parameters: 
        precNode : Nœud précédent (le 'mid' du niveau précédent)
        colDate : Date du niveau courant 
        price : Prix du sous-jacent au nœud
        tree : Référence à l’arbre complet 
        """
        super().__init__(time_index=precNode.time_index + 1 if precNode else 0,
                         stock_price=price)
        self.precMid = precNode
        self.columnDate = colDate
        self.tree = tree

        # Détection de la présence d’un dividende dans la période suivante
        exDivDate = getattr(self.tree.market, "exdivdate", None)
        self.isDivInTheFollowingPeriod = False

        if exDivDate is not None:
            # True si la date de détachement est entre colDate et nextDate()
            if (not self.areSameDates(self.columnDate, exDivDate)
                    and self.columnDate < exDivDate <= self.nextDate()):
                self.isDivInTheFollowingPeriod = True

    def nextDate(self):
        """
        Retourne la date correspondant au pas de temps suivant
        """
        return self.columnDate + dt.timedelta(days=365 * self.tree.dt)

    def areSameDates(self, d1, d2):
        """
        Vérifie l’égalité entre deux dates avec une tolérance
        """
        if d1 is None or d2 is None:
            return False
        # Tolérance = 1/1000 du pas de temps
        tol_days = (self.tree.dt * 365) / 1000.0
        return abs((d1 - d2).days) <= tol_days
