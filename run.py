import numpy as np
import pandas as pd
from argparse import ArgumentParser
from multiprocessing import Process, Lock
from problems.common import build_problem, generate_initial_samples
from pymoo.performance_indicator.hv import Hypervolume
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import load_config, check_pareto, find_pareto_front
from system.simple_gui import SimpleGUI


def generate_initial_dataframe(X, Y, hv):
    data = {}
    sample_len = len(X)
    n_var, n_obj = X.shape[1], Y.shape[1]

    # id
    data['id'] = np.arange(sample_len, dtype=int)

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

    # pareto optimality
    data['is_pareto'] = check_pareto(Y)

    return pd.DataFrame(data=data)


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
    n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']

    # build problem
    problem, true_pfront, X, Y = build_problem(problem_cfg, get_pfront=True, get_init_samples=True)
    ref_point = problem.ref_point
    hv = Hypervolume(ref_point=ref_point) # hypervolume calculator

    # generate initial data csv file
    dataframe = generate_initial_dataframe(X, Y, hv)
    dataframe.to_csv(data_path, index=False)

    # main process of optimization and evaluation
    def optimize_process(lock, worker_id):
        print(f'worker {worker_id} started')

        for _ in range(general_cfg['n_iter']):

            # read file
            with lock:
                old_df = pd.read_csv(data_path)

            X = old_df[[f'x{i + 1}' for i in range(n_var)]].to_numpy()
            Y = old_df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()

            # run optimization
            result_df = optimize(config, X, Y, seed=worker_id)
            # run evaluation
            result_df = evaluate(problem, result_df)
            
            # write file
            with lock:
                old_df = pd.read_csv(data_path)
                last_id = old_df['id'].iloc[-1]
                ids = np.arange(len(result_df), dtype=int) + last_id + 1
                result_df['id'] = ids
                new_df = pd.concat([old_df, result_df], ignore_index=True)
                Y = new_df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
                new_df.loc[len(new_df)-len(result_df):len(new_df), 'hv'] = hv.calc(Y)
                new_df['is_pareto'] = check_pareto(Y)
                new_df.to_csv(data_path, index=False)

        print(f'worker {worker_id} ended')

    def optimize_command():
        global worker_id
        Process(target=optimize_process, args=(lock, worker_id)).start()
        worker_id += 1

    def load_command():
        with lock:
            df = pd.read_csv(data_path)
        Y = df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
        is_pareto = df['is_pareto'].to_numpy()
        hv_value = df['hv'].to_numpy()
        return Y, Y[is_pareto], hv_value

    # gui
    gui = SimpleGUI(config, optimize_command, load_command)
    gui.init_draw(true_pfront)
    gui.mainloop()


if __name__ == '__main__':
    main()