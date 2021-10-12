'''
Gaussian process surrogate model.
'''

import numpy as np
import math
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import RBF, ConstantKernel
from sklearn.gaussian_process.kernels import Matern as MaternKernel, _check_length_scale
from sklearn.utils.optimize import _check_optimize_result
from scipy.optimize import minimize
from scipy.linalg import solve_triangular
from scipy.spatial.distance import pdist, cdist, squareform
from scipy.special import kv, gamma

from autooed.mobo.surrogate_model.base import SurrogateModel
from autooed.utils.operand import safe_divide


class Matern(MaternKernel):
    '''
    Customized version of Matern kernel to avoid numerical error.
    '''
    def __call__(self, X, Y=None, eval_gradient=False):
        X = np.atleast_2d(X)
        length_scale = _check_length_scale(X, self.length_scale)
        if Y is None:
            dists = pdist(X / length_scale, metric='euclidean')
        else:
            if eval_gradient:
                raise ValueError(
                    "Gradient can only be evaluated when Y is None.")
            dists = cdist(X / length_scale, Y / length_scale,
                            metric='euclidean')

        if self.nu == 0.5:
            K = np.exp(-dists)
        elif self.nu == 1.5:
            K = dists * math.sqrt(3)
            K = (1. + K) * np.exp(-K)
        elif self.nu == 2.5:
            K = dists * math.sqrt(5)
            K = (1. + K + K ** 2 / 3.0) * np.exp(-K)
        else:  # general case; expensive to evaluate
            K = dists
            K[K == 0.0] += np.finfo(float).eps  # strict zeros result in nan
            tmp = (math.sqrt(2 * self.nu) * K)
            K.fill((2 ** (1. - self.nu)) / gamma(self.nu))
            K *= tmp ** self.nu
            K *= kv(self.nu, tmp)

        if Y is None:
            # convert from upper-triangular matrix to square matrix
            K = squareform(K)
            np.fill_diagonal(K, 1)

        if eval_gradient:
            if self.hyperparameter_length_scale.fixed:
                # Hyperparameter l kept fixed
                K_gradient = np.empty((X.shape[0], X.shape[0], 0))
                return K, K_gradient

            # We need to recompute the pairwise dimension-wise distances
            if self.anisotropic:
                D = (X[:, np.newaxis, :] - X[np.newaxis, :, :])**2 \
                    / (length_scale ** 2)
            else:
                D = squareform(dists**2)[:, :, np.newaxis]

            if self.nu == 0.5:
                K_gradient = safe_divide(K[..., np.newaxis] * D,
                    np.sqrt(D.sum(2))[:, :, np.newaxis])
                K_gradient[~np.isfinite(K_gradient)] = 0
            elif self.nu == 1.5:
                K_gradient = \
                    3 * D * np.exp(-np.sqrt(3 * D.sum(-1)))[..., np.newaxis]
            elif self.nu == 2.5:
                tmp = np.sqrt(5 * D.sum(-1))[..., np.newaxis]
                K_gradient = 5.0 / 3.0 * D * (tmp + 1) * np.exp(-tmp)
            else:
                # approximate gradient numerically
                def f(theta):  # helper function
                    return self.clone_with_theta(theta)(X, Y)
                return K, _approx_fprime(self.theta, f, 1e-10)

            if not self.anisotropic:
                return K, K_gradient[:, :].sum(-1)[:, :, np.newaxis]
            else:
                return K, K_gradient
        else:
            return K


def constrained_optimization(obj_func, initial_theta, bounds):
    '''
    Customized version of constrained optimization to avoid convergence warning.
    '''
    opt_res = minimize(obj_func, initial_theta, method="L-BFGS-B", jac=True, bounds=bounds)
    # NOTE: Temporarily disable the checking below because of the numerical instability sometimes.
    # _check_optimize_result("lbfgs", opt_res)
    return opt_res.x, opt_res.fun


class GaussianProcess(SurrogateModel):
    '''
    Gaussian process.
    '''
    def __init__(self, problem, nu=1, **kwargs):
        '''
        Initialize a Gaussian process.

        Parameters
        ----------
        problem: autooed.problem.Problem
            The optimization problem.
        nu: int
            The parameter nu controlling the type of the Matern kernel. Choices are 1, 3, 5 and -1.
        '''
        super().__init__(problem)
        
        self.nu = nu
        self.gps = []

        for _ in range(self.n_obj):
            if nu > 0:
                main_kernel = Matern(length_scale=np.ones(self.n_var), length_scale_bounds=(np.sqrt(1e-3), np.sqrt(1e3)), nu=0.5 * nu)
            else:
                main_kernel = RBF(length_scale=np.ones(self.n_var), length_scale_bounds=(np.sqrt(1e-3), np.sqrt(1e3)))
            
            kernel = ConstantKernel(constant_value=1.0, constant_value_bounds=(np.sqrt(1e-3), np.sqrt(1e3))) * \
                main_kernel + \
                ConstantKernel(constant_value=1e-2, constant_value_bounds=(np.exp(-6), np.exp(0)))
            
            gp = GaussianProcessRegressor(kernel=kernel, optimizer=constrained_optimization)
            self.gps.append(gp)

    def _fit(self, X, Y):
        for i, gp in enumerate(self.gps):
            gp.fit(X, Y[:, i])
        
    def _evaluate(self, X, std, gradient, hessian):
        F, dF, hF = [], [], [] # mean
        S, dS, hS = [], [], [] # std

        for gp in self.gps:

            # mean
            K = gp.kernel_(X, gp.X_train_) # K: shape (N, N_train)
            y_mean = K.dot(gp.alpha_)
            
            F.append(y_mean) # y_mean: shape (N,)

            if std:
                if gp._K_inv is None:
                    L_inv = solve_triangular(gp.L_.T,
                                                np.eye(gp.L_.shape[0]))
                    gp._K_inv = L_inv.dot(L_inv.T)

                y_var = gp.kernel_.diag(X)
                y_var -= np.einsum("ij,ij->i",
                                    np.dot(K, gp._K_inv), K)

                y_var_negative = y_var < 0
                if np.any(y_var_negative):
                    y_var[y_var_negative] = 0.0

                y_std = np.sqrt(y_var)

                S.append(y_std) # y_std: shape (N,)

            if not (gradient or hessian): continue

            ell = np.exp(gp.kernel_.theta[1:-1]) # ell: shape (n_var,)
            sf2 = np.exp(gp.kernel_.theta[0]) # sf2: shape (1,)
            d = np.expand_dims(cdist(X / ell, gp.X_train_ / ell), 2) # d: shape (N, N_train, 1)
            X_, X_train_ = np.expand_dims(X, 1), np.expand_dims(gp.X_train_, 0)
            dd_N = X_ - X_train_ # numerator
            dd_D = d * ell ** 2 # denominator
            dd = safe_divide(dd_N, dd_D) # dd: shape (N, N_train, n_var)

            if self.nu == 1:
                dK = -sf2 * np.exp(-d) * dd

            elif self.nu == 3:
                dK = -3 * sf2 * np.exp(-np.sqrt(3) * d) * d * dd

            elif self.nu == 5:
                dK = -5. / 3 * sf2 * np.exp(-np.sqrt(5) * d) * (1 + np.sqrt(5) * d) * d * dd

            else: # RBF
                dK = -sf2 * np.exp(-0.5 * d ** 2) * d * dd

            dK_T = dK.transpose(0, 2, 1) # dK: shape (N, N_train, n_var), dK_T: shape (N, n_var, N_train)
                
            if gradient:
                dy_mean = dK_T @ gp.alpha_ # gp.alpha_: shape (N_train,)
                dF.append(dy_mean) # dy_mean: shape (N, n_var)

                # TODO: check
                if std:
                    K = np.expand_dims(K, 1) # K: shape (N, 1, N_train)
                    K_Ki = K @ gp._K_inv # gp._K_inv: shape (N_train, N_train), K_Ki: shape (N, 1, N_train)
                    dK_Ki = dK_T @ gp._K_inv # dK_Ki: shape (N, n_var, N_train)

                    dy_var = -np.sum(dK_Ki * K + K_Ki * dK_T, axis=2) # dy_var: shape (N, n_var)
                    dy_std = 0.5 * safe_divide(dy_var, y_std) # dy_std: shape (N, n_var)
                    dS.append(dy_std)

            if hessian:
                d = np.expand_dims(d, 3) # d: shape (N, N_train, 1, 1)
                dd = np.expand_dims(dd, 2) # dd: shape (N, N_train, 1, n_var)
                hd_N = d * np.expand_dims(np.eye(len(ell)), (0, 1)) - np.expand_dims(X_ - X_train_, 3) * dd # numerator
                hd_D = d ** 2 * np.expand_dims(ell ** 2, (0, 1, 3)) # denominator
                hd = safe_divide(hd_N, hd_D) # hd: shape (N, N_train, n_var, n_var)

                if self.nu == 1:
                    hK = -sf2 * np.exp(-d) * (hd - dd ** 2)

                elif self.nu == 3:
                    hK = -3 * sf2 * np.exp(-np.sqrt(3) * d) * (d * hd + (1 - np.sqrt(3) * d) * dd ** 2)

                elif self.nu == 5:
                    hK = -5. / 3 * sf2 * np.exp(-np.sqrt(5) * d) * (-5 * d ** 2 * dd ** 2 + (1 + np.sqrt(5) * d) * (dd ** 2 + d * hd))

                else: # RBF
                    hK = -sf2 * np.exp(-0.5 * d ** 2) * ((1 - d ** 2) * dd ** 2 + d * hd)

                hK_T = hK.transpose(0, 2, 3, 1) # hK: shape (N, N_train, n_var, n_var), hK_T: shape (N, n_var, n_var, N_train)

                hy_mean = hK_T @ gp.alpha_ # hy_mean: shape (N, n_var, n_var)
                hF.append(hy_mean)

                # TODO: check
                if std:
                    K = np.expand_dims(K, 2) # K: shape (N, 1, 1, N_train)
                    dK = np.expand_dims(dK_T, 2) # dK: shape (N, n_var, 1, N_train)
                    dK_Ki = np.expand_dims(dK_Ki, 2) # dK_Ki: shape (N, n_var, 1, N_train)
                    hK_Ki = hK_T @ gp._K_inv # hK_Ki: shape (N, n_var, n_var, N_train)

                    hy_var = -np.sum(hK_Ki * K + 2 * dK_Ki * dK + K_Ki * hK_T, axis=3) # hy_var: shape (N, n_var, n_var)
                    hy_std = 0.5 * safe_divide(hy_var * y_std - dy_var * dy_std, y_var) # hy_std: shape (N, n_var, n_var)
                    hS.append(hy_std)

        F = np.stack(F, axis=1)
        dF = np.stack(dF, axis=1) if gradient else None
        hF = np.stack(hF, axis=1) if hessian else None
        
        S = np.stack(S, axis=1) if std else None
        dS = np.stack(dS, axis=1) if std and gradient else None
        hS = np.stack(hS, axis=1) if std and hessian else None

        out = {'F': F, 'dF': dF, 'hF': hF, 'S': S, 'dS': dS, 'hS': hS}
        return out
