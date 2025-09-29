class OptionTrade:
    def __init__(self, S0, K, r, sigma, T, N,
                 option_type="call", exercise="european", dividend=0.0):
        """
        Container for option trade parameters.
        """
        self.S0 = S0
        self.K = K
        self.r = r
        self.sigma = sigma
        self.T = T
        self.N = N
        self.option_type = option_type
        self.exercise = exercise
        self.dividend = dividend
