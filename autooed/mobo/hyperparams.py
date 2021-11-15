'''
Default hyperparameters with hierarchy: module_type -- module_class -- module_param.
'''

from multiprocessing import cpu_count


surrogate_hyperparams = {
    'gp': {
        '__name__': 'Gaussian Process',
        'nu': dict(dtype=int, default=1, choices=[1, 3, 5, -1]),
    },
    'nn': {
        '__name__': 'Neural Network',
        'hidden_size': dict(dtype=int, default=50, constr=lambda x: x > 0),
        'hidden_layers': dict(dtype=int, default=3, constr=lambda x: x > 0),
        'activation': dict(dtype=str, default='tanh', choices=['relu', 'tanh']),
        'lr': dict(dtype=float, default=1e-3, constr=lambda x: x > 0),
        'weight_decay': dict(dtype=float, default=1e-4, constr=lambda x: x > 0),
        'n_epoch': dict(dtype=int, default=100, constr=lambda x: x > 0),
    },
    'bnn': {
        '__name__': 'Bayesian Neural Network',
        'hidden_size': dict(dtype=int, default=50, constr=lambda x: x > 0),
        'hidden_layers': dict(dtype=int, default=3, constr=lambda x: x > 0),
        'activation': dict(dtype=str, default='tanh', choices=['relu', 'tanh']),
        'lr': dict(dtype=float, default=1e-3, constr=lambda x: x > 0),
        'weight_decay': dict(dtype=float, default=1e-4, constr=lambda x: x > 0),
        'n_epoch': dict(dtype=int, default=100, constr=lambda x: x > 0),
    },
}


acquisition_hyperparams = {
    'ei': {
        '__name__': 'Expected Improvement',
    },
    'identity': {
        '__name__': 'Identity',
    },
    'pi': {
        '__name__': 'Probability of Improvement',
    },
    'ts': {
        '__name__': 'Thompson Sampling',
        'n_spectral_pts': dict(dtype=int, default=100, constr=lambda x: x > 0),
        'mean_sample': dict(dtype=bool, default=False),
    },
    'ucb': {
        '__name__': 'Upper Confidence Bound',
    },
}


solver_hyperparams = {
    # multi-objective
    'nsga2': {
        '__name__': 'NSGA-II',
        'n_gen': dict(dtype=int, default=200, constr=lambda x: x > 0),
        'pop_size': dict(dtype=int, default=200, constr=lambda x: x > 0),
    },
    'moead': {
        '__name__': 'MOEA/D',
        'n_gen': dict(dtype=int, default=100, constr=lambda x: x > 0),
        'pop_size': dict(type=int, default=100, constr=lambda x: x > 0),
    },
    'parego': {
        '__name__': 'ParEGO',
        'n_process': dict(dtype=int, default=cpu_count(), constr=lambda x: x > 0),
    },
    'discovery': {
        '__name__': 'ParetoFrontDiscovery',
        'n_gen': dict(dtype=int, default=10, constr=lambda x: x > 0),
        'pop_size': dict(dtype=int, default=100, constr=lambda x: x > 0),
        'n_process': dict(dtype=int, default=cpu_count(), constr=lambda x: x > 0),
    },
    # single-objective
    'ga': {
        '__name__': 'Genetic Algorithm',
        'pop_size': dict(dtype=int, default=200, constr=lambda x: x > 0),
    },
    'cmaes': {
        '__name__': 'CMA-ES',
    },
}


selection_hyperparams = {
    'direct': {
        '__name__': 'Direct',
    },
    'random': {
        '__name__': 'Random',
    },
    'hvi': {
        '__name__': 'Hypervolume Improvement',
    },
    'uncertainty': {
        '__name__': 'Uncertainty',
    },
}


async_hyperparams = {
    'none': {
        '__name__': 'None',
    },
    'kb': {
        '__name__': 'Kriging Believer',
    },
    'lp': {
        '__name__': 'Local Penalizer',
        'penalize_acq': dict(dtype=str, default='lp', choices=['lp', 'llp', 'hlp']),
    },
    'bp': {
        '__name__': 'Believer Penalizer',
        'factor': dict(dtype=float, default=0.2, constr=lambda x: x >= 0 and x <= 1),
        'penalize_acq': dict(dtype=str, default='lp', choices=['lp', 'llp', 'hlp']),
    },
}


hyperparams = {
    'surrogate': surrogate_hyperparams,
    'acquisition': acquisition_hyperparams,
    'solver': solver_hyperparams,
    'selection': selection_hyperparams,
    'async': async_hyperparams,
}


def _check_module_type(module_type):
    assert module_type in hyperparams.keys(), f'Undefined module type {module_type}'


def _check_module_class(module_type, module_class):
    _check_module_type(module_type)
    assert module_class in hyperparams[module_type].keys(), f'Undefined module class {module_class}'


def _check_module_param(module_type, module_class, module_param):
    _check_module_class(module_type, module_class)
    assert module_param in hyperparams[module_type][module_class].keys(), f'Undefined module parameter {module_param}'


def get_hp_name_by_class(module_type, module_class):
    '''
    '''
    _check_module_class(module_type, module_class)
    module_params = hyperparams[module_type][module_class]
    assert '__name__' in module_params, f'Name of module class {module_class} is not defined'
    return module_params['__name__']


def get_hp_class_by_name(module_type, module_name):
    '''
    '''
    _check_module_type(module_type)
    for module_class, module_params in hyperparams[module_type].items():
        if module_name == module_params['__name__']:
            return module_class
    raise Exception(f'Cannot find module class with name {module_name}')


def get_hp_classes(module_type):
    '''
    Get all the classes of a given module type
    '''
    _check_module_type(module_type)
    return hyperparams[module_type]


def get_hp_class_names(module_type):
    '''
    '''
    _check_module_type(module_type)
    names = []
    for module_params in hyperparams[module_type].values():
        names.append(module_params['__name__'])
    return names


def get_hp_params(module_type, module_class):
    '''
    Get all the parameters of a given module class
    '''
    _check_module_class(module_type, module_class)
    return hyperparams[module_type][module_class]


def get_hp_value(module_type, module_class, module_param):
    '''
    Get the value of a given module parameter
    '''
    _check_module_param(module_type, module_class, module_param)
    return hyperparams[module_type][module_class][module_param]
