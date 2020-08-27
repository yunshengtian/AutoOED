import numpy as np
from numpy import linalg as LA
from scipy.stats.distributions import chi2
from scipy.stats import norm

from external import lhs
from mobo.surrogate_model.gaussian_process import GaussianProcess


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
