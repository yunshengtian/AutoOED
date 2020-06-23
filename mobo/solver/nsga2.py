from .solver import Solver
from pymoo.algorithms.nsga2 import NSGA2


class NSGA2Solver(Solver):
    '''
    Solver based on NSGA-II
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, algo=NSGA2, **kwargs)
