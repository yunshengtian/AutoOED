import os
import tkinter as tk
from config.utils import load_config
from problem.common import get_problem_config
from system.gui.widgets.factory import show_widget_error
from system.scientist.gui.map import config_map
from .view import ConfigView

from .design_bound import DesignBoundController
from .performance_bound import PerformanceBoundController
from .algo_advanced import AlgoAdvancedController


class ConfigController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_static_cfg = {} # static part of problem config (problem definition)
        self.problem_dynamic_cfg = {} # dynamic part of problem config (experiment customization)
        self.algo_cfg = {} # store advanced config of algorithm
        
        self.first_time = True

        self.view = None

    def get_config(self):
        return self.root_controller.get_config()

    def set_config(self, *args, **kwargs):
        return self.root_controller.set_config(*args, **kwargs)

    def load_config_from_file(self):
        '''
        Load experiment configurations from file
        '''
        filename = tk.filedialog.askopenfilename(parent=self.root_view.root)
        if not isinstance(filename, str) or filename == '': return

        try:
            config = load_config(filename)
        except:
            tk.messagebox.showinfo('Error', 'Invalid yaml file', parent=self.root_view.root)
            return
            
        self.set_config(config)

    def build_config_window(self):
        '''
        Build configuration window (for create/change)
        '''
        self.view = ConfigView(self.root_view, self.first_time)

        self.view.widget['problem_name'].widget.bind('<<ComboboxSelected>>', self.select_problem)
        self.view.widget['ref_point'].config(
            valid_check=lambda x: len(x) == self.problem_static_cfg['n_obj'], 
            error_msg='dimension of reference point mismatches number of objectives',
        )
        self.view.widget['set_design'].configure(command=self.config_design)
        self.view.widget['set_performance'].configure(command=self.config_performance)

        if self.first_time:
            self.view.widget['n_init'].config(
                default=0, 
                valid_check=lambda x: x >= 0, 
                error_msg='number of initial samples cannot be negative',
            )
            self.view.widget['set_x_init'].configure(command=self.set_x_init)
            self.view.widget['disp_x_init'].config(
                valid_check=lambda x: os.path.exists(x), 
                error_msg='file not exists',
            )
            self.view.widget['set_y_init'].configure(command=self.set_y_init)
            self.view.widget['disp_y_init'].config(
                valid_check=lambda x: os.path.exists(x), 
                error_msg='file not exists',
            )

        self.view.widget['algo_name'].widget.bind('<<ComboboxSelected>>', self.select_algorithm)
        self.view.widget['n_process'].config(
            valid_check=lambda x: x > 0, 
            error_msg='number of processes to use must be positive',
        )
        self.view.widget['set_advanced'].configure(command=self.set_algo_advanced)

        self.view.widget['n_worker'].config(
            default=1,
            valid_check=lambda x: x > 0, 
            error_msg='max number of evaluation workers must be positive',
        )

        self.view.widget['save'].configure(command=self.save_config)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        # load current config values to entry if not first time setting config
        if not self.first_time:
            self.load_curr_config()

        # disable widgets
        self.view.widget['ref_point'].disable()
        if self.first_time:
            self.view.widget['set_design'].disable()
            self.view.widget['set_performance'].disable()
            self.view.widget['set_advanced'].disable()
        else:
            self.view.widget['problem_name'].disable()

    def create_config(self):
        '''
        Create experiment configurations
        '''
        self.first_time = True
        self.build_config_window()

    def change_config(self):
        '''
        Change experiment configurations
        '''
        self.first_time = False
        self.build_config_window()

    def select_problem(self, event):
        '''
        Select problem to configure
        '''
        self.view.widget['ref_point'].enable()
        self.view.widget['set_design'].enable()
        self.view.widget['set_performance'].enable()

        # find problem static config by name selected
        name = event.widget.get()
        config = get_problem_config(name)

        self.problem_static_cfg.clear()
        self.problem_static_cfg.update(config)

        for key in ['var_lb', 'var_ub', 'obj_lb', 'obj_ub']:
            self.problem_dynamic_cfg.update({key: config[key]})
        
        if self.first_time:
            init_sample_path = config['init_sample_path']
            if init_sample_path is not None:
                if isinstance(init_sample_path, list) and len(init_sample_path) == 2:
                    x_init_path, y_init_path = init_sample_path[0], init_sample_path[1]
                    self.view.widget['disp_x_init'].set(x_init_path)
                    self.view.widget['disp_y_init'].set(y_init_path)
                elif isinstance(init_sample_path, str):
                    x_init_path = init_sample_path
                    self.view.widget['disp_x_init'].set(x_init_path)
                else:
                    tk.messagebox.showinfo('Error', 'Error in problem definition: init_sample_path must be specified as 1) a list [x_path, y_path]; or 2) a string x_path', parent=self.view.window)

    def config_design(self):
        '''
        Configure bounds for design variables
        '''
        DesignBoundController(self)

    def config_performance(self):
        '''
        Configure bounds for objectives
        '''
        PerformanceBoundController(self)

    def set_x_init(self):
        '''
        Set path of provided initial design variables
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_x_init'].set(filename)

    def set_y_init(self):
        '''
        Set path of provided initial performance values
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_y_init'].set(filename)

    def select_algorithm(self, event):
        '''
        Select algorithm
        '''
        self.view.widget['set_advanced'].enable()

    def set_algo_advanced(self):
        '''
        Set advanced settings of the algorithm
        '''
        AlgoAdvancedController(self)

    def load_curr_config(self):
        '''
        Set values of widgets as current configuration values
        '''
        curr_config = self.get_config()
        self.problem_dynamic_cfg.clear()
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                widget.enable()
                widget.set(curr_config[cfg_type][cfg_name])
                widget.select()
        self.view.widget['set_advanced'].enable()
        self.problem_dynamic_cfg.update(curr_config['problem'])

    def save_config(self):
        '''
        Save specified configuration values
        '''
        config = {
            'general': {}, 
            'problem': {}, 
            'algorithm': {},
        }

        # specifically deal with initial samples (TODO: clean)
        if self.first_time:
            try:
                config['problem']['n_init_sample'] = self.view.widget['n_init'].get()
            except:
                show_widget_error(master=self.view.window, widget=self.view.widget['n_init'], name=config_map['problem']['n_init_sample'])
                return
            try:
                x_init_path = self.view.widget['disp_x_init'].get()
            except:
                show_widget_error(master=self.view.window, widget=self.view.widget['disp_x_init'], name='Path of provided initial design variables')
                return
            try:
                y_init_path = self.view.widget['disp_y_init'].get()
            except:
                show_widget_error(master=self.view.window, widget=self.view.widget['disp_y_init'], name='Path of provided initial performance values')
                return

            if x_init_path is None and y_init_path is None: # no path of initial samples is provided
                config['problem']['init_sample_path'] = None
            elif x_init_path is None: # only path of initial Y is provided, error
                tk.messagebox.showinfo('Error', 'Only path of initial performance values is provided', parent=self.view.window)
                return
            elif y_init_path is None: # only path of initial X is provided
                config['problem']['init_sample_path'] = x_init_path
            else: # both path of initial X and initial Y are provided
                config['problem']['init_sample_path'] = [x_init_path, y_init_path]

        # set config values from widgets
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                try:
                    config[cfg_type][cfg_name] = widget.get()
                except:
                    show_widget_error(master=self.view.window, widget=widget, name=config_map[cfg_type][cfg_name])
                    return

        if self.first_time:
            if x_init_path is None and self.view.widget['n_init'].get() == 0:
                tk.messagebox.showinfo('Error', 'Either number of initial samples or path of initial design variables needs to be provided', parent=self.view.window)
                return

        config['problem'].update(self.problem_dynamic_cfg)
        config['algorithm'].update(self.algo_cfg)

        success = self.set_config(config, self.view.window)
        if success:
            self.view.window.destroy()