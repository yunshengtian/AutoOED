'''
Upper Confidence Bound acquisition function.
'''

import numpy as np

from autooed.utils.operand import expand
from autooed.mobo.acquisition.base import Acquisition


class UpperConfidenceBound(Acquisition):
    '''
    Upper Confidence Bound.
    '''
    def __init__(self, surrogate_model, **kwargs):
        super().__init__(surrogate_model)
        self.n_sample = None

    def _fit(self, X, Y):
        self.n_sample = X.shape[0]

    def _evaluate(self, X, gradient, hessian):
        val = self.surrogate_model.evaluate(X, dtype='continuous', std=True, gradient=gradient, hessian=hessian)

        lamda = np.sqrt(np.log(self.n_sample) / self.n_sample)
        
        y_mean, y_std = val['F'], val['S']
        F = y_mean - lamda * y_std

        dF, hF = None, None
        dy_mean, hy_mean, dy_std, hy_std = val['dF'], val['hF'], val['dS'], val['hS']
        
        if gradient or hessian:
            dF_y_mean = np.ones_like(y_mean)
            dF_y_std = -lamda * np.ones_like(y_std)

            dF_y_mean, dF_y_std = expand(dF_y_mean), expand(dF_y_std)

        if gradient:
            dF = dF_y_mean * dy_mean + dF_y_std * dy_std

        if hessian:
            hF_y_mean = 0
            hF_y_std = 0

            dy_mean, dy_std = expand(dy_mean), expand(dy_std)
            dy_mean_T, dy_std_T = dy_mean.transpose(0, 1, 3, 2), dy_std.transpose(0, 1, 3, 2)
            dF_y_mean, dF_y_std = expand(dF_y_mean), expand(dF_y_std)

            hF = dF_y_mean * hy_mean + dF_y_std * hy_std + \
                hF_y_mean * dy_mean * dy_mean_T + hF_y_std * dy_std * dy_std_T

        return F, dF, hF
