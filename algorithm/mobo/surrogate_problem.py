import numpy as np
import autograd
from pymoo.model.problem import Problem
from pymoo.model.problem import at_least2d

'''
Surrogate problem that mimics the real problem based on surrogate model
'''

class SurrogateProblem(Problem):

    def __init__(self, real_problem, surrogate_model, acquisition, transformation):
        '''
        Input:
            real_problem: the original optimization problem which this surrogate is approximating
            surrogate_model: fitted surrogate model
            acquisition: the acquisition function to evaluate the fitness of samples
            transformation: data normalization for surrogate model fitting
        '''
        self.real_problem = real_problem
        self.surrogate_model = surrogate_model
        self.acquisition = acquisition
        self.transformation = transformation
        xl = transformation.do(x=real_problem.xl)
        xu = transformation.do(x=real_problem.xu)
        super().__init__(n_var=real_problem.n_var, n_obj=real_problem.n_obj, n_constr=real_problem.n_constr, xl=xl, xu=xu)

    def _evaluate(self, x, out, *args, calc_gradient=False, calc_hessian=False, **kwargs):
        # evaluate value by surrogate model
        std = self.acquisition.requires_std
        val = self.surrogate_model.evaluate(x, std, calc_gradient, calc_hessian)

        # evaluate out['F/dF/hF'] by certain acquisition function
        out['F'], out['dF'], out['hF'] = self.acquisition.evaluate(val, calc_gradient, calc_hessian)
        
        # multiply a +1/-1 factor for converting maximization to minimization
        factor = (2 * self.real_problem.minimize - 1)
        for key in ['F', 'dF', 'hF']:
            if out[key] is not None:
                out[key] *= factor
        
        # evaluate constraints by real problem
        x_ori = self.transformation.undo(x)
        out['G'] = self.real_problem.evaluate_constraint(x_ori)

    def evaluate(self, X, *args, return_values_of="auto", return_as_dictionary=False, **kwargs):
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
        assert self.surrogate_model is not None, 'surrogate model must be set first before evaluation'

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

        # handle hF (hessian) computation, which is not supported by Pymoo
        calc_hessian = (type(return_values_of) == list and 'hF' in return_values_of)

        # set in the dictionary if the output should be calculated - can be used for the gradient
        out = {}
        for val in return_values_of:
            out[val] = None

        # calculate the output array - either elementwise or not. also consider the gradient
        self._evaluate(X, out, *args, calc_gradient=calc_gradient, calc_hessian=calc_hessian, **kwargs)
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

