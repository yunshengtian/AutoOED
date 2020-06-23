import numpy as np
from problems import Problem

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

    def evaluate(self, *args, return_values_of="auto", **kwargs):
        assert self.surrogate_model is not None, 'surrogate model must be set first before evaluation'
        
        # handle hF (hessian) computation, which is not supported by Pymoo
        calc_hessian = (type(return_values_of) == list and 'hF' in return_values_of)
        
        return super().evaluate(*args, return_values_of=return_values_of, calc_hessian=calc_hessian, **kwargs)

    def _evaluate(self, x, out, *args, calc_gradient=False, calc_hessian=False, **kwargs):
        # evaluate value by surrogate model
        std = self.acquisition.requires_std
        val = self.surrogate_model.evaluate(x, std, calc_gradient, calc_hessian)

        # evaluate out['F/dF/hF'] by certain acquisition function
        out['F'], out['dF'], out['hF'] = self.acquisition.evaluate(val, calc_gradient, calc_hessian)
        
        # evaluate constraints by real problem
        x_ori = self.transformation.undo(x)
        out['G'], out['CV'], out['feasible'] = self.real_problem.evaluate(x_ori, return_values_of=['G', 'CV', 'feasible'], requires_F=False)
