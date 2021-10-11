import os, sys
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

    if path.endswith('so'):
        lib_path = path
    else:
        # decide compiler
        if path.endswith('c'):
            compiler = 'gcc'
        elif path.endswith('cpp'):
            compiler = 'g++'
        else:
            raise NotImplementedError
        # compile
        lib_path = os.path.join(os.path.dirname(path), lib_name + '.so')
        os.system(f'{compiler} -shared -o {lib_path} {path}')
        if not os.path.exists(lib_path):
            raise Exception('Failed to compile the library, make sure you have gcc or g++ installed on your computer')

    c_lib = ctypes.CDLL(lib_path)
    getattr(c_lib, func_name).argtypes = (np.ctypeslib.ndpointer(dtype=c_type, shape=(n_in,)),)
    getattr(c_lib, func_name).restype = np.ctypeslib.ndpointer(dtype=c_type, shape=(n_out,))
    return lambda x: getattr(c_lib, func_name)(np.array(x, dtype=py_type))


class MatlabEngine:

    def __init__(self, path, n_out):
        self.dir_name, self.func_name = os.path.dirname(path), os.path.basename(path)
        assert self.func_name.endswith('.m')
        self.func_name = self.func_name[:-2]
        self.n_out = n_out

    def evaluate(self, x):
        import matlab.engine
        eng = matlab.engine.start_matlab()
        eng.addpath(self.dir_name)
        return getattr(eng, self.func_name)(*x, nargout=self.n_out)


def import_matlab_func(path, n_out):
    '''
    Import matlab function from path
    '''
    return MatlabEngine(path, n_out).evaluate


def import_obj_func(path, n_var, n_obj):
    '''
    '''
    # TODO: deal with custom import in obj func
    ftype = path.split('.')[-1]
    if ftype == 'py':
        try:
            sys.path.insert(0, os.path.dirname(path))
            eval_func = import_python_func(path=path, module_name='obj_func', func_name='evaluate_objective')
        except Exception as e:
            raise Exception(f'failed to import objective evaluation function from python file ({e})')
    elif ftype in ['c', 'cpp', 'so']:
        try:
            eval_func = import_c_func(path=path, lib_name='obj_func', func_name='evaluate_objective',
                n_in=n_var, n_out=n_obj)
        except Exception as e:
            raise Exception(f'failed to import objective evaluation function from c/cpp file ({e})')
    elif ftype == 'm':
        try:
            eval_func = import_matlab_func(path=path, n_out=n_obj)
        except Exception as e:
            raise Exception(f'failed to import objective evaluation function from matlab file ({e})')
    else:
        raise Exception('only python, c/cpp and matlab files are supported')
    return eval_func


def import_constr_func(path, n_var, n_constr):
    '''
    '''
    # TODO: deal with custom import in constr func
    ftype = path.split('.')[-1]
    if ftype == 'py':
        try:
            sys.path.insert(0, os.path.dirname(path))
            eval_func = import_python_func(path=path, module_name='constr_func', func_name='evaluate_constraint')
        except Exception as e:
            raise Exception(f'failed to import constraint evaluation function from python file ({e})')  
    elif ftype in ['c', 'cpp', 'so']:
        try:
            eval_func = import_c_func(path=path, lib_name='constr_func', func_name='evaluate_constraint',
                n_in=n_var, n_out=n_constr)
        except Exception as e:
            raise Exception(f'failed to import constraint evaluation function from c/cpp file ({e})')
    elif ftype == 'm':
        try:
            eval_func = import_matlab_func(path=path, n_out=n_constr)
        except Exception as e:
            raise Exception(f'failed to import objective evaluation function from matlab file ({e})')
    else:
        raise Exception('only python, c/cpp and matlab files are supported')
    return eval_func
