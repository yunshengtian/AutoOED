'''
Random selection.
'''

import numpy as np

from autooed.mobo.selection.base import Selection


class Random(Selection):
    '''
    Selection by random sampling.
    '''
    def _select(self, X_candidate, Y_candidate, X, Y, batch_size):
        random_indices = np.random.choice(len(X_candidate), size=batch_size, replace=False)
        return X_candidate[random_indices]
