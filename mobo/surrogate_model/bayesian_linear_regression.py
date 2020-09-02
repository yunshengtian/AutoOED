import numpy as np
from scipy import optimize

from mobo.surrogate_model.base import SurrogateModel


class BayesianLinearRegression(SurrogateModel):
    '''
    Bayesian Linear Regression
    '''
    def __init__(self, n_var, n_obj, **kwargs):
        super().__init__(n_var, n_obj)

        self.models = []

    def fit(self, X, Y):
        self.models = []

        for i in range(self.n_obj):
            alpha, beta = optimize.fmin(self.negative_mll, np.random.rand(2), args=(X, Y[:, i]), disp=False)

            A = beta * np.dot(X.T, X) + alpha * np.eye(X.shape[1])
            A_inv = np.linalg.inv(A)

            m = beta * np.dot(A_inv, X.T)
            m = np.dot(m, Y[:, i])

            self.models.append((m, A_inv, beta))

    def evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
        mu = np.zeros((self.n_obj, X.shape[0]))
        var = np.zeros((self.n_obj, X.shape[0]))

        for i in range(self.n_obj):
            m, A_inv, beta = self.models[i]
            mu[i] = np.dot(m, X.T)
            if std:
                var[i] = 1. / beta + np.diag(np.dot(np.dot(X, A_inv), X.T))
                var[i] = np.maximum(var[i], 0)
        
        F = mu.T
        S = var.T if std else None

        # TODO: not implemented
        dF, hF, dS, hS = [None] * 4
        
        out = {'F': F, 'dF': dF, 'hF': hF, 'S': S, 'dS': dS, 'hS': hS}
        return out

    def negative_mll(self, theta, X, Y):
        '''
        Negative log likelihood of the data marginalized over the hyperparameter theta
        Input:
            theta: hyperparameter (alpha, beta) on a log scale
        '''
        if np.any(theta == np.inf) or np.any((-10 > theta) + (theta > 10)):
            return np.inf

        alpha, beta = np.exp(theta[0]), np.exp(theta[1])
        N, D = X.shape[0], X.shape[1]

        A = beta * np.dot(X.T, X) + alpha * np.eye(D)
        A_inv = np.linalg.inv(A)

        m = beta * np.dot(A_inv, X.T)
        m = np.dot(m, Y)

        mll = D * np.log(alpha)
        mll += N * np.log(beta)
        mll -= N * np.log(2 * np.pi)
        mll -= beta * np.linalg.norm(Y - np.dot(X, m), 2)
        mll -= alpha * np.dot(m.T, m)
        mll -= np.log(np.maximum(np.linalg.det(A), 1e-10))
        return -0.5 * mll
