import numpy as np

def evaluate_objective(x):
    n_var = len(x)
    f1 = x[0]
    g = 1 + 9.0 / (n_var - 1) * np.sum(x[1:])
    f2 = g * (1 - np.power((f1 / g), 0.5))
    return f1, f2