import yaml
import numpy as np
from argparse import Namespace
from problems.common import build_problem, generate_initial_samples
from mobo.algorithms import get_algorithm


def process_args(args_path):
    '''
    Post-process to arguments specified in config file for file simplicity
    '''
    with open(args_path, 'r') as f:
        all_args = yaml.load(f, Loader=yaml.FullLoader)

    general_args = Namespace(**all_args['general'])
    framework_args = all_args.copy()
    framework_args.pop('general')

    n_var, n_obj = general_args.n_var, general_args.n_obj
    n_process, batch_size = general_args.n_process, general_args.batch_size
    framework_args['surrogate'].update({'n_var': n_var, 'n_obj': n_obj})
    framework_args['solver'].update({'n_obj': n_obj, 'n_process': n_process, 'batch_size': batch_size})
    framework_args['selection'].update({'batch_size': batch_size})

    return general_args, framework_args


def optimize(problem, X_init, Y_init):
    '''
    Run MOBO optimization from X_init and Y_init to produce X_next_df
    '''
    # load config
    args, framework_args = process_args('experiment_config.yml')

    # set seed
    np.random.seed(args.seed)

    # initialize optimizer
    optimizer = get_algorithm(args.algo)(problem, args.ref_point, framework_args)

    # solve
    X_next_df = optimizer.solve(X_init, Y_init) # see _build_dataframe() in mobo/mobo.py for the dataframe format

    return X_next_df


if __name__ == '__main__':

    # load config
    args, _ = process_args('experiment_config.yml')

    # build problem
    problem, true_pfront = build_problem(args.problem, args.n_var, args.n_obj)

    # generate initial samples
    X_init, Y_init = generate_initial_samples(problem, args.n_init_sample)

    # run optimization
    result_df = optimize(problem, X_init, Y_init)
    
    print(result_df)