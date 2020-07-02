import yaml
import numpy as np
from problems.common import build_problem, generate_initial_samples
from mobo.algorithms import get_algorithm


def load_config(config_path):
    '''
    Post-process to arguments specified in config file for file simplicity
    '''
    with open(config_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    genearl_cfg, problem_cfg, algo_cfg = config['general'], config['problem'], config['algorithm']

    n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
    n_process, batch_size = genearl_cfg['n_process'], genearl_cfg['batch_size']

    algo_cfg['surrogate'].update({'n_var': n_var, 'n_obj': n_obj})
    algo_cfg['solver'].update({'n_obj': n_obj, 'n_process': n_process, 'batch_size': batch_size})
    algo_cfg['selection'].update({'batch_size': batch_size})

    return config


def optimize(config, X_init, Y_init, seed=None):
    '''
    Run MOBO optimization from X_init and Y_init to produce X_next_df
    '''
    problem_cfg, algo_cfg = config['problem'], config['algorithm']

    # set random seed
    np.random.seed(seed)
    algo_cfg['solver'].update({'seed': seed})

    # build problem
    problem, _ = build_problem(problem_cfg)

    # initialize optimizer
    optimizer = get_algorithm(algo_cfg['name'])(problem, algo_cfg)

    # solve
    X_next_df = optimizer.solve(X_init, Y_init) # see _build_dataframe() in mobo/mobo.py for the dataframe format

    return X_next_df


if __name__ == '__main__':

    # load config
    config = load_config('experiment_config.yml')
    genearl_cfg, problem_cfg = config['general'], config['problem']

    # build problem
    problem, _ = build_problem(problem_cfg)

    # generate initial samples
    X_init, Y_init = generate_initial_samples(problem, genearl_cfg['n_init_sample'])

    # run optimization
    result_df = optimize(config, X_init, Y_init)
    
    print(result_df)