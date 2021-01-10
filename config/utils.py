import os
import yaml
from problem.common import get_problem_config


def load_config(config_path):
    '''
    Load config from file path
    '''
    try:
        with open(config_path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except:
        raise Exception('not a valid yaml file')
    return config


def load_default_config():
    '''
    Load default config for optional values
    '''
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    default_config_path = f'{curr_dir}/experiment/default_config.yml'
    return load_config(default_config_path)


def process_config(config):
    '''
    Post-process to arguments specified in config file for file simplicity
    '''
    general_cfg, problem_cfg, algo_cfg = config['general'], config['problem'], config['algorithm']

    # fill default values by depth-first search
    default_config = load_default_config()
    def correct_values_dfs(config, default_config):
        for key, value in default_config.items():
            if key not in config:
                if value == 'required':
                    raise Exception(f'Required value for "{key}" missing in config')
                else:
                    config[key] = value
            elif config[key] is None:
                config[key] = value
            if isinstance(value, dict):
                correct_values_dfs(config[key], default_config[key])
    correct_values_dfs(config, default_config)

    # fill default dynamic values of problem config
    for key in ['var_lb', 'var_ub']:
        if key not in problem_cfg:
            problem_cfg[key] = None

    static_problem_cfg = get_problem_config(problem_cfg['name'])

    n_var, n_obj = static_problem_cfg['n_var'], static_problem_cfg['n_obj']
    n_process, batch_size = algo_cfg['n_process'], general_cfg['batch_size']

    algo_cfg['surrogate'].update({'n_var': n_var, 'n_obj': n_obj})
    algo_cfg['solver'].update({'n_obj': n_obj, 'n_process': n_process, 'batch_size': batch_size})
    algo_cfg['selection'].update({'batch_size': batch_size})

    return config
