import numpy as np
from algorithm.moo.moo import MOO
from pymoo.algorithms.moead import MOEAD as MOEAD_algo

from pymoo.factory import get_decomposition
from pymoo.model.individual import Individual
from pymoo.model.population import Population
from pymoo.model.problem import Problem


class MOEAD(MOO):
    '''
    MOEA/D
    '''
    def _solve(self, pop):
        # generate direction vectors by random sampling
        ref_dirs = np.random.random((self.batch_size, self.n_obj))
        ref_dirs /= np.expand_dims(np.sum(ref_dirs, axis=1), 1)

        algo = MOEAD_algo(ref_dirs=ref_dirs, n_neighbors=len(ref_dirs), eliminate_duplicates=False)
        repair, crossover, mutation = algo.mating.repair, algo.mating.crossover, algo.mating.mutation

        if isinstance(algo.decomposition, str):
            decomp = algo.decomposition
            if decomp == 'auto':
                if self.n_obj <= 2:
                    decomp = 'tchebi'
                else:
                    decomp = 'pbi'
            decomposition = get_decomposition(decomp)
        else:
            decomposition = algo.decomposition

        ideal_point = np.min(pop.get('F'), axis=0)

        # find the optimal individual for each reference direction
        opt_pop = Population(0, individual=Individual())
        for i in range(self.batch_size):
            N = algo.neighbors[i, :]
            FV = decomposition.do(pop.get("F"), weights=ref_dirs[i], ideal_point=ideal_point)
            opt_pop = Population.merge(opt_pop, pop[np.argmin(FV)])

        all_off = Population(0, individual=Individual())
        for i in np.random.permutation(self.batch_size):
            N = algo.neighbors[i, :]

            if np.random.random() < algo.prob_neighbor_mating:
                parents = N[np.random.permutation(algo.n_neighbors)][:crossover.n_parents]
            else:
                parents = np.random.permutation(algo.pop_size)[:crossover.n_parents]

            # do recombination and create an offspring
            off = crossover.do(self.real_problem, opt_pop, parents[None, :])
            off = mutation.do(self.real_problem, off)
            off = off[np.random.randint(0, len(off))]

            # repair first in case it is necessary
            if repair:
                off = algo.repair.do(self.real_problem, off, algorithm=algo)

            all_off = Population.merge(all_off, off)
        
        return all_off
