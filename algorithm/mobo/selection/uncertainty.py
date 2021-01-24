import numpy as np
from .base import Selection


class Uncertainty(Selection):
    '''
    Uncertainty
    '''
    def select(self, solution, surrogate_model, normalization, curr_pset, curr_pfront):

        X = solution['x']
        val = surrogate_model.evaluate(X, std=True)
        Y_std = val['S']
        X = normalization.undo(x=X)

        uncertainty = np.prod(Y_std, axis=1)
        top_indices = np.argsort(uncertainty)[::-1][:self.batch_size]
        return X[top_indices], None