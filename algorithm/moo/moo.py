import numpy as np
import pandas as pd
from collections.abc import Iterable

from pymoo.model.individual import Individual
from pymoo.model.population import Population

'''
Main algorithm framework for Multi-Objective Optimization.
'''

class MOO:
    '''
    Base class of MOO algorithm framework.
    '''
    algo = None

    def __init__(self, problem, algo_cfg):
        '''
        Initialize a MOO algorithm.

        Parameters
        ----------
        problem: problem.Problem
            The original / real optimization problem.
        algo_cfg: dict
            Algorithm configurations.
        '''
        self.real_problem = problem
        self.n_var, self.n_obj = problem.n_var, problem.n_obj
        self.transformation = self.real_problem.transformation # data transformation between all input types and continuous
        self.batch_size = algo_cfg['selection']['batch_size']

    def solve(self, X_init, Y_init):
        '''
        Solve the real multi-objective problem from initial data.

        Parameters
        ----------
        X_init: np.array
            Initial design variables.
        Y_init: np.array
            Initial performance values.

        Returns
        -------
        X_next: np.array
            Proposed design samples to evaluate next.
        Y_prediction: tuple
            (None, None) because there is no prediction in MOO algorithms.
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
        '''
        Solve for the offsprings given the parent population.

        Parameters
        ----------
        pop: pymoo.model.population.Population
            The parent population.
        
        Returns
        -------
        pymoo.model.population.Population
            The offspring population.
        '''
        raise NotImplementedError

    def predict(self, X_init, Y_init, X_next):
        return None, None

