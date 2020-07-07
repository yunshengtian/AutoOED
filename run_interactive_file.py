'''
Run with local tkinter GUI and csv file for data storage, having more GUI interactions for configurations, control and logging
'''

import pandas as pd
from multiprocessing import Lock
from pymoo.performance_indicator.hv import Hypervolume
from problems.common import build_problem
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import check_pareto, calc_pred_error, generate_initial_dataframe
from system.gui_interactive import InteractiveGUI


# multiprocessing lock
lock = Lock()


def init_command(config, data_path):
    '''
    Problem initialization command linked to GUI button click
    '''
    # build problem
    problem, true_pfront, X, Y = build_problem(config['problem'], get_pfront=True, get_init_samples=True)
    hv = Hypervolume(ref_point=problem.ref_point) # hypervolume calculator

    # generate initial data csv file
    dataframe = generate_initial_dataframe(X, Y, hv)
    dataframe.to_csv(data_path)

    return problem, true_pfront


def optimize_command(worker_id, config, data_path, problem):
    '''
    Optimization command linked to GUI button click
    Worker process of optimization algorithm execution
    '''
    n_var, n_obj = problem.n_var, problem.n_obj
    n_init_sample = config['problem']['n_init_sample']
    hv = Hypervolume(ref_point=problem.ref_point)

    # run several iterations of algorithm
    for _ in range(config['general']['n_iter']):

        # read current data from file
        with lock:
            old_df = pd.read_csv(data_path, index_col=0)
        X = old_df[[f'x{i + 1}' for i in range(n_var)]].to_numpy()
        Y = old_df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()

        # run optimization
        result_df = optimize(config, X, Y, seed=worker_id)
        # run evaluation
        result_df = evaluate(problem, result_df)
        
        # write optimized data to file
        with lock:
            old_df = pd.read_csv(data_path, index_col=0)
            new_df = pd.concat([old_df, result_df], ignore_index=True)
            Y = new_df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
            Y_expected = new_df[[f'expected_f{i + 1}' for i in range(n_obj)]].to_numpy()
            new_idx_range = slice(len(new_df)-len(result_df), len(new_df))
            new_df.loc[new_idx_range, 'hv'] = hv.calc(Y)
            new_df.loc[new_idx_range, 'pred_error'] = calc_pred_error(Y[n_init_sample:], Y_expected[n_init_sample:])
            new_df['is_pareto'] = check_pareto(Y)
            new_df.to_csv(data_path)


def load_command(config, data_path):
    '''
    Data loading command linked to GUI figure refresh
    '''
    n_obj = config['problem']['n_obj']

    with lock:
        df = pd.read_csv(data_path, index_col=0)
    Y = df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
    hv_value = df['hv'].to_numpy()
    pred_error = df['pred_error'].to_numpy()
    is_pareto = df['is_pareto'].to_numpy()

    return Y, Y[is_pareto], hv_value, pred_error


def main():
    gui = InteractiveGUI('csv', init_command, optimize_command, load_command)
    gui.mainloop()


if __name__ == '__main__':
    main()