import math
import datetime as dt
from typing import Optional

class Node:
    """
    Représente un nœud d’un arbre trinomial.
    Chaque nœud peut pointer vers ses nœuds enfants (up, mid, down).
    """

    def __init__(self, time_index: int, spot: float):
        self.time_index = time_index
        self.spot = spot
        self.option_value: Optional[float] = None
        self.p_reach: float = 0.0

        # Pointeurs
        self.next_up: Optional['Node'] = None
        self.next_mid: Optional['Node'] = None
        self.next_down: Optional['Node'] = None
        self.prev_mid: Optional['Node'] = None

    def move_up(self, alpha: float) -> 'Node':
        """Crée le nœud du dessus à l’étape suivante"""
        self.next_up = Node(self.time_index + 1, self.spot * alpha)
        self.next_up.prev_mid = self
        return self.next_up

    def move_mid(self, dt: float, r: float, D: float) -> 'Node':
        """Crée le nœud médian (forward ajusté dividende)"""
        forward = self.spot * math.exp(r * dt) - D
        self.next_mid = Node(self.time_index + 1, forward)
        self.next_mid.prev_mid = self
        return self.next_mid

    def move_down(self, alpha: float) -> 'Node':
        """Crée le nœud du dessous à l’étape suivante"""
        self.next_down = Node(self.time_index + 1, self.spot / alpha)
        self.next_down.prev_mid = self
        return self.next_down
