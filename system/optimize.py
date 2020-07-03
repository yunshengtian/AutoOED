import numpy as np
from problems.common import build_problem, generate_initial_samples
from mobo.algorithms import get_algorithm
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
    optimizer = get_algorithm(algo_cfg['name'])(problem, algo_cfg)

    # solve
    X_next_df = optimizer.solve(X_init, Y_init) # see _build_dataframe() in mobo/mobo.py for the dataframe format

    return X_next_df


if __name__ == '__main__':

    from argparse import ArgumentParser
    parser = ArgumentParser()
    parser.add_argument('--config-path', type=str, required=True)
    args = parser.parse_args()

    # load config
    config = load_config(args.config_path)
    genearl_cfg, problem_cfg = config['general'], config['problem']

    # build problem
    problem = build_problem(problem_cfg)

    # generate initial samples
    X_init, Y_init = generate_initial_samples(problem, genearl_cfg['n_init_sample'])

    # run optimization
    result_df = optimize(config, X_init, Y_init)
    
    print(result_df)