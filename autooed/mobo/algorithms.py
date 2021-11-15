'''
High-level algorithm specifications by providing spec.
'''

from autooed.mobo.mobo import MOBO


class DGEMO(MOBO):
    '''
    DGEMO [Luković et al. 2020].
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'identity',
        'solver': 'discovery',
        'selection': 'direct',
    }


class TSEMO(MOBO):
    '''
    TSEMO [Bradford et al. 2018].
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'ts',
        'solver': 'nsga2',
        'selection': 'hvi',
    }


class USEMO_EI(MOBO):
    '''
    USeMO [Belakaria and Deshwal 2020], using EI as acquisition.
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'nsga2',
        'selection': 'uncertainty',
    }


class MOEAD_EGO(MOBO):
    '''
    MOEA/D-EGO [Zhang et al. 2009].
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'moead',
        'selection': 'direct',
    }


class ParEGO(MOBO):
    '''
    ParEGO [Knowles et al. 2006].
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'parego',
        'selection': 'direct',
    }


'''
Define new algorithms here.
'''


class Custom(MOBO):
    '''
    Fully customized algorithms which totally rely on user arguments to specify each component.
    '''
    pass


algos = {
    'dgemo': DGEMO,
    'tsemo': TSEMO,
    'usemo-ei': USEMO_EI,
    'moead-ego': MOEAD_EGO,
    'parego': ParEGO,
    'custom': Custom,
}


def get_algorithm(name):
    '''
    Get class of algorithm by name.
    '''
    if name in algos:
        return algos[name]
    else:
        raise Exception(f'Undefined algorithm {name}')


def get_algorithm_list():
    '''
    Get names of available algorithms.
    '''
    return list(algos.keys())


def check_algorithm_exist(name):
    '''
    Check if algorithm exists
    '''
    return name in get_algorithm_list()


def build_algorithm(name, problem, module_cfg):
    '''
    Build algorithm instance.
    '''
    algo_cls = get_algorithm(name)
    return algo_cls(problem, module_cfg)
