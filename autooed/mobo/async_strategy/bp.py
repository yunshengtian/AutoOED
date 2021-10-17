'''
'''

import numpy as np

from autooed.mobo.factory import init_async_acquisition
from autooed.mobo.async_strategy.base import AsyncStrategy


class BelieverPenalizer(AsyncStrategy):

    def __init__(self, surrogate_model, acquisition, factor=0.2, penalize_acq='lp', **kwargs):
        super().__init__(surrogate_model, acquisition)
        self.factor = factor
        self.penalize_acq = penalize_acq
    
    def fit(self, X, Y, X_busy):
        # fit surrogate models based on true data
        self.surrogate_model.fit(X, Y)

        # determine KB and LP indices
        _, Y_busy_std = self.surrogate_model.predict(X_busy, std=True)
        Y_busy_std = self.surrogate_model.normalization.scale(y=Y_busy_std)
        KB_prob = np.maximum(1 - self.factor * Y_busy_std, 0.0)
        KB_idx = (np.random.uniform(size=Y_busy.shape) < KB_prob).all(axis=1)
        LP_idx = ~KB_idx

        # aggregate believed data, redefine busy data
        X = np.vstack([X, X_busy[KB_idx]])
        Y = np.vstack([Y, Y_busy[KB_idx]])
        X_busy = X_busy[LP_idx] if np.sum(LP_idx) > 0 else None

        # fit surrogate models based on believed data
        self.surrogate_model.fit(X, Y)

        # fit penalized acquisition functions
        acquisition = init_async_acquisition(self.penalize_acq, self.acquisition)
        acquisition.fit(X, Y, X_busy)

        return X, Y, acquisition
