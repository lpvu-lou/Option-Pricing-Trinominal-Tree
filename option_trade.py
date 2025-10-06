# Objectif :
# Définir la classe Option, représentant une option européenne
# (call ou put) avec son strike, sa maturité et sa fonction payoff.

from dataclasses import dataclass

@dataclass
class Option:
    """
    Classe représentant une option européenne (call ou put).

    Attributs :
    - K : prix d’exercice (strike)
    - T : maturité (en années)
    - is_call : True pour un call, False pour un put
    """

    K: float                  # Prix d’exercice
    T: float                  # Maturité (en années)
    is_call: bool = True      # Type d’option : True = Call, False = Put

    # Fonction de paiement (payoff) à la maturité
    def payoff(self, S: float) -> float:
        """
        Calcule le payoff à la maturité pour un prix du sous-jacent S :
            - Call : max(S - K, 0)
            - Put  : max(K - S, 0)
        """
        return max(S - self.K, 0.0) if self.is_call else max(self.K - S, 0.0)

    def __repr__(self):
        type_opt = "Call" if self.is_call else "Put"
        return f"Option({type_opt}, K={self.K}, T={self.T})"