import autograd.numpy as anp
from .problem import Problem


class OKA1(Problem):
    '''
    Okabe, Tatsuya, et al. "On test functions for evolutionary multi-objective optimization." International Conference on Parallel Problem Solving from Nature. Springer, Berlin, Heidelberg, 2004.
    '''
    def __init__(self):
        super().__init__(n_var=2, n_obj=2, type_var=anp.double)
        sin, cos = anp.sin(anp.pi / 12), anp.cos(anp.pi / 12)
        self.xl = anp.array([6 * sin, -2 * anp.pi * sin])
        self.xu = anp.array([6 * sin + 2 * anp.pi * cos, 6 * cos])
    
    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            sin, cos = anp.sin(anp.pi / 12), anp.cos(anp.pi / 12)
            x1, x2 = x[:, 0], x[:, 1]
            x1_ = cos * x1 - sin * x2
            x2_ = sin * x1 + cos * x2

            f1 = x1_
            f2 = anp.sqrt(2 * anp.pi) - anp.sqrt(anp.abs(x1_)) + 2 * anp.abs(x2_ - 3 * anp.cos(x1_) - 3) ** (1. / 3)

            out['F'] = anp.column_stack([f1, f2])

    def _calc_pareto_front(self, n_pareto_points=100):
        x1_ = anp.linspace(0, 2 * anp.pi, n_pareto_points)
        x2_ = 3 * anp.cos(x1_) + 3

        f1 = x1_
        f2 = anp.sqrt(2 * anp.pi) - anp.sqrt(anp.abs(x1_)) + 2 * anp.abs(x2_ - 3 * anp.cos(x1_) - 3) ** (1. / 3)

        return anp.column_stack([f1, f2])


class OKA2(Problem):
    '''
    Okabe, Tatsuya, et al. "On test functions for evolutionary multi-objective optimization." International Conference on Parallel Problem Solving from Nature. Springer, Berlin, Heidelberg, 2004.
    '''
    def __init__(self):
        super().__init__(n_var=3, n_obj=2, type_var=anp.double)
        self.xl = anp.array([-anp.pi, -5.0, -5.0])
        self.xu = anp.array([anp.pi, 5.0, 5.0])
    
    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            x1, x2, x3 = x[:, 0], x[:, 1], x[:, 2]

            f1 = x1
            f2 = 1 - (x1 + anp.pi) ** 2 / (4 * anp.pi ** 2) + \
                anp.abs(x2 - 5 * anp.cos(x1)) ** (1. / 3) + anp.abs(x3 - 5 * anp.sin(x1)) ** (1. / 3)

            out['F'] = anp.column_stack([f1, f2])

    def _calc_pareto_front(self, n_pareto_points=100):
        f1 = anp.linspace(-anp.pi, anp.pi, n_pareto_points)
        f2 = 1 - (f1 + anp.pi) ** 2 / (4 * anp.pi ** 2)
        return anp.column_stack([f1, f2])
