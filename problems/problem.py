import numpy as np
import autograd
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pymoo.model.problem import Problem as PymooProblem
from pymoo.model.problem import at_least2d, evaluate_in_parallel

from problems.utils import import_module_from_path


class Problem(PymooProblem):
    '''
    Problem definition built upon Pymoo's Problem class, added some custom features
    '''
    def __init__(self, *args, xl=None, xu=None, var_name=None, obj_name=None, **kwargs):
        # set default bounds
        xl, xu = self._process_bounds(xl, xu)

        # TODO: obj bound is currently not supported
        if 'fl' in kwargs: kwargs.pop('fl')
        if 'fu' in kwargs: kwargs.pop('fu')

        PymooProblem.__init__(self, *args, xl=xl, xu=xu, **kwargs)

        self.ref_point = None
        self.var_name = var_name if var_name is not None else [f'x{i + 1}' for i in range(self.n_var)]
        self.obj_name = obj_name if obj_name is not None else [f'f{i + 1}' for i in range(self.n_obj)]

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

    def _evaluate(self, x, out, *args, **kwargs):
        out['F'] = np.column_stack([*np.atleast_2d(self.evaluate_performance(x))])
        out['G'] = self.evaluate_constraint(x)
        if out['G'] is not None:
            out['G'] = np.column_stack([*np.atleast_2d(out['G'])])

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
    
    def evaluate(self,
                 X,
                 *args,
                 return_values_of="auto",
                 return_as_dictionary=False,
                 **kwargs):

        """
        Evaluate the given problem.

        The function values set as defined in the function.
        The constraint values are meant to be positive if infeasible. A higher positive values means "more" infeasible".
        If they are 0 or negative, they will be considered as feasible what ever their value is.

        Parameters
        ----------

        X : np.array
            A two dimensional matrix where each row is a point to evaluate and each column a variable.

        return_as_dictionary : bool
            If this is true than only one object, a dictionary, is returned. This contains all the results
            that are defined by return_values_of. Otherwise, by default a tuple as defined is returned.

        return_values_of : list of strings
            You can provide a list of strings which defines the values that are returned. By default it is set to
            "auto" which means depending on the problem the function values or additional the constraint violation (if
            the problem has constraints) are returned. Otherwise, you can provide a list of values to be returned.

            Allowed is ["F", "CV", "G", "dF", "dG", "dCV", "feasible"] where the d stands for
            derivative and h stands for hessian matrix.


        Returns
        -------

            A dictionary, if return_as_dictionary enabled, or a list of values as defined in return_values_of.

        """

        # call the callback of the problem
        if self.callback is not None:
            self.callback(X)

        # make the array at least 2-d - even if only one row should be evaluated
        only_single_value = len(np.shape(X)) == 1
        X = np.atleast_2d(X)

        # check the dimensionality of the problem and the given input
        if X.shape[1] != self.n_var:
            raise Exception('Input dimension %s are not equal to n_var %s!' % (X.shape[1], self.n_var))

        # automatic return the function values and CV if it has constraints if not defined otherwise
        if type(return_values_of) == str and return_values_of == "auto":
            return_values_of = ["F"]
            if self.n_constr > 0:
                return_values_of.append("CV")

        # all values that are set in the evaluation function
        values_not_set = [val for val in return_values_of if val not in self.evaluation_of]

        # have a look if gradients are not set and try to use autograd and calculate grading if implemented using it
        gradients_not_set = [val for val in values_not_set if val.startswith("d")]

        # whether gradient calculation is necessary or not
        calc_gradient = (len(gradients_not_set) > 0)

        # set in the dictionary if the output should be calculated - can be used for the gradient
        out = {}
        for val in return_values_of:
            out[val] = None

        # calculate the output array - either elementwise or not. also consider the gradient
        self._evaluate(X, out, *args, calc_gradient=calc_gradient, **kwargs)
        at_least2d(out)

        calc_gradient_of = [key for key, val in out.items()
                            if "d" + key in return_values_of and
                            out.get("d" + key) is None and
                            (type(val) == autograd.numpy.numpy_boxes.ArrayBox)]

        if len(calc_gradient_of) > 0:
            deriv = self._calc_gradient(out, calc_gradient_of)
            out = {**out, **deriv}

        # convert back to conventional numpy arrays - no array box as return type
        for key in out.keys():
            if type(out[key]) == autograd.numpy.numpy_boxes.ArrayBox:
                out[key] = out[key]._value

        # if constraint violation should be returned as well
        if self.n_constr == 0:
            CV = np.zeros([X.shape[0], 1])
        else:
            CV = Problem.calc_constraint_violation(out["G"])

        if "CV" in return_values_of:
            out["CV"] = CV

        # if an additional boolean flag for feasibility should be returned
        if "feasible" in return_values_of:
            out["feasible"] = (CV <= 0)

        # if asked for a value but not set in the evaluation set to None
        for val in return_values_of:
            if val not in out:
                out[val] = None

        # remove the first dimension of the output - in case input was a 1d- vector
        if only_single_value:
            for key in out.keys():
                if out[key] is not None:
                    out[key] = out[key][0, :]

        if return_as_dictionary:
            return out
        else:
            # if just a single value do not return a tuple
            if len(return_values_of) == 1:
                return out[return_values_of[0]]
            else:
                return tuple([out[val] for val in return_values_of])

    def __str__(self):
        return '========== Problem Definition ==========\n' + super().__str__()


class CustomProblem(Problem):
    '''
    Base class for custom problems, inherit this with a custom config, evaluate_performance() and evaluate_constraint()
    '''
    # main problem config, to be inherited
    config = {}

    # default values for problem config
    default_config = {
        'n_var': 'required',
        'n_obj': 'required',
        'n_constr': 0, # no constraints by default
        'var_lb': 0, # 0 as var lower bound by default
        'var_ub': 1, # 1 as var upper bound by default
        'obj_lb': None, # no obj lower bound by default
        'obj_ub': None, # no obj upper bound by default
    }

    # translate config keys to corresponding ones used in pymoo
    config_translate = {
        'var_lb': 'xl',
        'var_ub': 'xu',
        'obj_lb': 'fl',
        'obj_ub': 'fu',
    }

    def __init__(self, *args, xl=None, xu=None, **kwargs):
        # fill config with default_config when there are key missings
        for key, value in self.default_config.items():
            if key not in self.config:
                if value == 'required':
                    raise Exception('Invalid config for custom problem, required values are not provided')
                self.config[key] = value

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

        # problem name
        self.problem_name = self.config.pop('name')

        # set evaluation modules
        self.eval_p_module = import_module_from_path('eval_p', self.config.pop('performance_eval'))
        if self.config['constraint_eval'] is not None:
            self.eval_c_module = import_module_from_path('eval_c', self.config.pop('constraint_eval'))
        else:
            self.eval_c_module = None

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

    def name(self):
        '''
        Return problem name
        '''
        return self.problem_name

    def export(self):
        '''
        Export problem config
        '''
        return self.raw_config
