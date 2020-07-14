import numpy as np
import pandas as pd


def evaluate(problem, X_next):
    Y_next = np.column_stack(problem.evaluate_performance(X_next))
    return Y_next