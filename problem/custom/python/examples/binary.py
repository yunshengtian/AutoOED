import numpy as np
from problem import Problem


class BinaryProblem1(Problem):
    '''
    Example 1, with specified number of design variables and objectives
    '''
    config = {
        'type': 'binary',
        'n_var': 6,
        'n_obj': 2,
    }

    def evaluate_objective(self, x):
        f1 = np.max(x)
        f2 = np.min(x)
        return f1, f2


class BinaryProblem2(Problem):
    '''
    Example 2, with specified number of design variables, objectives and constraints
    NOTE: for constraint value (g), > 0 means violating constraint, <= 0 means satisfying constraint
    '''
    config = {
        'type': 'binary',
        'n_var': 4,
        'n_obj': 3,
        'n_constr': 2,
    }

    def evaluate_objective(self, x):
        f1 = np.sum(np.sin(x))
        f2 = np.sum(np.cos(x))
        f3 = np.sum(np.tan(x))
        return f1, f2, f3

    def evaluate_constraint(self, x):
        x1, x2, x3, x4 = x[0], x[1], x[2], x[3]
        g1 = x1 + x2 - 1 # x1 + x2 < 1
        g2 = (x2 + x3 - 2) ** 2 - 1e-5 # x2 + x3 = 2
        return g1, g2