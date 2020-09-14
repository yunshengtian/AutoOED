import numpy as np

from problems import Problem
from pymoo.util.normalization import normalize


class ZDT(Problem):

    config = {
        'n_var': 6,
        'n_obj': 2,
    }


class ZDT1(ZDT):

    def _calc_pareto_front(self, n_pareto_points=100):
        x = np.linspace(0, 1, n_pareto_points)
        return np.array([x, 1 - np.sqrt(x)]).T

    def evaluate_performance(self, x):
        f1 = x[0]
        g = 1 + 9.0 / (self.n_var - 1) * np.sum(x[1:])
        f2 = g * (1 - np.power((f1 / g), 0.5))
        return f1, f2

class ZDT2(ZDT):

    def _calc_pareto_front(self, n_pareto_points=100):
        x = np.linspace(0, 1, n_pareto_points)
        return np.array([x, 1 - np.power(x, 2)]).T

    def evaluate_performance(self, x):
        f1 = x[0]
        c = np.sum(x[1:])
        g = 1.0 + 9.0 * c / (self.n_var - 1)
        f2 = g * (1 - np.power((f1 * 1.0 / g), 2))
        return f1, f2


class ZDT3(ZDT):

    def _calc_pareto_front(self, n_points=100, flatten=True):
        regions = [[0, 0.0830015349],
                   [0.182228780, 0.2577623634],
                   [0.4093136748, 0.4538821041],
                   [0.6183967944, 0.6525117038],
                   [0.8233317983, 0.8518328654]]

        pf = []

        for r in regions:
            x1 = np.linspace(r[0], r[1], int(n_points / len(regions)))
            x2 = 1 - np.sqrt(x1) - x1 * np.sin(10 * np.pi * x1)
            pf.append(np.array([x1, x2]).T)

        if not flatten:
            pf = np.concatenate([pf[None,...] for pf in pf])
        else:
            pf = np.row_stack(pf)

        return pf

    def evaluate_performance(self, x):
        f1 = x[0]
        c = np.sum(x[1:])
        g = 1.0 + 9.0 * c / (self.n_var - 1)
        f2 = g * (1 - np.power(f1 * 1.0 / g, 0.5) - (f1 * 1.0 / g) * np.sin(10 * np.pi * f1))
        return f1, f2

