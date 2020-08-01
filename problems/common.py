import numpy as np
from pymoo.factory import get_from_list
from problems import Problem
from external import lhs

import importlib
from os.path import dirname, basename, isfile, join
import glob


def get_subclasses(cls):
    '''
    Get all leaf subclasses of a given class
    '''
    subclasses = []
    for subclass in cls.__subclasses__():
        subsubclasses = get_subclasses(subclass)
        if subsubclasses == []:
            subclasses.append(subclass)
        else:
            subclasses.extend(subsubclasses)
    return subclasses


def find_all_problem_modules():
    '''
    Return a list of module of all problems
    '''
    predefined_modules = glob.glob(join(dirname(__file__), "predefined/*.py"))
    predefined_modules = ['predefined.' + basename(f)[:-3] for f in predefined_modules if isfile(f) and not f.endswith('__init__.py')]
    custom_modules = glob.glob(join(dirname(__file__), "custom/*.py"))
    custom_modules = ['custom.' + basename(f)[:-3] for f in custom_modules if isfile(f) and not f.endswith('__init__.py')]
    all_modules = predefined_modules + custom_modules
    return all_modules


def find_all_problem_classes():
    '''
    Return a dict of {name: class} of all problems
    '''
    problems = {}
    all_modules = find_all_problem_modules()
    for module in all_modules:
        for key, val in importlib.import_module(f'problems.{module}').__dict__.items():
            key = key.lower()
            if not key.startswith('_') and not key.startswith('exampleproblem') and val in get_subclasses(Problem):
                problems[key] = val
    return problems


def get_problem(name, *args, **kwargs):
    '''
    Build problem from name and arguments
    '''
    problems = find_all_problem_classes()
    if name not in problems:
        raise Exception(f'Problem {name} not found')
    return problems[name](*args, **kwargs)


def get_problem_list():
    '''
    Get names of available problems
    '''
    problems = find_all_problem_classes()
    return list(problems.keys())


def generate_initial_samples(problem, n_sample):
    '''
    Generate feasible initial samples.
    Input:
        problem: the optimization problem
        n_sample: number of initial samples
    Output:
        X, Y: initial samples (design parameters, performances)
    '''
    X_feasible = np.zeros((0, problem.n_var))
    Y_feasible = np.zeros((0, problem.n_obj))

    # NOTE: when it's really hard to get feasible samples, the program hangs here
    while len(X_feasible) < n_sample:
        X = lhs(problem.n_var, n_sample)
        X = problem.xl + X * (problem.xu - problem.xl)
        Y, feasible = problem.evaluate(X, return_values_of=['F', 'feasible'])
        feasible = feasible.flatten()
        X_feasible = np.vstack([X_feasible, X[feasible]])
        Y_feasible = np.vstack([Y_feasible, Y[feasible]])
    
    indices = np.random.permutation(np.arange(len(X_feasible)))[:n_sample]
    X, Y = X_feasible[indices], Y_feasible[indices]
    return X, Y


def build_problem(config, get_pfront=False, get_init_samples=False):
    '''
    Build optimization problem from name, get initial samples
    Input:
        name: name of the problem (supports ZDT1-6, DTLZ1-7)
        n_var: number of design variables
        n_obj: number of objectives
    Output:
        problem: the optimization problem
        pareto_front: the true pareto front of the problem (if defined, otherwise None)
    '''
    name, n_var, n_obj, ref_point = config['name'], config['n_var'], config['n_obj'], config['ref_point']
    xl, xu = config['var_lb'], config['var_ub']
    # NOTE: either set ref_point from config file, or set from init random/provided samples
    # TODO: support provided init samples

    # build problem
    try:
        problem = get_problem(name, n_var=n_var, n_obj=n_obj, xl=xl, xu=xu)
    except:
        raise NotImplementedError('problem not supported yet!')

    # NOTE: when config mismatch between arguments and problem specification, use problem specification instead
    config['n_var'], config['n_obj'] = problem.n_var, problem.n_obj
    if problem.xl is not None: config['xl'] = problem.xl.tolist()
    if problem.xu is not None: config['xu'] = problem.xu.tolist()

    if get_pfront:
        try:
            pareto_front = problem.pareto_front()
        except:
            pareto_front = None

    if get_init_samples:
        X_init, Y_init = generate_initial_samples(problem, config['n_init_sample'])
        if ref_point is None:
            ref_point = np.max(Y_init, axis=0)
            config['ref_point'] = ref_point.tolist() # update reference point in config

    if ref_point is not None:
        problem.set_ref_point(ref_point)
    
    if not get_pfront and not get_init_samples:
        return problem
    elif get_pfront and get_init_samples:
        return problem, pareto_front, X_init, Y_init
    elif get_pfront:
        return problem, pareto_front
    elif get_init_samples:
        return problem, X_init, Y_init