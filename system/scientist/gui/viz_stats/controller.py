import numpy as np
from system.gui.utils.figure import embed_figure
from system.server.utils import calc_hypervolume, calc_pred_error
from .view import StatsView


class StatsController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = StatsView(self.root_view)

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.view.fig, self.root_view.frame_stat)

        # set values from root
        self.config, self.problem_cfg = self.root_controller.config, self.root_controller.problem_cfg
        self.data_agent = self.root_controller.data_agent

        # load from database
        Y = self.data_agent.load('Y')
        self.n_init_sample = len(Y)

        # plot hypervolume curve
        hv_value = np.full(self.n_init_sample, calc_hypervolume(Y, self.config['problem']['ref_point'], self.problem_cfg['minimize']))
        self.line_hv = self.view.ax1.plot(list(range(self.n_init_sample)), hv_value)[0]
        self.view.ax1.set_title('Hypervolume: %.4f' % hv_value[-1])

        # plot prediction error curve
        self.line_error = self.view.ax2.plot([], [])[0]

        # refresh figure
        self.view.fig.tight_layout()
        self.view.fig.canvas.draw()

    def set_config(self, config=None, problem_cfg=None):
        if config is not None:
            self.config = config
        if problem_cfg is not None:
            self.problem_cfg = problem_cfg

    def redraw(self):
        '''
        Redraw hypervolume and prediction error curves
        '''
        # load data
        Y, Y_expected = self.data_agent.load(['Y', 'Y_expected'])

        n_sample = len(Y)
        if n_sample == self.n_init_sample:
            return

        ref_point = self.config['problem']['ref_point']
        minimize = self.problem_cfg['minimize']

        # hypervolume
        line_hv_y = self.line_hv.get_ydata()
        hv_value = calc_hypervolume(Y, ref_point, minimize)
        hv_value = np.concatenate([line_hv_y, np.full(n_sample - len(line_hv_y), hv_value)])
        self.line_hv.set_data(np.arange(n_sample), hv_value)
        self.view.ax1.relim()
        self.view.ax1.autoscale_view()
        self.view.ax1.set_title('Hypervolume: %.4f' % hv_value[-1])

        # prediction error
        line_error_y = self.line_error.get_ydata()
        pred_error = calc_pred_error(Y[self.n_init_sample:], Y_expected[self.n_init_sample:])
        pred_error = np.concatenate([line_error_y, np.full(n_sample - self.n_init_sample - len(line_error_y), pred_error)])
        self.line_error.set_data(np.arange(self.n_init_sample, n_sample), pred_error)
        self.view.ax2.relim()
        self.view.ax2.autoscale_view()
        self.view.ax2.set_title('Model Prediction Error: %.4f' % pred_error[-1])