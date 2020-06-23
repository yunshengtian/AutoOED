import numpy as np
import autograd
from autograd.numpy import row_stack
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool
from pymoo.model.problem import Problem as PymooProblem
from pymoo.model.problem import at_least2d, evaluate_in_parallel

'''
Problem definition built upon Pymoo's Problem class, added some custom features
'''

class Problem(PymooProblem):
    
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
        # NOTE: pass return_values_of to evaluation function to avoid unnecessary computation
        if self.elementwise_evaluation:
            out = self._evaluate_elementwise(X, calc_gradient, out, *args, return_values_of=return_values_of, **kwargs)
        else:
            out = self._evaluate_batch(X, calc_gradient, out, *args, return_values_of=return_values_of, **kwargs)

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

    def _evaluate_batch(self, X, calc_gradient, out, *args, **kwargs):
        # NOTE: to use self-calculated dF (gradient) rather than autograd.numpy, which is not supported by Pymoo
        self._evaluate(X, out, *args, calc_gradient=calc_gradient, **kwargs)
        at_least2d(out)
        return out

    def _evaluate_elementwise(self, X, calc_gradient, out, *args, **kwargs):
        # NOTE: to use self-calculated dF (gradient) rather than autograd.numpy, which is not supported by Pymoo
        ret = []
        def func(_x):
            _out = {}
            self._evaluate(_x, _out, *args, calc_gradient=calc_gradient, **kwargs)
            return _out
        parallelization = self.parallelization
        if not isinstance(parallelization, (list, tuple)):
            parallelization = [self.parallelization]
        _type = parallelization[0]
        if len(parallelization) >= 1:
            _params = parallelization[1:]
        # just serialize evaluation
        if _type is None:
            [ret.append(func(x)) for x in X]
        elif _type == "threads":
            if len(_params) == 0:
                n_threads = cpu_count() - 1
            else:
                n_threads = _params[0]
            with ThreadPool(n_threads) as pool:
                params = []
                for k in range(len(X)):
                    params.append([X[k], calc_gradient, self._evaluate, args, kwargs])
                ret = np.array(pool.starmap(evaluate_in_parallel, params))
        elif _type == "dask":
            if len(_params) != 2:
                raise Exception("A distributed client objective is need for using dask. parallelization=(dask, "
                                "<client>, <function>).")
            else:
                client, fun = _params
            jobs = []
            for k in range(len(X)):
                jobs.append(client.submit(fun, X[k]))
            ret = [job.result() for job in jobs]
        else:
            raise Exception("Unknown parallelization method: %s (None, threads, dask)" % self.parallelization)
        # stack all the single outputs together
        for key in ret[0].keys():
            out[key] = row_stack([ret[i][key] for i in range(len(ret))])
        return out

    def __str__(self):
        return '========== Problem Definition ==========\n' + super().__str__()