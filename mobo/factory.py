'''
Factory for importing different components of the MOBO framework by name
'''

def get_surrogate_model(name):
    from mobo.surrogate_model import GaussianProcess, ThompsonSampling
    
    surrogate_model = {
        'gp': GaussianProcess,
        'ts': ThompsonSampling,
    }

    surrogate_model['default'] = GaussianProcess

    return surrogate_model[name]


def get_acquisition(name):
    from mobo.acquisition import IdentityFunc, PI, EI, UCB, LCB

    acquisition = {
        'identity': IdentityFunc,
        'pi': PI,
        'ei': EI,
        'ucb': UCB,
        'lcb': LCB,
    }

    acquisition['default'] = IdentityFunc

    return acquisition[name]


def get_solver(name):
    from mobo.solver import NSGA2Solver, MOEADSolver, ParEGOSolver

    solver = {
        'nsga2': NSGA2Solver,
        'moead': MOEADSolver,
        'parego': ParEGOSolver,
    }

    solver['default'] = NSGA2Solver

    return solver[name]


def get_selection(name):
    from mobo.selection import HVI, Uncertainty, Random, MOEADSelect

    selection = {
        'hvi': HVI,
        'uncertainty': Uncertainty,
        'random': Random,
        'moead': MOEADSelect,
    }

    selection['default'] = HVI

    return selection[name]


def init_from_config(config, framework_args):
    '''
    Initialize each component of the MOBO framework from config
    '''
    init_func = {
        'surrogate': get_surrogate_model,
        'acquisition': get_acquisition,
        'selection': get_selection,
        'solver': get_solver,
    }

    framework = {}
    for key, func in init_func.items():
        kwargs = framework_args[key]
        if config is None:
            # no config specified, initialize from user arguments
            name = kwargs['name']
        else:
            # initialize from config specifications, if certain keys are not provided, use default settings
            name = config[key] if key in config else 'default'
        framework[key] = func(name)(**kwargs)

    return framework