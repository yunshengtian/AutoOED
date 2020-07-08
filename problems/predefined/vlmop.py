import numpy as np
from problems import Problem


class VLMOP2(Problem):
    '''
    Van Veldhuizen, David A., and Gary B. Lamont. "Multiobjective evolutionary algorithm test suites." Proceedings of the 1999 ACM symposium on Applied computing. 1999.
    '''
    def __init__(self, n_var=2, **kwargs):
        super().__init__(n_var=n_var, n_obj=2, type_var=np.double)
        self.xl = -2.0 * np.ones(n_var)
        self.xu = 2.0 * np.ones(n_var)

    def evaluate_performance(self, x):
        n = self.n_var
        f1 = 1 - np.exp(-np.sum((x - 1 / np.sqrt(n)) ** 2, axis=1))
        f2 = 1 - np.exp(-np.sum((x + 1 / np.sqrt(n)) ** 2, axis=1))
        return f1, f2

    def _calc_pareto_front(self, n_pareto_points=100):
        n = self.n_var

        x = np.linspace(-1 / np.sqrt(n), 1 / np.sqrt(n), n_pareto_points)
        x_all = np.column_stack([x] * n)

        return self.evaluate(x_all, return_values_of=['F'])


class VLMOP3(Problem):
    '''
    Van Veldhuizen, David A., and Gary B. Lamont. "Multiobjective evolutionary algorithm test suites." Proceedings of the 1999 ACM symposium on Applied computing. 1999.
    '''
    def __init__(self, **kwargs):
        super().__init__(n_var=2, n_obj=3, type_var=np.double)
        self.xl = np.array([-3.0, -3.0])
        self.xu = np.array([3.0, 3.0])

    def evaluate_performance(self, x):
        x1, x2 = x[:, 0], x[:, 1]

        f1 = 0.5 * (x1 ** 2 + x2 ** 2) + np.sin(x1 ** 2 + x2 ** 2)
        f2 = (3 * x1 - 2 * x2 + 4) ** 2 / 8 + (x1 - x2 + 1) ** 2 / 27 + 15
        f3 = 1 / (x1 ** 2 + x2 ** 2 + 1) - 1.1 * np.exp(-x1 ** 2 - x2 ** 2)

        return f1, f2, f3

    def _calc_pareto_front(self):
        raise Exception("Not implemented yet.")