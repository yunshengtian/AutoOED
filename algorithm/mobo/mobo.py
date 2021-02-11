import numpy as np
from algorithm.mobo.surrogate_problem import SurrogateProblem
from algorithm.mobo.utils import Timer, find_pareto_front
from algorithm.mobo.factory import init_framework
from algorithm.mobo.normalization import StandardNormalization

'''
Main algorithm framework for Multi-Objective Bayesian Optimization
'''

class MOBO:
    '''
    Base class of algorithm framework, inherit this class with different specifications to create new algorithm classes
    '''
    spec = {}

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

        bounds = np.array([problem.xl, problem.xu])
        self.normalization = StandardNormalization(bounds) # data normalization for surrogate model fitting
        self.transformation = self.real_problem.transformation # data transformation between all input types and continuous

        # framework components
        framework = init_framework(self.spec, algo_cfg)
        
        self.surrogate_model = framework['surrogate'] # surrogate model
        self.acquisition = framework['acquisition'] # acquisition function
        self.solver = framework['solver'] # multi-objective solver for finding the paretofront
        self.selection = framework['selection'] # selection method for choosing new (batch of) samples to evaluate on real problem

        # other component-specific information that needs to be stored or exported (TODO: clean)
        self.info = None

    def solve(self, X_init, Y_init):
        '''
        Solve the real multi-objective problem from initial data (X_init, Y_init)
        '''
        # forward transformation
        X_init = self.transformation.do(X_init)

        # determine reference point from data if not specified by arguments
        if self.ref_point is None:
            self.ref_point = np.max(Y_init, axis=0)
        self.selection.set_ref_point(self.ref_point)

        # calculate current pareto set and pareto front
        curr_pfront, pidx = find_pareto_front(Y_init, return_index=True)
        curr_pset = X_init[pidx]

        timer = Timer(stdout=False)

        # data normalization
        self.normalization.fit(X_init, Y_init)
        X, Y = self.normalization.do(X_init, Y_init)

        # build surrogate models
        self.surrogate_model.fit(X, Y)
        timer.log('Surrogate model fitted')

        # define acquisition functions
        self.acquisition.fit(X, Y)

        # solve surrogate problem
        surr_problem = SurrogateProblem(self.real_problem, self.surrogate_model, self.acquisition, self.normalization)
        solution = self.solver.solve(surr_problem, X, Y)
        timer.log('Surrogate problem solved')

        # batch point selection
        self.selection.fit(X, Y)
        X_next, self.info = self.selection.select(solution, self.surrogate_model, self.normalization, curr_pset, curr_pfront)
        timer.log('Next sample batch selected')

        # evaluate prediction and uncertainty on surrogate models
        val = self.surrogate_model.evaluate(self.normalization.do(x=X_next), std=True)
        Y_expected = self.normalization.undo(y=val['F'])
        Y_uncertainty = val['S']
        timer.log('Performance of next batch predicted')

        # backward transformation
        X_next = self.transformation.undo(X_next)

        return X_next, (Y_expected, Y_uncertainty)

    def predict(self, X_init, Y_init, X_next):
        '''
        Predict the performance of X_next based on initial data (X_init, Y_init)
        '''
        # forward transformation
        X_init = self.transformation.do(X_init)
        X_next = self.transformation.do(X_next)
        
        timer = Timer(stdout=False)

        # data normalization
        self.normalization.fit(X_init, Y_init)
        X, Y = self.normalization.do(X_init, Y_init)

        # build surrogate models
        self.surrogate_model.fit(X, Y)
        timer.log('Surrogate model fitted')

        # evalaute prediction and uncertainty on surrogate models
        val = self.surrogate_model.evaluate(self.normalization.do(x=X_next), std=True)
        Y_expected = self.normalization.undo(y=val['F'])
        Y_uncertainty = val['S']
        timer.log('Performance of next batch predicted')

        return Y_expected, Y_uncertainty

    def __str__(self):
        return \
            '========== Framework Description ==========\n' + \
            f'# algorithm: {self.__class__.__name__}\n' + \
            f'# surrogate: {self.surrogate_model.__class__.__name__}\n' + \
            f'# acquisition: {self.acquisition.__class__.__name__}\n' + \
            f'# solver: {self.solver.__class__.__name__}\n' + \
            f'# selection: {self.selection.__class__.__name__}\n'