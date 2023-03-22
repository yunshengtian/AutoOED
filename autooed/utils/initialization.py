'''
Tools for generating initial samples.
'''

import numpy as np

from autooed.utils.sampling import lhs


def generate_random_initial_samples(problem, n_sample):
    '''
    Generate feasible random initial samples
    Input:
        problem: the optimization problem
        n_sample: number of random initial samples
    Output:
        X: initial samples (design parameters)
    '''
    X_feasible = np.zeros((0, problem.n_var))

    max_iter = 1000
    iter_count = 0

    while len(X_feasible) < n_sample and iter_count < max_iter:
        X = lhs(problem.n_var, n_sample) # TODO: support other types of initialization
        X = problem.xl + X * (problem.xu - problem.xl)
        feasible = problem.evaluate_feasible(X) # NOTE: assume constraint evaluation is fast
        if np.any(feasible):
            X_feasible = np.vstack([X_feasible, X[feasible]])
        iter_count += 1

    if iter_count >= max_iter and len(X_feasible) < n_sample:
        raise Exception(f'hard to generate valid samples, {len(X_feasible)}/{n_sample} generated')

    X = X_feasible[:n_sample]
    return problem.transformation.undo(X)


def load_provided_initial_samples(init_sample_path):
    '''
    Load provided initial samples from file
    Input:
        init_sample_path: path of provided initial samples
    Output:
        X, Y: initial samples (design parameters, performance values)
    '''
    assert init_sample_path is not None, 'path of initial samples is not provided'

    if isinstance(init_sample_path, list) and len(init_sample_path) == 2:
        X_path, Y_path = init_sample_path[0], init_sample_path[1] # initial X and initial Y are both provided
    elif isinstance(init_sample_path, str):
        X_path, Y_path = init_sample_path, None # only initial X is provided, initial Y needs to be evaluated
    else:
        raise Exception('path of initial samples must be specified as 1) a list [x_path, y_path]; or 2) a string x_path')

    def load_from_file(path):
        # NOTE: currently only support npy and csv format for initial sample path
        try:
            if path.endswith('.npy'):
                return np.load(path)
            elif path.endswith('.csv'):
                return np.genfromtxt(path, delimiter=',')
            else:
                raise NotImplementedError
        except:
            raise Exception(f'failed to load initial samples from path {path}')

    X = load_from_file(X_path)
    Y = load_from_file(Y_path) if Y_path is not None else None
    return X, Y


def verify_provided_initial_samples(X, Y, n_var, n_obj):
    '''
    '''
    assert X.ndim == 2, 'initial designs need to have exactly two dimensions'
    if Y is not None:
        assert Y.ndim == 2, 'initial performance values need to have exactly two dimensions'
        assert X.shape[0] == Y.shape[0], 'number of initial designs and performance values does not match'
    assert X.shape[0] >= 2, 'need to have at least two initial designs' # TODO

    assert X.shape[1] == n_var, 'dimension mismatch between problem and initial designs'
    if Y is not None:
        assert Y.shape[1] == n_obj, 'dimension mismatch between problem and initial performance values'


def get_initial_samples(problem, n_random_sample=0, init_sample_path=None):
    '''
    Getting initial samples of the problem
    Input:
        problem: the optimization problem
        n_random_sample: number of random initial samples
        init_sample_path: path to provided initial samples
    Output:
        X_init_evaluated:
        X_init_unevaluated:
        Y_init_evaluated:
    '''
    X_init_evaluated, X_init_unevaluated, Y_init_evaluated = None, None, None

    random_init = n_random_sample > 0
    provided_init = init_sample_path is not None
    assert random_init or provided_init, 'neither number of random initial samples nor path of provided initial samples is provided'
    
    if random_init:
        X_init_unevaluated = generate_random_initial_samples(problem, n_random_sample)

    if provided_init:
        X_init_provided, Y_init_provided = load_provided_initial_samples(init_sample_path)

        problem_cfg = problem.get_config()
        n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
        verify_provided_initial_samples(X_init_provided, Y_init_provided, n_var, n_obj)

        if Y_init_provided is None:
            if random_init:
                X_init_unevaluated = np.vstack([X_init_unevaluated, X_init_provided])
            else:
                X_init_unevaluated = X_init_provided
        else:
            X_init_evaluated = X_init_provided
            Y_init_evaluated = Y_init_provided

    return X_init_evaluated, X_init_unevaluated, Y_init_evaluated
