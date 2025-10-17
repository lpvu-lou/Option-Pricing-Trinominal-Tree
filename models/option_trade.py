from dataclasses import dataclass

@dataclass
class Option:
    K: float
    is_call: bool = True

    def payoff(self, S):
        return max(S - self.K, 0) if self.is_call else max(self.K - S, 0)