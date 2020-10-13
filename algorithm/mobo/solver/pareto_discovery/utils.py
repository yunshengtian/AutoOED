import numpy as np
from pymoo.factory import get_performance_indicator


def propose_next_batch(curr_pfront, ref_point, pred_pfront, pred_pset, batch_size, labels):
    '''
    Propose next batch of design variables to evaluate by maximizing hypervolume contribution.
    Greedely add samples with maximum hypervolume from each family.
    Input:
        curr_pfront: current pareto front of evaluated design samples
        pred_pfront: predicted pareto front from sampled objective functions
        pred_pset: predicted pareto set from sampled objective functions
        batch_size: batch size of design samples to be proposed
        labels: family labels for pred_pset
    Output:
        X_next: next batch of design variables to evaluate
        Y_next: expected output of next batch of design variables to evaluate
        family_lbls: family labels of proposed batch samples
    '''
    #assert len(pred_pset) >= batch_size, "predicted pareto set is smaller than proposed batch size!"

    curr_pfront = curr_pfront.copy()
    hv = get_performance_indicator('hv', ref_point=ref_point)
    idx_choices = np.ma.array(np.arange(len(pred_pset)), mask=False) # mask array for index choices
    iter_idx_choices = np.ma.array(np.arange(len(pred_pset)), mask=False) # mask array for index choices of unvisited family samples
    next_batch_indices = []
    family_lbls_next = []
    num_families = len(np.unique(labels))
    print('Number of families is: '+str(num_families))

    if len(pred_pset) < batch_size:
        print('Predicted pareto set is smaller than proposed batch size and has '+ str(len(pred_pset)) +' points.')
        next_batch_indices = [0] * (batch_size - len(pred_pset))
        batch_size = len(pred_pset)

    # greedily select indices that maximize hypervolume contribution
    for _ in range(batch_size):
        #if all families were visited, start new cycle
        if len(iter_idx_choices.compressed())==0:
            iter_idx_choices = idx_choices.copy()
        curr_hv = hv.calc(curr_pfront)
        max_hv_contrib = 0.
        max_hv_idx = -1
        for idx in iter_idx_choices.compressed():
            # calculate hypervolume contribution
            new_hv = hv.calc(np.vstack([curr_pfront, pred_pfront[idx]]))
            hv_contrib = new_hv - curr_hv
            if hv_contrib > max_hv_contrib:
                max_hv_contrib = hv_contrib
                max_hv_idx = idx
        if max_hv_idx == -1: # if all candidates have no hypervolume contribution, just randomly select one
            max_hv_idx = np.random.choice(iter_idx_choices.compressed())

        idx_choices.mask[max_hv_idx] = True # mask as selected
        curr_pfront = np.vstack([curr_pfront, pred_pfront[max_hv_idx]]) # add to current pareto front
        next_batch_indices.append(max_hv_idx)
        family_lbls_next.append(labels[max_hv_idx])
        #find which family to mask all family memebers as visited in this cycle
        family_ids = np.where(labels == labels[max_hv_idx])[0]
        for fid in family_ids:
            iter_idx_choices.mask[fid] = True

    X_next = pred_pset[next_batch_indices].copy()
    Y_next = pred_pfront[next_batch_indices].copy()
    return X_next, Y_next, family_lbls_next


def propose_next_batch_without_label(curr_pfront, ref_point, pred_pfront, pred_pset, batch_size):
    '''
    Propose next batch of design variables to evaluate by maximizing hypervolume contribution
    Input:
        curr_pfront: current pareto front of evaluated design samples
        pred_pfront: predicted pareto front from sampled objective functions
        pred_pset: predicted pareto set from sampled objective functions
        batch_size: batch size of design samples to be proposed
    Output:
        X_next: next batch of design variables to evaluate
    '''
    #assert len(pred_pset) >= batch_size, "predicted pareto set is smaller than proposed batch size!

    curr_pfront = curr_pfront.copy()
    hv = get_performance_indicator('hv', ref_point=ref_point)
    idx_choices = np.ma.array(np.arange(len(pred_pset)), mask=False) # mask array for index choices
    next_batch_indices = []

    if len(pred_pset) < batch_size:
        print('Predicted pareto set is smaller than proposed batch size and has '+ str(len(pred_pset)) +' points.')
        next_batch_indices = [0] * (batch_size - len(pred_pset))
        batch_size = len(pred_pset)

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

    X_next = pred_pset[next_batch_indices].copy()
    Y_next = pred_pfront[next_batch_indices].copy()
    return X_next, Y_next


def generate_weights_batch_dfs(i, n_dim, min_weight, max_weight, delta_weight, weight, weights_batch):
    if i == n_dim - 1:
        weight.append(1.0 - np.sum(weight[0:i]))
        weights_batch.append(weight.copy())
        weight = weight[0:i]
        return
    w = min_weight
    while w < max_weight + 0.5 * delta_weight and np.sum(weight[0:i]) + w < 1.0 + 0.5 * delta_weight:
        weight.append(w)
        generate_weights_batch_dfs(i + 1, n_dim, min_weight, max_weight, delta_weight, weight, weights_batch)
        weight = weight[0:i]
        w += delta_weight


def generate_weights_batch(n_dim, delta_weight):
    '''
    Generate n dimensional uniformly distributed weights using depth first search.
    e.g. generate_weights_batch(2, 0.5) returns [[0.0, 1.0], [0.5, 0.5], [1.0, 0.0]]
    '''
    weights_batch = []
    generate_weights_batch_dfs(0, n_dim, 0.0, 1.0, delta_weight, [], weights_batch)
    return np.array(weights_batch)


def get_sample_num_from_families(n_sample, family_sizes):
    '''
    Choose certain number of samples from all families, as uniformly as possible.
    Input:
        n_sample: total number of samples to be chosen
        family_sizes: array containing size of each family, shape = (n_family,)
    Output:
        sample_nums: number of samples we choose from each samily, shape = (n_family,)
    '''
    assert np.sum(family_sizes) >= n_sample

    family_sizes = np.array(family_sizes, dtype=np.int32)
    valid_idx = np.where(family_sizes > 0)[0]
    valid_family_sizes = family_sizes[valid_idx]
    n_family = len(valid_idx)
    sample_nums = np.zeros_like(family_sizes, dtype=np.int32)

    if n_sample > n_family:
        # distribute n_sample to n_family as uniformly as possible
        curr_n_sample_each_fam = min(n_sample // n_family, np.min(valid_family_sizes))
        remain_n_sample = n_sample - curr_n_sample_each_fam * n_family
        remain_family_sizes = valid_family_sizes - curr_n_sample_each_fam
        sample_nums[valid_idx] += curr_n_sample_each_fam
        sample_nums[valid_idx] += get_sample_num_from_families(remain_n_sample, remain_family_sizes)
    else:
        # randomly choose n_sample families to sample
        random_idx = np.random.choice(np.arange(n_family), n_sample, replace=False)
        sample_nums[valid_idx[random_idx]] = 1

    return sample_nums
