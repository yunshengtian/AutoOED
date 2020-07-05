'''
Run with local tkinter GUI and csv file for data storage
'''

import numpy as np
import pandas as pd
from argparse import ArgumentParser
from multiprocessing import Process, Lock
from pymoo.performance_indicator.hv import Hypervolume
from problems.common import build_problem
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import load_config, check_pareto, calc_pred_error
from system.gui_local import LocalGUI


def generate_initial_dataframe(X, Y, hv):
    '''
    Generate initial dataframe from initial X, Y and hypervolume
    '''
    data = {}
    sample_len = len(X)
    n_var, n_obj = X.shape[1], Y.shape[1]

    # design variables
    for i in range(n_var):
        data[f'x{i + 1}'] = X[:, i]

    # prediction and uncertainty
    for i in range(n_obj):
        data[f'f{i + 1}'] = Y[:, i]
    for i in range(n_obj):
        data[f'expected_f{i + 1}'] = np.zeros(sample_len)
    for i in range(n_obj):
        data[f'uncertainty_f{i + 1}'] = np.zeros(sample_len)

    # hypervolume
    data['hv'] = hv.calc(Y)

    # prediction error
    data['pred_error'] = np.ones(sample_len) * 100

    # pareto optimality
    data['is_pareto'] = check_pareto(Y)

    return pd.DataFrame(data=data)


# global index count for parallel workers
worker_id = 0


def main():

    parser = ArgumentParser()
    parser.add_argument('--config-path', type=str, default='config/example_config.yml')
    parser.add_argument('--data-path', type=str, default='data.csv')
    args = parser.parse_args()
    config_path, data_path = args.config_path, args.data_path

    # multiprocessing lock
    lock = Lock()

    # load config
    config = load_config(config_path)
    general_cfg, problem_cfg = config['general'], config['problem']

    # build problem
    problem, true_pfront, X, Y = build_problem(problem_cfg, get_pfront=True, get_init_samples=True)
    n_var, n_obj, ref_point = problem.n_var, problem.n_obj, problem.ref_point
    hv = Hypervolume(ref_point=ref_point) # hypervolume calculator

    # generate initial data csv file
    dataframe = generate_initial_dataframe(X, Y, hv)
    dataframe.to_csv(data_path)
    n_init_sample = len(X)

    def optimize_worker(worker_id):
        '''
        Worker process of optimization algorithm execution
        '''
        print(f'worker {worker_id} started')

        # run several iterations of algorithm
        for _ in range(general_cfg['n_iter']):

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

        print(f'worker {worker_id} ended')

    def optimize_command():
        '''
        Optimization command linked to GUI button click
        '''
        global worker_id
        Process(target=optimize_worker, args=(worker_id,)).start()
        worker_id += 1

    def load_command():
        '''
        Data loading command linked to GUI figure refresh
        '''
        with lock:
            df = pd.read_csv(data_path, index_col=0)
        Y = df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
        hv_value = df['hv'].to_numpy()
        pred_error = df['pred_error'].to_numpy()
        is_pareto = df['is_pareto'].to_numpy()
        return Y, Y[is_pareto], hv_value, pred_error

    # gui
    gui = LocalGUI(config, optimize_command, load_command)
    gui.init_draw(true_pfront)
    gui.mainloop()


if __name__ == '__main__':
    main()