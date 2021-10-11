import random
import numpy as np


def set_seed(seed):
    '''
    Set random seed.
    '''
    random.seed(seed)
    np.random.seed(seed)
