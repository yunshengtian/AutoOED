import numpy as np
from matplotlib.backend_bases import MouseButton
from system.server.utils import find_closest_point, check_pareto
from .view import SpaceView


class SpaceController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.config, self.problem_cfg = self.root_controller.config, self.root_controller.problem_cfg
        self.data_agent = self.root_controller.data_agent

        self.view = SpaceView(self.root_view, self.problem_cfg)

        # bind command of viewing history to scaler
        self.max_iter = 0
        self.view.scale_iter.configure(command=self.redraw)

        # load from database
        X, Y, is_pareto = self.data_agent.load(['X', 'Y', 'is_pareto'])

        # calculate pfront limit (for rescale plot afterwards)
        self.pfront_limit = None
        true_pfront = self.root_controller.true_pfront
        if true_pfront is not None:
            self.pfront_limit = [np.min(true_pfront, axis=1), np.max(true_pfront, axis=1)]

        # plot performance space
        scatter_list = []
        if true_pfront is not None:
            scatter_pfront = self.view.ax1.scatter(*true_pfront.T, color='gray', s=5, label='Oracle') # plot true pareto front
            scatter_list.append(scatter_pfront)
        self.scatter_x = X
        self.scatter_y = self.view.ax1.scatter(*Y.T, color='blue', s=10, label='Evaluated')
        self.scatter_y_pareto = self.view.ax1.scatter(*Y[is_pareto].T, color='red', s=10, label='Pareto front')
        self.scatter_y_new = self.view.ax1.scatter([], [], color='m', s=10, label='New evaluated')
        self.scatter_y_pred = self.view.ax1.scatter([], [], facecolors=(0, 0, 0, 0), edgecolors='m', s=15, label='New predicted')
        scatter_list.extend([self.scatter_y, self.scatter_y_pareto, self.scatter_y_new, self.scatter_y_pred])
        self.scatter_selected = None
        self.line_y_pred_list = []

        # support checking design variables
        self.line_x = None
        self.fill_x = None
        self.bar_x = None
        self.text_x = []
        self.view.fig.canvas.mpl_connect('button_press_event', self.check_design_values)

        # set pick event on legend to enable/disable certain visualization
        legend = self.view.fig.legend(loc='lower center', ncol=5)
        self.picker_map = {}
        for plot_obj, leg_obj, text in zip(scatter_list, legend.legendHandles, legend.get_texts()):
            leg_obj.set_picker(True)
            text.set_picker(True)
            self.picker_map[leg_obj] = plot_obj
            self.picker_map[text] = plot_obj
        self.view.fig.canvas.mpl_connect('pick_event', self.toggle_performance_visibility)

        # refresh figure
        self.view.fig.subplots_adjust(bottom=0.15)
        self.view.fig.canvas.draw()

    def set_config(self, config=None, problem_cfg=None):
        if config is not None:
            self.config = config
        if problem_cfg is not None:
            self.problem_cfg = problem_cfg

    def redraw(self, val):
        '''
        Redraw design and performance space when slider changes
        '''
        # get current iteration from slider value
        curr_iter = int(val)

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
            n_var, n_obj = self.problem_cfg['n_var'], self.problem_cfg['n_obj']
            var_lb, var_ub, var_name = self.problem_cfg['var_lb'], self.problem_cfg['var_ub'], self.problem_cfg['var_name']

            # find nearest performance values with associated design values
            loc = [event.xdata, event.ydata]
            all_y = self.scatter_y._offsets
            closest_y, closest_idx = find_closest_point(loc, all_y, return_index=True)
            closest_x = self.scatter_x[closest_idx]
            if n_obj == 3:
                closest_y = np.array(self.scatter_y._offsets3d).T[closest_idx]

            # clear checked design values
            self.clear_design_space()

            # highlight selected point
            self.scatter_selected = self.view.ax1.scatter(*closest_y, s=50, facecolors=(0, 0, 0, 0), edgecolors='g', linewidths=2)

            # plot checked design values as radar plot or bar chart
            transformed_x = (np.array(closest_x) - var_lb) / (var_ub - var_lb)
            if n_var > 2:
                self.line_x = self.view.ax2.plot(self.view.theta, transformed_x, color='g')[0]
                self.fill_x = self.view.ax2.fill(self.view.theta, transformed_x, color='g', alpha=0.2)[0]
                self.view.ax2.set_varlabels([f'{var_name[i]}\n{closest_x[i]:.4g}' for i in range(n_var)])
            else:
                self.bar_x = self.view.ax2.bar(self.view.xticks, transformed_x, color='g')
                self.text_x = []
                for i in range(n_var):
                    self.view.text_lb[i].set_text(str(var_lb[i]))
                    self.view.text_ub[i].set_text(str(var_ub[i]))
                    text = self.view.ax2.text(self.view.xticks[i], transformed_x[i], f'{closest_x[i]:.4g}', horizontalalignment='center', verticalalignment='bottom')
                    self.text_x.append(text)

        elif event.button == MouseButton.RIGHT: # clear checked design values
            self.clear_design_space()
            
        self.view.fig.canvas.draw()

    def clear_design_space(self):
        '''
        Clear design space plot
        '''
        if self.scatter_selected is not None:
            self.scatter_selected.remove()
            self.scatter_selected = None
            
        n_var, var_name = self.problem_cfg['n_var'], self.problem_cfg['var_name']

        if n_var > 2:
            self.view.ax2.set_varlabels(var_name)
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
        X, Y, Y_expected, is_pareto, batch_id = self.data_agent.load(['X', 'Y', 'Y_expected', 'is_pareto', 'batch_id'])
        max_iter = batch_id[-1]

        if reset_scaler:
            # reset the max iteration of scaler
            self.view.scale_iter.configure(to=max_iter)
            if self.view.curr_iter.get() == self.max_iter:
                self.max_iter = max_iter
                self.view.curr_iter.set(max_iter)
            else:
                # no need to redraw performance space if not focusing on the max iteration
                return

        if draw_iter is not None and draw_iter < batch_id[-1]:
            draw_idx = batch_id <= draw_iter
            X, Y, Y_expected, batch_id = X[draw_idx], Y[draw_idx], Y_expected[draw_idx], batch_id[draw_idx]
            max_iter = batch_id[-1]
            is_pareto = check_pareto(Y, self.problem_cfg['minimize'])
        
        # replot evaluated & pareto points
        self.scatter_x = X
        n_obj = Y.shape[1]
        if n_obj == 2:
            self.scatter_y.set_offsets(Y)
            self.scatter_y_pareto.set_offsets(Y[is_pareto])
        elif n_obj == 3:
            self.scatter_y._offsets3d = Y.T
            self.scatter_y_pareto._offsets3d = Y[is_pareto].T
        
        # rescale plot according to Y and true_pfront
        n_obj = self.problem_cfg['n_obj']
        x_min, x_max = np.min(Y[:, 0]), np.max(Y[:, 0])
        y_min, y_max = np.min(Y[:, 1]), np.max(Y[:, 1])
        if n_obj == 3: z_min, z_max = np.min(Y[:, 2]), np.max(Y[:, 2])
        if self.pfront_limit is not None:
            x_min, x_max = min(x_min, self.pfront_limit[0][0]), max(x_max, self.pfront_limit[1][0])
            y_min, y_max = min(y_min, self.pfront_limit[0][1]), max(y_max, self.pfront_limit[1][1])
            if n_obj == 3: z_min, z_max = min(z_min, self.pfront_limit[0][2]), max(z_max, self.pfront_limit[1][2])
        x_offset = (x_max - x_min) / 20
        y_offset = (y_max - y_min) / 20
        if n_obj == 3: z_offset = (z_max - z_min) / 20
        self.view.ax1.set_xlim(x_min - x_offset, x_max + x_offset)
        self.view.ax1.set_ylim(y_min - y_offset, y_max + y_offset)
        if n_obj == 3: self.view.ax1.set_zlim(z_min - z_offset, z_max + z_offset)

        # replot new evaluated & predicted points
        for line in self.line_y_pred_list:
            line.remove()
        self.line_y_pred_list = []

        if max_iter > 0:
            last_batch_idx = np.where(batch_id == max_iter)[0]
            if n_obj == 2:
                self.scatter_y_new.set_offsets(Y[last_batch_idx])
                self.scatter_y_pred.set_offsets(Y_expected[last_batch_idx])
            elif n_obj == 3:
                self.scatter_y_new._offsets3d = Y[last_batch_idx].T
                self.scatter_y_pred._offsets3d = Y_expected[last_batch_idx].T
            for y, y_expected in zip(Y[last_batch_idx], Y_expected[last_batch_idx]):
                line = self.view.ax1.plot(*[[y[i], y_expected[i]] for i in range(n_obj)], '--', color='m', alpha=0.5)[0]
                self.line_y_pred_list.append(line)
        else:
            empty_y = np.empty((0, n_obj))
            if n_obj == 2:
                self.scatter_y_new.set_offsets(empty_y)
                self.scatter_y_pred.set_offsets(empty_y)
            elif n_obj == 3:
                self.scatter_y_new._offsets3d = empty_y.T
                self.scatter_y_pred._offsets3d = empty_y.T

        self.view.fig.canvas.draw()

    def toggle_performance_visibility(self, event):
        '''
        Toggle visibility of plotted objs
        '''
        plot_obj = self.picker_map[event.artist]
        vis = not plot_obj.get_visible()
        plot_obj.set_visible(vis)

        if not self.scatter_y_new.get_visible() or not self.scatter_y_pred.get_visible():
            for line in self.line_y_pred_list:
                line.set_visible(False)
        if self.scatter_y_new.get_visible() and self.scatter_y_pred.get_visible():
            for line in self.line_y_pred_list:
                line.set_visible(True)

        self.view.fig.canvas.draw()
