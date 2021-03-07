from .nsga2 import NSGA2
from .moead import MOEAD


algos = {
    'nsga2': NSGA2,
    'moead': MOEAD,
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