import importlib
import os
import glob
import yaml
import numpy as np
from pymoo.factory import get_from_list
from problems import Problem, GeneratedProblem
from external import lhs


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


def find_python_problems():
    '''
    Find all problems created by python files
    Output:
        problems: a dict of {name: python_class} of all python problems
    '''
    # find modules of python problems
    predefined_modules = glob.glob(os.path.join(os.path.dirname(__file__), "predefined/*.py"))
    predefined_modules = ['predefined.' + os.path.basename(f)[:-3] for f in predefined_modules if os.path.isfile(f) and not f.endswith('__init__.py')]
    custom_modules = glob.glob(os.path.join(os.path.dirname(__file__), "custom/python/*.py"))
    custom_modules = ['custom.python.' + os.path.basename(f)[:-3] for f in custom_modules if os.path.isfile(f) and not f.endswith('__init__.py')]
    all_modules = predefined_modules + custom_modules

    # check if duplicate exists
    assert len(np.unique(all_modules)) == len(all_modules), 'name conflict exists in defined python problems'

    # build problem dict
    problems = {}
    for module in all_modules:
        for key, val in importlib.import_module(f'problems.{module}').__dict__.items():
            key = key.lower()
            if not key.startswith('_') and not key.startswith('exampleproblem') and val in get_subclasses(Problem):
                problems[key] = val
    return problems


def find_yaml_problems():
    '''
    Find all problems created by yaml files
    Output:
        problems: a dict of {name: yaml_path} of all yaml problems
    '''
    configs = {}
    config_dir = os.path.join(os.path.dirname(__file__), 'custom', 'yaml')
    for name in os.listdir(config_dir):
        if name.endswith('.yml'):
            configs[name[:-4]] = os.path.join(config_dir, name)
    return configs


def find_all_problems():
    '''
    Find all problems created by python and yaml files, also check for name conflict
    '''
    python_problems = find_python_problems()
    yaml_problems = find_yaml_problems()
    if len(np.unique(list(python_problems.keys()) + list(yaml_problems.keys()))) < len(python_problems) + len(yaml_problems):
        raise Exception('name conflict exists between defined python problems and yaml problems')
    else:
        return python_problems, yaml_problems


def get_problem(name, *args, **kwargs):
    '''
    Build problem from name and arguments
    '''
    python_problems, yaml_problems = find_all_problems()
    if name in python_problems:
        return python_problems[name](*args, **kwargs)
    elif name in yaml_problems:
        with open(yaml_problems[name], 'r') as fp:
            config = yaml.load(fp, Loader=yaml.FullLoader)
        return GeneratedProblem(config, *args, **kwargs)
    else:
        raise Exception(f'Problem {name} not found')


def get_problem_list():
    '''
    Get names of available problems
    '''
    python_problems, yaml_problems = find_all_problems()
    return list(python_problems.keys()) + list(yaml_problems.keys())


def get_yaml_problem_list():
    '''
    Get names of available generated problems
    '''
    return list(find_yaml_problems().keys())


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