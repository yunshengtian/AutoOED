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


def import_obj_func(path, n_var, n_obj):
    '''
    '''
    ftype = path.split('.')[-1]
    if ftype == 'py':
        try:
            eval_func = import_python_func(path=path, module_name='eval_obj', func_name='evaluate_objective')
        except:
            raise Exception('failed to import objective evaluation function from python file')
    elif ftype == 'c' or ftype == 'cpp':
        try:
            eval_func = import_c_func(path=path, lib_name='eval_obj', func_name='evaluate_objective',
                n_in=n_var, n_out=n_obj)
        except:
            raise Exception('failed to import objective evaluation function from c/cpp file')
    else:
        raise Exception('only python and c/cpp files are supported')
    return eval_func


def import_constr_func(path, n_var, n_constr):
    '''
    '''
    ftype = path.split('.')[-1]
    if ftype == 'py':
        try:
            eval_func = import_python_func(path=path, module_name='eval_constr', func_name='evaluate_constraint')
        except:
            raise Exception('failed to import constraint evaluation function from python file')  
    elif ftype == 'c' or ftype == 'cpp':
        try:
            eval_func = import_c_func(path=path, lib_name='eval_constr', func_name='evaluate_constraint',
                n_in=n_var, n_out=n_constr)
        except:
            raise Exception('failed to import constraint evaluation function from c/cpp file')
    else:
        raise Exception('only python and c/cpp files are supported')
    return eval_func
