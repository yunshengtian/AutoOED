from algorithm.moo.moo import MOO
from pymoo.algorithms.nsga2 import NSGA2 as NSGA2_algo


class NSGA2(MOO):
    '''
    NSGA-II
    '''
    algo = NSGA2_algo


algos = {
    'nsga2': NSGA2,
}


def get_algorithm(name):
    '''
    Get class of algorithm by name
    '''
    try:
        return algos[name]
    except:
        return None


def get_algorithm_list():
    '''
    Get names of available algorithms
    '''
    return list(algos.keys())