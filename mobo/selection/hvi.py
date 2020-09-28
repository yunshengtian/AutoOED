import numpy as np
from pymoo.factory import get_performance_indicator
from .base import Selection


class HVI(Selection):
    '''
    Hypervolume Improvement
    '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def select(self, solution, surrogate_model, transformation, curr_pset, curr_pfront):

        pred_pset = solution['x']
        val = surrogate_model.evaluate(pred_pset)
        pred_pfront = val['F']
        pred_pset, pred_pfront = transformation.undo(pred_pset, pred_pfront)

        curr_pfront = curr_pfront.copy()
        hv = get_performance_indicator('hv', ref_point=self.ref_point)
        idx_choices = np.ma.array(np.arange(len(pred_pset)), mask=False) # mask array for index choices
        next_batch_indices = []

        # greedily select indices that maximize hypervolume contribution
        for _ in range(self.batch_size):
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

        return pred_pset[next_batch_indices], None