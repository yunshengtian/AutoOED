import numpy as np
from collections.abc import Iterable
from pymoo.model.problem import Problem as PymooProblem

from problem.utils import import_python_func, import_c_func


class class_or_instance_method(classmethod):
    def __get__(self, instance, type_):
        descr_get = super().__get__ if instance is None else self.__func__.__get__
        return descr_get(instance, type_)


class Problem(PymooProblem):
    '''
    Base class for problems, inherit this with a custom config, evaluate_performance() and evaluate_constraint()
    '''
    config = {}

    def __init__(self, ref_point=None, **kwargs):

        self.config = self.process_config(self.config, **kwargs)

        PymooProblem.__init__(self, 
            n_var=self.config['n_var'], 
            n_obj=self.config['n_obj'], 
            n_constr=self.config['n_constr'], 
            xl=self.config['var_lb'], 
            xu=self.config['var_ub'],
        )

        self.name = lambda: self.config['name']
        self.ref_point = ref_point # TODO: check

        self.minimize = self.config['minimize']
        self.var_name = self.config['var_name']
        self.obj_name = self.config['obj_name']

    @class_or_instance_method
    def get_config(cls_or_self, *args, **kwargs):
        '''
        Get problem config
        '''
        if isinstance(cls_or_self, type):
            cls = cls_or_self
        else:
            cls = cls_or_self.__class__
        return cls.process_config(cls_or_self.config, *args, **kwargs)

    @classmethod
    def process_config(cls, config, var_lb=None, var_ub=None, obj_lb=None, obj_ub=None, init_sample_path=None, **kwargs):
        '''
        Post-process problem config
        ''' 
        config = config.copy()

        # default values for config
        default_config = {
            'name': cls.__name__,
            'n_var': 'required',
            'n_obj': 'required',
            'minimize': True, # minimization by default
            'n_constr': 0, # no constraints by default
            'var_lb': 0, # 0 as var lower bound by default
            'var_ub': 1, # 1 as var upper bound by default
            'obj_lb': None, # no obj lower bound by default
            'obj_ub': None, # no obj upper bound by default
            'var_name': None,
            'obj_name': None,
            'init_sample_path': None, # no provided initial sample path by default
        }

        # TODO: type check

        # fill config with default_config when there are key missings
        for key, value in default_config.items():
            if key not in config:
                if type(value) == str and value == 'required':
                    raise Exception('Invalid config for custom problem, required values are not provided')
                config[key] = value
            elif config[key] is None:
                config[key] = value
        
        # update config if kwargs are specified
        if var_lb is not None: config['var_lb'] = var_lb
        if var_ub is not None: config['var_ub'] = var_ub
        if obj_lb is not None: config['obj_lb'] = obj_lb
        if obj_ub is not None: config['obj_ub'] = obj_ub
        if init_sample_path is not None: config['init_sample_path'] = init_sample_path

        n_var, n_obj = config['n_var'], config['n_obj']

        # post-process minimize
        minimize = config['minimize']
        if not isinstance(minimize, Iterable):
            minimize = [minimize] * n_obj
        assert len(minimize) == n_obj, f'dimension mismatch, minimize should have {n_obj} dimensions'
        config['minimize'] = np.array(minimize, dtype=bool)

        # post-process bounds
        var_lb, var_ub = config['var_lb'], config['var_ub']

        if var_lb is None: var_lb = np.zeros(n_var)
        elif isinstance(var_lb, Iterable):
            var_lb = np.array(var_lb)
            var_lb[var_lb == None] = 0
            var_lb = var_lb.astype(float)
        else:
            var_lb = np.array([var_lb] * n_var, dtype=float)
        
        if var_ub is None: var_ub = np.ones(n_var)
        elif isinstance(var_ub, Iterable):
            var_ub = np.array(var_ub)
            var_ub[var_ub == None] = 1
            var_ub = var_ub.astype(float)
        else:
            var_ub = np.array([var_ub] * n_var, dtype=float)

        config['var_lb'], config['var_ub'] = var_lb, var_ub

        # post-process names
        if config['var_name'] is None: config['var_name'] = [f'x{i + 1}' for i in range(n_var)]
        if config['obj_name'] is None: config['obj_name'] = [f'f{i + 1}' for i in range(n_obj)]

        return config

    def set_ref_point(self, ref_point):
        '''
        Set reference point for hypervolume calculation
        '''
        assert len(ref_point) == self.n_obj, f'reference point should have {self.n_obj} dimensions'
        self.ref_point = ref_point

    """
    def evaluate_performance(self, x):
        '''
        Main function for objective evaluation
        '''
        return None
    """

    def evaluate_constraint(self, x):
        '''
        Main function for constraint evaluation
        '''
        return None

    def evaluate_feasible(self, x):
        '''
        Feasibility evaluation, can be computed from constraint evaluation
        '''
        if self.n_constr == 0:
            CV = np.zeros([x.shape[0], 1])
        else:
            G = self.evaluate_constraint(x)
            assert G is not None
            CV = Problem.calc_constraint_violation(np.column_stack(np.atleast_2d(G)))
        feasible = (CV <= 0).flatten()
        return feasible

    def _evaluate(self, x, out, *args, **kwargs):
        '''
        Deprecated evaluation function, please call evaluate_performance() and evaluate_constraint() instead
        '''
        raise NotImplementedError
    
    def __str__(self):
        s = '========== Problem Definition ==========\n'
        s += "# name: %s\n" % self.name()
        s += "# n_var: %s\n" % self.n_var
        s += "# n_obj: %s\n" % self.n_obj
        s += "# n_constr: %s\n" % self.n_constr
        return s


class GeneratedProblem(Problem):
    '''
    Generated custom problems from GUI, to be initialized from a config dict
    '''
    def __init__(self, config, **kwargs):
        self.config = config.copy()

        # import performance evaluation function
        if 'performance_eval' in self.config:
            eval_p_path = self.config.pop('performance_eval')
            if eval_p_path is not None:
                ftype = eval_p_path.split('.')[-1]
                if ftype == 'py':
                    try:
                        self.evaluate_performance = import_python_func(path=eval_p_path, module_name='eval_p', func_name='evaluate_performance')
                    except:
                        raise Exception('failed to import performance evaluation function from python file')
                elif ftype == 'c' or ftype == 'cpp':
                    try:
                        self.evaluate_performance = import_c_func(path=eval_p_path, lib_name='eval_p', func_name='evaluate_performance',
                            n_in=self.config['n_var'], n_out=self.config['n_obj'])
                    except:
                        raise Exception('failed to import performance evaluation function from c/cpp file')
                else:
                    raise Exception('only python and c/cpp files are supported')

        # import constraint evaluation function
        if 'constraint_eval' in self.config:
            eval_c_path = self.config.pop('constraint_eval')
            if eval_c_path is not None and self.config['n_constr'] > 0:
                ftype = eval_p_path.split('.')[-1]
                if ftype == 'py':
                    try:
                        self.evaluate_constraint = import_python_func(path=eval_c_path, module_name='eval_c', func_name='evaluate_constraint')
                    except:
                        raise Exception('failed to import constraint evaluation function from python file')  
                elif ftype == 'c' or ftype == 'cpp':
                    try:
                        self.evaluate_constraint = import_c_func(path=eval_c_path, lib_name='eval_c', func_name='evaluate_constraint',
                            n_in=self.config['n_var'], n_out=self.config['n_constr'])
                    except:
                        raise Exception('failed to import constraint evaluation function from c/cpp file')
                else:
                    raise Exception('only python and c/cpp files are supported')

        super().__init__(**kwargs)

