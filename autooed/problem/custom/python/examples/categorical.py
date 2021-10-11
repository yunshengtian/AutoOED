import numpy as np
from problem import Problem


class CategoricalProblem1(Problem):
    '''
    Example 1, with specified choices for all design variables and number of objectives
    '''
    config = {
        'type': 'categorical',
        'n_var': 3,
        'var_choices': ['big', 'medium', 'small'],
        'n_obj': 2,
    }

    def evaluate_objective(self, x):
        size1, size2, size3 = x[0], x[1], x[2]
        score_map = {'big': 5, 'medium': 3, 'small': 1}
        f1 = score_map[size1] + score_map[size2] + score_map[size3]
        f2 = score_map[size1] - 2 * score_map[size2] - 3 * score_map[size3]
        return f1, f2


class CategoricalProblem2(Problem):
    '''
    Example 2, with specified choices for each design variable and number of objectives
    '''
    config = {
        'type': 'categorical',
        'var': {
            'color': ['red', 'green', 'blue'],
            'size': ['big', 'medium', 'small'],
        },
        'n_obj': 2,
    }

    def evaluate_objective(self, x):
        color, size = x[0], x[1]
        if color == 'red':
            f1 = 1
        elif color == 'green':
            f1 = 2
        else:
            f1 = 0
        if size == 'big':
            f2 = -1
        else:
            f2 = 1
        return f1, f2


class CategoricalProblem3(Problem):
    '''
    Example 3, with specified choices for each design variable and number of objectives and constraints
    NOTE: for constraint value (g), > 0 means violating constraint, <= 0 means satisfying constraint
    '''
    config = {
        'type': 'categorical',
        'var': {
            'x1': [1, 3, 6, 8, 12],
            'x2': [0, 0.2, 0.4, 0.6, 0.8],
            'x3': [True, False],
        },
        'n_obj': 2,
        'n_constr': 1,
    }

    def evaluate_objective(self, x):
        x1, x2, x3 = x[0], x[1], x[2]
        f1 = x1 ** 3 + x2 ** 2 + 1
        if x3 == True:
            f2 = x1 + x2
        else:
            f2 = x1 - x2
        return f1, f2

    def evaluate_constraint(self, x):
        x1, x2, x3 = x[0], x[1], x[2]
        g = (x1 - 10 * x2) # x1 - 10 * x2 < 0
        return g