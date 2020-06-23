import autograd.numpy as anp

from .problem import Problem
from pymoo.problems.util import load_pareto_front_from_file


class DTLZ(Problem):
    def __init__(self, n_var, n_obj, k=None):

        if n_var:
            self.k = n_var - n_obj + 1
        elif k:
            self.k = k
            n_var = k + n_obj - 1
        else:
            raise Exception("Either provide number of variables or k!")

        super().__init__(n_var=n_var, n_obj=n_obj, n_constr=0, xl=0, xu=1, type_var=anp.double)

    def g1(self, X_M):
        return 100 * (self.k + anp.sum(anp.square(X_M - 0.5) - anp.cos(20 * anp.pi * (X_M - 0.5)), axis=1))

    def g2(self, X_M):
        return anp.sum(anp.square(X_M - 0.5), axis=1)

    def obj_func(self, X_, g, alpha=1):
        f = []

        for i in range(0, self.n_obj):
            _f = (1 + g)
            _f *= anp.prod(anp.cos(anp.power(X_[:, :X_.shape[1] - i], alpha) * anp.pi / 2.0), axis=1)
            if i > 0:
                _f *= anp.sin(anp.power(X_[:, X_.shape[1] - i], alpha) * anp.pi / 2.0)

            f.append(_f)

        f = anp.column_stack(f)
        return f


def generic_sphere(ref_dirs):
    return ref_dirs / anp.tile(anp.linalg.norm(ref_dirs, axis=1)[:, None], (1, ref_dirs.shape[1]))


class DTLZ1(DTLZ):
    def __init__(self, n_var=7, n_obj=3, **kwargs):
        super().__init__(n_var, n_obj, **kwargs)

    def _calc_pareto_front(self, ref_dirs=None):
        return 0.5 * ref_dirs

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            X_, X_M = x[:, :self.n_obj - 1], x[:, self.n_obj - 1:]
            g = self.g1(X_M)

            f = []
            for i in range(0, self.n_obj):
                _f = 0.5 * (1 + g)
                _f *= anp.prod(X_[:, :X_.shape[1] - i], axis=1)
                if i > 0:
                    _f *= 1 - X_[:, X_.shape[1] - i]
                f.append(_f)

            out["F"] = anp.column_stack(f)


class DTLZ2(DTLZ):
    def __init__(self, n_var=10, n_obj=3, **kwargs):
        super().__init__(n_var, n_obj, **kwargs)

    def _calc_pareto_front(self, ref_dirs):
        return generic_sphere(ref_dirs)

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            X_, X_M = x[:, :self.n_obj - 1], x[:, self.n_obj - 1:]
            g = self.g2(X_M)
            out["F"] = self.obj_func(X_, g, alpha=1)


class DTLZ3(DTLZ):
    def __init__(self, n_var=10, n_obj=3, **kwargs):
        super().__init__(n_var, n_obj, **kwargs)

    def _calc_pareto_front(self, ref_dirs):
        return generic_sphere(ref_dirs)

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            X_, X_M = x[:, :self.n_obj - 1], x[:, self.n_obj - 1:]
            g = self.g1(X_M)
            out["F"] = self.obj_func(X_, g, alpha=1)


class DTLZ4(DTLZ):
    def __init__(self, n_var=10, n_obj=3, alpha=100, d=100, **kwargs):
        super().__init__(n_var, n_obj, **kwargs)
        self.alpha = alpha
        self.d = d

    def _calc_pareto_front(self, ref_dirs):
        return generic_sphere(ref_dirs)

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            X_, X_M = x[:, :self.n_obj - 1], x[:, self.n_obj - 1:]
            g = self.g2(X_M)
            out["F"] = self.obj_func(X_, g, alpha=self.alpha)


class DTLZ5(DTLZ):
    def __init__(self, n_var=10, n_obj=3, **kwargs):
        super().__init__(n_var, n_obj, **kwargs)

    def _calc_pareto_front(self):
        if self.n_obj == 3:
            return load_pareto_front_from_file("dtlz5-3d.pf")
        else:
            raise Exception("Not implemented yet.")

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            X_, X_M = x[:, :self.n_obj - 1], x[:, self.n_obj - 1:]
            g = self.g2(X_M)

            theta = 1 / (2 * (1 + g[:, None])) * (1 + 2 * g[:, None] * X_)
            theta = anp.column_stack([x[:, 0], theta[:, 1:]])

            out["F"] = self.obj_func(theta, g)


class DTLZ6(DTLZ):
    def __init__(self, n_var=10, n_obj=3, **kwargs):
        super().__init__(n_var, n_obj, **kwargs)

    def _calc_pareto_front(self):
        if self.n_obj == 3:
            return load_pareto_front_from_file("dtlz6-3d.pf")
        else:
            raise Exception("Not implemented yet.")

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            X_, X_M = x[:, :self.n_obj - 1], x[:, self.n_obj - 1:]
            g = anp.sum(anp.power(X_M, 0.1), axis=1)

            theta = 1 / (2 * (1 + g[:, None])) * (1 + 2 * g[:, None] * X_)
            theta = anp.column_stack([x[:, 0], theta[:, 1:]])

            out["F"] = self.obj_func(theta, g)

