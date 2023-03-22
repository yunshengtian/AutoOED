import numpy as np
from collections.abc import Iterable
from pymoo.model.problem import Problem as PymooProblem

from autooed.problem.config import check_config, transform_config, complete_config
from autooed.problem.import_func import import_obj_func, import_constr_func
from autooed.problem.transformation import get_transformation


class class_or_instance_method(classmethod):
    def __get__(self, instance, type_):
        descr_get = super().__get__ if instance is None else self.__func__.__get__
        return descr_get(instance, type_)


class Problem(PymooProblem):
    '''
    Base class for problems, for custom problem specification, do either of the following:
    1) Inherit this with a custom config, evaluate_objective() and evaluate_constraint()
    2) Initialize this with a custom config with 'obj_func' and 'constr_func' specified
    '''
    config = {}

    def __init__(self, config=None):
        # pre-process config
        if config is not None:
            self.config = config
        if 'name' not in self.config:
            self.config['name'] = self.__class__.__name__
        check_config(self.config)

        # initialize continuous problem with transformed config
        PymooProblem.__init__(self, **transform_config(self.config))

        # complete config
        self.config = complete_config(self.config)

        # problem properties
        self.var_name = self.config['var_name']
        self.obj_name = self.config['obj_name']
        self.obj_type = self.config['obj_type']
        self.transformation = get_transformation(self.config)

        # import objective evaluation function
        if self.config['obj_func'] is not None:
            self.evaluate_objective = import_obj_func(self.config['obj_func'], self.config['n_var'], self.config['n_obj'])

        # import constraint evaluation function
        if self.config['constr_func'] is None:
            if not hasattr(self, 'evaluate_constraint'):
                if self.config['n_constr'] > 0:
                    raise Exception('no constraint function is provided')
                else:
                    self.evaluate_constraint = no_constraint_evaluation
        else:
            self.evaluate_constraint = import_constr_func(self.config['constr_func'], self.config['n_var'], self.config['n_constr'])

    def name(self):
        return self.config['name']

    @class_or_instance_method
    def get_config(cls_or_self, *args, **kwargs):
        '''
        Get problem config
        '''
        if isinstance(cls_or_self, type):
            cls = cls_or_self
        else:
            cls = cls_or_self.__class__

        config = cls_or_self.config.copy()
        if 'name' not in config:
            config['name'] = cls.__name__
        
        return complete_config(config, check=True)
    
    """
    def evaluate_objective(self, x):
        '''
        Main function for objective evaluation
        '''
        return None

    def evaluate_constraint(self, x):
        '''
        Main function for constraint evaluation
        '''
        return None
    """

    def evaluate_feasible(self, x):
        '''
        Feasibility evaluation, can be computed from constraint evaluation
        '''
        if self.n_constr == 0:
            CV = np.zeros([x.shape[0], 1])
        else:
            G = [self.evaluate_constraint(x_) for x_ in x]
            assert None not in G, 'constraint evaluation function is invalid'
            CV = Problem.calc_constraint_violation(np.atleast_2d(G))
        feasible = (CV <= 0).flatten()
        return feasible

    def _evaluate(self, x, out, *args, **kwargs):
        '''
        Deprecated evaluation function, please call evaluate_objective() and evaluate_constraint() instead
        '''
        raise NotImplementedError
    
    def __str__(self):
        s = '========== Problem Definition ==========\n'
        s += "# name: %s\n" % self.name()
        s += "# n_var: %s\n" % self.n_var
        s += "# n_obj: %s\n" % self.n_obj
        s += "# n_constr: %s\n" % self.n_constr
        return s


def no_constraint_evaluation(x):
    return None