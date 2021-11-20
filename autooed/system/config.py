'''
Experiment configuration related tools.
'''

import os
import yaml
from collections.abc import Iterable
from multiprocessing import cpu_count

from autooed.problem import get_problem_config, check_problem_exist
from autooed.mobo import check_algorithm_exist
from autooed.mobo.hyperparams import get_hp_classes, get_hp_value


'''
Layout of the config dict and explanation of each key.
'''
config_map = {
    'experiment': {
        'n_random_sample': 'Number of random initial samples',
        'init_sample_path': 'Path of provided initial samples',
        'n_worker': 'Number of evaluation workers',
        'batch_size': 'Batch size',
    },
    'problem': {
        'name': 'Problem name',
        'n_var': 'Number of design variables',
        'n_obj': 'Number of objectives',
        'n_constr': 'Number of constraints',
        'obj_func': 'Objective evaluation program',
        'constr_func': 'Constraint evaluation program',
        'obj_type': 'Objective type',
        'var_lb': 'Lower bound',
        'var_ub': 'Upper bound',
        'var_name': 'Names',
        'obj_name': 'Names',
    },
    'algorithm': {
        'name': 'Algorithm name',
        'n_process': 'Number of parallel processes to use',
        'async': 'Asynchronous strategy',
    },
}


def load_config(path):
    '''
    Load config from file.

    Parameters
    ----------
    path: str
        Path of the configuration file (in yaml format) to load.

    Returns
    -------
    config: dict
        Loaded config dict.
    '''
    try:
        with open(path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except:
        raise Exception('not a valid yaml file')
    return config


def save_config(config, path):
    '''
    Save config to file.

    Parameters
    ----------
    path: str
        Path to save the configuration file (in yaml format).
    '''
    try:
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except:
        raise Exception('not a valid config dictionary')


def check_config(config):
    '''
    Check validity of the config dict.

    Parameters
    ----------
    config: dict
        Experiment config dict.
    '''
    # format
    assert isinstance(config, dict), 'config is not a dictionary'

    # key
    for key in config:
        assert key in ['problem', 'experiment', 'algorithm'], f'invalid key {key} in config dictonary'

    # problem
    assert 'problem' in config, 'problem settings are not specified'
    assert isinstance(config['problem'], dict), 'problem settings must be specified as a dictionary'
    prob_cfg = config['problem']

    for key in prob_cfg:
        assert key in ['name'], f'invalid key {key} in problem config dictionary'

    assert 'name' in prob_cfg, 'problem name not provided'
    assert type(prob_cfg['name']) == str, 'problem name is not a string'
    assert check_problem_exist(prob_cfg['name']), f'problem {prob_cfg["name"]} does not exist'

    # experiment
    assert 'experiment' in config, 'experiment settings are not specified'
    assert isinstance(config['experiment'], dict), 'experiment settings must be specified as a dictionary'
    exp_cfg = config['experiment']

    for key in exp_cfg:
        assert key in ['n_random_sample', 'init_sample_path', 'batch_size', 'n_iter', 'n_worker'], f'invalid key {key} in experiment config dictionary'

    assert 'n_random_sample' in exp_cfg or 'init_sample_path' in exp_cfg, 'either number of random initial samples or path to initial samples need to be provided'
    init_sample_exist = False
    if 'n_random_sample' in exp_cfg and exp_cfg['n_random_sample'] is not None:
        assert type(exp_cfg['n_random_sample']) == int, 'invalid type of random initial samples'
        if exp_cfg['n_random_sample'] > 1:
            init_sample_exist = True
    if 'init_sample_path' in exp_cfg and exp_cfg['init_sample_path'] is not None:
        assert type(exp_cfg['init_sample_path']) in [str, list], 'invalid type of initial sample path'
        # TODO: check whether initial sample path is valid
        init_sample_exist = True
    assert init_sample_exist, 'either let the number of random initial samples be a integer greater than 1 or provide a valid path to initial samples'

    if 'batch_size' in exp_cfg and exp_cfg['batch_size'] is not None:
        assert type(exp_cfg['batch_size']) == int and exp_cfg['batch_size'] > 0, 'batch size must be a positive integer'

    if 'n_iter' in exp_cfg and exp_cfg['n_iter'] is not None:
        assert type(exp_cfg['n_iter']) == int and exp_cfg['n_iter'] > 0, 'number of algorithm iterations must be a positive integer'
    
    if 'n_worker' in exp_cfg and exp_cfg['n_worker'] is not None:
        assert type(exp_cfg['n_worker']) == int and exp_cfg['n_worker'] > 0, 'number of evaluation workers must be a positive integer'

    # algorithm
    assert 'algorithm' in config, 'algorithm settings are not specified'
    assert isinstance(config['algorithm'], dict), 'algorithm settings must be specified as a dictionary'
    algo_cfg = config['algorithm']

    for key in algo_cfg:
        assert key in ['name', 'n_process', 'async', 'surrogate', 'acquisition', 'solver', 'selection'], f'invalid key {key} in algorithm config dictionary'
    
    assert 'name' in algo_cfg, 'algorithm name is not provided'
    assert type(algo_cfg['name']) == str, 'invalid type of algorithm name'

    if algo_cfg['name'] == 'custom':
        assert 'surrogate' in algo_cfg, 'surrogate settings are not provided for custom algorithm'
        assert 'acquisition' in algo_cfg, 'acquisition settings are not provided for custom algorithm'
        assert 'solver' in algo_cfg, 'solver settings are not provided for custom algorithm'
        assert 'selection' in algo_cfg, 'selection settings are not provided for custom algorithm'
    else:
        assert check_algorithm_exist(algo_cfg['name']), f'algorithm {algo_cfg["name"]} does not exist'

    if 'n_process' in algo_cfg and algo_cfg['n_process'] is not None:
        assert type(algo_cfg['n_process']) == int and algo_cfg['n_process'] > 0, 'number of parallel processes for optimization algorithm must be a positive integer'
    
    if 'async' in algo_cfg and algo_cfg['async'] is not None:
        assert 'name' in algo_cfg['async'], 'asynchronous strategy name is not provided'
        assert algo_cfg['async']['name'] in get_hp_classes('async'), f'undefined asynchronous strategy {algo_cfg["async"]["name"]}'

    if 'surrogate' in algo_cfg and algo_cfg['surrogate'] is not None:
        assert isinstance(algo_cfg['surrogate'], dict), 'surrogate settings must be provided as a dictionary'
        if algo_cfg['name'] == 'custom':
            assert 'name' in algo_cfg['surrogate'], 'surrogate name is not provided'
            assert type(algo_cfg['surrogate']['name']) == str, 'invalid type of surrogate name'
        # TODO: check validity of arguments

    if 'acquisition' in algo_cfg and algo_cfg['acquisition'] is not None:
        assert isinstance(algo_cfg['acquisition'], dict), 'acquisition settings must be provided as a dictionary'
        if algo_cfg['name'] == 'custom':
            assert 'name' in algo_cfg['acquisition'], 'acquisition name is not provided'
            assert type(algo_cfg['acquisition']['name']) == str, 'invalid type of acquisition name'
        # TODO: check validity of arguments

    if 'solver' in algo_cfg and algo_cfg['solver'] is not None:
        assert isinstance(algo_cfg['solver'], dict), 'solver settings must be provided as a dictionary'
        if algo_cfg['name'] == 'custom':
            assert 'name' in algo_cfg['solver'], 'solver name is not provided'
            assert type(algo_cfg['solver']['name']) == str, 'invalid type of solver name'
        # TODO: check validity of arguments

    if 'selection' in algo_cfg and algo_cfg['selection'] is not None:
        assert isinstance(algo_cfg['selection'], dict), 'selection settings must be provided as a dictionary'
        if algo_cfg['name'] == 'custom':
            assert 'name' in algo_cfg['selection'], 'selection name is not provided'
            assert type(algo_cfg['selection']['name']) == str, 'invalid type of selection name'
        # TODO: check validity of arguments


def complete_config(config, check=False):
    '''
    Fill default values of the config.

    Parameters
    ----------
    config: dict
        Experiment config dict.
    check: bool
        Whether to check the validity of the config before filling default values.

    Returns
    -------
    new_config: dict
        Completed config dict with default values filled.
    '''
    if check:
        check_config(config)

    new_config = config.copy()
    prob_cfg, exp_cfg, algo_cfg = new_config['problem'], new_config['experiment'], new_config['algorithm']

    # experiment
    if 'n_random_sample' not in exp_cfg or exp_cfg['n_random_sample'] is None:
        exp_cfg['n_random_sample'] = 0

    if 'init_sample_path' not in exp_cfg:
        exp_cfg['init_sample_path'] = None
        
    if 'batch_size' not in exp_cfg or exp_cfg['batch_size'] is None:
        exp_cfg['batch_size'] = 1

    if 'n_iter' not in exp_cfg or exp_cfg['n_iter'] is None:
        exp_cfg['n_iter'] = 1

    if 'n_worker' not in exp_cfg or exp_cfg['n_worker'] is None:
        exp_cfg['n_worker'] = exp_cfg['batch_size']

    # algorithm
    if 'n_process' not in algo_cfg or algo_cfg['n_process'] is None:
        algo_cfg['n_process'] = cpu_count()

    if 'async' not in algo_cfg:
        algo_cfg['async'] = None
    
    if 'surrogate' not in algo_cfg or algo_cfg['surrogate'] is None:
        algo_cfg['surrogate'] = {}

    if 'acquisition' not in algo_cfg or algo_cfg['acquisition'] is None:
        algo_cfg['acquisition'] = {}

    if 'solver' not in algo_cfg or algo_cfg['solver'] is None:
        algo_cfg['solver'] = {}
    else:
        algo_cfg['solver'].update({'n_process': algo_cfg['n_process']})

    if 'selection' not in algo_cfg or algo_cfg['selection'] is None:
        algo_cfg['selection'] = {}

    return new_config
