from abc import ABC, abstractmethod
from problem.transformation import get_transformation

'''
Surrogate model that predicts the performance of given design variables.
'''

class SurrogateModel(ABC):
    '''
    Base class of surrogate model.
    '''
    def __init__(self, problem_cfg):
        '''
        Initialize a surrogate model.

        Parameters
        ----------
        problem_cfg: dict
            Problem configurations.
        '''
        self.transformation = get_transformation(problem_cfg)
        self.n_var = self.transformation.n_var_T
        self.n_obj = self.transformation.n_obj

    def fit(self, X, Y):
        X = self.transformation.constr(X)
        self._fit(X, Y)

    @abstractmethod
    def _fit(self, X, Y):
        '''
        Fit a surrogate model from data.

        Parameters
        ----------
        X: np.array
            Input design variables.
        Y: np.array
            Input performance values.
        '''
        pass

    def evaluate(self, X, *args, **kwargs):
        X = self.transformation.constr(X)
        return self._evaluate(X, *args, **kwargs)

    @abstractmethod
    def _evaluate(self, X, std=False, calc_gradient=False, calc_hessian=False):
        '''
        Predict the performance given a set of design variables.

        Parameters
        ----------
        std: bool
            Whether to calculate the standard deviation of the prediction.
        calc_gradient: bool, default=False
            Whether to calculate the gradient of the prediction.
        calc_hessian: bool, default=False
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
