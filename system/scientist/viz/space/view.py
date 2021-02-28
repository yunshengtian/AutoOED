import numpy as np
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

        self.n_var, self.n_obj = problem_cfg['n_var'], problem_cfg['n_obj']
        self.var_name, self.obj_name = problem_cfg['var_name'], problem_cfg['obj_name']
        var_type = problem_cfg['type']

        # compute lower and upper bound for design space radar plot
        if var_type in ['continuous', 'integer']:
            var_lb, var_ub = problem_cfg['var_lb'], problem_cfg['var_ub']
            if type(var_lb) in [int, float]:
                var_lb = [var_lb] * self.n_var
            if type(var_ub) in [int, float]:
                var_ub = [var_ub] * self.n_var
        elif var_type == 'binary':
            var_lb, var_ub = [0] * self.n_var, [1] * self.n_var
        elif var_type == 'categorical':
            var_lb = [0] * self.n_var
            if 'var' in problem_cfg:
                var_ub = []
                for var_info in problem_cfg['var'].values():
                    var_ub.append(len(var_info['choices']))
            else:
                var_ub = [len(problem_cfg['var_choices'])] * self.n_var
        elif var_type == 'mixed':
            var_lb, var_ub = [], []
            var_type_list = []
            for var_info in problem_cfg['var'].values():
                var_type_list.append(var_info['type'])
                if var_info['type'] in ['continuous', 'integer']:
                    var_lb.append(var_info['lb'])
                    var_ub.append(var_info['ub'])
                elif var_info['type'] == 'binary':
                    var_lb.append(0)
                    var_ub.append(1)
                elif var_info['type'] == 'categorical':
                    var_lb.append(0)
                    var_ub.append(len(var_info['choices']))
                else:
                    raise Exception(f'invalid variable type {var_info["type"]}')
        else:
            raise Exception(f'invalid problem type {problem_cfg["type"]}')
        
        self.var_lb, self.var_ub = np.array(var_lb), np.array(var_ub)

        # figure placeholder in GUI
        self.fig = plt.figure(figsize=(10, 5))
        self.gs = GridSpec(1, 2, figure=self.fig, width_ratios=[3, 2])

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.fig, self.root_view.frame_plot)

        # performance space figure
        if self.n_obj == 2:
            self.ax1 = self.fig.add_subplot(self.gs[0])
        elif self.n_obj == 3:
            self.ax1 = self.fig.add_subplot(self.gs[0], projection='3d')
        else:
            raise NotImplementedError
        self.ax1.set_title('Performance Space')
        self.ax1.set_xlabel(self.obj_name[0])
        self.ax1.set_ylabel(self.obj_name[1])
        if self.n_obj == 3:
            self.ax1.set_zlabel(self.obj_name[2])

        # design space figure
        if self.n_var > 2:
            self.theta = radar_factory(self.n_var)
            self.ax2 = self.fig.add_subplot(self.gs[1], projection='radar')
            self.ax2.set_xticks(self.theta)
            self.ax2.set_varlabels(self.var_name)
            self.ax2.set_yticklabels([])
            self.ax2.set_title('Selected Design', position=(0.5, 1.1))
            self.ax2.set_ylim(0, 1)
        else:
            self.ax2 = self.fig.add_subplot(self.gs[1])
            for spine in self.ax2.spines.values():
                spine.set_visible(False)
            self.ax2.get_xaxis().set_ticks([])
            self.ax2.get_yaxis().set_ticks([])
            self.xticks = [0] if self.n_var == 1 else [-1, 1]
            self.ax2.bar(self.xticks, [1] * self.n_var, color='g', alpha=0.2)
            self.ax2.set_xticks(self.xticks)
            self.text_lb = [None] * self.n_var
            self.text_ub = [None] * self.n_var
            for i in range(self.n_var):
                if var_type in ['continuous', 'integer'] or (var_type == 'mixed' and var_type_list[i] in ['continuous', 'integer']):
                    self.text_lb[i] = self.ax2.text(self.xticks[i] - 0.5, 0, str(self.var_lb[i]), horizontalalignment='right', verticalalignment='center')
                    self.text_ub[i] = self.ax2.text(self.xticks[i] - 0.5, 1, str(self.var_ub[i]), horizontalalignment='right', verticalalignment='center')
            self.ax2.set_xticklabels(self.var_name)
            self.ax2.set_title('Selected Design')
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

    def save_performance_figure(self, path, title=None):
        '''
        '''
        fig = plt.figure()
        if self.n_obj == 2:
            ax = fig.add_subplot(111)
        elif self.n_obj == 3:
            ax = fig.add_subplot(111, projection='3d')
        else:
            raise NotImplementedError

        if title is None:
            ax.set_title(self.ax1.get_title())
        else:
            ax.set_title(title)

        ax.set_xlabel(self.obj_name[0])
        ax.set_ylabel(self.obj_name[1])
        if self.n_obj == 3:
            ax.set_zlabel(self.obj_name[2])

        handles, labels = self.ax1.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if label.startswith('New'): continue
            if self.n_obj == 2:
                new_handle = ax.scatter(*np.array(handle.get_offsets().data).T, label=label)
            elif self.n_obj == 3:
                new_handle = ax.scatter3D(*np.array(handle.get_offsets().data).T, label=label)
            else:
                raise NotImplementedError
            new_handle.set_edgecolors(handle.get_edgecolors())
            new_handle.set_facecolors(handle.get_facecolors())
            new_handle.set_sizes(handle.get_sizes())

        ax.legend()
        fig.tight_layout()
        fig.savefig(path)

    def save_design_figure(self, path, line_x, bar_x, text_x, title=None):
        '''
        '''
        fig = plt.figure()

        if self.n_var > 2:
            ax = fig.add_subplot(111, projection='radar')
            ax.set_xticks(self.ax2.get_xticks())
            ax.set_xticklabels(self.ax2.get_xticklabels())
            ax.set_yticklabels([])
            ax.set_ylim(0, 1)
            
            if title is None:
                ax.set_title(self.ax2.get_title(), position=(0.5, 1.1))
            else:
                ax.set_title(title, position=(0.5, 1.1))

            if line_x is not None:
                ax.plot(*line_x.get_data(), color='g')
                ax.fill(*line_x.get_data(), color='g', alpha=0.2)
            
        else:
            ax = fig.add_subplot(111)
            for spine in ax.spines.values():
                spine.set_visible(False)
            ax.get_xaxis().set_ticks([])
            ax.get_yaxis().set_ticks([])

            xticks = self.ax2.get_xticks()
            ax.set_xticks(xticks)
            ax.set_xticklabels(self.ax2.get_xticklabels())
            ax.set_xlim(-3, 3)
            ax.set_ylim(0, 1.04)
            
            if title is None:
                ax.set_title(self.ax2.get_title())
            else:
                ax.set_title(title)

            ax.bar(xticks, [1] * self.n_var, color='g', alpha=0.2)
            if bar_x is not None:
                bar_heights = []
                for bar in bar_x.get_children():
                    bar_heights.append(bar.get_height())
                ax.bar(xticks, bar_heights, color='g')

            for i, (text_lb, text_ub) in enumerate(zip(self.text_lb, self.text_ub)):
                if text_lb is not None:
                    ax.text(xticks[i] - 0.5, 0, str(self.var_lb[i]), horizontalalignment='right', verticalalignment='center')
                if text_ub is not None:
                    ax.text(xticks[i] - 0.5, 1, str(self.var_ub[i]), horizontalalignment='right', verticalalignment='center')

            for txt in text_x:
                ax.text(*txt.get_position(), txt.get_text(), horizontalalignment='right', verticalalignment='center')

        fig.tight_layout()
        fig.savefig(path)

