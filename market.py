import math

class Market:
    def __init__(self, S0, r, sigma, T, dividend=0.0):
        self.S0 = S0
        self.r = r
        self.sigma = sigma
        self.T = T
        self.dividend = dividend

    def forward_price(self, dt):
        return self.S0 * math.exp(self.r * dt)

