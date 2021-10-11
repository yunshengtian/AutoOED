'''
Uncertainty selection.
'''

import numpy as np

from autooed.mobo.selection.base import Selection


class Uncertainty(Selection):
    '''
    Selection based on uncertainty.
    '''
    def _select(self, X_candidate, Y_candidate, X, Y, batch_size):
        val = self.surrogate_model.evaluate(X_candidate, dtype='continuous', std=True)
        Y_candidate_std = val['S']
        uncertainty = np.prod(Y_candidate_std, axis=1)
        top_indices = np.argsort(uncertainty)[::-1][:batch_size]
        return X_candidate[top_indices]
