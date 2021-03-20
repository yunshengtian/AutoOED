from abc import ABC, abstractmethod

'''
Acquisition functions that define the objectives for surrogate multi-objective problem.
'''

class Acquisition(ABC):
    '''
    Base class of acquisition function.

    Attributes
    ----------
    requires_std: bool, default=False
        Whether requires std output from surrogate model, set False to avoid unnecessary computation.
    '''
    requires_std = False

    def __init__(self, *args, **kwargs):
        pass

    def fit(self, X, Y):
        '''
        Fit the parameters of acquisition function from data.

        Parameters
        ----------
        X: np.array
            Input design variables.
        Y: np.array
            Input performance values.
        '''
        pass

    @abstractmethod
    def evaluate(self, val, calc_gradient=False, calc_hessian=False):
        '''
        Evaluate the output from surrogate model using acquisition function.
        
        Parameters
        ----------
        val: dict
            Output from surrogate model storing properties of the predicted performance.\n
            - val['F']: mean, shape (N, n_obj)
            - val['dF']: gradient of mean, shape (N, n_obj, n_var)
            - val['hF']: hessian of mean, shape (N, n_obj, n_var, n_var)
            - val['S']: std, shape (N, n_obj)
            - val['dS']: gradient of std, shape (N, n_obj, n_var)
            - val['hS']: hessian of std, shape (N, n_obj, n_var, n_var)
        calc_gradient: bool, default=False
            Whether to calculate the gradient of the prediction.
        calc_hessian: bool, default=False
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
