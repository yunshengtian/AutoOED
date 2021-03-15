import numpy as np
import pandas as pd
from collections.abc import Iterable

from pymoo.model.individual import Individual
from pymoo.model.population import Population

'''
Main algorithm framework for Multi-Objective Optimization
'''

class MOO:
    '''
    Base class of algorithm framework, inherit this class with specific algorithm classes specified as 'algo'
    '''
    algo = None

    def __init__(self, problem, algo_cfg):
        '''
        Input:
            problem: the original / real optimization problem
        '''
        self.real_problem = problem
        self.n_var, self.n_obj = problem.n_var, problem.n_obj
        self.transformation = self.real_problem.transformation # data transformation between all input types and continuous
        self.batch_size = algo_cfg['selection']['batch_size']

    def solve(self, X_init, Y_init):
        '''
        Solve the real multi-objective problem from initial data (X_init, Y_init)
        '''
        # forward transformation
        X_init = self.transformation.do(X_init)

        # convert maximization to minimization
        X, Y = X_init, Y_init.copy()
        obj_type = self.real_problem.obj_type
        if isinstance(obj_type, str):
            obj_type = [obj_type] * Y.shape[1]
        assert isinstance(obj_type, Iterable)
        maxm_idx = np.array(obj_type) == 'max'
        Y[:, maxm_idx] = -Y[:, maxm_idx]

        # construct population
        pop = Population(0, individual=Individual())
        pop = pop.new('X', X)
        pop.set('F', Y)
        pop.set('CV', np.zeros([X.shape[0], 1])) # assume input samples are all feasible

        off = self._solve(pop)

        X_next = off.get('X')[:self.batch_size]
        
        # backward transformation
        X_next = self.transformation.undo(X_next)

        return X_next, (None, None)

    def _solve(self, pop):
        raise NotImplementedError

    def predict(self, X_init, Y_init, X_next):
        '''
        Predict the performance of X_next based on initial data (X_init, Y_init), not supported for moo algorithms
        '''
        return None, None

