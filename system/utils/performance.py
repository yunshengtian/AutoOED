import numpy as np
from pymoo.performance_indicator.hv import Hypervolume


def check_pareto(Y, minimize):
    '''
    Check pareto optimality of the input performance data
    '''
    # convert maximization to minimization
    Y = Y.copy()
    if type(minimize) not in [list, np.ndarray]:
        minimize = np.array([minimize] * Y.shape[1], dtype=bool)
    maxm_idx = np.array(minimize) == False
    Y[:, maxm_idx] = -Y[:, maxm_idx]

    # find pareto indices
    sorted_indices = np.argsort(Y.T[0])
    is_pareto = np.zeros(len(Y), dtype=bool)
    for idx in sorted_indices:
        # check domination relationship
        if not (np.logical_and((Y <= Y[idx]).all(axis=1), (Y < Y[idx]).any(axis=1))).any():
            is_pareto[idx] = True
    return is_pareto


def calc_hypervolume(Y, ref_point, minimize):
    '''
    Calculate hypervolume
    '''
    # convert maximization to minimization
    Y, ref_point = np.array(Y), np.array(ref_point)
    if type(minimize) not in [list, np.ndarray]:
        minimize = np.array([minimize] * Y.shape[1], dtype=bool)
    maxm_idx = np.array(minimize) == False
    Y[:, maxm_idx] = -Y[:, maxm_idx]
    ref_point[maxm_idx] = -ref_point[maxm_idx]

    # calculate
    return Hypervolume(ref_point=ref_point).calc(Y)


def calc_pred_error(Y, Y_expected):
    '''
    Calculate average prediction error
    '''
    pred_error = np.sum(np.linalg.norm(Y - Y_expected, axis=1)) / len(Y)
    return pred_error


def find_closest_point(y, Y, return_index=False):
    '''
    Find the closest point to y in array Y
    '''
    idx = np.argmin(np.linalg.norm(np.array(y) - Y, axis=1))
    if return_index:
        return Y[idx], idx
    else:
        return Y[idx]