import numpy as np
from time import time
from problem.common import build_problem
from algorithm.utils import get_algorithm


def build_optimizer(config):
    '''
    Build optimizer based on problem and configurations
    Input:
        config: experiment configuration
    '''
    prob_cfg, algo_cfg = config['problem'], config['algorithm']

    problem = build_problem(prob_cfg['name'])
    algo = get_algorithm(algo_cfg['name'])
    optimizer = algo(problem, algo_cfg)
    
    return optimizer


def optimize(config, X_init, Y_init):
    '''
    Run MOBO optimization from X_init and Y_init to produce X_next
    '''
    # set random seed
    seed = int(time())
    np.random.seed(seed)
    config = config.copy()
    config['algorithm']['solver'].update({'seed': seed})

    # build optimizer
    optimizer = build_optimizer(config)

    # solve for best X_next
    X_next, (Y_expected, Y_uncertainty) = optimizer.solve(X_init, Y_init)
    
    return X_next, (Y_expected, Y_uncertainty)


def predict(config, X_init, Y_init, X_next):
    '''
    Predict performance of X_next based on X_init and Y_init
    '''
    # build optimizer
    optimizer = build_optimizer(config)

    # predict performance of X_next
    Y_expected, Y_uncertainty = optimizer.predict(X_init, Y_init, X_next)

    return Y_expected, Y_uncertainty


def evaluate(name, x_next):
    '''
    Evaluate performance of x_next
    '''
    # build problem
    problem = build_problem(name)

    # evaluate x_next with real problem
    y_next = np.array(problem.evaluate_objective(x_next))

    return y_next