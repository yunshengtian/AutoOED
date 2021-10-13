import random
import numpy as np
from time import time

from autooed.problem import build_problem
from autooed.mobo import get_algorithm


def _build_optimizer(config):
    '''
    Build optimizer based on problem and configurations.

    Parameters
    ----------
    config: dict
        Experiment configuration
    '''
    prob_cfg, algo_cfg = config['problem'], config['algorithm']

    problem = build_problem(prob_cfg['name'])
    algo = get_algorithm(algo_cfg['name'])
    optimizer = algo(problem, algo_cfg)
    
    return optimizer


def _set_random_seed(config):
    '''
    Set random seed based on time.
    '''
    # set random seed
    seed = int(time() * 100) % 10000
    random.seed(seed)
    np.random.seed(seed)

    config = config.copy()
    config['algorithm']['solver'].update({'seed': seed})
    return config


def optimize(config, X, Y, random=True):
    '''
    Run MOBO optimization from X and Y to produce X_next
    '''
    if random:
        config = _set_random_seed(config)

    # build optimizer
    optimizer = _build_optimizer(config)

    # solve for best X_next
    batch_size = config['experiment']['batch_size']
    X_next = optimizer.optimize(X, Y, batch_size)

    return X_next


def predict(config, X, Y, X_next):
    '''
    Predict performance of X_next based on X_init and Y_init
    '''
    # build optimizer
    optimizer = _build_optimizer(config)

    # predict performance of X_next
    Y_next_mean, Y_next_std = optimizer.predict(X, Y, X_next, fit=True)

    return Y_next_mean, Y_next_std


def optimize_predict(config, X, Y, random=True):
    '''
    Optimize then predit.
    '''
    if random:
        config = _set_random_seed(config)

    # build optimizer
    optimizer = _build_optimizer(config)

    # solve for best X_next
    batch_size = config['experiment']['batch_size']
    X_next = optimizer.optimize(X, Y, batch_size)

    # predict performance of X_next
    Y_next_mean, Y_next_std = optimizer.predict(X, Y, X_next)
    
    return X_next, (Y_next_mean, Y_next_std)


def evaluate(name, x_next):
    '''
    Evaluate performance of x_next
    '''
    # build problem
    problem = build_problem(name)

    # evaluate x_next with real problem
    y_next = np.array(problem.evaluate_objective(x_next))

    return y_next
