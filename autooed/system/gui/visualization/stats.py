import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

from autooed.system.gui.widgets.utils.figure import embed_figure
from autooed.system.params import FIGURE_DPI


class VizStatsView:

    def __init__(self, root_view, problem_cfg):
        self.root_view = root_view
        self.n_obj, self.obj_name = problem_cfg['n_obj'], problem_cfg['obj_name']

        # figure placeholder in GUI
        self.fig = plt.figure(dpi=FIGURE_DPI)
        grid = plt.GridSpec(self.n_obj, 2)

        self.ax = {}
        self.line = {}

        # hypervolume curve figure
        self.ax['hv'] = self.fig.add_subplot(grid[:, 0])
        if self.n_obj == 1:
            self.ax['hv'].set_title('Optimum')
            self.ax['hv'].set_xlabel('Evaluations')
            self.ax['hv'].set_ylabel('Optimum')
        else:
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

    def redraw(self, hypervolume, model_error, n_init_sample):
        # hypervolume
        if len(hypervolume) > 0:
            self.line['hv'].set_data(np.arange(len(hypervolume)), hypervolume)
            self.ax['hv'].relim()
            self.ax['hv'].autoscale_view()
            if self.n_obj == 1:
                self.ax['hv'].set_title('Optimum: %.4f' % hypervolume[-1])
            else:
                self.ax['hv'].set_title('Hypervolume: %.4f' % hypervolume[-1])

        # model prediction error
        if len(model_error) > 0:
            for i in range(self.n_obj):
                self.line[f'error_{i}'].set_data(np.arange(len(model_error)) + n_init_sample, model_error[:, i])
                self.ax[f'error_{i}'].relim()
                self.ax[f'error_{i}'].autoscale_view()
                self.ax[f'error_{i}'].set_title(f'Model Prediction Error of {self.obj_name[i]}: %.4f' % model_error[-1, i])

        self.fig.canvas.draw()

    def save_hv_figure(self, path, title=None):
        fig = plt.figure()
        ax = fig.add_subplot(111)

        if title is None:
            ax.set_title(self.ax['hv'].get_title())
        else:
            ax.set_title(title)
        
        ax.set_xlabel(self.ax['hv'].get_xlabel())
        ax.set_ylabel(self.ax['hv'].get_ylabel())
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))

        ax.plot(*self.line['hv'].get_data())

        fig.tight_layout()
        fig.savefig(path)
    
    def save_error_figure(self, path, title=None):
        fig = plt.figure()

        for i in range(self.n_obj):
            ax = fig.add_subplot(self.n_obj, 1, i + 1)

            if title is None:
                ax.set_title(self.ax[f'error_{i}'].get_title())
            elif title != '':
                ax.set_title(title + f' of {self.obj_name[i]}')

            ax.set_xlabel(self.ax[f'error_{i}'].get_xlabel())
            ax.set_ylabel(self.ax[f'error_{i}'].get_ylabel())
            ax.xaxis.set_major_locator(MaxNLocator(integer=True))

            ax.plot(*self.line[f'error_{i}'].get_data())
        
        fig.tight_layout()
        fig.savefig(path)


class VizStatsController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.problem_cfg = self.root_controller.problem_cfg
        self.agent = self.root_controller.agent

        self.view = VizStatsView(self.root_view, self.problem_cfg)

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.view.fig, self.root_view.frame_stat)

        # refresh figure
        self.view.fig.tight_layout()
        self.redraw()

    def redraw(self):
        '''
        Redraw hypervolume and prediction error curves
        '''
        hypervolume = self.agent.load_hypervolume()
        model_error = self.agent.load_model_error()
        n_init_sample = self.agent.get_n_init_sample()

        self.view.redraw(hypervolume, model_error, n_init_sample)

    def save_hv_figure(self, path, title=None):
        self.view.save_hv_figure(path, title=title)

    def save_error_figure(self, path, title=None):
        self.view.save_error_figure(path, title=title)