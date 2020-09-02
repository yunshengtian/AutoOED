import numpy as np
import torch
from scipy import optimize

from mobo.surrogate_model.neural_network import NeuralNetwork
from mobo.surrogate_model.bayesian_linear_regression import BayesianLinearRegression


class DNGO(NeuralNetwork, BayesianLinearRegression):
    '''
    Deep Networks for Global Optimization [1]: Bayesian Linear Regression with basis function extracted from a neural network
    
    [1] J. Snoek, O. Rippel, K. Swersky, R. Kiros, N. Satish, 
        N. Sundaram, M.~M.~A. Patwary, Prabhat, R.~P. Adams
        Scalable Bayesian Optimization Using Deep Neural Networks
        Proc. of ICML'15
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def fit(self, X, Y):
        X = torch.FloatTensor(X)

        NeuralNetwork.fit(self, X, Y)

        self.models = []
        
        for i in range(self.n_obj):
            phi = self.net[i].basis_func(X).data.numpy()

            alpha, beta = optimize.fmin(self.negative_mll, np.random.rand(2), args=(phi, Y[:, i]), disp=False)

            A = beta * np.dot(phi.T, phi) + alpha * np.eye(phi.shape[1])
            A_inv = np.linalg.inv(A)

            m = beta * np.dot(A_inv, phi.T)
            m = np.dot(m, Y[:, i])

            self.models.append((m, A_inv, beta))
    
    def evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
        X = torch.FloatTensor(X)

        mu = np.zeros((self.n_obj, X.shape[0]))
        var = np.zeros((self.n_obj, X.shape[0]))

        for i in range(self.n_obj):
            phi = self.net[i].basis_func(X).data.numpy()

            m, A_inv, beta = self.models[i]
            mu[i] = np.dot(m, phi.T)
            if std:
                var[i] = 1. / beta + np.diag(np.dot(np.dot(phi, A_inv), phi.T))
                var[i] = np.maximum(var[i], 0)
        
        F = mu.T
        S = var.T if std else None

        # TODO: not implemented
        dF, hF, dS, hS = [None] * 4
        
        out = {'F': F, 'dF': dF, 'hF': hF, 'S': S, 'dS': dS, 'hS': hS}
        return out