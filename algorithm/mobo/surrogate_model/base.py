from abc import ABC, abstractmethod

'''
Surrogate model that predicts the performance of given design variables
'''

class SurrogateModel(ABC):
    '''
    Base class of surrogate model
    '''
    def __init__(self, n_var, n_obj):
        self.n_var = n_var
        self.n_obj = n_obj

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
