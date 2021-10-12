'''
Useful operands.
'''

import numpy as np


def safe_divide(x1, x2):
    '''
    Divide x1 / x2, return 0 where x2 == 0.
    '''
    return np.divide(x1, x2, out=np.zeros(np.broadcast(x1, x2).shape), where=(x2 != 0))


def expand(x, axis=-1):
    '''
    Concise way of expand_dims.
    '''
    return np.expand_dims(x, axis=axis)
