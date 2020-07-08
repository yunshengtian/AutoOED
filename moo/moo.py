import numpy as np
import pandas as pd
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.operators.sampling.random_sampling import FloatRandomSampling
from pymoo.operators.sampling.latin_hypercube_sampling import LatinHypercubeSampling
from mobo.lhs import lhs

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

        return self._build_dataframe(X_next)

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

    def _build_dataframe(self, X):
        '''
        Build a dataframe from proposed samples X,
        where columns are: [x1, x2, ..., f1, f2, ..., expected_f1, expected_f2, ..., uncertianty_f1, uncertainty_f2, ...]
        '''
        data = {}
        sample_len = len(X)

        # design variables
        for i in range(self.n_var):
            data[f'x{i + 1}'] = X[:, i]

        # prediction and uncertainty
        for i in range(self.n_obj):
            data[f'f{i + 1}'] = np.zeros(sample_len)
        for i in range(self.n_obj):
            data[f'expected_f{i + 1}'] = np.ones(sample_len) * np.inf
        for i in range(self.n_obj):
            data[f'uncertainty_f{i + 1}'] = np.zeros(sample_len)

        return pd.DataFrame(data=data)
        