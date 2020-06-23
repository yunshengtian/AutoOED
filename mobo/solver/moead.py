from .solver import Solver
import numpy as np
from pymoo.algorithms.moead import MOEAD


class MOEADSolver(Solver):
    '''
    Solver based on MOEA/D
    '''
    def __init__(self, *args, **kwargs):
        pop_size, n_obj = kwargs['pop_size'], kwargs['n_obj']
        # generate direction vectors by random sampling
        ref_dirs = np.random.random((pop_size, n_obj))
        ref_dirs /= np.expand_dims(np.sum(ref_dirs, axis=1), 1)
        kwargs['ref_dirs'] = ref_dirs
        kwargs['eliminate_duplicates'] = False
        super().__init__(*args, algo=MOEAD, **kwargs)