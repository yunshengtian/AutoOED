import numpy as np
import pandas as pd


def evaluate(problem, X_next_df):
    n_var, n_obj = problem.n_var, problem.n_obj
    X_next = X_next_df[[f'x{i + 1}' for i in range(n_var)]].to_numpy()
    Y_next = np.column_stack(problem.evaluate_performance(X_next))
    XY_next_df = X_next_df.copy()
    for i in range(n_obj):
        XY_next_df[f'f{i + 1}'] = Y_next[:, i]
    return XY_next_df