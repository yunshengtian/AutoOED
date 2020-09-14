import os
import importlib
import ctypes
import numpy as np


def import_python_func(path, module_name, func_name):
    '''
    Import python function from path
    '''
    spec = importlib.util.spec_from_file_location(module_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, func_name)


def import_c_func(path, lib_name, func_name, n_in, n_out, dtype='float'):
    '''
    Import c/cpp function from path
    '''
    # decide compiler
    if path.endswith('c'):
        compiler = 'gcc'
    elif path.endswith('cpp'):
        compiler = 'g++'
    else:
        raise NotImplementedError

    # type conversion
    if dtype == 'float':
        c_type = ctypes.c_float
        py_type = np.float32
    elif dtype == 'int':
        c_type = ctypes.c_int
        py_type = np.int
    elif dtype == 'double':
        c_type = ctypes.c_double
        py_type = np.float64
    else:
        raise NotImplementedError

    lib_path = os.path.join(os.path.dirname(path), lib_name + '.so')
    os.system(f'{compiler} -shared -o {lib_path} {path}')
    c_lib = ctypes.CDLL(lib_path)
    getattr(c_lib, func_name).argtypes = (np.ctypeslib.ndpointer(dtype=c_type, shape=(n_in,)),)
    getattr(c_lib, func_name).restype = np.ctypeslib.ndpointer(dtype=c_type, shape=(n_out,))
    return lambda x: getattr(c_lib, func_name)(np.array(x, dtype=py_type))


def process_problem_config(config):
    '''
    Post-process loaded problem config
    '''
    config = config.copy()

    default_config = {
        'name': 'required',
        'n_var': 'required',
        'n_obj': 'required',
        'minimize': True, # minimization by default
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