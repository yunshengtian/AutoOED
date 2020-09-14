import numpy as np
from pymoo.model.problem import Problem as PymooProblem

from problems.utils import import_python_func, import_c_func, process_problem_config


class Problem(PymooProblem):
    '''
    Real problem definition built upon Pymoo's Problem class, added some custom features
    '''
    def __init__(self, name=None, n_var=None, n_obj=None, n_constr=0,
        var_lb=None, var_ub=None, obj_lb=None, obj_ub=None, var_name=None, obj_name=None, 
        init_sample_path=None, minimize=True, ref_point=None, **kwargs):

        self.name = lambda: self.__class__.__name__ if name is None else name

        # set default bounds (TODO: obj bound is currently not supported)
        var_lb, var_ub = self._process_bounds(var_lb, var_ub)

        PymooProblem.__init__(self, n_var, n_obj, n_constr, var_lb, var_ub)

        self.var_name = var_name if var_name is not None else [f'x{i + 1}' for i in range(self.n_var)]
        self.obj_name = obj_name if obj_name is not None else [f'f{i + 1}' for i in range(self.n_obj)]
        
        self.init_sample_path = init_sample_path
        self.ref_point = ref_point

        if type(minimize) not in [list, np.ndarray]:
            minimize = [minimize] * self.n_obj
        assert len(minimize) == self.n_obj
        self.minimize = np.array(minimize, dtype=bool)

    def _process_bounds(self, var_lb, var_ub):
        '''
        Set default values for bounds if not specified
        '''
        if var_lb is None: var_lb = 0
        elif type(var_lb) in [list, np.ndarray]:
            var_lb = np.array(var_lb)
            var_lb[var_lb == None] = 0
            var_lb = var_lb.astype(float)
        
        if var_ub is None: var_ub = 1
        elif type(var_ub) in [list, np.ndarray]:
            var_ub = np.array(var_ub)
            var_ub[var_ub == None] = 1
            var_ub = var_ub.astype(float)
        
        return var_lb, var_ub

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
        return '========== Problem Definition ==========\n' + super().__str__()


class CustomProblem(Problem):
    '''
    Base class for custom problems, inherit this with a custom config, evaluate_performance() and evaluate_constraint()
    '''
    # main problem config, to be inherited
    config = {}

    def __init__(self, var_lb=None, var_ub=None, **kwargs):

        self.config = process_problem_config(self.config)

        # allow dynamically changing design bounds
        if var_lb is not None: self.config['var_lb'] = var_lb
        if var_ub is not None: self.config['var_ub'] = var_ub

        super().__init__(**self.config)


class GeneratedProblem(CustomProblem):
    '''
    Generated custom problems from GUI, to be initialized from a config dict
    '''
    def __init__(self, config, n_var=None, n_obj=None, **kwargs):
        self.raw_config = config.copy()
        self.config = config.copy()
        if n_var is not None: self.config['n_var'] = n_var
        if n_obj is not None: self.config['n_obj'] = n_obj

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

