import numpy as np
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.gridspec import GridSpec
from matplotlib.backend_bases import MouseButton
from mpl_toolkits.mplot3d import Axes3D
import tkinter as tk
from tkinter import ttk

from autooed.utils.pareto import check_pareto
from autooed.system.gui.widgets.utils.radar import radar_factory
from autooed.system.params import FIGURE_DPI
from autooed.system.gui.widgets.utils.layout import grid_configure
from autooed.system.gui.widgets.utils.figure import embed_figure
from autooed.system.gui.widgets.factory import create_widget


def find_closest_point(y, Y, return_index=False):
    '''
    Find the closest point to y in array Y
    '''
    idx = np.argmin(np.linalg.norm(np.array(y) - Y, axis=1))
    if return_index:
        return Y[idx], idx
    else:
        return Y[idx]


def find_closest_line(y, lines, return_index=False):
    '''
    Find the closest line to y in lines
    '''
    # y: np.array, shape = (2,)
    # lines: np.array, shape = (n_lines, n_obj, 2)
    lines = np.array(lines)
    assert lines.ndim == 3
    n_lines, n_obj = lines.shape[0], lines.shape[1]

    if y[0] < 0: # smaller than the left bound
        idx = np.argmin(np.abs(lines[:, 0, 1] - y[1]))

    elif y[0] >= n_obj - 1: # larger than the right bound
        idx = np.argmin(np.abs(lines[:, n_obj - 1, 1] - y[1]))

    else: # inside bounds
        x_begin, x_end = int(y[0]), int(y[0]) + 1
        key_lines = np.vstack([lines[:, x_begin, 1], lines[:, x_end, 1]]).T # shape = (n_lines, 2)
        interp_values = key_lines[:, 0] + (y[0] - x_begin) * (key_lines[:, 1] - key_lines[:, 0]) # shape = (n_lines,)
        idx = np.argmin(np.abs(interp_values - y[1]))

    if return_index:
        return lines[idx], idx
    else:
        return lines[idx]


def parallel_transform(Y):
    '''
    Transform performance values from cartesian to parallel coordinates
    '''
    Y = np.array(Y)
    return np.dstack([np.vstack([np.arange(Y.shape[1])] * len(Y)), Y])


def parallel_untransform(segments):
    '''
    Transform performance values from parallel to cartesian coordinates
    '''
    segments = np.array(segments)
    return segments[:, :, 1]


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
        self.fig = plt.figure(dpi=FIGURE_DPI)
        self.gs = GridSpec(1, 2, figure=self.fig, width_ratios=[3, 2])

        # connect matplotlib figure with tkinter GUI
        embed_figure(self.fig, self.root_view.frame_plot)

        # performance space figure
        if self.n_obj == 1 or self.n_obj == 2 or self.n_obj > 3:
            self.ax1 = self.fig.add_subplot(self.gs[0])
        elif self.n_obj == 3:
            self.ax1 = self.fig.add_subplot(self.gs[0], projection='3d')
        else:
            raise NotImplementedError
        
        self.ax1.set_title('Performance Space')
        if self.n_obj == 1:
            self.ax1.set_xlabel(self.obj_name[0])
        elif self.n_obj == 2:
            self.ax1.set_xlabel(self.obj_name[0])
            self.ax1.set_ylabel(self.obj_name[1])
        elif self.n_obj == 3:
            self.ax1.set_xlabel(self.obj_name[0])
            self.ax1.set_ylabel(self.obj_name[1])
            self.ax1.set_zlabel(self.obj_name[2])
        elif self.n_obj > 3:
            self.ax1.set_xticks(np.arange(self.n_obj, dtype=int))
            self.ax1.set_xticklabels(self.obj_name)
        else:
            raise NotImplementedError

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
                    self.text_lb[i] = self.ax2.text(self.xticks[i] - 0.5, 0, f'{self.var_lb[i]:.4g}', horizontalalignment='right', verticalalignment='center')
                    self.text_ub[i] = self.ax2.text(self.xticks[i] - 0.5, 1, f'{self.var_ub[i]:.4g}', horizontalalignment='right', verticalalignment='center')
            self.ax2.set_xticklabels(self.var_name)
            self.ax2.set_title('Selected Design')
            self.ax2.set_xlim(-3, 3)
            self.ax2.set_ylim(0, 1.04)

        # configure slider widget
        frame_slider = create_widget('frame', master=self.root_view.frame_plot, row=2, column=0)
        grid_configure(frame_slider, [0], [1])
        
        self.label_iter = tk.Label(master=frame_slider, text='Iteration')
        self.label_iter.grid(row=0, column=0, sticky='EW')
        self.curr_iter = tk.IntVar()
        self.scale_iter = ttk.Scale(master=frame_slider, orient=tk.HORIZONTAL, variable=self.curr_iter, from_=0, to=0)
        self.scale_iter.grid(row=0, column=1, sticky='EW')

    def save_performance_figure(self, path, title=None):
        '''
        '''
        fig = plt.figure()
        if self.n_obj == 1 or self.n_obj == 2 or self.n_obj > 3:
            ax = fig.add_subplot(111)
        elif self.n_obj == 3:
            ax = fig.add_subplot(111, projection='3d')
        else:
            raise NotImplementedError

        if title is None:
            ax.set_title(self.ax1.get_title())
        else:
            ax.set_title(title)

        if self.n_obj == 1:
            ax.set_xlabel(self.obj_name[0])
        elif self.n_obj == 2:
            ax.set_xlabel(self.obj_name[0])
            ax.set_ylabel(self.obj_name[1])
        elif self.n_obj == 3:
            ax.set_xlabel(self.obj_name[0])
            ax.set_ylabel(self.obj_name[1])
            ax.set_zlabel(self.obj_name[2])
        elif self.n_obj > 3:
            ax.set_xticks(np.arange(self.n_obj, dtype=int))
            ax.set_xticklabels(self.obj_name)
        else:
            raise NotImplementedError

        handles, labels = self.ax1.get_legend_handles_labels()
        for handle, label in zip(handles, labels):
            if label.startswith('New'): continue
            if self.n_obj == 1 or self.n_obj == 2 or self.n_obj == 3:
                offsets = handle.get_offsets().data
                if len(offsets) == 0: continue
                if self.n_obj == 1:
                    new_handle = ax.scatter(*np.array(offsets).T, label=label, marker='x')
                elif self.n_obj == 2:
                    new_handle = ax.scatter(*np.array(offsets).T, label=label)
                else:
                    new_handle = ax.scatter3D(*np.array(offsets).T, label=label)
                new_handle.set_edgecolors(handle.get_edgecolors())
                new_handle.set_facecolors(handle.get_facecolors())
                new_handle.set_sizes(handle.get_sizes())
            elif self.n_obj > 3:
                segments = handle.get_segments()
                if len(segments) == 0: continue
                new_handle = ax.add_collection(LineCollection(segments, label=label))
                new_handle.set_alpha(handle.get_alpha())
                new_handle.set_color(handle.get_color())
                bottom, top = ax.get_ylim()
                Y = parallel_untransform(segments)
                ax.set_ylim(min(bottom, np.min(Y)), max(top, np.max(Y)))
            else:
                raise NotImplementedError

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


class VizSpaceController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.problem_cfg = self.root_controller.problem_cfg
        self.agent = self.root_controller.agent
        self.n_var, self.var_name = self.problem_cfg['n_var'], self.problem_cfg['var_name']
        self.n_obj, self.obj_name = self.problem_cfg['n_obj'], self.problem_cfg['obj_name']

        self.view = VizSpaceView(self.root_view, self.problem_cfg)

        # bind command of viewing history to scaler
        self.max_iter = 0
        self.view.scale_iter.configure(command=self.redraw)

        # calculate pfront limit (for rescale plot afterwards)
        self.pfront_limit = None
        true_pfront = self.root_controller.true_pfront
        if true_pfront is not None:
            if self.n_obj == 1:
                self.pfront_limit = true_pfront
            else:
                self.pfront_limit = [np.min(true_pfront, axis=1), np.max(true_pfront, axis=1)]

        # initialize performance space
        plot_obj_list = []
        
        if self.n_obj == 1:

            if true_pfront is not None:
                plot_pfront = self.view.ax1.scatter(true_pfront, 0, marker='x', color='gray', label='Oracle')
                plot_obj_list.append(plot_pfront)
            self.plot_x = None
            self.plot_y = self.view.ax1.scatter([], [], marker='x', color='blue', label='Evaluated')
            self.plot_y_pareto = self.view.ax1.scatter([], [], marker='x', color='red', label='Optimum')
            self.plot_y_new = self.view.ax1.scatter([], [], marker='x', color='m', label='New evaluated')
            plot_obj_list.extend([self.plot_y, self.plot_y_pareto, self.plot_y_new])
            self.plot_selected = None
            self.plot_y_pred = None # unused
            self.line_y_pred_list = None # usused
        
        elif self.n_obj == 2 or self.n_obj == 3:

            if true_pfront is not None:
                plot_pfront = self.view.ax1.scatter(*true_pfront.T, color='gray', s=5, label='Oracle') # plot true pareto front
                plot_obj_list.append(plot_pfront)
            self.plot_x = None
            self.plot_y = self.view.ax1.scatter([], [], color='blue', s=10, label='Evaluated')
            self.plot_y_pareto = self.view.ax1.scatter([], [], color='red', s=10, label='Pareto front')
            self.plot_y_new = self.view.ax1.scatter([], [], color='m', s=10, label='New evaluated')
            self.plot_y_pred = self.view.ax1.scatter([], [], facecolors=(0, 0, 0, 0), edgecolors='m', s=15, label='New predicted')
            plot_obj_list.extend([self.plot_y, self.plot_y_pareto, self.plot_y_new, self.plot_y_pred])
            self.plot_selected = None
            self.line_y_pred_list = []

        elif self.n_obj > 3:

            if true_pfront is not None:
                plot_pfront = self.view.ax1.add_collection(LineCollection([], color='grey', label='Oracle', alpha=0.5))
                plot_pfront.set_segments(parallel_transform(true_pfront))
                plot_obj_list.append(plot_pfront)
            self.plot_x = None
            self.plot_y = self.view.ax1.add_collection(LineCollection([], color='blue', label='Evaluated', alpha=0.5))
            self.plot_y_pareto = self.view.ax1.add_collection(LineCollection([], color='red', label='Pareto front', alpha=0.8))
            self.plot_y_new = self.view.ax1.add_collection(LineCollection([], color='m', label='New evaluated', alpha=0.8))
            plot_obj_list.extend([self.plot_y, self.plot_y_pareto, self.plot_y_new])
            self.plot_selected = None
            self.plot_y_pred = None # unused
            self.line_y_pred_list = None # usused
            
        else:
            raise NotImplementedError

        # support checking design variables
        self.line_x = None
        self.fill_x = None
        self.bar_x = None
        self.text_x = []
        self.view.fig.canvas.mpl_connect('button_press_event', self.check_design_values)

        # set pick event on legend to enable/disable certain visualization
        legend = self.view.fig.legend(loc='lower center', ncol=5, frameon=False)
        self.picker_map = {}
        for plot_obj, leg_obj, text in zip(plot_obj_list, legend.legendHandles, legend.get_texts()):
            leg_obj.set_picker(True)
            text.set_picker(True)
            self.picker_map[leg_obj] = plot_obj
            self.picker_map[text] = plot_obj
        self.view.fig.canvas.mpl_connect('pick_event', self.toggle_performance_visibility)

        # refresh figure
        self.view.fig.subplots_adjust(bottom=0.15)
        self.redraw_performance_space(reset_scaler=True)

    def redraw(self, val):
        '''
        Redraw design and performance space when slider changes
        '''
        # get current iteration from slider value
        curr_iter = int(round(float(val)))
        self.view.label_iter.config(text=f'Iteration {curr_iter}')

        # clear design space
        self.clear_design_space()

        # replot performance space
        self.redraw_performance_space(curr_iter)

    def check_design_values(self, event):
        '''
        Mouse clicking event, for checking design values
        '''
        if event.inaxes != self.view.ax1: return

        if event.button == MouseButton.LEFT and event.dblclick: # check certain design values
            var_type, var_name = self.problem_cfg['type'], self.problem_cfg['var_name']
            var_lb, var_ub = self.view.var_lb, self.view.var_ub

            # find nearest performance values with associated design values
            loc = [event.xdata, event.ydata]
            if self.n_obj == 1 or self.n_obj == 2 or self.n_obj == 3:
                all_y = self.plot_y._offsets
                if len(all_y) == 0: return
                closest_y, closest_idx = find_closest_point(loc, all_y, return_index=True)
                if self.n_obj == 3:
                    closest_y = np.array(self.plot_y._offsets3d).T[closest_idx]
            elif self.n_obj > 3:
                closest_line, closest_idx = find_closest_line(loc, self.plot_y.get_segments(), return_index=True)
            else:
                raise NotImplementedError
            closest_x = self.plot_x[closest_idx]

            # clear checked design values
            self.clear_design_space()

            # highlight selected point
            if self.n_obj == 1 or self.n_obj == 2 or self.n_obj == 3:
                self.plot_selected = self.view.ax1.scatter(*closest_y, s=50, facecolors=(0, 0, 0, 0), edgecolors='g', linewidths=2)
            elif self.n_obj > 3:
                self.plot_selected = self.view.ax1.plot(*closest_line.T, color='g', alpha=0.8)[0]
            else:
                raise NotImplementedError

            # compute normalized x
            if var_type in ['continuous', 'integer', 'binary']:
                normalized_x = (np.array(closest_x) - var_lb) / (var_ub - var_lb)
            elif var_type == 'categorical':
                normalized_x = []
                if 'var' in self.problem_cfg:
                    for i, (x, var_info) in enumerate(zip(closest_x, self.problem_cfg['var'].values())):
                        normalized_x.append((var_info['choices'].index(x) + 1) / var_ub[i])
                else:
                    for i, x in enumerate(closest_x):
                        normalized_x.append((self.problem_cfg['var_choices'].index(x) + 1) / var_ub[i])
                normalized_x = np.array(normalized_x)
            elif var_type == 'mixed':
                normalized_x = []
                var_type_list = []
                for i, (x, var_info) in enumerate(zip(closest_x, self.problem_cfg['var'].values())):
                    var_type_list.append(var_info['type'])
                    if var_info['type'] in ['continuous', 'integer']:
                        lb, ub = var_info['lb'], var_info['ub']
                        normalized_x.append((x - lb) / (ub - lb))
                    elif var_info['type'] == 'binary':
                        normalized_x.append(x)
                    elif var_info['type'] == 'categorical':
                        normalized_x.append((var_info['choices'].index(x) + 1) / var_ub[i])
                    else:
                        raise Exception(f'invalid variable type {var_info["type"]}')
                normalized_x = np.array(normalized_x)
            else:
                raise Exception(f'invalid problem type {var_type}')

            # compute text label
            closest_x_str = []
            for i in range(self.n_var):
                if var_type == 'continuous':
                    closest_x_str.append(f'{closest_x[i]:.4g}')
                elif var_type in ['integer', 'binary', 'categorical']:
                    closest_x_str.append(f'{closest_x[i]}')
                elif var_type == 'mixed':
                    if var_type_list[i] == 'continuous':
                        closest_x_str.append(f'{closest_x[i]:.4g}')
                    else:
                        closest_x_str.append(f'{closest_x[i]}')
                else:
                    raise Exception(f'invalid problem type {var_type}')
            
            # plot checked design values as radar plot or bar chart
            if self.n_var > 2:
                self.line_x = self.view.ax2.plot(self.view.theta, normalized_x, color='g')[0]
                self.fill_x = self.view.ax2.fill(self.view.theta, normalized_x, color='g', alpha=0.2)[0]
                self.view.ax2.set_varlabels([f'{var_name[i]}\n{closest_x_str[i]}' for i in range(self.n_var)])
            else:
                self.bar_x = self.view.ax2.bar(self.view.xticks, normalized_x, color='g')
                self.text_x = []
                for i in range(self.n_var):
                    if var_type in ['continuous', 'integer'] or (var_type == 'mixed' and var_type_list[i] in ['continuous', 'integer']):
                        self.view.text_lb[i].set_text(str(var_lb[i]))
                        self.view.text_ub[i].set_text(str(var_ub[i]))
                    text = self.view.ax2.text(self.view.xticks[i], normalized_x[i], f'{closest_x_str[i]}', horizontalalignment='center', verticalalignment='bottom')
                    self.text_x.append(text)

        elif event.button == MouseButton.RIGHT: # clear checked design values
            self.clear_design_space()
            
        self.view.fig.canvas.draw()

    def clear_design_space(self):
        '''
        Clear design space plot
        '''
        if self.plot_selected is not None:
            self.plot_selected.remove()
            self.plot_selected = None

        if self.n_var > 2:
            self.view.ax2.set_varlabels(self.var_name)
            if self.line_x is not None:
                self.line_x.remove()
                self.line_x = None
            if self.fill_x is not None:
                self.fill_x.remove()
                self.fill_x = None
        else:
            if self.bar_x is not None:
                self.bar_x.remove()
                self.bar_x = None
            for text in self.text_x:
                text.remove()
            self.text_x = []

    def redraw_performance_space(self, draw_iter=None, reset_scaler=False):
        '''
        Redraw performance space
        '''
        # load data
        X, Y, Y_pred_mean, pareto, batch = self.agent.load(['X', 'Y', '_Y_pred_mean', 'pareto', 'batch'])
        valid_idx = np.where((~np.isnan(Y)).all(axis=1))[0]
        if len(valid_idx) == 0: return
        X, Y, Y_pred_mean, pareto, batch = X[valid_idx], Y[valid_idx], Y_pred_mean[valid_idx], pareto[valid_idx], batch[valid_idx]
        max_iter = batch[-1]

        if reset_scaler:
            # reset the max iteration of scaler
            self.view.scale_iter.configure(to=max_iter)
            if self.view.curr_iter.get() >= self.max_iter:
                self.max_iter = max_iter
                self.view.curr_iter.set(max_iter)
                self.view.label_iter.config(text=f'Iteration {max_iter}')
            else:
                # no need to redraw performance space if not focusing on the max iteration
                return

        if draw_iter is not None and draw_iter < batch[-1]:
            draw_idx = batch <= draw_iter
            X, Y, Y_pred_mean, batch = X[draw_idx], Y[draw_idx], Y_pred_mean[draw_idx], batch[draw_idx]
            max_iter = batch[-1]
            pareto = check_pareto(Y, self.problem_cfg['obj_type'])
        
        # replot evaluated & pareto points
        self.plot_x = X
        if self.n_obj == 1:
            self.plot_y.set_offsets(np.hstack([Y, np.zeros_like(Y)]))
            self.plot_y_pareto.set_offsets(np.hstack([Y[pareto], np.zeros_like(Y[pareto])]))
        elif self.n_obj == 2:
            self.plot_y.set_offsets(Y)
            self.plot_y_pareto.set_offsets(Y[pareto])
        elif self.n_obj == 3:
            self.plot_y._offsets3d = Y.T
            self.plot_y_pareto._offsets3d = Y[pareto].T
        elif self.n_obj > 3:
            self.plot_y.set_segments(parallel_transform(Y))
            self.plot_y_pareto.set_segments(parallel_transform(Y[pareto]))
        else:
            raise NotImplementedError
        
        # rescale plot according to Y and true_pfront
        if self.n_obj == 1:
            x_min, x_max = np.min(Y), np.max(Y)
            if self.pfront_limit is not None:
                x_min, x_max = min(x_min, self.pfront_limit), max(x_max, self.pfront_limit)
            x_offset = (x_max - x_min) / 20
            self.view.ax1.set_xlim(x_min - x_offset, x_max + x_offset)
        elif self.n_obj == 2 or self.n_obj == 3:
            x_min, x_max = np.min(Y[:, 0]), np.max(Y[:, 0])
            y_min, y_max = np.min(Y[:, 1]), np.max(Y[:, 1])
            if self.n_obj == 3: z_min, z_max = np.min(Y[:, 2]), np.max(Y[:, 2])
            if self.pfront_limit is not None:
                x_min, x_max = min(x_min, self.pfront_limit[0][0]), max(x_max, self.pfront_limit[1][0])
                y_min, y_max = min(y_min, self.pfront_limit[0][1]), max(y_max, self.pfront_limit[1][1])
                if self.n_obj == 3: z_min, z_max = min(z_min, self.pfront_limit[0][2]), max(z_max, self.pfront_limit[1][2])
            x_offset = (x_max - x_min) / 20
            y_offset = (y_max - y_min) / 20
            if self.n_obj == 3: z_offset = (z_max - z_min) / 20
            self.view.ax1.set_xlim(x_min - x_offset, x_max + x_offset)
            self.view.ax1.set_ylim(y_min - y_offset, y_max + y_offset)
            if self.n_obj == 3: self.view.ax1.set_zlim(z_min - z_offset, z_max + z_offset)
        elif self.n_obj > 3:
            y_min, y_max = np.min(Y), np.max(Y)
            if self.pfront_limit is not None:
                y_min, y_max = min(y_min, np.min(self.pfront_limit)), max(y_max, np.max(self.pfront_limit))
            y_offset = (y_max - y_min) / 20
            x_min, x_max = 0, self.n_obj - 1
            x_offset = (x_max - x_min) / 20
            self.view.ax1.set_xlim(x_min - x_offset, x_max + x_offset)
            self.view.ax1.set_ylim(y_min - y_offset, y_max + y_offset)
        else:
            raise NotImplementedError

        # replot new evaluated & predicted points
        if self.n_obj == 2 or self.n_obj == 3:
            line_vis = True
            for line in self.line_y_pred_list:
                line_vis = line_vis and line.get_visible()
                line.remove()
            self.line_y_pred_list = []

        if max_iter > 0:
            last_batch = np.where(batch == max_iter)[0]
            if self.n_obj == 1:
                self.plot_y_new.set_offsets(np.hstack([Y[last_batch], np.zeros_like(Y[last_batch])]))
            elif self.n_obj == 2:
                self.plot_y_new.set_offsets(Y[last_batch])
                self.plot_y_pred.set_offsets(Y_pred_mean[last_batch])
            elif self.n_obj == 3:
                self.plot_y_new._offsets3d = Y[last_batch].T
                self.plot_y_pred._offsets3d = Y_pred_mean[last_batch].T
            elif self.n_obj > 3:
                self.plot_y_new.set_segments(parallel_transform(Y[last_batch]))
            else:
                raise NotImplementedError
            if self.n_obj == 2 or self.n_obj == 3:
                for y, y_pred_mean in zip(Y[last_batch], Y_pred_mean[last_batch]):
                    line = self.view.ax1.plot(*[[y[i], y_pred_mean[i]] for i in range(self.n_obj)], '--', color='m', alpha=0.5)[0]
                    line.set_visible(line_vis)
                    self.line_y_pred_list.append(line)
        else:
            empty_y = np.empty((0, self.n_obj))
            if self.n_obj == 1:
                self.plot_y_new.set_offsets(np.empty((0, 2)))
            elif self.n_obj == 2:
                self.plot_y_new.set_offsets(empty_y)
                self.plot_y_pred.set_offsets(empty_y)
            elif self.n_obj == 3:
                self.plot_y_new._offsets3d = empty_y.T
                self.plot_y_pred._offsets3d = empty_y.T
            elif self.n_obj > 3:
                self.plot_y_new.set_segments([])
            else:
                raise NotImplementedError

        self.view.fig.canvas.draw()

    def toggle_performance_visibility(self, event):
        '''
        Toggle visibility of plotted objs
        '''
        plot_obj = self.picker_map[event.artist]
        vis = not plot_obj.get_visible()
        plot_obj.set_visible(vis)
        if vis:
            event.artist.set_color('black')
        else:
            event.artist.set_color('gray')

        if self.n_obj == 2 or self.n_obj == 3:
            if not self.plot_y_new.get_visible() or not self.plot_y_pred.get_visible():
                for line in self.line_y_pred_list:
                    line.set_visible(False)
            if self.plot_y_new.get_visible() and self.plot_y_pred.get_visible():
                for line in self.line_y_pred_list:
                    line.set_visible(True)

        self.view.fig.canvas.draw()

    def save_performance_figure(self, path, title=None):
        '''
        '''
        self.view.save_performance_figure(path, title=title)

    def save_design_figure(self, path, title=None):
        '''
        '''
        self.view.save_design_figure(path, self.line_x, self.bar_x, self.text_x, title=title)