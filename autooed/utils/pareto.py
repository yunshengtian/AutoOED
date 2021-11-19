'''
Pareto-related tools.
'''

import numpy as np
from collections.abc import Iterable
from pymoo.performance_indicator.hv import Hypervolume


def convert_minimization(Y, obj_type=None):
    '''
    Convert maximization to minimization.
    '''
    if obj_type is None: return Y

    if isinstance(obj_type, str):
        obj_type = [obj_type] * Y.shape[1]
    assert isinstance(obj_type, Iterable), f'Objective type {type(obj_type)} is not supported'

    maxm_idx = np.array(obj_type) == 'max'
    Y = Y.copy()
    Y[:, maxm_idx] = -Y[:, maxm_idx]

    return Y


def find_pareto_front(Y, return_index=False, obj_type=None):
    '''
    Find pareto front (undominated part) of the input performance data.
    '''
    if len(Y) == 0: return np.array([])

    Y = convert_minimization(Y, obj_type)

    sorted_indices = np.argsort(Y.T[0])
    pareto_indices = []
    for idx in sorted_indices:
        # check domination relationship
        if not (np.logical_and((Y <= Y[idx]).all(axis=1), (Y < Y[idx]).any(axis=1))).any():
            pareto_indices.append(idx)
    pareto_front = Y[pareto_indices].copy()

    if return_index:
        return pareto_front, pareto_indices
    else:
        return pareto_front


def check_pareto(Y, obj_type=None):
    '''
    Check pareto optimality of the input performance data
    '''
    Y = convert_minimization(Y, obj_type)

    # find pareto indices
    sorted_indices = np.argsort(Y.T[0])
    pareto = np.zeros(len(Y), dtype=bool)
    for idx in sorted_indices:
        # check domination relationship
        if not (np.logical_and((Y <= Y[idx]).all(axis=1), (Y < Y[idx]).any(axis=1))).any():
            pareto[idx] = True
    return pareto


def calc_hypervolume(Y, ref_point, obj_type=None):
    '''
    Calculate hypervolume
    '''
    Y = convert_minimization(Y, obj_type)

    return Hypervolume(ref_point=ref_point).calc(Y)


def calc_pred_error(Y, Y_pred_mean, average=False):
    '''
    Calculate prediction error
    '''
    assert len(Y.shape) == len(Y_pred_mean.shape) == 2
    pred_error = np.abs(Y - Y_pred_mean)
    if average:
        pred_error = np.sum(pred_error, axis=0) / len(Y)
    return pred_error
