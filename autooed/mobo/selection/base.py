'''
Selection methods for new batch of samples to evaluate on real problem.
'''

from abc import ABC, abstractmethod
import numpy as np


class Selection(ABC):
    '''
    Base class of selection method.
    '''
    def __init__(self, surrogate_model, **kwargs):
        '''
        Initialize a selection method.

        Parameters
        ----------
        '''
        self.surrogate_model = surrogate_model
        self.transformation = surrogate_model.transformation

    def select(self, X_candidate, Y_candidate, X, Y, batch_size):
        '''
        Select the next batch of design samples to evaluate from proposed candidates.

        Parameters
        ----------
        X_candidate: np.array
            Candidate design samples (raw).
        Y_candidate: np.array
            Objective values of candidate design samples.
        X: np.array
            Current design samples (raw).
        Y: np.array
            Objective values of current design samples.
        batch_size: int
            Batch size.
        Returns
        -------
        X_next: np.array
            Next batch of samples selected (raw).
        '''

        # fill the candidates in case less than batch size (TODO: optimize)
        len_candidate = len(X_candidate)
        if len_candidate < batch_size:
            indices = np.concatenate([np.arange(len_candidate), np.random.choice(np.arange(len_candidate), batch_size - len_candidate)])
            X_candidate = X_candidate[indices]
            Y_candidate = Y_candidate[indices]

        X_candidate = self.transformation.do(X_candidate)
        X = self.transformation.do(X)

        X_next = self._select(X_candidate, Y_candidate, X, Y, batch_size)
        X_next = self.transformation.undo(X_next)
        return X_next

    @abstractmethod
    def _select(self, X_candidate, Y_candidate, X, Y, batch_size):
        '''
        Select new samples from the solution obtained by solver.

        Parameters
        ----------
        X_candidate: np.array
            Candidate design samples (continuous).
        Y_candidate: np.array
            Objective values of candidate design samples.
        X: np.array
            Current design samples (continuous).
        Y: np.array
            Objective values of current design samples.
        batch_size: int
            Batch size.
        Returns
        -------
        X_next: np.array
            Next batch of samples selected (continuous).
        '''
        pass
