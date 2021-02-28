import os
import yaml
from collections.abc import Iterable
from problem.common import get_problem_config, check_problem_exist
from problem.config import transform_config
from algorithm.utils import check_algorithm_exist


def load_config(path):
    '''
    Load config from file
    '''
    try:
        with open(path, 'r') as f:
            config = yaml.load(f, Loader=yaml.FullLoader)
    except:
        raise Exception('not a valid yaml file')
    return config


def save_config(config, path):
    '''
    Save config to file
    '''
    try:
        with open(path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    except:
        raise Exception('not a valid config dictionary')


def check_config(config):
    '''
    Check validity of the config
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
        assert key in ['name', 'ref_point'], f'invalid key {key} in problem config dictionary'

    assert 'name' in prob_cfg, 'problem name not provided'
    assert type(prob_cfg['name']) == str, 'problem name is not a string'
    assert check_problem_exist(prob_cfg['name']), f'problem {prob_cfg["name"]} does not exist'

    if 'ref_point' in prob_cfg and prob_cfg['ref_point'] is not None:
        assert isinstance(prob_cfg['ref_point'], Iterable) and type(prob_cfg['ref_point']) != str, 'invalid type of reference point'
        full_prob_cfg = get_problem_config(prob_cfg['name'])
        n_obj = full_prob_cfg['n_obj']
        assert len(prob_cfg['ref_point']) == n_obj, 'dimension of reference point mismatches number of objectives'

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
        assert type(exp_cfg['init_sample_path']) == str, 'invalid type of initial sample path'
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
        assert key in ['name', 'n_process', 'surrogate', 'acquisition', 'solver', 'selection'], f'invalid key {key} in algorithm config dictionary'
    
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
    
    if 'surrogate' in algo_cfg and algo_cfg['surrogate'] is not None:
        assert isinstance(algo_cfg['surrogate'], dict), 'surrogate settings must be provided as a dictionary'
        assert 'name' in algo_cfg['surrogate'], 'surrogate name is not provided'
        assert type(algo_cfg['surrogate']['name']) == str, 'invalid type of surrogate name'
        # TODO: check validity of arguments

    if 'acquisition' in algo_cfg and algo_cfg['acquisition'] is not None:
        assert isinstance(algo_cfg['acquisition'], dict), 'acquisition settings must be provided as a dictionary'
        assert 'name' in algo_cfg['acquisition'], 'acquisition name is not provided'
        assert type(algo_cfg['acquisition']['name']) == str, 'invalid type of acquisition name'
        # TODO: check validity of arguments

    if 'solver' in algo_cfg and algo_cfg['solver'] is not None:
        assert isinstance(algo_cfg['solver'], dict), 'solver settings must be provided as a dictionary'
        assert 'name' in algo_cfg['solver'], 'solver name is not provided'
        assert type(algo_cfg['solver']['name']) == str, 'invalid type of solver name'
        # TODO: check validity of arguments

    if 'selection' in algo_cfg and algo_cfg['selection'] is not None:
        assert isinstance(algo_cfg['selection'], dict), 'selection settings must be provided as a dictionary'
        assert 'name' in algo_cfg['selection'], 'selection name is not provided'
        assert type(algo_cfg['selection']['name']) == str, 'invalid type of selection name'
        # TODO: check validity of arguments


def complete_config(config, check=False):
    '''
    Fill default values of the config
    '''
    if check:
        check_config(config)

    new_config = config.copy()
    prob_cfg, exp_cfg, algo_cfg = new_config['problem'], new_config['experiment'], new_config['algorithm']
    
    # problem
    if 'ref_point' not in prob_cfg:
        prob_cfg['ref_point'] = None

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
        algo_cfg['n_process'] = 1
    
    if 'surrogate' not in algo_cfg or algo_cfg['surrogate'] is None:
        algo_cfg['surrogate'] = {
            'name': 'gp',
            'n_spectral_pts': 100,
            'nu': 5,
            'mean_sample': False,
        }

    if 'acquisition' not in algo_cfg or algo_cfg['acquisition'] is None:
        algo_cfg['acquisition'] = {
            'name': 'identity',
        }

    if 'solver' not in algo_cfg or algo_cfg['solver'] is None:
        algo_cfg['solver'] = {
            'name': 'nsga2',
            'pop_size': 100,
            'n_gen': 200,
            'pop_init_method': 'nds',
        }

    if 'selection' not in algo_cfg or algo_cfg['selection'] is None:
        algo_cfg['selection'] = {
            'name': 'hvi',
        }

    # update arguments for algorithm config
    full_prob_cfg = get_problem_config(prob_cfg['name'])
    trans_prob_cfg = transform_config(full_prob_cfg)
    n_var, n_obj = trans_prob_cfg['n_var'], full_prob_cfg['n_obj']
    n_process, batch_size = algo_cfg['n_process'], exp_cfg['batch_size']

    algo_cfg['surrogate'].update({'problem_cfg': full_prob_cfg})
    algo_cfg['solver'].update({'n_obj': n_obj, 'n_process': n_process, 'batch_size': batch_size})
    algo_cfg['selection'].update({'batch_size': batch_size})

    return new_config
