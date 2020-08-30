'''
Factory for importing different components of the MOBO framework by name
'''

def get_surrogate_model(name):
    from mobo.surrogate_model import GaussianProcess, ThompsonSampling, NeuralNetwork
    
    surrogate_model = {
        'gp': GaussianProcess,
        'ts': ThompsonSampling,
        'nn': NeuralNetwork,
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


def init_framework(spec, config):
    '''
    Initialize each component of the MOBO framework from spec provided by algorithm and config provided by user
    '''
    init_func = {
        'surrogate': get_surrogate_model,
        'acquisition': get_acquisition,
        'selection': get_selection,
        'solver': get_solver,
    }

    framework = {}
    for key, func in init_func.items():
        kwargs = config[key]
        if spec is None:
            # no spec specified, initialize from user config
            name = kwargs['name']
        else:
            # initialize from default specifications from algorithm, if certain keys are not provided, use default settings
            name = spec[key] if key in spec else 'default'
        framework[key] = func(name)(**kwargs) # initialize framework components by parameters from user config

    return framework