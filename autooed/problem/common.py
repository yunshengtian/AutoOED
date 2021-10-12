import importlib
import os
import glob
import numpy as np
from pymoo.factory import get_from_list

from autooed.problem.problem import Problem
from autooed.problem.config import load_config, save_config, complete_config


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


def find_predefined_python_problems():
    '''
    Find all predefined problems created by python files
    Output:
        problems: a dict of {name: python_class} of all predefined python problems
    '''
    # find modules of predefined problems
    modules = glob.glob(os.path.join(os.path.dirname(__file__), "predefined/*.py"))
    modules = ['predefined.' + os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

    # check if duplicate exists
    assert len(np.unique(modules)) == len(modules), 'name conflict exists in defined python problems'

    # build problem dict
    problems = {}
    for module in modules:
        for key, val in importlib.import_module(f'autooed.problem.{module}').__dict__.items():
            if not key.startswith('_') and val in get_subclasses(Problem):
                problems[key] = val
    return problems


def find_custom_python_problems():
    '''
    Find all custom problems created by python files
    Output:
        problems: a dict of {name: python_class} of all custom python problems
    '''
    # find modules of custom problems
    modules = glob.glob(os.path.join(os.path.dirname(__file__), "custom/python/*.py"))
    modules = ['custom.python.' + os.path.basename(f)[:-3] for f in modules if os.path.isfile(f) and not f.endswith('__init__.py')]

    # check if duplicate exists
    assert len(np.unique(modules)) == len(modules), 'name conflict exists in defined python problems'

    # build problem dict
    problems = {}
    for module in modules:
        for key, val in importlib.import_module(f'autooed.problem.{module}').__dict__.items():
            if not key.startswith('_') and val in get_subclasses(Problem):
                problems[key] = val
    return problems


def find_python_problems():
    '''
    Find all problems created by python files
    Output:
        problems: a dict of {name: python_class} of all python problems
    '''
    problems = {}
    problems.update(find_predefined_python_problems())
    problems.update(find_custom_python_problems())
    return problems


def get_yaml_problem_dir():
    '''
    Return directory of yaml problems
    '''
    problem_dir = os.path.join(os.path.dirname(__file__), 'custom', 'yaml')
    os.makedirs(problem_dir, exist_ok=True)
    return problem_dir


def find_yaml_problems():
    '''
    Find all problems created by yaml files
    Output:
        problems: a dict of {name: yaml_path} of all yaml problems
    '''
    configs = {}
    config_dir = get_yaml_problem_dir()
    for name in os.listdir(config_dir):
        if name.endswith('.yml'):
            configs[name[:-4]] = os.path.join(config_dir, name)
    return configs


def load_yaml_problem(name):
    '''
    Load problem config from yaml file
    '''
    path = os.path.join(get_yaml_problem_dir(), f'{name}.yml')
    return load_config(path)


def save_yaml_problem(config):
    '''
    Save problem config as yaml file
    '''
    name = config['name']
    path = os.path.join(get_yaml_problem_dir(), f'{name}.yml')
    save_config(config, path)


def remove_yaml_problem(name):
    '''
    Remove a problem from saved problems
    '''
    path = os.path.join(get_yaml_problem_dir(), f'{name}.yml')
    try:
        os.remove(path)
    except:
        raise Exception("problem doesn't exist")


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


def get_predefined_python_problem_list():
    '''
    Get names of predefined python problems
    '''
    return list(find_predefined_python_problems().keys())


def get_custom_python_problem_list():
    '''
    Get names of custom python problems
    '''
    return list(find_custom_python_problems().keys())


def get_python_problem_list():
    '''
    Get names of all python problems
    '''
    return list(find_python_problems().keys())


def get_yaml_problem_list():
    '''
    Get names of (generated) yaml problems
    '''
    return list(find_yaml_problems().keys())


def get_problem_list():
    '''
    Get names of available problems
    '''
    python_problems, yaml_problems = find_all_problems()
    return list(python_problems.keys()) + list(yaml_problems.keys())


def check_problem_exist(name):
    '''
    Check if problem exists
    '''
    python_problems, yaml_problems = find_all_problems()
    return name in python_problems or name in yaml_problems


def get_problem_config(name):
    '''
    Get config dict of problem
    '''
    config = None

    # check for custom python problems
    custom_problems = find_custom_python_problems()
    if name in custom_problems:
        config = custom_problems[name].get_config()
        return complete_config(config, check=True)

    # check for custom yaml problems
    yaml_problems = find_yaml_problems()
    if name in yaml_problems:
        config_path = yaml_problems[name]
        config = load_config(config_path)
        return complete_config(config, check=True)

    # check for predefined python problems
    predefined_problems = find_predefined_python_problems()
    if name in predefined_problems:
        config = predefined_problems[name].get_config()
        return complete_config(config, check=True)
        
    raise Exception(f'problem {name} is not defined')


def build_problem(name, get_pfront=False):
    '''
    Build optimization problem
    Input:
        name: problem name
        get_pfront: if return predefined true Pareto front of the problem
    Output:
        problem: the optimization problem
        pareto_front: the true Pareto front of the problem (if defined, otherwise None)
    '''
    problem = None
    
    # build problem
    python_problems, yaml_problems = find_all_problems()
    if name in python_problems:
        problem = python_problems[name]()
    elif name in yaml_problems:
        full_prob_cfg = load_config(yaml_problems[name])
        problem = Problem(config=full_prob_cfg)
    else:
        raise Exception(f'Problem {name} not found')

    # get true pareto front
    if get_pfront:
        try:
            pareto_front = problem.pareto_front()
        except:
            pareto_front = None
        return problem, pareto_front
    else:
        return problem

