import os
import tkinter as tk
from experiment.config import load_config
from problem.common import get_problem_config
from system.gui.widgets.factory import show_widget_error
from system.scientist.map import config_map
from .view import MenuConfigView

from .algo_advanced import AlgoAdvancedController


class MenuConfigController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_cfg = {} # problem config
        self.algo_cfg = {} # advanced algorithm config
        
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
        self.view = MenuConfigView(self.root_view, self.first_time)

        self.view.widget['problem_name'].widget.bind('<<ComboboxSelected>>', self.select_problem)

        if self.first_time:
            self.view.widget['set_x_init'].configure(command=self.set_x_init)
            self.view.widget['set_y_init'].configure(command=self.set_y_init)

        self.view.widget['algo_name'].widget.bind('<<ComboboxSelected>>', self.select_algorithm)
        self.view.widget['set_advanced'].configure(command=self.set_algo_advanced)

        self.view.widget['save'].configure(command=self.save_config)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        # load current config values to entry if not first time setting config
        if not self.first_time:
            self.load_curr_config()

        # disable widgets
        if self.first_time:
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
        # find problem static config by name selected
        name = event.widget.get()
        config = get_problem_config(name)

        self.problem_cfg.clear()
        self.problem_cfg.update(config)
        
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
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                widget.enable()
                widget.set(curr_config[cfg_type][cfg_name])
                widget.select()
        self.view.widget['set_advanced'].enable()

    def save_config(self):
        '''
        Save specified configuration values
        '''
        config = self.get_config()
        if config is None:
            config = {
                'problem': {},
                'experiment': {},
                'algorithm': {},
            }

        # specifically deal with initial samples (TODO: clean)
        if self.first_time:
            init_type = self.view.widget['init_type'].get()

            if init_type == 'Random':
                try:
                    config['problem']['n_random_sample'] = self.view.widget['n_init'].get()
                except:
                    show_widget_error(master=self.view.window, widget=self.view.widget['n_init'], name=config_map['problem']['n_random_sample'])
                    return

            elif init_type == 'Provided':
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

                assert x_init_path is not None, 'Path of initial design variables must be provided'
                if y_init_path is None: # only path of initial X is provided
                    config['problem']['init_sample_path'] = x_init_path
                else: # both path of initial X and initial Y are provided
                    config['problem']['init_sample_path'] = [x_init_path, y_init_path]

            else:
                raise Exception()

        # set config values from widgets
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                try:
                    config[cfg_type][cfg_name] = widget.get()
                except:
                    show_widget_error(master=self.view.window, widget=widget, name=config_map[cfg_type][cfg_name])
                    return

        config['algorithm'].update(self.algo_cfg)

        success = self.set_config(config, self.view.window)
        if success:
            self.view.window.destroy()