import numpy as np
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting
from pymoo.operators.sampling.random_sampling import FloatRandomSampling
from pymoo.operators.sampling.latin_hypercube_sampling import LatinHypercubeSampling
from algorithm.external import lhs


class Solver:
    '''
    Multi-objective solver.
    '''
    def __init__(self, n_gen, pop_init_method, batch_size, algo, seed=None, **kwargs):
        '''
        Initialize a solver.

        Parameters
        ----------
        n_gen: int
            Number of generations to solve.
        pop_init_method: str
            Method to initialize population.
        batch_size: int
            Batch size, i.e. population size.
        algo: pymoo.model.algorithm.Algorithm
            Class of multi-objective algorithm to use.
        seed: int, default=None
            Random seed.
        kwargs: dict
            Other keyword arguments for algorithm to initialize.
        '''
        self.n_gen = n_gen
        self.pop_init_method = pop_init_method
        self.batch_size = batch_size
        self.seed = seed
        self.algo_type = algo
        self.algo_kwargs = kwargs
        self.solution = None

    def solve(self, problem, X, Y):
        '''
        Solve the multi-objective problem.

        Parameters
        ----------
        problem: mobo.surrogate_problem.SurrogateProblem
            The surrogate problem to be solved.
        X: np.array
            Current design variables.
        Y: np.array
            Current performance values.

        Returns
        -------
        solution: dict
            A dictionary containing information of the solution.\n
            - solution['x']: Proposed design samples.
            - solution['y']: Performance of proposed design samples.
            - solution['algo']: The algoritm of the solver, containing some history information of the solving process.
        '''
        # initialize population
        sampling = self._get_sampling(X, Y)

        # setup algorithm
        algo = self.algo_type(sampling=sampling, **self.algo_kwargs)

        # optimization
        res = minimize(problem, algo, ('n_gen', self.n_gen), seed=self.seed)

        # construct solution
        self.solution = {'x': res.pop.get('X'), 'y': res.pop.get('F'), 'algo': res.algorithm}

        # fill the solution in case less than batch size
        pop_size = len(self.solution['x'])
        if pop_size < self.batch_size:
            indices = np.concatenate([np.arange(pop_size), np.random.choice(np.arange(pop_size), self.batch_size - pop_size)])
            self.solution['x'] = np.array(self.solution['x'])[indices]
            self.solution['y'] = np.array(self.solution['y'])[indices]

        return self.solution

    def _get_sampling(self, X, Y):
        '''
        Initialize population from data.

        Parameters
        ----------
        X: np.array
            Design variables.
        Y: np.array
            Performance values.

        Returns
        -------
        sampling: np.array or pymoo.model.sampling.Sampling
            Initial population or a sampling method for generating initial population.
        '''
        if self.pop_init_method == 'lhs':
            sampling = LatinHypercubeSampling()
        elif self.pop_init_method == 'nds':
            sorted_indices = NonDominatedSorting().do(Y)
            pop_size = self.algo_kwargs['pop_size']
            sampling = X[np.concatenate(sorted_indices)][:pop_size]
            # NOTE: use lhs if current samples are not enough
            if len(sampling) < pop_size:
                rest_sampling = lhs(X.shape[1], pop_size - len(sampling))
                sampling = np.vstack([sampling, rest_sampling])
        elif self.pop_init_method == 'random':
            sampling = FloatRandomSampling()
        else:
            raise NotImplementedError

        return sampling


