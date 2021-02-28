config_map = {
    'experiment': {
        'n_random_sample': 'Number of random initial samples',
        'init_sample_path': 'Path of provided initial samples',
        'n_worker': 'Number of evaluation workers',
        'batch_size': 'Batch size',
    },
    'problem': {
        'name': 'Problem name',
        'n_var': 'Number of design variables',
        'n_obj': 'Number of objectives',
        'n_constr': 'Number of constraints',
        'obj_func': 'Objective evaluation script',
        'constr_func': 'Constraint evaluation script',
        'obj_type': 'Objective type',
        'var_lb': 'Lower bound',
        'var_ub': 'Upper bound',
        'var_name': 'Names',
        'obj_name': 'Names',
        'ref_point': 'Reference point',
    },
    'algorithm': {
        'name': 'Algorithm name',
        'n_process': 'Number of parallel processes to use',
    },
}

algo_config_map = {
    'surrogate': {
        'name': 'Name',
        'nu': 'Type of Matern kernel',
        'n_spectral_pts': 'Number of points for spectral sampling',
        'mean_sample': 'Use mean sample for Thompson sampling',
        'hidden_sizes': 'Size of hidden layers',
        'activation': 'Activation',
        'lr': 'Learning rate',
        'weight_decay': 'Weight decay',
        'n_epoch': 'Number of training epoch',
    },
    'acquisition': {
        'name': 'Name',
    },
    'solver': {
        'name': 'Name',
        'n_gen': 'Number of generations',
        'pop_size': 'Population size',
        'pop_init_method': 'Population initialization method',
    },
    'selection': {
        'name': 'Name',
    },
}

algo_value_map = {
    'surrogate': {
        'name': {
            'gp': 'Gaussian Process',
            'ts': 'Thompson Sampling',
        },
    },
    'acquisition': {
        'name': {
            'identity': 'Identity',
            'pi': 'Probability of Improvement',
            'ei': 'Expected Improvement',
            'ucb': 'Upper Confidence Bound',
            'lcb': 'Lower Confidence Bound',
        },
    },
    'solver': {
        'name': {
            'nsga2': 'NSGA-II',
            'moead': 'MOEA/D',
            'parego': 'ParEGO Solver',
            'discovery': 'Pareto Discovery',
        },
        'pop_init_method': {
            'random': 'Random',
            'nds': 'Non-Dominated Sort',
            'lhs': 'Latin-Hypercube Sampling',
        },
    },
    'selection': {
        'name': {
            'hvi': 'Hypervolume Improvement',
            'uncertainty': 'Uncertainty',
            'random': 'Random',
            'moead': 'MOEA/D-EGO Selection',
            'dgemo': 'DGEMO Selection',
        },
    },
}

algo_value_inv_map = {}
for cfg_type, val_map in algo_value_map.items():
    algo_value_inv_map[cfg_type] = {}
    for key, value_map in val_map.items():
        algo_value_inv_map[cfg_type][key] = {v: k for k, v in value_map.items()}

worker_map = {
    'id': 'ID',
    'name': 'Name',
    'address': 'IP address',
    'description': 'Description',
}