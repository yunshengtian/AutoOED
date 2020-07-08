import numpy as np
from problems import CustomProblem

'''
Example custom problem definitions (performance and constraint evaluation functions here might not make any sense)
'''

class ExampleProblem1(CustomProblem):
    '''
    Example 1, with specified number of design variables and objectives
    '''
    config = {
        'n_var': 6,
        'n_obj': 2,
        # use n_constr = 0, xl = 0, xu = 1 by default
    }

    def evaluate_performance(self, x):
        f1 = np.max(x)
        f2 = np.min(x)
        return f1, f2


class ExampleProblem2(CustomProblem):
    '''
    Example 2, with specified number of design variables and objectives, also bounds on design variables
    '''
    config = {
        'n_var': 10,
        'n_obj': 2,
        'xl': [0, 0, 0, 1],
        'xu': [1, 1, 1, 10],
        # use n_constr = 0 by default
    }

    def evaluate_performance(self, x):
        f1 = np.sum(x)
        f2 = np.sum(np.abs(x))
        return f1, f2


class ExampleProblem3(CustomProblem):
    '''
    Example 3, with specified number of design variables and objectives, bounds on design variables and constraint functions
    NOTE: for constraint value (g), > 0 means violating constraint, <= 0 means satisfying constraint
    '''
    config = {
        'n_var': 4,
        'n_obj': 3,
        'n_constr': 2,
        'xl': 0,
        'xu': 1,
    }

    def evaluate_performance(self, x):
        f1 = np.sum(np.sin(x))
        f2 = np.sum(np.cos(x))
        f3 = np.sum(np.tan(x))
        return f1, f2, f3

    def evaluate_constraint(self, x):
        x1, x2, x3, x4 = x[:, 0], x[:, 1], x[:, 2], x[:, 3]
        g1 = x1 + x2 - 1 # x1 + x2 < 1
        g2 = (x2 + x3 - 2) ** 2 - 1e-5 # x2 + x3 = 2
        return g1, g2