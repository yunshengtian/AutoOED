import numpy as np
from problem import Problem


class IntegerProblem1(Problem):
    '''
    Example 1, with specified number of design variables and objectives, also same bounds for all design variables
    '''
    config = {
        'type': 'integer',
        'n_var': 6,
        'n_obj': 2,
        'var_lb': 0,
        'var_ub': 1,
    }

    def evaluate_objective(self, x):
        f1 = np.max(x)
        f2 = np.min(x)
        return f1, f2


class IntegerProblem2(Problem):
    '''
    Example 2, with specified number of design variables and objectives, also different bounds for each design variable
    '''
    config = {
        'type': 'integer',
        'n_var': 4,
        'n_obj': 2,
        'var_lb': [0, 2, 5, 1],
        'var_ub': [1, 4, 6, 3],
    }

    def evaluate_objective(self, x):
        f1 = np.sum(x)
        f2 = np.sum(np.abs(x))
        return f1, f2


class IntegerProblem3(Problem):
    '''
    Example 3, with specified number of design variables, objectives and constraints, also same bounds for all design variables
    NOTE: for constraint value (g), > 0 means violating constraint, <= 0 means satisfying constraint
    '''
    config = {
        'type': 'integer',
        'n_var': 4,
        'n_obj': 3,
        'n_constr': 2,
        'var_lb': -1,
        'var_ub': 1,
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