'''
Ackley problem suite.
'''

import numpy as np
from autooed.problem.problem import Problem


class Ackley(Problem):
    '''
    '''
    def __init__(self):
        super().__init__()
        self.a = 20
        self.b = 1/5
        self.c = 2 * np.pi
    
    def evaluate_objective(self, x):
        part1 = -1. * self.a * np.exp(-1. * self.b * np.sqrt((1. / self.n_var) * np.sum(x * x)))
        part2 = -1. * np.exp((1. / self.n_var) * np.sum(np.cos(self.c * x)))
        f = part1 + part2 + self.a + np.exp(1)
        return f,

    def _calc_pareto_front(self):
        return 0.


class Ackley2D(Ackley):

    config = {
        'type': 'continuous',
        'n_var': 2,
        'n_obj': 1,
        'var_lb': -32.768,
        'var_ub': 32.768,
    }


class Ackley5D(Ackley):

    config = {
        'type': 'continuous',
        'n_var': 5,
        'n_obj': 1,
        'var_lb': -32.768,
        'var_ub': 32.768,
    }


class Ackley10D(Ackley):

    config = {
        'type': 'continuous',
        'n_var': 10,
        'n_obj': 1,
        'var_lb': -32.768,
        'var_ub': 32.768,
    }
