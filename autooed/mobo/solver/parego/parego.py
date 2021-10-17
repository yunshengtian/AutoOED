'''
ParEGO multi-objective solver.
'''

import numpy as np
from pymoo.optimize import minimize
from pymoo.algorithms.so_cmaes import CMAES
from multiprocess import Process, Queue, cpu_count

from autooed.utils.sampling import lhs
from autooed.mobo.solver.base import Solver
from autooed.mobo.solver.parego.evaluator import ScalarizedEvaluator
from autooed.mobo.solver.parego.decomposition import augmented_tchebicheff, AugmentedTchebicheff


def optimization(problem, x, weights, queue):
    '''
    Parallel worker for single-objective CMA-ES optimization.
    '''
    evaluator = ScalarizedEvaluator(decomposition=AugmentedTchebicheff(), weights=weights)
    res = minimize(problem, CMAES(x), evaluator=evaluator)
    queue.put([res.X[0], res.F[0]])


class ParEGO(Solver):
    '''
    Solver based on ParEGO.
    NOTE: only compatible with Direct selection.
    '''
    def __init__(self, problem, n_process=cpu_count(), **kwargs):
        super().__init__(problem)
        self.n_process = n_process

    def _solve(self, X, Y, batch_size):
        '''
        Solve the multi-objective problem by multiple scalarized single-objective solvers.
        '''
        # generate scalarization weights
        weights = np.random.random((batch_size, self.problem.n_obj))
        weights /= np.expand_dims(np.sum(weights, axis=1), 1)

        # initial solutions
        X = np.vstack([X, lhs(X.shape[1], batch_size)])
        F = self.problem.evaluate(X, return_values_of=['F'])

        # optimization
        xs, ys = [], []
        queue = Queue()
        n_active_process = 0
        for i in range(batch_size):
            x0 = X[np.argmin(augmented_tchebicheff(F, weights[i]))]
            Process(target=optimization, args=(self.problem, x0, weights[i], queue)).start()
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

        return np.array(xs), np.array(ys)
