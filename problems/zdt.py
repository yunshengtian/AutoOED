import autograd.numpy as anp

from .problem import Problem
from pymoo.util.normalization import normalize


class ZDT(Problem):

    def __init__(self, n_var=30, **kwargs):
        super().__init__(n_var=n_var, n_obj=2, n_constr=0, xl=0, xu=1, type_var=anp.double, **kwargs)


class ZDT1(ZDT):

    def _calc_pareto_front(self, n_pareto_points=100):
        x = anp.linspace(0, 1, n_pareto_points)
        return anp.array([x, 1 - anp.sqrt(x)]).T

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            f1 = x[:, 0]
            g = 1 + 9.0 / (self.n_var - 1) * anp.sum(x[:, 1:], axis=1)
            f2 = g * (1 - anp.power((f1 / g), 0.5))

            out["F"] = anp.column_stack([f1, f2])


class ZDT2(ZDT):

    def _calc_pareto_front(self, n_pareto_points=100):
        x = anp.linspace(0, 1, n_pareto_points)
        return anp.array([x, 1 - anp.power(x, 2)]).T

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            f1 = x[:, 0]
            c = anp.sum(x[:, 1:], axis=1)
            g = 1.0 + 9.0 * c / (self.n_var - 1)
            f2 = g * (1 - anp.power((f1 * 1.0 / g), 2))

            out["F"] = anp.column_stack([f1, f2])


class ZDT3(ZDT):

    def _calc_pareto_front(self, n_points=100, flatten=True):
        regions = [[0, 0.0830015349],
                   [0.182228780, 0.2577623634],
                   [0.4093136748, 0.4538821041],
                   [0.6183967944, 0.6525117038],
                   [0.8233317983, 0.8518328654]]

        pf = []

        for r in regions:
            x1 = anp.linspace(r[0], r[1], int(n_points / len(regions)))
            x2 = 1 - anp.sqrt(x1) - x1 * anp.sin(10 * anp.pi * x1)
            pf.append(anp.array([x1, x2]).T)

        if not flatten:
            pf = anp.concatenate([pf[None,...] for pf in pf])
        else:
            pf = anp.row_stack(pf)

        return pf

    def _evaluate(self, x, out, *args, requires_F=True, **kwargs):
        if requires_F:
            f1 = x[:, 0]
            c = anp.sum(x[:, 1:], axis=1)
            g = 1.0 + 9.0 * c / (self.n_var - 1)
            f2 = g * (1 - anp.power(f1 * 1.0 / g, 0.5) - (f1 * 1.0 / g) * anp.sin(10 * anp.pi * f1))

            out["F"] = anp.column_stack([f1, f2])

