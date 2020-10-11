import numpy as np
from pymoo.model.evaluator import Evaluator

'''
Evaluate a scalar value of a multi-objective problem by scalarization (decomposition)
'''

class ScalarizedEvaluator(Evaluator):

    def __init__(self, *args, decomposition, weights, **kwargs):
        super().__init__(*args, **kwargs)
        self.decomposition = decomposition
        self.weights = weights
        self.ideal_point = None

    def _eval(self, problem, pop, **kwargs):

        out = problem.evaluate(pop.get("X"),
                               return_values_of=self.evaluate_values_of,
                               return_as_dictionary=True,
                               **kwargs)

        for key, val in out.items():
            if val is None:
                continue
            else:
                if key == 'F':
                    if self.ideal_point is None:
                        self.ideal_point = np.min(val, axis=0)
                    else:
                        self.ideal_point = np.minimum(self.ideal_point, np.min(val, axis=0))
                    val = self.decomposition.do(val, self.weights, ideal_point=self.ideal_point)
                    if len(val) > 1: val = np.expand_dims(val, 1)
                pop.set(key, val)