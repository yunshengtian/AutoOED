from abc import ABC, abstractmethod

'''
Selection methods for new batch of samples to evaluate on real problem
'''

class Selection(ABC):
    '''
    Base class of selection method
    '''
    def __init__(self, batch_size, ref_point=None, **kwargs):
        self.batch_size = batch_size
        self.ref_point = ref_point

    def fit(self, X, Y):
        '''
        Fit the parameters of selection method from data
        '''
        pass

    def set_ref_point(self, ref_point):
        self.ref_point = ref_point

    @abstractmethod
    def select(self, solution, surrogate_model, normalization, curr_pset, curr_pfront):
        '''
        Select new samples from solution obtained by solver
        Input:
            solution['x']: design variables of solution
            solution['y']: acquisition values of solution
            solution['algo']: solver algorithm, having some relevant information from optimization
            surrogate_model: fitted surrogate model
            normalization: data normalization for surrogate model fitting
            curr_pset: current pareto set found
            curr_pfront: current pareto front found
            (some inputs may not be necessary for some selection criterion)
        Output:
            X_next: next batch of samples selected
            info: other informations need to be stored or exported, None if not necessary
        '''
        pass












