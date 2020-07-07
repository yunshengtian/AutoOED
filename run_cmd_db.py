'''
Run with local tkinter GUI and SQLite database for data storage, receiving command line input for config and data paths
'''

import numpy as np
import pandas as pd
from time import time
from argparse import ArgumentParser
from multiprocessing import Process
from problems.common import build_problem
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import load_config
from system.database import Database
from system.gui_simple import SimpleGUI


# global index count for parallel workers
worker_id = 0


def main():

    parser = ArgumentParser()
    parser.add_argument('--config-path', type=str, default='config/example_config.yml')
    parser.add_argument('--data-path', type=str, default='data.db')
    args = parser.parse_args()
    config_path, data_path = args.config_path, args.data_path
    start_time = time()

    # load config
    config = load_config(config_path)
    general_cfg, problem_cfg = config['general'], config['problem']

    # build problem
    problem, true_pfront, X, Y = build_problem(problem_cfg, get_pfront=True, get_init_samples=True)
    n_var, n_obj = problem.n_var, problem.n_obj

    # init database
    db = Database(data_path, problem)
    db.init(X, Y)

    def optimize_worker(worker_id):
        '''
        Worker process of optimization algorithm execution
        '''
        print(f'worker {worker_id} started, time: {time() - start_time}')

        # run several iterations of algorithm
        for _ in range(general_cfg['n_iter']):

            # read current data from database
            select_result = db.select_multiple(
                keys_list=[[f'x{i + 1}' for i in range(n_var)], [f'f{i + 1}' for i in range(n_obj)]])
            X, Y = select_result[0], select_result[1]

            # run optimization
            result_df = optimize(config, X, Y, seed=worker_id)
            # run evaluation
            result_df = evaluate(problem, result_df)
            
            # write optimized data to database
            X = result_df[[f'x{i + 1}' for i in range(n_var)]].to_numpy()
            Y = result_df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
            Y_expected = result_df[[f'expected_f{i + 1}' for i in range(n_obj)]].to_numpy()
            Y_uncertainty = result_df[[f'uncertainty_f{i + 1}' for i in range(n_obj)]].to_numpy()
            db.insert(X, Y, Y_expected, Y_uncertainty)

        print(f'worker {worker_id} ended, time: {time() - start_time}')

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
        select_result = db.select_multiple(
            keys_list=[[f'f{i + 1}' for i in range(n_obj)] + ['hv', 'pred_error'], ['is_pareto']],
            dtype_list=[float, bool])
        Y, hv_value, pred_error, is_pareto = \
            select_result[0][:, :n_obj], select_result[0][:, n_obj].squeeze(), select_result[0][:, n_obj + 1].squeeze(), select_result[1].squeeze()
        return Y, Y[is_pareto], hv_value, pred_error

    def quit_command():
        '''
        Command triggered when GUI quit
        '''
        db.quit()

    # gui
    gui = SimpleGUI(config, optimize_command, load_command, quit_command)
    gui.init_draw(true_pfront)
    gui.mainloop()


if __name__ == '__main__':
    main()