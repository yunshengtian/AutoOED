from mobo.mobo import MOBO

'''
High-level algorithm specifications by providing config
'''


class TSEMO(MOBO):
    '''
    TSEMO
    '''
    config = {
        'surrogate': 'ts',
        'acquisition': 'identity',
        'solver': 'nsga2',
        'selection': 'hvi',
    }


class USEMO_EI(MOBO):
    '''
    USeMO, using EI as acquisition
    '''
    config = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'nsga2',
        'selection': 'uncertainty',
    }


class MOEAD_EGO(MOBO):
    '''
    MOEA/D-EGO
    '''
    config = {
        'surrogate': 'gp',
        'acquisition': 'ei',
        'solver': 'moead',
        'selection': 'moead',
    }


class ParEGO(MOBO):
    '''
    ParEGO
    '''
    config = {
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
    config = None


algos = {
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
    return algos[name]


def get_algorithm_list():
    '''
    Get names of available algorithms
    '''
    return list(algos.keys())