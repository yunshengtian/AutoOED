from algorithm.mobo.mobo import MOBO

'''
High-level algorithm specifications by providing spec.
'''


class DGEMO(MOBO):
    '''
    DGEMO [Luković et al. 2020].
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'identity',
        'solver': 'discovery',
        'selection': 'dgemo',
    }


class TSEMO(MOBO):
    '''
    TSEMO [Bradford et al. 2018].
    '''
    spec = {
        'surrogate': 'ts',
        'acquisition': 'identity',
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
        'selection': 'moead',
    }


class ParEGO(MOBO):
    '''
    ParEGO [Knowles et al. 2006].
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'parego',
        'selection': 'random',
    }


'''
Define new algorithms here
'''


class Custom(MOBO):
    '''
    Fully customized algorithms which totally rely on user arguments to specify each component.
    '''
    spec = None


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