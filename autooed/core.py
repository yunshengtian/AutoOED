'''
Core functions of optimization, prediction and evaluation, given problem and experiment configurations.
'''

import random
import numpy as np
from time import time

from autooed.problem import build_problem
from autooed.mobo import get_algorithm


def _build_optimizer(config):
    '''
    Build optimizer based on the problem and experiment configurations.

    Parameters
    ----------
    config: dict
        Experiment configuration dict.

    Returns
    -------
    optimizer: autooed.mobo.mobo.MOBO
        The built optimizer.
    '''
    prob_cfg, algo_cfg = config['problem'], config['algorithm']

    problem = build_problem(prob_cfg['name'])
    algo = get_algorithm(algo_cfg['name'])
    optimizer = algo(problem, algo_cfg)
    
    return optimizer


def _set_random_seed(config):
    '''
    Set random seed based on time.

    Parameters
    ----------
    config: dict
        Experiment configuration dict.

    Returns
    -------
    config: dict
        Experiment configuration dict with the updated random seed.
    '''
    # set random seed
    seed = int(time() * 100) % 10000
    random.seed(seed)
    np.random.seed(seed)

    config = config.copy()
    config['algorithm']['solver'].update({'seed': seed})
    return config


def optimize(config, X, Y, X_busy=None, random=True, batch_size=None):
    '''
    Optimize on existing designs and performance to propose next designs to evaluate.

    Parameters
    ----------
    config: dict
        Experiment configuration dict.
    X: np.array
        Given existing designs.
    Y: np.array
        Performance of the given designs.
    X_busy: np.array
        Designs under evaluation.
    random: bool
        Whether to set random seeds before optimization.

    Returns
    -------
    X_next: np.array
        The proposed designs to evaluate next.
    '''
    if random:
        config = _set_random_seed(config)

    # build optimizer
    optimizer = _build_optimizer(config)

    # solve for best X_next
    if batch_size is None:
        batch_size = config['experiment']['batch_size']
    X_next = optimizer.optimize(X, Y, X_busy, batch_size)

    return X_next


def predict(config, X, Y, X_next):
    '''
    Predict performance of certain designs based on existing designs and performance.

    Parameters
    ----------
    config: dict
        Experiment configuration dict.
    X: np.array
        Given existing designs.
    Y: np.array
        Performance of the given designs.
    X_next: np.array
        Designs to be predicted.

    Returns
    -------
    Y_next_mean: np.array
        Mean of the predicted performance.
    Y_next_std: np.array
        Standard deviation of the predicted performance.
    '''
    # build optimizer
    optimizer = _build_optimizer(config)

    # predict performance of X_next
    Y_next_mean, Y_next_std = optimizer.predict(X, Y, X_next, fit=True)

    return Y_next_mean, Y_next_std


def optimize_predict(config, X, Y, X_busy=None, random=True, batch_size=None):
    '''
    Optimize on existing designs and performance to propose next designs to evaluate along with the predicted performance.

    Parameters
    ----------
    config: dict
        Experiment configuration dict.
    X: np.array
        Given existing designs.
    Y: np.array
        Performance of the given designs.
    X_busy: np.array
        Designs under evaluation.
    random: bool
        Whether to set random seeds before optimization.

    Returns
    -------
    X_next: np.array
        The proposed designs to evaluate next.
    Y_next: tuple
        Predicted performance of the proposed designs, in the format of (Y_next_mean, Y_next_std).
    '''
    if random:
        config = _set_random_seed(config)

    # build optimizer
    optimizer = _build_optimizer(config)

    # solve for best X_next
    if batch_size is None:
        batch_size = config['experiment']['batch_size']
    X_next = optimizer.optimize(X, Y, X_busy, batch_size)

    # predict performance of X_next
    Y_next_mean, Y_next_std = optimizer.predict(X, Y, X_next)
    
    return X_next, (Y_next_mean, Y_next_std)


def evaluate(name, x_next):
    '''
    Evaluate performance of a given design.

    Parameters
    ----------
    name: str
        Name of the problem.
    x_next: np.array
        Design to be evaluated.

    Returns
    -------
    y_next: np.array
        Performance of the given design.
    '''
    # build problem
    problem = build_problem(name)

    # evaluate x_next with real problem
    y_next = np.array(problem.evaluate_objective(x_next))

    return y_next
