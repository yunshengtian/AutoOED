import numpy as np
from matplotlib.backend_bases import MouseButton
from system.utils.performance import find_closest_point, check_pareto
from .view import VizSpaceView


class VizSpaceController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        # set values from root
        self.config, self.problem_cfg = self.root_controller.config, self.root_controller.problem_cfg
        self.data_agent = self.root_controller.data_agent

        self.view = VizSpaceView(self.root_view, self.problem_cfg)

        # bind command of viewing history to scaler
        self.max_iter = 0
        self.view.scale_iter.configure(command=self.redraw)

        # calculate pfront limit (for rescale plot afterwards)
        self.pfront_limit = None
        true_pfront = self.root_controller.true_pfront
        if true_pfront is not None:
            self.pfront_limit = [np.min(true_pfront, axis=1), np.max(true_pfront, axis=1)]

        # initialize performance space
        scatter_list = []
        if true_pfront is not None:
            scatter_pfront = self.view.ax1.scatter(*true_pfront.T, color='gray', s=5, label='Oracle') # plot true pareto front
            scatter_list.append(scatter_pfront)
        self.scatter_x = None
        self.scatter_y = self.view.ax1.scatter([], [], color='blue', s=10, label='Evaluated')
        self.scatter_y_pareto = self.view.ax1.scatter([], [], color='red', s=10, label='Pareto front')
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
        self.redraw_performance_space(reset_scaler=True)

    def set_config(self, config=None):
        if config is not None:
            self.config = config

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
            var_type, var_name = self.problem_cfg['type'], self.problem_cfg['var_name']
            var_lb, var_ub = self.view.var_lb, self.view.var_ub

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
            for i in range(n_var):
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
            if n_var > 2:
                self.line_x = self.view.ax2.plot(self.view.theta, normalized_x, color='g')[0]
                self.fill_x = self.view.ax2.fill(self.view.theta, normalized_x, color='g', alpha=0.2)[0]
                self.view.ax2.set_varlabels([f'{var_name[i]}\n{closest_x_str[i]}' for i in range(n_var)])
            else:
                self.bar_x = self.view.ax2.bar(self.view.xticks, normalized_x, color='g')
                self.text_x = []
                for i in range(n_var):
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
        X, Y, Y_expected, pareto, batch = self.data_agent.load(['X', 'Y', 'Y_expected', 'pareto', 'batch'])
        valid_idx = np.where((~np.isnan(Y)).all(axis=1))[0]
        if len(valid_idx) == 0: return
        X, Y, Y_expected, pareto, batch = X[valid_idx], Y[valid_idx], Y_expected[valid_idx], pareto[valid_idx], batch[valid_idx]
        max_iter = batch[-1]

        if reset_scaler:
            # reset the max iteration of scaler
            self.view.scale_iter.configure(to=max_iter)
            if self.view.curr_iter.get() == self.max_iter:
                self.max_iter = max_iter
                self.view.curr_iter.set(max_iter)
            else:
                # no need to redraw performance space if not focusing on the max iteration
                return

        if draw_iter is not None and draw_iter < batch[-1]:
            draw_idx = batch <= draw_iter
            X, Y, Y_expected, batch = X[draw_idx], Y[draw_idx], Y_expected[draw_idx], batch[draw_idx]
            max_iter = batch[-1]
            pareto = check_pareto(Y, self.problem_cfg['obj_type'])
        
        # replot evaluated & pareto points
        self.scatter_x = X
        n_obj = Y.shape[1]
        if n_obj == 2:
            self.scatter_y.set_offsets(Y)
            self.scatter_y_pareto.set_offsets(Y[pareto])
        elif n_obj == 3:
            self.scatter_y._offsets3d = Y.T
            self.scatter_y_pareto._offsets3d = Y[pareto].T
        
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
        line_vis = True
        for line in self.line_y_pred_list:
            line_vis = line_vis and line.get_visible()
            line.remove()
        self.line_y_pred_list = []

        if max_iter > 0:
            last_batch = np.where(batch == max_iter)[0]
            if n_obj == 2:
                self.scatter_y_new.set_offsets(Y[last_batch])
                self.scatter_y_pred.set_offsets(Y_expected[last_batch])
            elif n_obj == 3:
                self.scatter_y_new._offsets3d = Y[last_batch].T
                self.scatter_y_pred._offsets3d = Y_expected[last_batch].T
            for y, y_expected in zip(Y[last_batch], Y_expected[last_batch]):
                line = self.view.ax1.plot(*[[y[i], y_expected[i]] for i in range(n_obj)], '--', color='m', alpha=0.5)[0]
                line.set_visible(line_vis)
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
