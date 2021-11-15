'''
NSGA-II multi-objective solver.
'''

import numpy as np
from pymoo.algorithms.so_genetic_algorithm import GA as GAAlgo
from pymoo.algorithms.so_cmaes import CMAES as CMAESAlgo
from pymoo.optimize import minimize

from autooed.utils.sampling import lhs
from autooed.mobo.solver.base import Solver


class GA(Solver):
    '''
    Single-objective solver based on Genetic Algorithm.
    '''
    def __init__(self, problem, pop_size=200, **kwargs):
        super().__init__(problem)
        self.algo = GAAlgo(pop_size=pop_size)

    def _solve(self, X, Y, batch_size):

        # initialize population
        X = np.vstack([X, lhs(X.shape[1], batch_size)])
        self.algo.initialization.sampling = X
        
        res = minimize(self.problem, self.algo)
        opt_X, opt_F = res.pop.get('X'), res.pop.get('F')
        opt_idx = np.argsort(opt_F.flatten())[:batch_size]

        return opt_X[opt_idx], opt_F[opt_idx]


class CMAES(Solver):
    '''
    Single-objective solver based on CMAES.
    '''
    def __init__(self, problem, **kwargs):
        super().__init__(problem)

    def _solve(self, X, Y, batch_size):

        # initialize population
        X = np.vstack([X, lhs(X.shape[1], batch_size)])
        F = self.problem.evaluate(X)
        x0 = X[np.argmin(F)]

        algo = CMAESAlgo(x0=x0)
        res = minimize(self.problem, algo)
        opt_X, opt_F = res.pop.get('X'), res.pop.get('F')
        opt_idx = np.argsort(opt_F.flatten())[:batch_size]

        return opt_X[opt_idx], opt_F[opt_idx]
