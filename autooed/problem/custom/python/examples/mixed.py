import numpy as np
from problem import Problem


class MixedProblem1(Problem):
    '''
    Example 1, with specified choices for each design variable and number of objectives
    '''
    config = {
        'type': 'mixed',
        'var': {
            'x1': {
                'type': 'continuous',
                'lb': 0.4,
                'ub': 1.2,
            },
            'x2': {
                'type': 'binary',
            },
            'x3': {
                'type': 'categorical',
                'choices': ['warm', 'hot', 'cold', 'cool'],
            },
        },
        'n_obj': 2,
        'n_constr': 1,
    }

    def evaluate_objective(self, x):
        x1, x2, x3 = x['x1'], x['x2'], x['x3']
        f1 = x1 ** 3 + x2 ** 2 + 1
        if x3 == 'cold':
            f2 = x1 + x2
        else:
            f2 = x1 - x2
        return f1, f2

    def evaluate_constraint(self, x):
        x1, x2, x3 = x['x1'], x['x2'], x['x3']
        g = (x1 - x2) # x1 - x2 < 0
        return g