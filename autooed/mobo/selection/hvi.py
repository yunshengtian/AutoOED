'''
Hypervolume improvement selection.
'''

import numpy as np
from pymoo.factory import get_performance_indicator

from autooed.utils.pareto import find_pareto_front
from autooed.mobo.selection.base import Selection


class HypervolumeImprovement(Selection):
    '''
    Selection based on Hypervolume improvement.
    '''
    def _select(self, X_candidate, Y_candidate, X, Y, batch_size):

        pred_pset, pred_pfront = X_candidate, Y_candidate
        curr_pfront = find_pareto_front(Y)
        ref_point = np.max(np.vstack([Y_candidate, Y]), axis=0)

        hv = get_performance_indicator('hv', ref_point=ref_point)
        idx_choices = np.ma.array(np.arange(len(pred_pset)), mask=False) # mask array for index choices
        next_batch_indices = []

        # greedily select indices that maximize hypervolume contribution
        for _ in range(batch_size):
            curr_hv = hv.calc(curr_pfront)
            max_hv_contrib = 0.
            max_hv_idx = -1
            for idx in idx_choices.compressed():
                # calculate hypervolume contribution
                new_hv = hv.calc(np.vstack([curr_pfront, pred_pfront[idx]]))
                hv_contrib = new_hv - curr_hv
                if hv_contrib > max_hv_contrib:
                    max_hv_contrib = hv_contrib
                    max_hv_idx = idx
            if max_hv_idx == -1: # if all candidates have no hypervolume contribution, just randomly select one
                max_hv_idx = np.random.choice(idx_choices.compressed())

            idx_choices.mask[max_hv_idx] = True # mask as selected
            curr_pfront = np.vstack([curr_pfront, pred_pfront[max_hv_idx]]) # add to current pareto front
            next_batch_indices.append(max_hv_idx)
        next_batch_indices = np.array(next_batch_indices)

        X_next = pred_pset[next_batch_indices]
        return X_next
