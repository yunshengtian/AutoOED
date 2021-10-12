'''
Surrogate model that predicts the objective values of given design variables.
'''

from abc import ABC, abstractmethod
import numpy as np

from autooed.utils.normalization import StandardNormalization


class SurrogateModel(ABC):
    '''
    Base class of surrogate model.
    '''
    def __init__(self, problem, **kwargs):
        '''
        Initialize a surrogate model.

        Parameters
        ----------
        problem: autooed.problem.Problem
            The optimization problem.
        '''
        self.problem = problem
        self.n_var, self.n_obj = problem.n_var, problem.n_obj
        self.bounds = np.array([problem.xl, problem.xu])
        self.transformation = problem.transformation
        self.normalization = StandardNormalization(self.bounds)
        self.fitted = False

    def fit(self, X, Y, dtype='raw'):
        '''
        Fit a surrogate model from data.

        Parameters
        ----------
        X: np.array
            Input design variables.
        Y: np.array
            Input objective values.
        '''
        assert dtype in ['raw', 'continuous', 'normalized'], f'Undefined data type {dtype} in surrogate fitting'

        if dtype == 'raw':
            X = self.transformation.do(X)
            
        if dtype == 'raw' or dtype == 'continuous':
            self.normalization.fit(X, Y)
            X, Y = self.normalization.do(x=X, y=Y)

        self._fit(X, Y)
        self.fitted = True

    @abstractmethod
    def _fit(self, X, Y):
        '''
        Fit a surrogate model from normalized and continuous data.

        Parameters
        ----------
        X: np.array
            Input design variables (normalized, continuous).
        Y: np.array
            Input objective values (normalized).
        '''
        pass

    def evaluate(self, X, dtype='raw', std=False, gradient=False, hessian=False):
        '''
        Predict the performance given a set of design variables.

        Parameters
        ----------
        X: np.array
            Input design variables.
        std: bool
            Whether to calculate the standard deviation of the prediction.
        gradient: bool
            Whether to calculate the gradient of the prediction.
        hessian: bool
            Whether to calculate the hessian of the prediction.

        Returns
        -------
        out: dict
            A output dictionary containing following properties of performance:\n
            - out['F']: mean, shape (N, n_obj)
            - out['dF']: gradient of mean, shape (N, n_obj, n_var)
            - out['hF']: hessian of mean, shape (N, n_obj, n_var, n_var)
            - out['S']: std, shape (N, n_obj)
            - out['dS']: gradient of std, shape (N, n_obj, n_var)
            - out['hS']: hessian of std, shape (N, n_obj, n_var, n_var)
        '''
        assert self.fitted, f'Surrogate model is not fitted yet'

        assert dtype in ['raw', 'continuous', 'normalized'], f'Undefined data type {dtype} in surrogate evaluation'

        if dtype == 'raw':
            X = self.transformation.do(X)

        if dtype == 'raw' or dtype == 'continuous':
            X = self.normalization.do(x=X)
        
        out = self._evaluate(X, std, gradient, hessian)

        out['F'] = self.normalization.undo(y=out['F'])
        if gradient: out['dF'] = self.normalization.rescale(y=out['dF'].transpose(0, 2, 1)).transpose(0, 2, 1)
        if std: out['S'] = self.normalization.rescale(y=out['S'])
        if std and gradient: out['dS'] = self.normalization.rescale(y=out['dS'].transpose(0, 2, 1)).transpose(0, 2, 1)
        
        return out

    @abstractmethod
    def _evaluate(self, X, std, gradient, hessian):
        '''
        Predict the performance given a set of normalized and continuous design variables.

        Parameters
        ----------
        X: np.array
            Input design variables (normalized, continuous).
        std: bool
            Whether to calculate the standard deviation of the prediction.
        gradient: bool
            Whether to calculate the gradient of the prediction.
        hessian: bool
            Whether to calculate the hessian of the prediction.

        Returns
        -------
        out: dict
            A output dictionary containing following properties of performance:\n
            - out['F']: mean, shape (N, n_obj)
            - out['dF']: gradient of mean, shape (N, n_obj, n_var)
            - out['hF']: hessian of mean, shape (N, n_obj, n_var, n_var)
            - out['S']: std, shape (N, n_obj)
            - out['dS']: gradient of std, shape (N, n_obj, n_var)
            - out['hS']: hessian of std, shape (N, n_obj, n_var, n_var)
        '''
        pass

    def predict(self, X, dtype='raw', std=False):
        '''
        '''
        out = self.evaluate(X, dtype=dtype, std=std)
        if std:
            return out['F'], out['S']
        else:
            return out['F']
