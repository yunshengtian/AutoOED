import importlib


def import_module_from_path(name, path):
    '''
    Import module from path
    '''
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def process_problem_config(config):
    '''
    Post-process loaded problem config
    '''
    config = config.copy()

    default_config = {
        'name': 'required',
        'n_var': 'required',
        'n_obj': 'required',
        'n_constr': 0, # no constraints by default
        'var_lb': 0, # 0 as var lower bound by default
        'var_ub': 1, # 1 as var upper bound by default
        'obj_lb': None, # no obj lower bound by default
        'obj_ub': None, # no obj upper bound by default
        'init_sample_path': None, # no provided initial sample path by default
    }

    # fill config with default_config when there are key missings
    for key, value in default_config.items():
        if key not in config:
            if value == 'required':
                raise Exception('Invalid config for custom problem, required values are not provided')
            config[key] = value

    if 'var_name' not in config: config['var_name'] = [f'x{i + 1}' for i in range(config['n_var'])]
    if 'obj_name' not in config: config['obj_name'] = [f'f{i + 1}' for i in range(config['n_obj'])]

    return config