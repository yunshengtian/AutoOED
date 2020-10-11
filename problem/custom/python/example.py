import numpy as np
from problem import Problem

'''
Example custom problem definitions (performance and constraint evaluation functions here might not make any sense)

Problem configuration is defined as a 'config' dict, where each key means:
    n_var: number of design variables
    n_obj: number of objectives
    n_constr: number of constraints (except bounds)
    var_lb: lower bounds of design variables
    var_ub: upper bounds of design variables
    obj_lb: lower bounds of objectives
    obj_ub: upper bounds of objectives
    var_name: names of design variables
    obj_name: names of objectives
    init_sample_path: path of provided initial samples

Default values if not specifed in problem config:
    n_constr: 0
    var_lb: 0
    var_ub: 1
    obj_lb: None
    obj_ub: None
    var_name: ['x1', ..., 'x{n_var}']
    obj_name: ['f1', ..., 'f{n_obj}']
    init_sample_path: None
'''

class ExampleProblem1(Problem):
    '''
    Example 1, with specified number of design variables and objectives
    '''
    config = {
        'n_var': 6,
        'n_obj': 2,
    }

    def evaluate_performance(self, x):
        f1 = np.max(x)
        f2 = np.min(x)
        return f1, f2


class ExampleProblem2(Problem):
    '''
    Example 2, with specified number of design variables and objectives, also bounds on design variables
    '''
    config = {
        'n_var': 10,
        'n_obj': 2,
        'var_lb': [0, 0, 0, 1],
        'var_ub': [1, 1, 1, 10],
    }

    def evaluate_performance(self, x):
        f1 = np.sum(x)
        f2 = np.sum(np.abs(x))
        return f1, f2


class ExampleProblem3(Problem):
    '''
    Example 3, with specified number of design variables and objectives, bounds on design variables and constraint functions
    NOTE: for constraint value (g), > 0 means violating constraint, <= 0 means satisfying constraint
    '''
    config = {
        'n_var': 4,
        'n_obj': 3,
        'n_constr': 2,
        'var_lb': 0,
        'var_ub': 1,
    }

    def evaluate_performance(self, x):
        f1 = np.sum(np.sin(x))
        f2 = np.sum(np.cos(x))
        f3 = np.sum(np.tan(x))
        return f1, f2, f3

    def evaluate_constraint(self, x):
        x1, x2, x3, x4 = x[0], x[1], x[2], x[3]
        g1 = x1 + x2 - 1 # x1 + x2 < 1
        g2 = (x2 + x3 - 2) ** 2 - 1e-5 # x2 + x3 = 2
        return g1, g2