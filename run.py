import numpy as np
import pandas as pd
from multiprocessing import Process, Lock
from problems.common import build_problem, generate_initial_samples
from optimize import optimize, process_args
from evaluate import evaluate
import tkinter
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2Tk)
from matplotlib.backend_bases import key_press_handler


def generate_initial_dataframe(X, Y, n_var, n_obj):
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
        data[f'Expected_f{i + 1}'] = np.zeros(sample_len)
    for i in range(n_obj):
        data[f'Uncertainty_f{i + 1}'] = np.zeros(sample_len)

    return pd.DataFrame(data=data)


worker_id = 0


def main():

    # gui
    root = tkinter.Tk()
    fig = plt.figure()
    ax = fig.add_subplot(111)

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    widget = canvas.get_tk_widget()
    widget.pack(side=tkinter.TOP, fill=tkinter.BOTH, expand=1)

    lock = Lock()

    # load config
    args, _ = process_args('experiment_config.yml')

    # build problem
    problem, true_pfront = build_problem(args.problem, args.n_var, args.n_obj)

    # generate initial samples
    X, Y = generate_initial_samples(problem, args.n_init_sample)
    dataframe = generate_initial_dataframe(X, Y, args.n_var, args.n_obj)
    dataframe.to_csv('data.csv', index=False)

    sc = ax.scatter(*Y.T, color='blue', s=10)
    if true_pfront is not None:
        ax.scatter(*true_pfront.T, color='gray', s=5)

    def optimize_process(lock, worker_id):
        print(f'worker {worker_id} started')

        old_df = pd.read_csv('data.csv')
        X = old_df[[f'x{i + 1}' for i in range(args.n_var)]].to_numpy()
        Y = old_df[[f'f{i + 1}' for i in range(args.n_obj)]].to_numpy()

        # run optimization
        result_df = optimize(problem, X, Y, seed=worker_id)
        # run evaluation
        result_df = evaluate(problem, result_df)
        
        lock.acquire()

        # write file
        old_df = pd.read_csv('data.csv')
        last_id = old_df['id'].iloc[-1]
        ids = np.arange(len(result_df), dtype=int) + last_id + 1
        result_df['id'] = ids
        new_df = pd.concat([old_df, result_df])
        new_df.to_csv('data.csv', index=False)

        lock.release()

        print(f'worker {worker_id} ended')

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

    def redraw():
        df = pd.read_csv('data.csv')
        Y = df[[f'f{i + 1}' for i in range(args.n_obj)]].to_numpy()
        x, y = Y.T[0], Y.T[1]
        sc.set_offsets(np.c_[x, y])
        fig.canvas.draw()
        root.after(100, redraw)

    root.after(100, redraw)

    tkinter.mainloop()


if __name__ == '__main__':
    main()