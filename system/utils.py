import yaml
import numpy as np
import pandas as pd
from problems.common import build_problem, get_problem_list
from mobo.algorithms import get_algorithm_list


def correct_config(config):
    '''
    Correct n_var and n_obj in config file due to problem specification
    Update default values if not specified in config
    '''
    general_cfg, problem_cfg, algo_cfg = config['general'], config['problem'], config['algorithm']
    problem = build_problem(problem_cfg)
    problem_cfg['n_var'], problem_cfg['n_obj'] = problem.n_var, problem.n_obj

    # fill default values by depth-first search
    default_config = load_default_config()
    def correct_values_dfs(config, default_config):
        for key, value in default_config.items():
            if key not in config:
                if value == 'required':
                    raise Exception('Required value missing in config')
                else:
                    config[key] = value
            elif config[key] is None:
                config[key] = value
            if isinstance(value, dict):
                correct_values_dfs(config[key], default_config[key])
    correct_values_dfs(config, default_config)

    # process default values for optional configurations
    if 'var_name' not in problem_cfg or problem_cfg['var_name'] is None:
        problem_cfg['var_name'] = [f'x{i + 1}' for i in range(problem.n_var)]
    if 'obj_name' not in problem_cfg or problem_cfg['obj_name'] is None:
        problem_cfg['obj_name'] = [f'f{i + 1}' for i in range(problem.n_obj)]


def process_config(config):
    '''
    Post-process to arguments specified in config file for file simplicity
    '''
    general_cfg, problem_cfg, algo_cfg = config['general'], config['problem'], config['algorithm']
    correct_config(config)

    n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
    n_process, batch_size = general_cfg['n_process'], general_cfg['batch_size']

    problem_cfg['n_init_sample'] = general_cfg['n_init_sample'] 
    algo_cfg['surrogate'].update({'n_var': n_var, 'n_obj': n_obj})
    algo_cfg['solver'].update({'n_obj': n_obj, 'n_process': n_process, 'batch_size': batch_size})
    algo_cfg['selection'].update({'batch_size': batch_size})

    return config


def load_config(config_path):
    '''
    Load config from file path and process config
    '''
    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except:
        raise Exception('not a valid yaml file')
    
    return process_config(config)


def load_default_config():
    '''
    Load default config for optional values
    '''
    default_config_path = 'config/default_config.yml'
    with open(default_config_path, 'r') as f:
        default_config = yaml.load(f, Loader=yaml.FullLoader)
    return default_config
    

def get_available_algorithms():
    '''
    Get names of available algorithms
    '''
    return get_algorithm_list()


def get_available_problems():
    '''
    Get names of available problems
    '''
    return get_problem_list()


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


def calc_pred_error(Y, Y_expected):
    '''
    Calculate averaged relative prediction error (in %)
    '''
    pred_error = np.sum(np.linalg.norm(Y - Y_expected, axis=1) / np.linalg.norm(Y)) / len(Y) * 100.0
    return pred_error


def find_closest_point(y, Y, return_index=False):
    '''
    Find the closest point to y in array Y
    '''
    idx = np.argmin(np.linalg.norm(np.array(y) - Y, axis=1))
    if return_index:
        return Y[idx], idx
    else:
        return Y[idx]


def generate_initial_dataframe(X, Y, hv):
    '''
    Generate initial dataframe from initial X, Y and hypervolume
    '''
    data = {}
    sample_len = len(X)
    n_var, n_obj = X.shape[1], Y.shape[1]

    # design variables
    for i in range(n_var):
        data[f'x{i + 1}'] = X[:, i]

    # prediction and uncertainty
    for i in range(n_obj):
        data[f'f{i + 1}'] = Y[:, i]
    for i in range(n_obj):
        data[f'expected_f{i + 1}'] = np.zeros(sample_len)
    for i in range(n_obj):
        data[f'uncertainty_f{i + 1}'] = np.zeros(sample_len)

    # hypervolume
    data['hv'] = hv.calc(Y)

    # prediction error
    data['pred_error'] = np.ones(sample_len) * 100

    # pareto optimality
    data['is_pareto'] = check_pareto(Y)

    return pd.DataFrame(data=data)
