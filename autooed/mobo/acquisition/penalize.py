import numpy as np
from scipy.stats import norm
from scipy.optimize import minimize

from autooed.utils.sampling import lhs
from autooed.utils.operand import safe_divide
from autooed.mobo.acquisition.base import Acquisition
from autooed.mobo.surrogate_model.gp import GaussianProcess


class PenalizedAcquisition(Acquisition):

    def __init__(self, base_acq):
        self.base_acq = base_acq
        self.X_busy = None

    def fit(self, X, Y, X_busy=None, dtype='raw'):
        '''
        Fit the parameters of acquisition function from raw data.

        Parameters
        ----------
        X: np.array
            Input design variables (raw).
        Y: np.array
            Input performance values.
        '''
        assert dtype in ['raw', 'continuous', 'normalized'], f'Undefined data type {dtype} in acquisition fitting'

        self.base_acq.fit(X, Y, dtype=dtype)
        if X_busy is None: return

        if dtype == 'raw':
            X = self.transformation.do(X)
            X_busy = self.transformation.do(X_busy)

        self.X_busy = X_busy
        self._fit(X, Y)

    def evaluate(self, X, dtype='raw', gradient=False, hessian=False):
        '''
        Evaluate the acquisition values of the design variables.
        
        Parameters
        ----------
        X: np.array
            Input design variables.
        gradient: bool
            Whether to calculate the gradient of the prediction.
        hessian: bool
            Whether to calculate the hessian of the prediction.
        
        Returns
        -------
        F: np.array
            Acquisition value, shape (N, n_obj).
        dF: np.array
            Gradient of F, shape (N, n_obj, n_var).
        hF: np.array
            Hessian of F, shape (N, n_obj, n_var, n_var).
        '''
        assert dtype in ['raw', 'continuous', 'normalized'], f'Undefined data type {dtype} in acquisition evaluation'

        if self.X_busy is None:
            return self.base_acq.evaluate(X, dtype, gradient, hessian)

        if dtype == 'raw':
            X = self.transformation.do(X)
        
        return self._evaluate(X, gradient, hessian)


def distance(X, X0):
    X, X0 = np.atleast_2d(X), np.atleast_2d(X0)
    return np.sqrt(np.square(X[:, None, :] - X0[None, :, :]).sum(axis=-1))


def hammer_function(X, X0, R, S):
    '''
    Define the exclusion zones
    '''
    return norm.logcdf(safe_divide(distance(X, X0)[:, :, None] - R, S)).sum(1)


def calc_dF_norm(X, surrogate_model):
    val = surrogate_model.evaluate(X, dtype='continuous', std=False, gradient=True, hessian=False)
    return -np.linalg.norm(val['dF'], axis=-1)


def calc_dF_norm_per_obj(x, surrogate_model, i):
    x = np.atleast_2d(x)
    assert x.shape[0] == 1
    return calc_dF_norm(x, surrogate_model).flatten()[i]


def estimate_lipschitz_constant(surrogate_model, n_sample=500):
    '''
    Estimate Lipschitz constant from a surrogate model
    
    Returns
    -------
    L: float
    '''
    n_var, n_obj = surrogate_model.n_var, surrogate_model.n_obj

    # find a good x0
    X_sample = lhs(n_var, n_sample)
    dF_norm_sample = calc_dF_norm(X_sample, surrogate_model)

    # optimize for L for each objective
    bounds = np.vstack([np.zeros(n_var), np.ones(n_var)]).T
    L = np.zeros(n_obj)
    for i in range(n_obj):
        x0 = X_sample[np.argmin(dF_norm_sample[:, i])]
        res = minimize(calc_dF_norm_per_obj, x0, method='L-BFGS-B', bounds=bounds, args=(surrogate_model, i))
        L[i] = -float(res.fun)
        if L[i] < 1e-7: L[i] = 10.0

    return L


def estimate_local_lipschitz_constant(surrogate_model, X_busy, n_sample=500):
    '''
    Estimate local Lipschitz constant from a surrogate model
    
    Returns
    -------
    L: np.array ~ (n_busy, n_obj)
    '''
    assert isinstance(surrogate_model, GaussianProcess)
    n_var, n_obj = surrogate_model.n_var, surrogate_model.n_obj
    n_busy = len(X_busy)

    L = np.zeros((n_busy, n_obj))
    for i in range(n_obj):
        length_scale = surrogate_model.gps[i].kernel_.get_params()['k1__k2__length_scale']
        lower_bounds = np.maximum(X_busy - 0.5 * length_scale, 0.0)
        upper_bounds = np.minimum(X_busy + 0.5 * length_scale, 1.0)
        
        for j in range(n_busy):
            bounds = np.vstack([lower_bounds[j], upper_bounds[j]]).T
            X_sample = lower_bounds[j] + lhs(n_var, n_sample) * (upper_bounds[j] - lower_bounds[j])
            dF_i_norm_sample = calc_dF_norm(X_sample, surrogate_model)[:, i]
            x0 = X_sample[np.argmin(dF_i_norm_sample)]
            res = minimize(calc_dF_norm_per_obj, x0, method='L-BFGS-B', bounds=bounds, args=(surrogate_model, i))
            L[j][i] = -float(res.fun)
            if L[j][i] < 1e-7: L[j][i] = 10.0

    return L


class LocalPenalization(PenalizedAcquisition):
    '''
    Local Penalization.
    '''
    def _fit(self, X, Y):
        Y_busy_mean, Y_busy_std = self.base_acq.surrogate_model.predict(self.X_busy, dtype='continuous', std=True)
        L = estimate_lipschitz_constant(self.base_acq.surrogate_model)
        self.R = np.abs(Y_busy_mean - np.min(Y, axis=0)) / L
        self.S = Y_busy_std / L

    def _evaluate(self, X, gradient, hessian):
        '''
        Creates a penalized acquisition function using 'hammer' functions
        around the points collected in the batch
        .. Note:: the penalized acquisition is always mapped to the log
        space. This way gradients can be computed additively and are more
        stable.
        '''
        F, dF, hF = self.base_acq.evaluate(X, gradient, hessian)

        F = np.log1p(np.exp(-F)) # softplus transform
        F = -np.exp(np.log(F) + hammer_function(X, self.X_busy, self.R, self.S))

        if gradient or hessian:
            raise Exception('Gradient or hessian computation is not implemented yet in Local Penalization.')

        return F, None, None


class LocalLipschitzPenalization(LocalPenalization):
    '''
    Local Penalization with local Lipschitz constant.
    '''
    def _fit(self, X, Y):
        Y_busy_mean, Y_busy_std = self.base_acq.surrogate_model.predict(self.X_busy, dtype='continuous', std=True)
        L = estimate_local_lipschitz_constant(self.base_acq.surrogate_model, self.X_busy)
        self.R = np.abs(Y_busy_mean - np.min(Y, axis=0)) / L
        self.S = Y_busy_std / L


class HardLocalPenalization(PenalizedAcquisition):
    '''
    Hard Local Penalization. (TODO: check implementation)
    '''
    def _fit(self, X, Y):
        Y_busy_mean, Y_busy_std = self.base_acq.surrogate_model.predict(self.X_busy, dtype='continuous', std=True)
        L = estimate_lipschitz_constant(self.base_acq.surrogate_model)
        self.R = (np.max(Y, axis=0) - Y_busy_mean) / L
        self.S = Y_busy_std / L

    def _evaluate(self, X, gradient, hessian):
        F, dF, hF = self.base_acq.evaluate(X, gradient, hessian)

        F = np.log1p(np.exp(-F)) # softplus transform

        h_vals = 1 / ((self.R + self.S)[None, :, :] * distance(X, self.X_busy)[:, :, None]).prod(axis=1).T
        clipped_h_vals = []
        for i in range(h_vals.shape[0]):
            clipped_h_vals.append(np.linalg.norm(np.vstack([h_vals[None, i], np.ones_like(h_vals[None, i])]), -5, axis=0))
        clipped_h_vals = np.vstack(clipped_h_vals).T
        
        F *= -clipped_h_vals

        if gradient or hessian:
            raise Exception('Gradient or hessian computation is not implemented yet in Hard Local Penalization.')

        return F, None, None
