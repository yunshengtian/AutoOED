from autooed.mobo.algorithms import get_algorithm_list, get_algorithm, build_algorithm
from autooed.problem.common import build_problem


def check_algorithm_exist(name):
    '''
    Check if algorithm exists
    '''
    return name in get_algorithm_list()
