import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator
import numpy as np


class VizStatsView:

    def __init__(self, root_view, problem_cfg):
        self.root_view = root_view
        self.n_obj, self.obj_name = problem_cfg['n_obj'], problem_cfg['obj_name']

        # figure placeholder in GUI
        self.fig = plt.figure(figsize=(10, 5))
        grid = plt.GridSpec(self.n_obj, 2)

        self.ax = {}
        self.line = {}

        # hypervolume curve figure
        self.ax['hv'] = self.fig.add_subplot(grid[:, 0])
        self.ax['hv'].set_title('Hypervolume')
        self.ax['hv'].set_xlabel('Evaluations')
        self.ax['hv'].set_ylabel('Hypervolume')
        self.ax['hv'].xaxis.set_major_locator(MaxNLocator(integer=True))
        self.line['hv'] = self.ax['hv'].plot([], [])[0]

        # model prediction error figure
        for i in range(self.n_obj):
            self.ax[f'error_{i}'] = self.fig.add_subplot(grid[i, 1])
            self.ax[f'error_{i}'].set_title(f'Model Prediction Error of {self.obj_name[i]}')
            self.ax[f'error_{i}'].set_xlabel('Evaluations')
            self.ax[f'error_{i}'].set_ylabel('Error')
            self.ax[f'error_{i}'].xaxis.set_major_locator(MaxNLocator(integer=True))
            self.line[f'error_{i}'] = self.ax[f'error_{i}'].plot([], [])[0]

    def redraw(self, hypervolume, model_error):
        # hypervolume
        if len(hypervolume) > 0:
            self.line['hv'].set_data(np.arange(len(hypervolume)), hypervolume)
            self.ax['hv'].relim()
            self.ax['hv'].autoscale_view()
            self.ax['hv'].set_title('Hypervolume: %.4f' % hypervolume[-1])

        # model prediction error
        if len(model_error) > 0:
            for i in range(self.n_obj):
                self.line[f'error_{i}'].set_data(np.arange(len(model_error)), model_error[:, i])
                self.ax[f'error_{i}'].relim()
                self.ax[f'error_{i}'].autoscale_view()
                self.ax[f'error_{i}'].set_title(f'Model Prediction Error of {self.obj_name[i]}: %.4f' % model_error[-1, i])

        self.fig.canvas.draw()