from abc import ABC, abstractmethod
from problem.transformation import get_transformation

'''
Surrogate model that predicts the performance of given design variables
'''

class SurrogateModel(ABC):
    '''
    Base class of surrogate model
    '''
    def __init__(self, problem_cfg):
        self.transformation = get_transformation(problem_cfg)
        self.n_var = self.transformation.n_var_T
        self.n_obj = self.transformation.n_obj

    def fit(self, X, Y):
        X = self.transformation.constr(X)
        self._fit(X, Y)

    @abstractmethod
    def _fit(self, X, Y):
        '''
        Fit the surrogate model from data (X, Y)
        '''
        pass

    def evaluate(self, X, *args, **kwargs):
        X = self.transformation.constr(X)
        return self._evaluate(X, *args, **kwargs)

    @abstractmethod
    def _evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
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
