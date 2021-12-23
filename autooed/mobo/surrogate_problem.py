'''
Surrogate problem that mimics the real problem based on surrogate model.
'''

import numpy as np
import autograd
from pymoo.model.problem import Problem
from pymoo.model.problem import at_least2d


class SurrogateProblem(Problem):

    def __init__(self, problem, acquisition):
        '''
        Initialize the surrogate problem.

        Parameters
        ----------
        problem: autooed.problem.Problem
            The original optimization problem which this surrogate is approximating.
        acquisition: autooed.mobo.acquisition.base.Acquisition
            The acquisition function to evaluate the fitness of samples.
        '''
        self.problem = problem
        self.transformation = problem.transformation
        self.acquisition = acquisition
        super().__init__(
            n_var=problem.n_var, n_obj=problem.n_obj, n_constr=problem.n_constr, 
            xl=problem.xl, xu=problem.xu
        )

    def _evaluate(self, X, out, *args, gradient, hessian, **kwargs):
        '''
        The main evaluation computation.

        Parameters
        ----------
        X: np.array
            Input design variables (continuous).
        out: dict
            A dictionary serving as output, which should contain evaluation results, including performance, constraint values, and even derivatives of performance.
        gradient: bool
            Whether to calculate the gradient of performance.
        hessian: bool
            Whether to calculate the hessian of performance.
        '''
        # evaluate F, dF, hF by acquisition function
        out['F'], out['dF'], out['hF'] = self.acquisition.evaluate(X, dtype='continuous', gradient=gradient, hessian=hessian)
        
        # evaluate cheap constraints by real problem
        X_raw = self.transformation.undo(X)
        out['G'] = np.array([self.problem.evaluate_constraint(x_raw) for x_raw in X_raw])

    def evaluate(self, X, *args, return_values_of="auto", return_as_dictionary=False, **kwargs):
        '''
        Evaluate the given problem.

        The function values set as defined in the function.
        The constraint values are meant to be positive if infeasible. A higher positive values means "more" infeasible".
        If they are 0 or negative, they will be considered as feasible what ever their value is.

        Parameters
        ----------
        X : np.array
            A two dimensional matrix where each row is a point to evaluate and each column a variable.
        return_as_dictionary : bool, default=False
            If this is true than only one object, a dictionary, is returned. This contains all the results
            that are defined by return_values_of. Otherwise, by default a tuple as defined is returned.
        return_values_of : list of strings, default='auto'
            You can provide a list of strings which defines the values that are returned. By default it is set to
            "auto" which means depending on the problem the function values or additional the constraint violation (if
            the problem has constraints) are returned. Otherwise, you can provide a list of values to be returned.\n
            Allowed is ["F", "CV", "G", "dF", "dG", "dCV", "feasible"] where the d stands for
            derivative and h stands for hessian matrix.

        Returns
        -------
            A dictionary, if return_as_dictionary enabled, or a list of values as defined in return_values_of.
        '''
        assert self.acquisition.fitted, 'Acquisition function is not fitted before surrogate problem evaluation'

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
        gradient = (len(gradients_not_set) > 0)

        # handle hF (hessian) computation, which is not supported by Pymoo
        hessian = (type(return_values_of) == list and 'hF' in return_values_of)

        # set in the dictionary if the output should be calculated - can be used for the gradient
        out = {}
        for val in return_values_of:
            out[val] = None

        # calculate the output array - either elementwise or not. also consider the gradient
        self._evaluate(X, out, *args, gradient=gradient, hessian=hessian, **kwargs)
        at_least2d(out)

        gradient_of = [key for key, val in out.items()
                            if "d" + key in return_values_of and
                            out.get("d" + key) is None and
                            (type(val) == autograd.numpy.numpy_boxes.ArrayBox)]

        if len(gradient_of) > 0:
            deriv = self._gradient(out, gradient_of)
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

    def evaluate_constraint(self, X):
        '''
        A constraint evaluation function for continuous design variables, which is needed in the solver.

        Parameters
        ----------
        X: np.array
            Design variables (continuous).

        Returns
        -------
        G: np.array
            Constraint violations (<=0 means satisfying constraints, >0 means violating constraints).
        '''
        X = self.transformation.undo(X)

        if X.ndim == 1:
            return self.problem.evaluate_constraint(X)
        elif X.ndim == 2:
            G = np.array([self.problem.evaluate_constraint(x) for x in X])
            if None in G:
                return None
            else:
                return G
        else:
            raise NotImplementedError

    def __str__(self):
        return '========== Problem Definition ==========\n' + super().__str__()

