import numpy as np
from algorithm.moo.moo import MOO
from pymoo.algorithms.nsga2 import NSGA2 as NSGA2_algo

from pymoo.model.individual import Individual
from pymoo.model.population import Population
from pymoo.model.problem import Problem


class NSGA2(MOO):
    '''
    NSGA-II.
    '''
    def __init__(self, problem, algo_cfg):
        super().__init__(problem, algo_cfg)

    def _solve(self, pop):
        algo = NSGA2_algo(pop_size=self.batch_size)

        # filter out best samples so far
        pop = algo.survival.do(self.real_problem, pop, self.batch_size, algorithm=algo)

        # mate for offsprings (TODO: check) (NOTE: assume the while loop can stop)
        off = Population(0, individual=Individual())
        while len(off) < self.batch_size:
            new_off = algo.mating.do(self.real_problem, pop, len(pop), algorithm=algo)
            new_X = new_off.get('X')
            if self.real_problem.n_constr > 0:
                new_G = np.array([self.real_problem.evaluate_constraint(x) for x in new_X])
                new_CV = Problem.calc_constraint_violation(new_G)
                valid_idx = new_CV <= 0
            else:
                valid_idx = np.full(len(new_off), True)
            if np.any(valid_idx):
                off = Population.merge(off, new_off[valid_idx])
        
        return off