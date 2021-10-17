'''
NSGA-II multi-objective solver.
'''

import numpy as np
from pymoo.algorithms.nsga2 import NSGA2 as NSGA2Algo
from pymoo.optimize import minimize

from autooed.utils.sampling import lhs
from autooed.mobo.solver.base import Solver


class NSGA2(Solver):
    '''
    Solver based on NSGA-II.
    '''
    def __init__(self, problem, n_gen=200, pop_size=200, **kwargs):
        super().__init__(problem)
        self.n_gen = n_gen
        self.algo = NSGA2Algo(pop_size=pop_size)

    def _solve(self, X, Y, batch_size):

        # initialize population
        X = np.vstack([X, lhs(X.shape[1], batch_size)])
        self.algo.initialization.sampling = X
        
        res = minimize(self.problem, self.algo, ('n_gen', self.n_gen))

        return res.pop.get('X'), res.pop.get('F')
