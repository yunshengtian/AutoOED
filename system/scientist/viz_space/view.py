from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
from system.gui.utils.radar import radar_factory

import tkinter as tk
from system.gui.utils.grid import grid_configure
from system.gui.utils.figure import embed_figure


class VizSpaceView:

    def __init__(self, root_view, problem_cfg):
        self.root_view = root_view

        n_var, n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
        var_name, obj_name = problem_cfg['var_name'], problem_cfg['obj_name']
        var_lb, var_ub = problem_cfg['var_lb'], problem_cfg['var_ub']

        # figure placeholder in GUI
        self.fig = plt.figure(figsize=(10, 5))
        self.gs = GridSpec(1, 2, figure=self.fig, width_ratios=[3, 2])

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.fig, self.root_view.frame_plot)

        # performance space figure
        if n_obj == 2:
            self.ax1 = self.fig.add_subplot(self.gs[0])
        elif n_obj == 3:
            self.ax1 = self.fig.add_subplot(self.gs[0], projection='3d')
        else:
            raise NotImplementedError
        self.ax1.set_title('Performance Space')
        self.ax1.set_xlabel(obj_name[0])
        self.ax1.set_ylabel(obj_name[1])
        if n_obj == 3:
            self.ax1.set_zlabel(obj_name[2])

        # design space figure
        if n_var > 2:
            self.theta = radar_factory(n_var)
            self.ax2 = self.fig.add_subplot(self.gs[1], projection='radar')
            self.ax2.set_xticks(self.theta)
            self.ax2.set_varlabels(var_name)
            self.ax2.set_yticklabels([])
            self.ax2.set_title('Design Space', position=(0.5, 1.1))
            self.ax2.set_ylim(0, 1)
        else:
            self.ax2 = self.fig.add_subplot(self.gs[1])
            for spine in self.ax2.spines.values():
                spine.set_visible(False)
            self.ax2.get_xaxis().set_ticks([])
            self.ax2.get_yaxis().set_ticks([])
            self.xticks = [0] if n_var == 1 else [-1, 1]
            self.ax2.bar(self.xticks, [1] * n_var, color='g', alpha=0.2)
            self.ax2.set_xticks(self.xticks)
            self.text_lb = [None] * n_var
            self.text_ub = [None] * n_var
            for i in range(n_var):
                self.text_lb[i] = self.ax2.text(self.xticks[i] - 0.5, 0, str(var_lb[i]), horizontalalignment='right', verticalalignment='center')
                self.text_ub[i] = self.ax2.text(self.xticks[i] - 0.5, 1, str(var_ub[i]), horizontalalignment='right', verticalalignment='center')
            self.ax2.set_xticklabels(var_name)
            self.ax2.set_title('Design Space')
            self.ax2.set_xlim(-3, 3)
            self.ax2.set_ylim(0, 1.04)

        # configure slider widget
        frame_slider = tk.Frame(master=self.root_view.frame_plot)
        frame_slider.grid(row=2, column=0, padx=5, pady=0, sticky='EW')
        grid_configure(frame_slider, [0], [1])
        
        label_iter = tk.Label(master=frame_slider, text='Iteration:')
        label_iter.grid(row=0, column=0, sticky='EW')
        self.curr_iter = tk.IntVar()
        self.scale_iter = tk.Scale(master=frame_slider, orient=tk.HORIZONTAL, variable=self.curr_iter, from_=0, to=0)
        self.scale_iter.grid(row=0, column=1, sticky='EW')
