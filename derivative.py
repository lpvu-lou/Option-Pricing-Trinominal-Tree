# derivative.py
from typing import Callable

class OneDimDerivative:
    """
    Generic one-dimensional finite difference derivative calculator.
    It can compute Delta, Vega, Rho... depending on the function passed.
    """
    def __init__(self, function: Callable[[object, float], float],
                 parameters: object, shift: float = 1e-2):
        """
        :param function: callable that takes (params, variable) and returns price
        :param parameters: any object or dict containing other model parameters
        :param shift: finite difference increment (default 0.01)
        """
        self.f = function
        self.params = parameters
        self.shift = shift

    def first(self, x: float) -> float:
        """Central finite difference derivative."""
        up = self.f(self.params, x + self.shift)
        down = self.f(self.params, x - self.shift)
        return (up - down) / (2.0 * self.shift)
