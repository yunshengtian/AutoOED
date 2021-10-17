'''
Bayesian neural network surrogate model.
'''

import numpy as np
import torch

from autooed.mobo.surrogate_model.nn import NeuralNetwork, jacobian, hessian


class BayesianRegression:
    """
    Bayesian regression model

    w ~ N(w|0, alpha^(-1)I)
    y = X @ w
    t ~ N(t|X @ w, beta^(-1))
    """
    def __init__(self, alpha:float=1., beta:float=1.):
        self.alpha = alpha
        self.beta = beta
        self.w_mean = None
        self.w_precision = None

    def _is_prior_defined(self) -> bool:
        return self.w_mean is not None and self.w_precision is not None

    def _get_prior(self, ndim:int) -> tuple:
        if self._is_prior_defined():
            return self.w_mean, self.w_precision
        else:
            return np.zeros(ndim), self.alpha * np.eye(ndim)

    def fit(self, X:np.ndarray, t:np.ndarray):
        """
        bayesian update of parameters given training dataset

        Parameters
        ----------
        X : (N, n_features) np.ndarray
            training data independent variable
        t : (N,) np.ndarray
            training data dependent variable
        """
        mean_prev, precision_prev = self._get_prior(np.size(X, 1))

        w_precision = precision_prev + self.beta * X.T @ X
        w_mean = np.linalg.solve(
            w_precision,
            precision_prev @ mean_prev + self.beta * X.T @ t
        )
        self.w_mean = w_mean
        self.w_precision = w_precision
        self.w_cov = np.linalg.inv(self.w_precision)

    def predict(self, X:np.ndarray, return_std:bool=False, sample_size:int=None):
        """
        return mean (and standard deviation) of predictive distribution

        Parameters
        ----------
        X : (N, n_features) np.ndarray
            independent variable
        return_std : bool, optional
            flag to return standard deviation (the default is False)
        sample_size : int, optional
            number of samples to draw from the predictive distribution
            (the default is None, no sampling from the distribution)

        Returns
        -------
        y : (N,) np.ndarray
            mean of the predictive distribution
        y_std : (N,) np.ndarray
            standard deviation of the predictive distribution
        y_sample : (N, sample_size) np.ndarray
            samples from the predictive distribution
        """
        if sample_size is not None:
            w_sample = np.random.multivariate_normal(
                self.w_mean, self.w_cov, size=sample_size
            )
            y_sample = X @ w_sample.T
            return y_sample
        y = X @ self.w_mean
        if return_std:
            y_var = 1 / self.beta + np.sum(X @ self.w_cov * X, axis=1)
            y_std = np.sqrt(y_var)
            return y, y_std
        return y

    def export_params(self):
        return self.w_mean, self.w_cov, self.beta


class BayesianNeuralNetwork(NeuralNetwork):
    '''
    Deep Networks for Global Optimization [1]: Bayesian Linear Regression with basis function extracted from a neural network
    
    [1] J. Snoek, O. Rippel, K. Swersky, R. Kiros, N. Satish, 
        N. Sundaram, M.~M.~A. Patwary, Prabhat, R.~P. Adams
        Scalable Bayesian Optimization Using Deep Neural Networks
        Proc. of ICML'15
    '''
    def __init__(self, problem, hidden_size=50, hidden_layers=3, activation='tanh', lr=1e-3, weight_decay=1e-4, n_epoch=100, **kwargs):
        '''
        Initialize a Bayesian neural network as surrogate model.

        Parameters
        ----------
        problem: autooed.problem.Problem
            The optimization problem.
        hidden_size: int
            Size of the hidden layer of the neural network.
        hidden_layers: int
            Number of hidden layers of the neural network.
        activation: str
            Type of activation function.
        lr: float
            Learning rate.
        weight_decay: float
            Weight decay.
        n_epoch: int
            Number of training epochs.
        '''
        super().__init__(problem, hidden_size, hidden_layers, activation, lr, weight_decay, n_epoch)

        self.regressor = [BayesianRegression()] * self.n_obj

    def _fit(self, X, Y):
        super()._fit(X, Y)
        
        for i in range(self.n_obj):
            phi = self.net[i].basis_func(torch.FloatTensor(X)).data.numpy()
            self.regressor[i].fit(phi, Y[:, i])
    
    def _evaluate(self, X, std, gradient, hessian):
        F, dF, hF = [], [], [] # mean
        S, dS, hS = [], [], [] # std

        X = torch.FloatTensor(X)
        X.requires_grad = True

        for i in range(self.n_obj):

            phi = self.net[i].basis_func(X)

            w_mean = torch.FloatTensor(self.regressor[i].w_mean)
            w_cov = torch.FloatTensor(self.regressor[i].w_cov)
            beta = self.regressor[i].beta

            y_mean = torch.matmul(phi, w_mean)
            F.append(y_mean.detach().numpy())

            if std:
                y_var = 1 / beta + torch.sum(torch.matmul(phi, w_cov) * phi, axis=1)
                y_std = torch.sqrt(y_var)
                S.append(y_std.detach().numpy())

            if not (gradient or hessian): continue

            if gradient:
                dy_mean = jacobian(y_mean, X)
                dF.append(dy_mean.numpy())

                if std:
                    dy_std = jacobian(y_std, X)
                    dS.append(dy_std.numpy())

            if hessian:
                hy_mean = hessian(y_mean, X)
                hF.append(hy_mean.numpy())

                if std:
                    hy_std = hessian(y_std, X)
                    hS.append(hy_std.numpy())
        
        F = np.stack(F, axis=1)
        dF = np.stack(dF, axis=1) if gradient else None
        hF = np.stack(hF, axis=1) if hessian else None
        
        S = np.stack(S, axis=1) if std else None
        dS = np.stack(dS, axis=1) if std and gradient else None
        hS = np.stack(hS, axis=1) if std and hessian else None
        
        out = {'F': F, 'dF': dF, 'hF': hF, 'S': S, 'dS': dS, 'hS': hS}
        return out
