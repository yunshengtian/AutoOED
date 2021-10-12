'''
OKA problem suite.
'''

import numpy as np
from autooed.problem.problem import Problem


class OKA1(Problem):
    '''
    Okabe, Tatsuya, et al. "On test functions for evolutionary multi-objective optimization." International Conference on Parallel Problem Solving from Nature. Springer, Berlin, Heidelberg, 2004.
    '''
    config = {
        'type': 'continuous',
        'n_var': 2,
        'n_obj': 2,
        'var_lb': [6 * np.sin(np.pi / 12), -2 * np.pi * np.sin(np.pi / 12)],
        'var_ub': [6 * np.sin(np.pi / 12) + 2 * np.pi * np.cos(np.pi / 12), 6 * np.cos(np.pi / 12)],
    }
    
    def evaluate_objective(self, x):
        sin, cos = np.sin(np.pi / 12), np.cos(np.pi / 12)
        x1, x2 = x[0], x[1]
        x1_ = cos * x1 - sin * x2
        x2_ = sin * x1 + cos * x2

        f1 = x1_
        f2 = np.sqrt(2 * np.pi) - np.sqrt(np.abs(x1_)) + 2 * np.abs(x2_ - 3 * np.cos(x1_) - 3) ** (1. / 3)
        return f1, f2

    def _calc_pareto_front(self, n_pareto_points=100):
        x1_ = np.linspace(0, 2 * np.pi, n_pareto_points)
        x2_ = 3 * np.cos(x1_) + 3

        f1 = x1_
        f2 = np.sqrt(2 * np.pi) - np.sqrt(np.abs(x1_)) + 2 * np.abs(x2_ - 3 * np.cos(x1_) - 3) ** (1. / 3)

        return np.column_stack([f1, f2])


class OKA2(Problem):
    '''
    Okabe, Tatsuya, et al. "On test functions for evolutionary multi-objective optimization." International Conference on Parallel Problem Solving from Nature. Springer, Berlin, Heidelberg, 2004.
    '''
    config = {
        'type': 'continuous',
        'n_var': 3,
        'n_obj': 2,
        'var_lb': [-np.pi, -5.0, -5.0],
        'var_ub': [np.pi, 5.0, 5.0],
    }
    
    def evaluate_objective(self, x):
        x1, x2, x3 = x[0], x[1], x[2]

        f1 = x1
        f2 = 1 - (x1 + np.pi) ** 2 / (4 * np.pi ** 2) + \
            np.abs(x2 - 5 * np.cos(x1)) ** (1. / 3) + np.abs(x3 - 5 * np.sin(x1)) ** (1. / 3)
        return f1, f2

    def _calc_pareto_front(self, n_pareto_points=100):
        f1 = np.linspace(-np.pi, np.pi, n_pareto_points)
        f2 = 1 - (f1 + np.pi) ** 2 / (4 * np.pi ** 2)
        return np.column_stack([f1, f2])
