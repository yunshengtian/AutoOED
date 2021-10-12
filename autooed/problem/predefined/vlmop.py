'''
VLMOP problem suite.
'''

import numpy as np

from autooed.problem.problem import Problem


class VLMOP2(Problem):
    '''
    Van Veldhuizen, David A., and Gary B. Lamont. "Multiobjective evolutionary algorithm test suites." Proceedings of the 1999 ACM symposium on Applied computing. 1999.
    '''
    config = {
        'type': 'continuous',
        'n_var': 2,
        'n_obj': 2,
        'var_lb': -2,
        'var_ub': 2,
    }

    def evaluate_objective(self, x):
        n = self.n_var
        f1 = 1 - np.exp(-np.sum((x - 1 / np.sqrt(n)) ** 2))
        f2 = 1 - np.exp(-np.sum((x + 1 / np.sqrt(n)) ** 2))
        return f1, f2

    def _calc_pareto_front(self, n_pareto_points=100):
        n = self.n_var

        x = np.linspace(-1 / np.sqrt(n), 1 / np.sqrt(n), n_pareto_points)
        x_all = np.column_stack([x] * n)

        return np.array([self.evaluate_objective(x_) for x_ in x_all])


class VLMOP3(Problem):
    '''
    Van Veldhuizen, David A., and Gary B. Lamont. "Multiobjective evolutionary algorithm test suites." Proceedings of the 1999 ACM symposium on Applied computing. 1999.
    '''
    config = {
        'type': 'continuous',
        'n_var': 2,
        'n_obj': 3,
        'var_lb': -3,
        'var_ub': 3,
    }

    def evaluate_objective(self, x):
        x1, x2 = x[0], x[1]

        f1 = 0.5 * (x1 ** 2 + x2 ** 2) + np.sin(x1 ** 2 + x2 ** 2)
        f2 = (3 * x1 - 2 * x2 + 4) ** 2 / 8 + (x1 - x2 + 1) ** 2 / 27 + 15
        f3 = 1 / (x1 ** 2 + x2 ** 2 + 1) - 1.1 * np.exp(-x1 ** 2 - x2 ** 2)

        return f1, f2, f3

    def _calc_pareto_front(self):
        raise Exception("Not implemented yet.")
