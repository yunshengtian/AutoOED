'''
Run with local tkinter GUI and sqlite database for data storage
'''

import numpy as np
import pandas as pd
from argparse import ArgumentParser
from multiprocessing import Process
from pymoo.performance_indicator.hv import Hypervolume
from problems.common import build_problem
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import load_config
from system.database import db_create, db_init, db_insert, db_multiple_select
from system.gui_local import LocalGUI


# global index count for parallel workers
worker_id = 0


def main():

    parser = ArgumentParser()
    parser.add_argument('--config-path', type=str, default='config/example_config.yml')
    parser.add_argument('--data-path', type=str, default='data.db')
    args = parser.parse_args()
    config_path, data_path = args.config_path, args.data_path

    # load config
    config = load_config(config_path)
    general_cfg, problem_cfg = config['general'], config['problem']

    # build problem
    problem, true_pfront, X, Y = build_problem(problem_cfg, get_pfront=True, get_init_samples=True)
    n_var, n_obj, ref_point = problem.n_var, problem.n_obj, problem.ref_point
    hv = Hypervolume(ref_point=ref_point) # hypervolume calculator

    # init database
    db_create(data_path, config)
    db_init(data_path, hv, X, Y)

    def optimize_worker(worker_id):
        '''
        Worker process of optimization algorithm execution
        '''
        print(f'worker {worker_id} started')

        # run several iterations of algorithm
        for _ in range(general_cfg['n_iter']):

            # read current data from database
            select_result = db_multiple_select(data_path, 
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
            db_insert(data_path, hv, X, Y, Y_expected, Y_uncertainty)

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
        select_result = db_multiple_select(data_path, 
            keys_list=[[f'f{i + 1}' for i in range(n_obj)], ['hv'], ['is_pareto']],
            dtype_list=[float, float, bool])
        Y, hv_value, is_pareto = select_result[0], select_result[1].squeeze(), select_result[2].squeeze()
        return Y, Y[is_pareto], hv_value

    # gui
    gui = LocalGUI(config, optimize_command, load_command)
    gui.init_draw(true_pfront)
    gui.mainloop()


if __name__ == '__main__':
    main()