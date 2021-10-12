'''
Thompson Sampling acquisition function.
'''

import numpy as np
from numpy import linalg as LA
from scipy.stats.distributions import chi2
from scipy.stats import norm

from autooed.utils.sampling import lhs
from autooed.mobo.acquisition.base import Acquisition
from autooed.mobo.surrogate_model import GaussianProcess


class ThompsonSampling(Acquisition):
    '''
    Thompson Sampling.
    '''
    def __init__(self, surrogate_model, n_spectral_pts=100, mean_sample=False, **kwargs):
        super().__init__(surrogate_model)
        assert isinstance(surrogate_model, GaussianProcess), 'Thompson Sampling requires Gaussian Process as the surroagte model'
        self.M = n_spectral_pts
        self.thetas, self.Ws, self.bs, self.sf2s = None, None, None, None
        self.mean_sample = mean_sample

    def _fit(self, X, Y):
        X, Y = self.normalization.do(x=X, y=Y)

        self.thetas, self.Ws, self.bs, self.sf2s = [], [], [], []
        n_sample = X.shape[0]
        gps, n_var, nu = self.surrogate_model.gps, self.surrogate_model.n_var, self.surrogate_model.nu

        for i, gp in enumerate(gps):
            gp.fit(X, Y[:, i])

            ell = np.exp(gp.kernel_.theta[1:-1])
            sf2 = np.exp(2 * gp.kernel_.theta[0])
            sn2 = np.exp(2 * gp.kernel_.theta[-1])

            sw1, sw2 = lhs(n_var, self.M), lhs(n_var, self.M)
            if nu > 0:
                W = np.tile(1. / ell, (self.M, 1)) * norm.ppf(sw1) * np.sqrt(nu / chi2.ppf(sw2, df=nu))
            else:
                W = np.random.uniform(size=(self.M, n_var)) * np.tile(1. / ell, (self.M, 1))
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

    def _evaluate(self, X, gradient=False, hessian=False):
        X = self.normalization.do(x=X)

        F, dF, hF = [], [], []
        n_sample = X.shape[0] if len(X.shape) > 1 else 1

        for theta, W, b, sf2 in zip(self.thetas, self.Ws, self.bs, self.sf2s):
            factor = np.sqrt(2. * sf2 / self.M)
            W_X_b = W @ X.T + np.tile(b, (1, n_sample))
            F.append(factor * (theta @ np.cos(W_X_b)))

            if gradient:
                dF.append(-factor * np.expand_dims(theta, 0) * np.sin(W_X_b).T @ W)
            
            if hessian:
                hF.append(-factor * np.einsum('ij,jk->ikj', np.expand_dims(theta, 0) * np.cos(W_X_b).T, W) @ W)
            
        F = np.stack(F, axis=1)
        dF = np.stack(dF, axis=1) if gradient else None
        hF = np.stack(hF, axis=1) if hessian else None

        F = self.normalization.undo(y=F)
        if gradient: dF = self.normalization.rescale(y=dF.transpose(0, 2, 1)).transpose(0, 2, 1)
        
        return F, dF, hF
