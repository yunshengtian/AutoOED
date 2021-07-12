import numpy as np

def evaluate_objective(self, x):
    n_var = len(x)
    f1 = x[0]
    c = np.sum(x[1:])
    g = 1.0 + 9.0 * c / (n_var - 1)
    f2 = g * (1 - np.power((f1 * 1.0 / g), 2))
    return f1, f2