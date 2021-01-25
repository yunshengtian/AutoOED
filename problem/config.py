from collections.abc import Iterable
import numpy as np
import yaml


def load_config(path):
    '''
    Load config from file path
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
        assert key in ['name', 'type', 
            'n_var', 'var_name', 'var_lb', 'var_ub', 'var_choices', 'var', 
            'n_obj', 'obj_name', 'obj_type', 'obj_func', 'ref_point', 
            'n_constr', 'constr_func'], f'invalid key {key} in config dictionary'

    # name
    assert 'name' in config, 'problem name is not specified'
    assert type(config['name']) == str, 'problem name must be a string'

    # type
    assert 'type' in config, 'problem type is not specified'
    assert type(config['type']) == str, 'problem type must be a string'
    assert config['type'] in ['continuous', 'integer', 'binary', 'categorical', 'mixed'], 'invalid problem type'
    
    # var
    if config['type'] in ['continuous', 'integer', 'binary']:
        assert 'n_var' in config, 'number of variables is not provided'
        assert type(config['n_var']) == int and config['n_var'] > 0, 'number of variables must be a positive integer'
        n_var = config['n_var']

    if config['type'] in ['continuous', 'integer']:
        assert 'var_lb' in config, 'lower bound is not provided'
        assert 'var_ub' in config, 'upper bound is not provided'

        assert type(config['var_lb']) in [int, float] or (isinstance(config['var_lb'], Iterable) and type(config['var_lb']) != str), 'invalid type of lower bound'
        assert type(config['var_ub']) in [int, float] or (isinstance(config['var_ub'], Iterable) and type(config['var_ub']) != str), 'invalid type of upper bound'

        if isinstance(config['var_lb'], Iterable):
            assert len(config['var_lb']) == config['n_var'], 'number of lower bounds mismatches number of variables'
            for lb in config['var_lb']:
                assert type(lb) in [int, float], 'invalid type of lower bound'
            lb_list = list(config['var_lb'])
        else:
            lb_list = [config['var_lb']] * config['n_var']

        if isinstance(config['var_ub'], Iterable):
            assert len(config['var_ub']) == config['n_var'], 'number of upper bounds mismatches number of variables'
            for ub in config['var_ub']:
                assert type(ub) in [int, float], 'invalid type of upper bound'
            ub_list = list(config['var_ub'])
        else:
            ub_list = [config['var_ub']] * config['n_var']

        for lb, ub in zip(lb_list, ub_list):
            assert lb < ub, f'upper bound must be greater than lower bound'

    elif config['type'] == 'binary':
        pass

    elif config['type'] == 'categorical':
        if 'var' in config:
            assert isinstance(config['var'], dict), 'variable properties are not specified as a dictionary'
            assert len(config['var']) > 0, 'the dictionary of variable properties is empty'
            n_var = len(config['var'])

            for var_name, var_choices in config['var'].items():
                assert type(var_name) == str, 'invalid type of variable name'
                assert isinstance(var_choices, Iterable) and type(var_choices) != str, 'invalid type of variable choices'
                assert len(var_choices) == len(np.unique(var_choices)), 'duplicates in variable choices'

        else:
            assert 'n_var' in config, 'number of variables is not provided'
            assert type(config['n_var']) == int and config['n_var'] > 0, 'number of variables must be a positive integer'
            assert 'var_choices' in config, 'variable choices are not provided'
            assert isinstance(config['var_choices'], Iterable) and type(config['var_choices']) != str, 'invalid type of variable choices'
            assert len(config['var_choices']) == len(np.unique(config['var_choices'])), 'duplicates in variable choices'
            n_var = config['n_var']

    elif config['type'] == 'mixed':
        assert 'var' in config, 'variable properties are not provided'
        assert isinstance(config['var'], dict), 'variable properties are not specified as a dictionary'
        assert len(config['var']) > 0, 'the dictionary of variable properties is empty'
        n_var = len(config['var'])

        for var_name, var_info in config['var'].items():
            assert type(var_name) == str, 'invalid type of variable name'
            assert isinstance(var_info, dict), 'variable properties are not specified as a dictionary'
            assert 'type' in var_info, f'type of variable {var_name} is not provided'
            assert type(var_info['type']) == str, f'type of variable {var_name} is not a string'
            assert var_info['type'] in ['continuous', 'integer', 'binary', 'categorical'], f'invalid type of variable {var_name}'

            # key
            if var_info['type'] == 'continuous' or var_info['type'] == 'integer':
                for key in var_info:
                    assert key in ['type', 'lb', 'ub'], f'invalid key {key} in dictionary of variable {var_name}'
                assert 'lb' in var_info, f'lower bound of variable {var_name} is not provided'
                assert 'ub' in var_info, f'upper bound of variable {var_name} is not provided'

            elif var_info['type'] == 'binary':
                for key in var_info:
                    assert key in ['type'], f'invalid key {key} in the dictionary of variable {var_name}'
            
            elif var_info['type'] == 'categorical':
                for key in var_info:
                    assert key in ['type', 'choices'], f'invalid key {key} in the dictionary of variable {var_name}'
                assert 'choices' in var_info, f'choices of variable {var_name} are not provided'

            # value
            if var_info['type'] == 'continuous':
                assert type(var_info['lb']) in [int, float], f'invalid lower bound of variable {var_name}'
                assert type(var_info['ub']) in [int, float], f'invalid upper bound of variable {var_name}'
                assert var_info['lb'] < var_info['ub'], f'lower bound is no less than upper bound of variable {var_name}'

            elif var_info['type'] == 'integer':
                assert var_info['lb'] == int(var_info['lb']), f'invalid lower bound of variable {var_name}'
                assert var_info['ub'] == int(var_info['ub']), f'invalid upper bound of variable {var_name}'
                assert var_info['lb'] < var_info['ub'], f'lower bound is no less than upper bound of variable {var_name}'

            elif var_info['type'] == 'binary':
                pass

            elif var_info['type'] == 'categorical':
                assert isinstance(var_info['choices'], Iterable) and type(var_info['choices']) != str, f'invalid choices of variable {var_name}'
                assert len(var_info['choices']) == len(np.unique(var_info['choices'])), f'duplicates in the choices of variable {var_name}'
    
    if 'var_name' in config and config['var_name'] is not None:
        assert isinstance(config['var_name'], Iterable) and type(config['var_name']) != str, 'invalid variable names'
        assert len(config['var_name']) == n_var, 'number of variable names mismatches number of variables'
        assert len(config['var_name']) == len(np.unique(config['var_name'])), 'duplicates in variable names'
        for var_name in config['var_name']:
            assert type(var_name) == str, f'name of variable {var_name} is not a string'

    # obj
    assert 'n_obj' in config, 'number of objectives is not specified'
    assert type(config['n_obj']) == int and config['n_obj'] > 1, 'number of variables must be an integer greater than 1'
    n_obj = config['n_obj']

    if 'obj_name' in config and config['obj_name'] is not None:
        assert isinstance(config['obj_name'], Iterable) and type(config['obj_name']) != str, 'invalid objective names'
        assert len(config['obj_name']) == n_obj, 'number of objective names mismatches number of objectives'
        assert len(config['obj_name']) == len(np.unique(config['obj_name'])), 'duplicates in objective names'
        for obj_name in config['obj_name']:
            assert type(obj_name) == str, f'name of objective {obj_name} is not a string'

    if 'obj_type' in config and config['obj_type'] is not None:
        if type(config['obj_type']) == str:
            assert config['obj_type'] in ['min', 'max'], 'invalid objective type'
        else:
            assert isinstance(config['obj_type'], Iterable), 'invalid type of objective type'
            assert len(config['obj_type']) == n_obj, 'number of objective types mismatches number of objectives'
            for obj_type in config['obj_type']:
                assert obj_type in ['min', 'max'], 'invalid objective type'

    if 'obj_func' in config and config['obj_func'] is not None:
        assert type(config['obj_func']) == str, 'invalid type of objective function'
        # TODO: check if objective function is importable

    if 'ref_point' in config and config['ref_point'] is not None:
        assert isinstance(config['ref_point'], Iterable) and type(config['ref_point']) != str, 'invalid type of reference point'
        assert len(config['ref_point']) == n_obj, 'dimension of reference point mismatches number of objectives'
        for ref_point in config['ref_point']:
            assert ref_point is None or type(ref_point) in [int, float], 'invalid type of reference point'

    # constr
    if 'n_constr' in config and config['n_constr'] is not None:
        assert type(config['n_constr']) == int and config['n_constr'] >= 0, 'number of constraints must be a non-negative integer'

    if 'constr_func' in config and config['constr_func'] is not None:
        assert type(config['constr_func']) == str, 'invalid type of constraint function'
        # TODO: check if constraint function is importable


def transform_config(config, check=False):
    '''
    Transform and return the config for optimization
    Keys:
        n_var
        n_obj
        n_constr
        xl
        xu
    '''
    if check:
        check_config(config)

    new_config = {}
    
    # var
    if config['type'] == 'continuous' or config['type'] == 'integer':
        new_config['n_var'] = config['n_var']

        if isinstance(config['var_lb'], Iterable):
            new_config['xl'] = list(config['var_lb'])
        else:
            new_config['xl'] = config['var_lb']

        if isinstance(config['var_ub'], Iterable):
            new_config['xu'] = list(config['var_ub'])
        else:
            new_config['xu'] = config['var_ub']

    elif config['type'] == 'binary':
        new_config['n_var'] = config['n_var']
        new_config['xl'] = 0
        new_config['xu'] = 1

    elif config['type'] == 'categorical':
        if 'var' in config:
            new_config['n_var'] = len(config['var'])
        else:
            new_config['n_var'] = len(config['var_choices'])

        new_config['xl'] = 0
        new_config['xu'] = 1

    elif config['type'] == 'mixed':
        new_config['n_var'] = 0
        new_config['xl'] = []
        new_config['xu'] = []

        for var_info in config['var'].values():
            if var_info['type'] in ['continuous', 'integer']:
                new_config['n_var'] += 1
                new_config['xl'].append(var_info['lb'])
                new_config['xu'].append(var_info['ub'])
            
            elif var_info['type'] == 'binary':
                new_config['n_var'] += 1
                new_config['xl'].append(0)
                new_config['xu'].append(1)
            
            elif var_info['type'] == 'categorical':
                len_choices = len(var_info['choices'])
                new_config['n_var'] += len_choices
                new_config['xl'].extend([0] * len_choices)
                new_config['xu'].extend([1] * len_choices)

    # obj
    new_config['n_obj'] = config['n_obj']

    # constr
    if 'n_constr' in config and config['n_constr'] is not None:
        new_config['n_constr'] = config['n_constr']
    else:
        new_config['n_constr'] = 0
    
    return new_config


def complete_config(config, check=False):
    '''
    Fill default values of the config
    Keys:
        n_var
        var_name
        obj_name
        obj_type
        obj_func
        ref_point
        n_constr
        constr_func
    '''
    if check:
        check_config(config)

    new_config = config.copy()

    # var
    if 'n_var' not in config:
        new_config['n_var'] = len(config['var'])
        
    if 'var_name' not in config or config['var_name'] is None:
        new_config['var_name'] = [f'x{i}' for i in range(1, new_config['n_var'] + 1)]

    # obj
    if 'obj_name' not in config or config['obj_name'] is None:
        new_config['obj_name'] = [f'f{i}' for i in range(1, config['n_obj'] + 1)]
    
    if 'obj_type' not in config or config['obj_type'] is None:
        new_config['obj_type'] = ['min'] * config['n_obj']

    if 'obj_func' not in config:
        new_config['obj_func'] = None

    if 'ref_point' not in config:
        new_config['ref_point'] = None
    else:
        if config['ref_point'] is not None and None in config['ref_point']:
            new_config['ref_point'] = None

    # constr
    if 'n_constr' not in config or config['n_constr'] is None:
        new_config['n_constr'] = 0

    if 'constr_func' not in config:
        new_config['constr_func'] = None

    return new_config
