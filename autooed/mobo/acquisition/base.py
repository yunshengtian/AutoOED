'''
Acquisition functions that define the objectives for surrogate multi-objective problem.
'''

from abc import ABC, abstractmethod


class Acquisition(ABC):
    '''
    Base class of acquisition function.
    '''
    def __init__(self, surrogate_model, **kwargs):
        '''
        Initialize the acquisition function.

        Parameters
        ----------
        surrogate_model: autooed.mobo.surrogate_model.base.SurrogateModel
            The surrogate model.
        '''
        self.surrogate_model = surrogate_model
        self.transformation = surrogate_model.transformation
        self.normalization = surrogate_model.normalization
        self.fitted = False

    def fit(self, X, Y, dtype='raw'):
        '''
        Fit the parameters of acquisition function from raw data.

        Parameters
        ----------
        X: np.array
            Input design variables (raw).
        Y: np.array
            Input performance values.
        '''
        assert self.surrogate_model.fitted, 'Surrogate model is not fitted before fitting acquisition function'
    
        assert dtype in ['raw', 'continuous', 'normalized'], f'Undefined data type {dtype} in acquisition fitting'

        if dtype == 'raw':
            X = self.transformation.do(X)

        self._fit(X, Y)
        self.fitted = True

    @abstractmethod
    def _fit(self, X, Y):
        '''
        Fit the parameters of acquisition function from normalized and continuous data.

        Parameters
        ----------
        X: np.array
            Input design variables (continuous).
        Y: np.array
            Input performance values.
        '''
        pass

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
        assert self.fitted, 'Acquisition function is not fitted before evaluation'

        assert dtype in ['raw', 'continuous', 'normalized'], f'Undefined data type {dtype} in acquisition evaluation'

        if dtype == 'raw':
            X = self.transformation.do(X)
        
        return self._evaluate(X, gradient, hessian)

    @abstractmethod
    def _evaluate(self, X, gradient, hessian):
        '''
        Evaluate the acquisition values of the normalized and continuous design variables.
        
        Parameters
        ----------
        X: np.array
            Input design variables (continuous).
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
        pass