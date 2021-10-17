'''
Asynchronous MOBO strategy.
'''

from abc import ABC, abstractmethod


class AsyncStrategy(ABC):

    def __init__(self, surrogate_model, acquisition, **kwargs):
        self.surrogate_model = surrogate_model
        self.acquisition = acquisition

    @abstractmethod
    def fit(self, X, Y, X_busy):
        pass
