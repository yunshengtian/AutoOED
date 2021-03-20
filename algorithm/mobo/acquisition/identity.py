from .base import Acquisition


class IdentityFunc(Acquisition):
    '''
    Identity function.

    Attributes
    ----------
    requires_std: bool, default=False
        Whether requires std output from surrogate model.
    '''
    def evaluate(self, val, calc_gradient=False, calc_hessian=False):
        F, dF, hF = val['F'], val['dF'], val['hF']
        return F, dF, hF
