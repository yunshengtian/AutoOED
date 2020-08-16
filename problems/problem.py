from abc import ABC, abstractmethod
import numpy as np
from pymoo.model.problem import Problem as PymooProblem

from problems.utils import import_module_from_path, process_problem_config


class Problem(PymooProblem, ABC):
    '''
    Real problem definition built upon Pymoo's Problem class, added some custom features
    '''
    def __init__(self, *args, name=None, xl=None, xu=None, fl=None, fu=None, var_name=None, obj_name=None, init_sample_path=None, **kwargs):
        # set default bounds (TODO: obj bound is currently not supported)
        xl, xu = self._process_bounds(xl, xu)

        self.name = lambda: self.__class__.__name__ if name is None else name

        PymooProblem.__init__(self, *args, xl=xl, xu=xu, **kwargs)

        self.ref_point = None
        self.var_name = var_name if var_name is not None else [f'x{i + 1}' for i in range(self.n_var)]
        self.obj_name = obj_name if obj_name is not None else [f'f{i + 1}' for i in range(self.n_obj)]
        self.init_sample_path = init_sample_path

    def _process_bounds(self, xl, xu):
        '''
        Set default values for bounds if not specified
        '''
        if xl is None: xl = 0
        elif isinstance(xl, list) or isinstance(xl, np.ndarray):
            xl = np.array(xl)
            xl[xl == None] = 0
            xl = xl.astype(float)
        
        if xu is None: xu = 1
        elif isinstance(xu, list) or isinstance(xu, np.ndarray):
            xu = np.array(xu)
            xu[xu == None] = 1
            xu = xu.astype(float)
        
        return xl, xu

    def set_ref_point(self, ref_point):
        '''
        Set reference point for hypervolume calculation
        '''
        assert len(ref_point) == self.n_obj, f'reference point should have {self.n_obj} dimensions'
        self.ref_point = ref_point

    @abstractmethod
    def evaluate_performance(self, x):
        '''
        Main function for objective evaluation
        '''
        raise NotImplementedError

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
            CV = Problem.calc_constraint_violation(np.column_stack(G))
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

    # translate config keys to corresponding ones used in pymoo
    config_translate = {
        'var_lb': 'xl',
        'var_ub': 'xu',
        'obj_lb': 'fl',
        'obj_ub': 'fu',
    }

    def __init__(self, *args, xl=None, xu=None, **kwargs):

        self.config = process_problem_config(self.config)

        # allow dynamically changing design bounds
        if xl is not None: self.config['var_lb'] = xl
        if xu is not None: self.config['var_ub'] = xu
                
        # translate config
        for old_key, new_key in self.config_translate.items():
            self.config[new_key] = self.config.pop(old_key)

        super().__init__(**self.config)


class GeneratedProblem(CustomProblem):
    '''
    Generated custom problems from GUI, to be initialized from a config dict
    '''
    def __init__(self, config, *args, n_var=None, n_obj=None, xl=None, xu=None, **kwargs):
        self.raw_config = config.copy()
        self.config = config.copy()
        if n_var is not None: self.config['n_var'] = n_var
        if n_obj is not None: self.config['n_obj'] = n_obj

        # set evaluation modules
        self.eval_p_module = import_module_from_path('eval_p', self.config.pop('performance_eval'))
        self.eval_c_module = None
        if 'constraint_eval' in self.config:
            eval_c_path = self.config.pop('constraint_eval')
            if eval_c_path is not None:
                self.eval_c_module = import_module_from_path('eval_c', eval_c_path)

        super().__init__(*args, xl=xl, xu=xu, **kwargs)

    def evaluate_performance(self, x):
        '''
        Evaluate objectives from imported module
        '''
        return self.eval_p_module.evaluate_performance(x)

    def evaluate_constraint(self, x):
        '''
        Evaluate constraints from imported module (if have)
        '''
        if self.eval_c_module is not None:
            return self.eval_c_module.evaluate_constraint(x)
        else:
            return None

    def export(self):
        '''
        Export problem config
        '''
        return self.raw_config
