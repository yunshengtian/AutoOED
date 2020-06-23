import numpy as np
from ..solver import Solver
from pymoo.optimize import minimize
from pymoo.algorithms.so_cmaes import CMAES
from pymoo.decomposition.tchebicheff import Tchebicheff
from .utils import ScalarizedEvaluator
from multiprocessing import Process, Queue


def optimization(problem, x, weights, queue):
    '''
    Parallel worker for single-objective CMA-ES optimization
    '''
    evaluator = ScalarizedEvaluator(decomposition=Tchebicheff(), weights=weights)
    res = minimize(problem, CMAES(x), evaluator=evaluator)
    queue.put([res.X[0], res.F[0]])


class ParEGOSolver(Solver):
    '''
    Solver based on ParEGO
    '''
    def __init__(self, *args, **kwargs):
        self.pop_size = kwargs['pop_size']
        self.n_process = kwargs.pop('n_process')
        super().__init__(*args, algo=CMAES, **kwargs)

    def solve(self, problem, X, Y):
        '''
        Solve the multi-objective problem by multiple scalarized single-objective solvers
        '''
        # initialize population
        sampling = self._get_sampling(X, Y)
        if not isinstance(sampling, np.ndarray):
            sampling = sampling.do(problem, self.pop_size)

        # generate scalarization weights
        weights = np.random.random((self.pop_size, Y.shape[1]))
        weights /= np.expand_dims(np.sum(weights, axis=1), 1)

        # optimization
        xs, ys = [], []
        queue = Queue()
        n_active_process = 0
        for i, x0 in enumerate(sampling):
            Process(target=optimization, args=(problem, x0, weights[i], queue)).start()
            n_active_process += 1
            if n_active_process >= self.n_process:
                x, y = queue.get()
                xs.append(x)
                ys.append(y)
                n_active_process -= 1

        # gather result
        for _ in range(n_active_process):
            x, y = queue.get()
            xs.append(x)
            ys.append(y)
        
        # construct solution
        self.solution = {'x': np.array(xs), 'y': np.array(ys)}
        return self.solution