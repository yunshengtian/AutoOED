from abc import ABC, abstractmethod
import numpy as np
from numpy import linalg as LA
from sklearn.gaussian_process import GaussianProcessRegressor
from sklearn.gaussian_process.kernels import Matern, RBF, ConstantKernel
from sklearn.utils.optimize import _check_optimize_result
from scipy.optimize import minimize
from scipy.spatial.distance import cdist
from scipy.stats import norm
from scipy.stats.distributions import chi2
from scipy.linalg import solve_triangular
from external import lhs
from mobo.utils import safe_divide

'''
Surrogate model that predicts the performance of given design variables
'''

class SurrogateModel(ABC):
    '''
    Base class of surrogate model
    '''

    @abstractmethod
    def fit(self, X, Y):
        '''
        Fit the surrogate model from data (X, Y)
        '''
        pass

    @abstractmethod
    def evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
        '''
        Predict the performance given set of design variables X
        Input:
            std / calc_gradient / calc_hessian : whether to calculate std / gradient / hessian of prediction
        Output:
            val['F']: mean, shape (N, n_obj)
            val['dF']: gradient of mean, shape (N, n_obj, n_var)
            val['hF']: hessian of mean, shape (N, n_obj, n_var, n_var)
            val['S']: std, shape (N, n_obj)
            val['dS']: gradient of std, shape (N, n_obj, n_var)
            val['hS']: hessian of std, shape (N, n_obj, n_var, n_var)
        '''
        pass


class GaussianProcess(SurrogateModel):
    '''
    Gaussian process
    '''
    def __init__(self, n_var, n_obj, nu, **kwargs):
        self.n_var = n_var
        self.n_obj = n_obj
        self.nu = nu
        self.gps = []

        def constrained_optimization(obj_func, initial_theta, bounds):
            opt_res = minimize(obj_func, initial_theta, method="L-BFGS-B", jac=True, bounds=bounds)
            '''
            NOTE: Temporarily disable the checking below because this error sometimes occurs:
                ConvergenceWarning: lbfgs failed to converge (status=2):
                ABNORMAL_TERMINATION_IN_LNSRCH
                , though we already optimized enough number of iterations and scaled the data.
                Still don't know the exact reason of this yet.
            '''
            # _check_optimize_result("lbfgs", opt_res)
            return opt_res.x, opt_res.fun

        for _ in range(n_obj):
            if nu > 0:
                main_kernel = Matern(length_scale=np.ones(n_var), length_scale_bounds=(np.sqrt(1e-3), np.sqrt(1e3)), nu=0.5 * nu)
            else:
                main_kernel = RBF(length_scale=np.ones(n_var), length_scale_bounds=(np.sqrt(1e-3), np.sqrt(1e3)))
            
            kernel = ConstantKernel(constant_value=1.0, constant_value_bounds=(np.sqrt(1e-3), np.sqrt(1e3))) * \
                main_kernel + \
                ConstantKernel(constant_value=1e-2, constant_value_bounds=(np.exp(-6), np.exp(0)))
            
            gp = GaussianProcessRegressor(kernel=kernel, optimizer=constrained_optimization)
            self.gps.append(gp)

    def fit(self, X, Y):
        for i, gp in enumerate(self.gps):
            gp.fit(X, Y[:, i])
        
    def evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
        F, dF, hF = [], [], [] # mean
        S, dS, hS = [], [], [] # std

        for gp in self.gps:

            # mean
            K = gp.kernel_(X, gp.X_train_) # K: shape (N, N_train)

            y_mean = K.dot(gp.alpha_)
            y_mean = gp._y_train_mean + y_mean

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

                S.append(y_var) # y_var: shape (N,)

            if not (calc_gradient or calc_hessian): continue

            ell = np.exp(gp.kernel_.theta[1:-1]) # ell: shape (n_var,)
            sf2 = np.exp(gp.kernel_.theta[0]) # sf2: shape (1,)
            d = np.expand_dims(cdist(X / ell, gp.X_train_ / ell), 2) # d: shape (N, N_train, 1)
            X_, X_train_ = np.expand_dims(X, 1), np.expand_dims(gp.X_train_, 0)
            dd_N = X_ - X_train_ # numerator
            dd_D = d * ell ** 2 # denominator
            dd = safe_divide(dd_N, dd_D) # dd: shape (N, N_train, n_var)

            if calc_gradient or calc_hessian:
                if self.nu == 1:
                    dK = -sf2 * np.exp(-d) * dd

                elif self.nu == 3:
                    dK = -3 * sf2 * np.exp(-np.sqrt(3) * d) * d * dd

                elif self.nu == 5:
                    dK = -5. / 3 * sf2 * np.exp(-np.sqrt(5) * d) * (1 + np.sqrt(5) * d) * d * dd

                else: # RBF
                    dK = -sf2 * np.exp(-0.5 * d ** 2) * d * dd

                dK_T = dK.transpose(0, 2, 1) # dK: shape (N, N_train, n_var), dK_T: shape (N, n_var, N_train)
                
            if calc_gradient:
                dF.append(dK_T @ gp.alpha_) # gp.alpha_: shape (N_train,), dF appended: shape (N, n_var)

                # TODO: check
                if std:
                    K = np.expand_dims(K, 1) # K: shape (N, 1, N_train)
                    K_Ki = K @ gp._K_inv # gp._K_inv: shape (N_train, N_train), K_Ki: shape (N, 1, N_train)
                    dK_Ki = dK_T @ gp._K_inv # dK_Ki: shape (N, n_var, N_train)

                    dS.append(-np.sum(dK_Ki * K + K_Ki * dK_T, axis=2)) # dS appended: shape (N, n_var)

            if calc_hessian:
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

                hF.append(hK_T @ gp.alpha_) # hF appended: shape (N, n_var, n_var)

                # TODO: check
                if std:
                    K = np.expand_dims(K, 2) # K: shape (N, 1, 1, N_train)
                    dK = np.expand_dims(dK_T, 2) # dK: shape (N, n_var, 1, N_train)
                    dK_Ki = np.expand_dims(dK_Ki, 2) # dK_Ki: shape (N, n_var, 1, N_train)
                    hK_Ki = hK_T @ gp._K_inv # hK_Ki: shape (N, n_var, n_var, N_train)

                    hS.append(-np.sum(hK_Ki * K + 2 * dK_Ki * dK + K_Ki * hK_T, axis=3)) # hS appended: shape (N, n_var, n_var)

        F = np.stack(F, axis=1)
        dF = np.stack(dF, axis=1) if calc_gradient else None
        hF = np.stack(hF, axis=1) if calc_hessian else None
        
        S = np.stack(S, axis=1) if std else None
        dS = np.stack(dS, axis=1) if std and calc_gradient else None
        hS = np.stack(hS, axis=1) if std and calc_hessian else None

        out = {'F': F, 'dF': dF, 'hF': hF, 'S': S, 'dS': dS, 'hS': hS}
        return out


class ThompsonSampling(GaussianProcess):
    '''
    Sampled functions from Gaussian process using Thompson Sampling
    '''
    def __init__(self, n_var, n_obj, nu, n_spectral_pts, mean_sample, **kwargs):
        super().__init__(n_var, n_obj, nu)

        self.M = n_spectral_pts
        self.thetas, self.Ws, self.bs, self.sf2s = None, None, None, None
        self.mean_sample = mean_sample

    def fit(self, X, Y):
        self.thetas, self.Ws, self.bs, self.sf2s = [], [], [], []
        n_sample = X.shape[0]

        for i, gp in enumerate(self.gps):
            gp.fit(X, Y[:, i])

            ell = np.exp(gp.kernel_.theta[1:-1])
            sf2 = np.exp(2 * gp.kernel_.theta[0])
            sn2 = np.exp(2 * gp.kernel_.theta[-1])

            sw1, sw2 = lhs(self.n_var, self.M), lhs(self.n_var, self.M)
            if self.nu > 0:
                W = np.tile(1. / ell, (self.M, 1)) * norm.ppf(sw1) * np.sqrt(self.nu / chi2.ppf(sw2, df=self.nu))
            else:
                W = np.random.uniform(size=(self.M, self.n_var)) * np.tile(1. / ell, (self.M, 1))
            b = 2 * np.pi * lhs(1, self.M)
            phi = np.sqrt(2. * sf2 / self.M) * np.cos(W @ X.T + np.tile(b, (1, n_sample)))
            A = phi @ phi.T + sn2 * np.eye(self.M)
            invcholA = LA.inv(LA.cholesky(A))
            invA = invcholA.T @ invcholA
            mu_theta = invA @ phi @ Y[:, i]
            if self.mean_sample:
                theta = mu_theta
            else:
                cov_theta = sn2 * invA
                cov_theta = 0.5 * (cov_theta + cov_theta.T)
                theta = mu_theta + LA.cholesky(cov_theta) @ np.random.standard_normal(self.M)

            self.thetas.append(theta.copy())
            self.Ws.append(W.copy())
            self.bs.append(b.copy())
            self.sf2s.append(sf2)

    def evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
        F, dF, hF = [], [], []
        n_sample = X.shape[0] if len(X.shape) > 1 else 1

        for theta, W, b, sf2 in zip(self.thetas, self.Ws, self.bs, self.sf2s):
            factor = np.sqrt(2. * sf2 / self.M)
            W_X_b = W @ X.T + np.tile(b, (1, n_sample))
            F.append(factor * (theta @ np.cos(W_X_b)))

            if calc_gradient:
                dF.append(-factor * np.expand_dims(theta, 0) * np.sin(W_X_b).T @ W)
            
            if calc_hessian:
                hF.append(-factor * np.einsum('ij,jk->ikj', np.expand_dims(theta, 0) * np.cos(W_X_b).T, W) @ W)
            
        F = np.stack(F, axis=1)
        dF = np.stack(dF, axis=1) if calc_gradient else None
        hF = np.stack(hF, axis=1) if calc_hessian else None

        S = np.zeros((n_sample, self.n_obj)) if std else None
        dS = np.zeros((n_sample, self.n_obj, self.n_var)) if std and calc_gradient else None
        hS = np.zeros((n_sample, self.n_obj, self.n_var, self.n_var)) if std and calc_hessian else None
        
        out = {'F': F, 'dF': dF, 'hF': hF, 'S': S, 'dS': dS, 'hS': hS}
        return out

