'''
Multi-objective solver for finding the Pareto front of the surrogate problem.
'''

from abc import ABC, abstractmethod
import numpy as np

from autooed.utils.sampling import lhs
from autooed.mobo.surrogate_problem import SurrogateProblem


class Solver(ABC):
    '''
    Base class of multi-objective solver.
    '''
    def __init__(self, problem, **kwargs):
        '''
        Initialize a solver.

        Parameters
        ----------
        '''
        self.real_problem = problem # real problem
        self.problem = None # surrogate problem
        self.transformation = problem.transformation

    def solve(self, X, Y, batch_size, acquisition):
        '''
        Solve the multi-objective problem and propose a batch of candidates.

        Parameters
        ----------
        X: np.array
            Current design variables (raw).
        batch_size: int
            Size of the candidate batch.

        Returns
        -------
        X_candidate: np.array
            Proposed candidate design variables (raw).
        Y_candidate: np.array
            Objective values of proposed candidate designs.
        '''
        self.problem = SurrogateProblem(self.real_problem, acquisition)
        X = self.transformation.do(X)
        X_candidate, Y_candidate = self._solve(X, Y, batch_size)
        X_candidate = self.transformation.undo(X_candidate)
        return X_candidate, Y_candidate

    @abstractmethod
    def _solve(self, X, Y):
        '''
        Solve the multi-objective problem and propose a batch of candidates.

        Parameters
        ----------
        X: np.array
            Current design variables (continuous).

        Returns
        -------
        X_candidate: np.array
            Proposed candidate design variables (continuous).
        Y_candidate: np.array
            Objective values of proposed candidate designs.
        '''
        pass
