import numpy as np

from problems import Problem
from pymoo.factory import get_reference_directions
from pymoo.problems.util import load_pareto_front_from_file


class DTLZ(Problem):
    def __init__(self, n_var, n_obj, var_lb=None, var_ub=None, k=None):

        if n_var:
            self.k = n_var - n_obj + 1
        elif k:
            self.k = k
            n_var = k + n_obj - 1
        else:
            raise Exception("Either provide number of variables or k!")

        super().__init__(n_var=n_var, n_obj=n_obj, n_constr=0, var_lb=var_lb, var_ub=var_ub, type_var=np.double)

    def g1(self, x_m):
        return 100 * (self.k + np.sum(np.square(x_m - 0.5) - np.cos(20 * np.pi * (x_m - 0.5))))

    def g2(self, x_m):
        return np.sum(np.square(x_m - 0.5))

    def obj_func(self, x_, g, alpha=1):
        f = []

        for i in range(0, self.n_obj):
            _f = (1 + g)
            _f *= np.prod(np.cos(np.power(x_[:x_.shape[0] - i], alpha) * np.pi / 2.0))
            if i > 0:
                _f *= np.sin(np.power(x_[x_.shape[0] - i], alpha) * np.pi / 2.0)

            f.append(_f)

        f = np.column_stack(f)
        return f


def generic_sphere(ref_dirs):
    return ref_dirs / np.tile(np.linalg.norm(ref_dirs, axis=1)[:, None], (1, ref_dirs.shape[1]))


class DTLZ1(DTLZ):
    def __init__(self, n_var=7, n_obj=3, var_lb=None, var_ub=None, **kwargs):
        super().__init__(n_var, n_obj, var_lb, var_ub)

    def _calc_pareto_front(self):
        ref_kwargs = dict(n_points=100) if self.n_obj == 2 else dict(n_partitions=15)
        ref_dirs = get_reference_directions('das-dennis', n_dim=self.n_obj, **ref_kwargs)
        return 0.5 * ref_dirs

    def evaluate_performance(self, x):
        x_, x_m = x[:self.n_obj - 1], x[self.n_obj - 1:]
        g = self.g1(x_m)

        f = []
        for i in range(0, self.n_obj):
            _f = 0.5 * (1 + g)
            _f *= np.prod(x_[:x_.shape[0] - i])
            if i > 0:
                _f *= 1 - x_[x_.shape[0] - i]
            f.append(_f)
        return f


class DTLZ2(DTLZ):
    def __init__(self, n_var=10, n_obj=3, var_lb=None, var_ub=None, **kwargs):
        super().__init__(n_var, n_obj, var_lb, var_ub)

    def _calc_pareto_front(self):
        ref_kwargs = dict(n_points=100) if self.n_obj == 2 else dict(n_partitions=15)
        ref_dirs = get_reference_directions('das-dennis', n_dim=self.n_obj, **ref_kwargs)
        return generic_sphere(ref_dirs)

    def evaluate_performance(self, x):
        x_, x_m = x[:self.n_obj - 1], x[self.n_obj - 1:]
        g = self.g2(x_m)
        return self.obj_func(x_, g, alpha=1)


class DTLZ3(DTLZ):
    def __init__(self, n_var=10, n_obj=3, var_lb=None, var_ub=None, **kwargs):
        super().__init__(n_var, n_obj, var_lb, var_ub)

    def _calc_pareto_front(self):
        ref_kwargs = dict(n_points=100) if self.n_obj == 2 else dict(n_partitions=15)
        ref_dirs = get_reference_directions('das-dennis', n_dim=self.n_obj, **ref_kwargs)
        return generic_sphere(ref_dirs)

    def evaluate_performance(self, x):
        x_, x_m = x[:self.n_obj - 1], x[self.n_obj - 1:]
        g = self.g1(x_m)
        return self.obj_func(x_, g, alpha=1)


class DTLZ4(DTLZ):
    def __init__(self, n_var=10, n_obj=3, var_lb=None, var_ub=None, alpha=100, d=100, **kwargs):
        super().__init__(n_var, n_obj, var_lb, var_ub)
        self.alpha = alpha
        self.d = d

    def _calc_pareto_front(self):
        ref_kwargs = dict(n_points=100) if self.n_obj == 2 else dict(n_partitions=15)
        ref_dirs = get_reference_directions('das-dennis', n_dim=self.n_obj, **ref_kwargs)
        return generic_sphere(ref_dirs)

    def evaluate_performance(self, x):
        x_, x_m = x[:self.n_obj - 1], x[self.n_obj - 1:]
        g = self.g2(x_m)
        return self.obj_func(x_, g, alpha=self.alpha)


class DTLZ5(DTLZ):
    def __init__(self, n_var=10, n_obj=3, var_lb=None, var_ub=None, **kwargs):
        super().__init__(n_var, n_obj, var_lb, var_ub)

    def _calc_pareto_front(self):
        if self.n_obj == 3:
            return load_pareto_front_from_file("dtlz5-3d.pf")
        else:
            raise Exception("Not implemented yet.")

    def evaluate_performance(self, x):
        x_, x_m = x[:self.n_obj - 1], x[self.n_obj - 1:]
        g = self.g2(x_m)

        theta = 1 / (2 * (1 + g)) * (1 + 2 * g * x_)
        theta = np.concatenate([x[0], theta[1:]])

        return self.obj_func(theta, g)


class DTLZ6(DTLZ):
    def __init__(self, n_var=10, n_obj=3, var_lb=None, var_ub=None, **kwargs):
        super().__init__(n_var, n_obj, var_lb, var_ub)

    def _calc_pareto_front(self):
        if self.n_obj == 3:
            return load_pareto_front_from_file("dtlz6-3d.pf")
        else:
            raise Exception("Not implemented yet.")

    def evaluate_performance(self, x):
        x_, x_m = x[:self.n_obj - 1], x[self.n_obj - 1:]
        g = np.sum(np.power(x_m, 0.1))

        theta = 1 / (2 * (1 + g)) * (1 + 2 * g * x_)
        theta = np.concatenate([x[0], theta[1:]])

        return self.obj_func(theta, g)

