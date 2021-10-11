import autograd.numpy as anp
from pymoo.model.decomposition import Decomposition


def augmented_tchebicheff(F, weights):
    rho = 0.05
    return (F * weights).max(axis=1) + rho * (F * weights).sum(axis=1)


class AugmentedTchebicheff(Decomposition):

    def _do(self, F, weights, **kwargs):
        return augmented_tchebicheff(F, weights)
