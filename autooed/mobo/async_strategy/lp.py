'''
'''

from autooed.mobo.factory import init_async_acquisition
from autooed.mobo.async_strategy.base import AsyncStrategy


class LocalPenalizer(AsyncStrategy):

    def __init__(self, surrogate_model, acquisition, penalize_acq='lp', **kwargs):
        super().__init__(surrogate_model, acquisition)
        self.penalize_acq = penalize_acq
    
    def fit(self, X, Y, X_busy):
        # fit surrogate models
        self.surrogate_model.fit(X, Y)

        # fit penalized acquisition functions
        acquisition = init_async_acquisition(self.penalize_acq, self.acquisition)
        acquisition.fit(X, Y, X_busy)

        return X, Y, acquisition

