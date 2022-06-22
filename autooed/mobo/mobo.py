'''
Main algorithm framework for Multi-Objective Bayesian Optimization.
'''

import numpy as np

from autooed.mobo.factory import init_surrogate_model, init_acquisition, init_solver, init_selection
from autooed.mobo.async_strategy.factory import init_async_strategy
from autooed.utils.pareto import convert_minimization


class MOBO:
    '''
    Base class of MOBO algorithm framework. Inherit this class with different specifications to create new algorithm classes.

    Attributes
    ----------
    spec: dict
        Algorithm specifications including 'surrogate', 'acquisition', 'solver' and 'selection'.
    '''
    spec = {
        'surrogate': None,
        'acquisition': None,
        'solver': None,
        'selection': None,
    }

    def __init__(self, problem, module_cfg):
        '''
        Initialize a MOBO algorithm.

        Parameters
        ----------
        problem: autooed.problem.Problem
            The optimization problem.
        module_cfg: dict
            Module configurations. (TODO: clean)
        '''
        self.problem = problem
        self.n_var, self.n_obj = problem.n_var, problem.n_obj
        self.obj_type = problem.obj_type
        self.bounds = np.array([problem.xl, problem.xu])

        # data transformation between all domains and continuous
        self.transformation = self.problem.transformation # TODO: clean?

        # surrogate model
        self.surrogate_model = init_surrogate_model(self.spec['surrogate'], module_cfg['surrogate'],
            self.problem)
        
        # acquisition function
        self.acquisition = init_acquisition(self.spec['acquisition'], module_cfg['acquisition'],
            self.surrogate_model)

        # multi-objective solver for finding the pareto front
        self.solver = init_solver(self.spec['solver'], module_cfg['solver'],
            self.problem)

        # selection method for choosing new batch of samples to evaluate on real problem
        self.selection = init_selection(self.spec['selection'], module_cfg['selection'],
            self.surrogate_model)

        # asynchronous optimization strategy
        if 'async' in module_cfg and module_cfg['async'] != None:
            self.async_strategy = init_async_strategy(module_cfg['async'],
                self.surrogate_model, self.acquisition)
        else:
            self.async_strategy = None

    def optimize(self, X, Y, X_busy, batch_size):
        '''
        Optimize for the next batch of samples given the initial data.

        Parameters
        ----------
        X: np.array
            Initial design variables.
        Y: np.array
            Initial objective values.
        X_busy: np.array
            Design variables currently being evaluated.
        batch_size: int
            Batch size.

        Returns
        -------
        X_next: np.array
            Proposed design samples to evaluate next.
        '''
        # convert maximization to minimization
        Y = convert_minimization(Y, self.obj_type)

        if self.async_strategy is None or X_busy is None:
            return self._optimize(X, Y, batch_size)
        else:
            return self._optimize_async(X, Y, X_busy, batch_size)

    def _optimize(self, X, Y, batch_size):
        '''
        Synchronous optimization.
        '''
        # fit surrogate models
        self.surrogate_model.fit(X, Y)

        # fit acquisition functions
        self.acquisition.fit(X, Y)

        # solve surrogate problem
        X_candidate, Y_candidate = self.solver.solve(X, Y, batch_size, self.acquisition)

        # next batch selection
        X_next = self.selection.select(X_candidate, Y_candidate, X, Y, batch_size)

        return X_next

    def _optimize_async(self, X, Y, X_busy, batch_size):
        '''
        Asynchronous optimization.
        '''
        # fit surrogate models and acquisition functions based on the asynchronous strategy
        X, Y, acquisition = self.async_strategy.fit(X, Y, X_busy)

        # solve surrogate problem
        X_candidate, Y_candidate = self.solver.solve(X, Y, batch_size, acquisition)

        # next batch selection
        X_next = self.selection.select(X_candidate, Y_candidate, X, Y, batch_size)

        return X_next

    def predict(self, X, Y, X_next, fit=False):
        '''
        Predict the performance of X_next based on initial data.

        Parameters
        ----------
        X: np.array
            Initial design variables.
        Y: np.array
            Initial performance values.
        X_next: np.array
            Next batch of designs to be predicted.

        Returns
        -------
        Y_next_mean: np.array
            Mean of predicted objectives.
        Y_next_std: np.array
            Standard deviation of predicted objectives.
        '''
        # convert maximization to minimization
        Y = convert_minimization(Y, self.obj_type)

        if fit or self.async_strategy is not None:
            # fit surrogate models
            self.surrogate_model.fit(X, Y)

        # predict objectives
        Y_next_mean, Y_next_std = self.surrogate_model.predict(X_next, std=True)

        # convert back from minimization to maximization
        Y_next_mean = convert_minimization(Y_next_mean, self.obj_type)

        return Y_next_mean, Y_next_std

    def __str__(self):
        return \
            '========== Algorithm Setup ==========\n' + \
            f'# algorithm: {self.__class__.__name__}\n' + \
            f'# surrogate: {self.surrogate_model.__class__.__name__}\n' + \
            f'# acquisition: {self.acquisition.__class__.__name__}\n' + \
            f'# solver: {self.solver.__class__.__name__}\n' + \
            f'# selection: {self.selection.__class__.__name__}\n'
