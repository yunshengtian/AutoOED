import numpy as np
import pandas as pd
from collections.abc import Iterable
from pymoo.model.individual import Individual
from pymoo.model.population import Population
from pymoo.model.problem import Problem

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
        self.algo = self.algo(pop_size=self.batch_size)

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

        # filter out best samples so far
        pop = self.algo.survival.do(self.real_problem, pop, self.batch_size, algorithm=self.algo)

        # mate for offsprings (TODO: check) (NOTE: assume the while loop can stop)
        off = Population(0, individual=Individual())
        while len(off) < self.batch_size:
            new_off = self.algo.mating.do(self.real_problem, pop, len(pop), algorithm=self.algo)
            new_X = new_off.get('X')
            if self.real_problem.n_constr > 0:
                new_G = np.array([self.real_problem.evaluate_constraint(x) for x in new_X])
                new_CV = Problem.calc_constraint_violation(new_G)
                valid_idx = new_CV <= 0
            else:
                valid_idx = np.arange(len(new_off))
            if np.any(valid_idx):
                off = Population.merge(off, new_off[valid_idx])

        X_next = off.get('X')[:self.batch_size]
        
        # backward transformation
        X_next = self.transformation.undo(X_next)

        return X_next

    def predict(self, X_init, Y_init, X_next):
        '''
        Predict the performance of X_next based on initial data (X_init, Y_init), not supported for moo algorithms
        '''
        # forward transformation
        X_init = self.transformation.do(X_init)
        X_next = self.transformation.do(X_next)

        sample_len = len(X_next)
        Y_expected = np.ones((sample_len, self.n_obj)) * np.inf
        Y_uncertainty = np.zeros((sample_len, self.n_obj))
        
        return Y_expected, Y_uncertainty

