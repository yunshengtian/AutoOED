import numpy as np
from time import time
from problems.common import build_problem
from system.utils import build_optimizer


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
    X_next = optimizer.solve(X_init, Y_init)
    
    return X_next


def predict(config, X_init, Y_init, X_next):
    '''
    Predict performance of X_next based on X_init and Y_init
    '''
    # build optimizer
    optimizer = build_optimizer(config)

    # predict performance of X_next
    Y_expected, Y_uncertainty = optimizer.predict(X_init, Y_init, X_next)

    return Y_expected, Y_uncertainty


def evaluate(config, X_next):
    '''
    Evaluate performance of X_next
    '''
    # build problem
    problem = build_problem(config['problem'])

    # evaluate X_next with real problem
    Y_next = np.column_stack(problem.evaluate_performance(X_next))

    return Y_next