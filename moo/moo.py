import numpy as np
import pandas as pd
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.operators.sampling.random_sampling import FloatRandomSampling
from pymoo.operators.sampling.latin_hypercube_sampling import LatinHypercubeSampling
from external import lhs

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
            ref_point: reference point for hypervolume calculation
            algo_cfg: algorithm configurations
        '''
        self.real_problem = problem
        self.n_var, self.n_obj = problem.n_var, problem.n_obj
        self.ref_point = problem.ref_point

        self.pop_size = algo_cfg['solver']['batch_size']
        self.pop_init_method = algo_cfg['solver']['pop_init_method']

    def solve(self, X, Y):
        '''
        Solve the multi-objective problem
        '''
        # initialize population
        sampling = self._get_sampling(X, Y)

        # setup algorithm
        algo = self.algo(pop_size=self.pop_size, sampling=sampling)

        # optimization
        res = minimize(self.real_problem, algo, n_gen=1)

        # construct solution
        X_next = res.pop.get('X')

        return X_next

    def predict(self, X_init, Y_init, X_next):
        '''
        Predict the performance of X_next based on initial data (X_init, Y_init), not supported for moo algorithms
        '''
        sample_len = len(X_next)
        Y_expected = np.ones((sample_len, self.n_obj)) * np.inf
        Y_uncertainty = np.zeros((sample_len, self.n_obj))
        return Y_expected, Y_uncertainty

    def _get_sampling(self, X, Y):
        '''
        Initialize population from data
        '''
        if self.pop_init_method == 'lhs':
            sampling = LatinHypercubeSampling()
        elif self.pop_init_method == 'nds':
            sorted_indices = NonDominatedSorting().do(Y)
            pop_size = self.pop_size
            sampling = X[np.concatenate(sorted_indices)][:pop_size]
            # NOTE: use lhs if current samples are not enough
            if len(sampling) < pop_size:
                rest_sampling = lhs(X.shape[1], pop_size - len(sampling))
                sampling = np.vstack([sampling, rest_sampling])
        elif self.pop_init_method == 'random':
            sampling = FloatRandomSampling()
        else:
            raise NotImplementedError

        return sampling
