import yaml
import numpy as np
from problems.common import build_problem


def correct_config(problem_cfg):
    '''
    Correct n_var and n_obj in config file due to problem specification
    '''
    problem = build_problem(problem_cfg)
    problem_cfg['n_var'], problem_cfg['n_obj'] = problem.n_var, problem.n_obj


def load_config(config_path):
    '''
    Post-process to arguments specified in config file for file simplicity
    '''
    with open(config_path, 'r') as f:
        config = yaml.load(f, Loader=yaml.FullLoader)

    general_cfg, problem_cfg, algo_cfg = config['general'], config['problem'], config['algorithm']
    if 'ref_point' not in problem_cfg:
        problem_cfg['ref_point'] = None
    correct_config(problem_cfg)

    n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
    n_process, batch_size = general_cfg['n_process'], general_cfg['batch_size']

    # set default values for optional configurations
    if 'var_name' not in problem_cfg:
        problem_cfg['var_name'] = [f'x{i + 1}' for i in range(n_var)]
    if 'obj_name' not in problem_cfg:
        problem_cfg['obj_name'] = [f'f{i + 1}' for i in range(n_obj)]

    problem_cfg['n_init_sample'] = general_cfg['n_init_sample'] # TODO
    algo_cfg['surrogate'].update({'n_var': n_var, 'n_obj': n_obj})
    algo_cfg['solver'].update({'n_obj': n_obj, 'n_process': n_process, 'batch_size': batch_size})
    algo_cfg['selection'].update({'batch_size': batch_size})

    return config


def check_pareto(Y):
    '''
    Check pareto optimality of the input performance data
    '''
    sorted_indices = np.argsort(Y.T[0])
    is_pareto = np.zeros(len(Y), dtype=bool)
    for idx in sorted_indices:
        # check domination relationship
        if not (np.logical_and((Y <= Y[idx]).all(axis=1), (Y < Y[idx]).any(axis=1))).any():
            is_pareto[idx] = True
    return is_pareto


def find_pareto_front(Y):
    '''
    Return pareto front of the input performance data
    '''
    sorted_indices = np.argsort(Y.T[0])
    pareto_indices = []
    for idx in sorted_indices:
        # check domination relationship
        if not (np.logical_and((Y <= Y[idx]).all(axis=1), (Y < Y[idx]).any(axis=1))).any():
            pareto_indices.append(idx)
    return Y[pareto_indices]
