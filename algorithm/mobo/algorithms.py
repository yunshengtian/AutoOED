from algorithm.mobo.mobo import MOBO

'''
High-level algorithm specifications by providing spec
'''


class DGEMO(MOBO):
    '''
    DGEMO
    '''
    config = {
        'surrogate': 'gp',
        'acquisition': 'identity',
        'solver': 'discovery',
        'selection': 'dgemo',
    }


class TSEMO(MOBO):
    '''
    TSEMO
    '''
    spec = {
        'surrogate': 'ts',
        'acquisition': 'identity',
        'solver': 'nsga2',
        'selection': 'hvi',
    }


class USEMO_EI(MOBO):
    '''
    USeMO, using EI as acquisition
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'nsga2',
        'selection': 'uncertainty',
    }


class MOEAD_EGO(MOBO):
    '''
    MOEA/D-EGO
    '''
    spec = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'moead',
        'selection': 'moead',
    }


class ParEGO(MOBO):
    '''
    ParEGO
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
    Totally rely on user arguments to specify each component
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