from algorithm.mobo.algorithms import get_algorithm_list as get_algo_list_mobo
from algorithm.moo.algorithms import get_algorithm_list as get_algo_list_moo
from algorithm.mobo.algorithms import get_algorithm as get_algorithm_mobo
from algorithm.moo.algorithms import get_algorithm as get_algorithm_moo


def get_algorithm_list():
    '''
    Get names of available algorithms
    '''
    return get_algo_list_mobo() + get_algo_list_moo()


def get_algorithm(name):
    '''
    Get algorithm by its name
    '''
    algo = get_algorithm_mobo(name)
    if algo is None:
        algo = get_algorithm_moo(name)
    if algo is None:
        raise Exception('Invalid algorithm name')
    return algo


def check_algorithm_exist(name):
    '''
    Check if algorithm exists
    '''
    return name in get_algorithm_list()


def get_algorithm_class(name):
    '''
    Check if algorithm is MOBO or MOO
    '''
    if name in get_algo_list_mobo():
        return 'MOBO'
    if name in get_algo_list_moo():
        return 'MOO'
    raise Exception('Invalid algorithm name')