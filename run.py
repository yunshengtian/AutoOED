import numpy as np
import pandas as pd
from argparse import ArgumentParser
from multiprocessing import Process, Lock
from problems.common import build_problem, generate_initial_samples
from pymoo.performance_indicator.hv import Hypervolume
from system.optimize import optimize
from system.evaluate import evaluate
from system.utils import load_config, check_pareto, find_pareto_front

import tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler


def generate_initial_dataframe(X, Y, n_var, n_obj, hv_value):
    data = {}
    sample_len = len(X)

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
    data['hv'] = hv_value

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

    # gui
    root = tkinter.Tk()
    fig = plt.figure(figsize=(12, 6))
    ax1 = fig.add_subplot(121)
    ax1.set_title('Performance Space')
    ax2 = fig.add_subplot(122)
    ax2.set_xlabel('Evaluations')
    ax2.set_ylabel('Hypervolume')

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    # multiprocessing lock
    lock = Lock()

    # load config
    config = load_config(config_path)
    general_cfg, problem_cfg = config['general'], config['problem']
    n_init_sample = general_cfg['n_init_sample']
    n_var, n_obj, ref_point = problem_cfg['n_var'], problem_cfg['n_obj'], problem_cfg['ref_point']
    f1_name, f2_name = problem_cfg['obj_name']
    ax1.set_xlabel(f1_name)
    ax1.set_ylabel(f2_name)

    # build problem
    problem, true_pfront = build_problem(problem_cfg)

    # generate initial samples & reference point
    X, Y = generate_initial_samples(problem, n_init_sample)
    if ref_point is None:
        ref_point = np.max(Y, axis=0)
        problem.set_ref_point(ref_point)
    hv = Hypervolume(ref_point=ref_point)
    hv_value = hv.calc(Y)
    dataframe = generate_initial_dataframe(X, Y, n_var, n_obj, hv_value)
    dataframe.to_csv(data_path, index=False)
    ax2.set_title('Hypervolume: %.2f' % hv_value)

    # draw initial figures
    if true_pfront is not None:
        ax1.scatter(*true_pfront.T, color='gray', s=5, label='True Pareto front')
    sc1 = ax1.scatter(*Y.T, color='blue', s=10, label='Evaluated')
    sc2 = ax1.scatter(*find_pareto_front(Y).T, color='red', s=10, label='Approximated Pareto front')
    ax1.legend(loc='upper right')
    line = ax2.plot(np.arange(n_init_sample, dtype=int), np.full(n_init_sample, hv_value))[0]

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

    # gui events
    def optimize_worker():
        global worker_id
        Process(target=optimize_process, args=(lock, worker_id)).start()
        worker_id += 1
    
    button = tkinter.Button(master=root, text="optimize", command=optimize_worker)
    button.pack(side=tkinter.BOTTOM)

    def gui_quit():
        root.quit()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", gui_quit)

    # refresh figures
    def redraw():
        with lock:
            df = pd.read_csv(data_path)

        # refresh performance space
        Y = df[[f'f{i + 1}' for i in range(n_obj)]].to_numpy()
        is_pareto = df['is_pareto'].to_numpy()
        sc1.set_offsets(Y)
        sc2.set_offsets(Y[is_pareto])

        # refresh hypervolume
        hv_value = df['hv'].to_numpy()
        line.set_data(np.arange(len(Y), dtype=int), hv_value)
        ax2.relim()
        ax2.autoscale_view()
        ax2.set_title('Hypervolume: %.2f' % hv_value[-1])

        fig.canvas.draw()
        root.after(100, redraw)

    root.after(100, redraw)

    tkinter.mainloop()


if __name__ == '__main__':
    main()