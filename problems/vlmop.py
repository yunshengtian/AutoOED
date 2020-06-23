import autograd.numpy as anp
from .problem import Problem


class VLMOP2(Problem):
    '''
    Van Veldhuizen, David A., and Gary B. Lamont. "Multiobjective evolutionary algorithm test suites." Proceedings of the 1999 ACM symposium on Applied computing. 1999.
    '''
    def __init__(self, n_var=2):
        super().__init__(n_var=n_var, n_obj=2, type_var=anp.double)
        self.xl = -2.0 * anp.ones(n_var)
        self.xu = 2.0 * anp.ones(n_var)

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            n = self.n_var

            f1 = 1 - anp.exp(-anp.sum((x - 1 / anp.sqrt(n)) ** 2, axis=1))
            f2 = 1 - anp.exp(-anp.sum((x + 1 / anp.sqrt(n)) ** 2, axis=1))

            out['F'] = anp.column_stack([f1, f2])

    def _calc_pareto_front(self, n_pareto_points=100):
        n = self.n_var

        x = anp.linspace(-1 / anp.sqrt(n), 1 / anp.sqrt(n), n_pareto_points)
        x_all = anp.column_stack([x] * n)

        return self.evaluate(x_all, return_values_of=['F'])


class VLMOP3(Problem):
    '''
    Van Veldhuizen, David A., and Gary B. Lamont. "Multiobjective evolutionary algorithm test suites." Proceedings of the 1999 ACM symposium on Applied computing. 1999.
    '''
    def __init__(self):
        super().__init__(n_var=2, n_obj=3, type_var=anp.double)
        self.xl = anp.array([-3.0, -3.0])
        self.xu = anp.array([3.0, 3.0])

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            x1, x2 = x[:, 0], x[:, 1]

            f1 = 0.5 * (x1 ** 2 + x2 ** 2) + anp.sin(x1 ** 2 + x2 ** 2)
            f2 = (3 * x1 - 2 * x2 + 4) ** 2 / 8 + (x1 - x2 + 1) ** 2 / 27 + 15
            f3 = 1 / (x1 ** 2 + x2 ** 2 + 1) - 1.1 * anp.exp(-x1 ** 2 - x2 ** 2)

            out['F'] = anp.column_stack([f1, f2, f3])

    def _calc_pareto_front(self):
        raise Exception("Not implemented yet.")