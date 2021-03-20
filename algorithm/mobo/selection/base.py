from abc import ABC, abstractmethod

'''
Selection methods for new batch of samples to evaluate on real problem.
'''

class Selection(ABC):
    '''
    Base class of selection method.
    '''
    def __init__(self, batch_size, ref_point=None, **kwargs):
        '''
        Initialize a selection method.

        Parameters
        ----------
        batch_size: int
            Batch size.
        ref_point: np.array, default=None
            Reference point.
        '''
        self.batch_size = batch_size
        self.ref_point = ref_point

    def fit(self, X, Y):
        '''
        Fit the parameters of selection method from data.

        Parameters
        ----------
        X: np.array
            Design variables.
        Y: np.array
            Performance values.
        '''
        pass

    def set_ref_point(self, ref_point):
        '''
        Set reference point.

        Parameters
        ----------
        ref_point: np.array
            Reference point.
        '''
        self.ref_point = ref_point

    @abstractmethod
    def select(self, solution, surrogate_model, normalization, curr_pset, curr_pfront):
        '''
        Select new samples from the solution obtained by solver (some parameters may not be necessary for some selection criteria).

        Parameters
        ----------
        solution: dict
            Solution dictionary obtained by solver.\n
                - solution['x']: design variables of solution
                - solution['y']: acquisition values of solution
                - solution['algo']: solver algorithm, having some relevant information from optimization
        surrogate_model: mobo.surrogate_model.base.SurrogateModel
            Fitted surrogate model.
        normalization: mobo.normalization.Normalization
            Data normalization for surrogate model fitting.
        curr_pset: np.array
            Current pareto set found.
        curr_pfront: np.array
            Current pareto front found.
        
        Returns
        -------
        X_next: np.array
            Next batch of samples selected.
        info: dict
            Other informations need to be stored or exported, None if not necessary.
        '''
        pass
