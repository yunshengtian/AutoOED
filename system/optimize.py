import numpy as np
from problems.common import build_problem, generate_initial_samples
from mobo.algorithms import get_algorithm as get_algorithm_mobo
from moo.algorithms import get_algorithm as get_algorithm_moo
from system.utils import load_config


def optimize(config, X_init, Y_init, seed=None):
    '''
    Run MOBO optimization from X_init and Y_init to produce X_next_df
    '''
    problem_cfg, algo_cfg = config['problem'], config['algorithm']

    # set random seed
    np.random.seed(seed)
    algo_cfg['solver'].update({'seed': seed})

    # build problem
    problem = build_problem(problem_cfg)

    # initialize optimizer
    algo = get_algorithm_mobo(algo_cfg['name'])
    if algo is None:
        algo = get_algorithm_moo(algo_cfg['name'])
    if algo is None:
        raise Exception('Invalid algorithm name')
    optimizer = algo(problem, algo_cfg)

    # solve
    return optimizer.solve(X_init, Y_init)
