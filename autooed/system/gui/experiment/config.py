import os
import tkinter as tk
from tkinter import ttk
from multiprocessing import cpu_count

from autooed.problem import get_problem_config, get_problem_list
from autooed.mobo import get_algorithm_list
from autooed.mobo.hyperparams import get_hp_class_names, get_hp_class_by_name, get_hp_name_by_class

from autooed.system.params import PADX
from autooed.system.config import config_map, load_config, complete_config
from autooed.system.gui.widgets.utils.layout import grid_configure, center
from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.experiment.hyperparam import HyperparamController


class ExpConfigView:

    def __init__(self, root_view, first_time):

        self.root_view = root_view

        title = 'Create Experiment' if first_time else 'Update Config'
        self.master_window = self.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title=title)

        self.frame = {}
        self.widget = {}

        if first_time:

            # experiment section
            self.frame['exp'] = create_widget('frame', master=self.window, row=0, column=0, padx=2 * PADX)
            grid_configure(self.frame['exp'], 0, 0)
            self.widget['exp_name'] = create_widget('labeled_entry', master=self.frame['exp'], row=0, column=0,
                text='Experiment name', class_type='string', width=10, required=True, 
                valid_check=lambda x: not x.startswith('sqlite_'), error_msg='experiment name cannot start with sqlite_')
            self.widget['cfg_input_type'] = create_widget('labeled_radiobutton',
                master=self.frame['exp'], row=1, column=0, label_text='Create config by', button_text_list=['User interface', 'Loading from file'])

        # enter config section
        self.frame['enter'] = tk.Frame(master=self.window)
        self.frame['enter'].grid(row=1 if first_time else 0, column=0, sticky='NSEW')
        grid_configure(self.frame['enter'], 0, 0)

        nb_cfg = ttk.Notebook(self.frame['enter'])
        nb_cfg.grid(row=0, column=0, sticky='NSEW')

        if first_time:

            # problem subsection
            frame_problem = tk.Frame(master=nb_cfg)
            grid_configure(frame_problem, 0, 0)
            nb_cfg.add(child=frame_problem, text='Problem')

            self.widget['problem_name'] = create_widget('labeled_combobox', 
                master=frame_problem, row=0, column=0, text=config_map['problem']['name'], values=get_problem_list(), width=15, required=True)

            self.widget['init_type'] = create_widget('labeled_radiobutton',
                master=frame_problem, row=1, column=0, label_text='Initialization', button_text_list=['Random', 'From file'], default='Random')

            frame_random_init = create_widget('frame', master=frame_problem, row=2, column=0, padx=0, pady=0)
            frame_provided_init = create_widget('frame', master=frame_problem, row=2, column=0, padx=0, pady=0)
            grid_configure(frame_random_init, 0, 0)
            grid_configure(frame_provided_init, 0, 0)

            self.widget['n_init'] = create_widget('labeled_spinbox', 
                master=frame_random_init, row=0, column=0, text=config_map['experiment']['n_random_sample'], 
                from_=2, to=int(1e10), required=True)

            self.widget['set_x_init'], self.widget['disp_x_init'] = create_widget('labeled_button_entry',
                master=frame_provided_init, row=0, column=0, label_text='Path of initial design variables', button_text='Browse', width=30, required=True,
                valid_check=lambda x: os.path.exists(x), error_msg='file of initial design variables does not exist')
            self.widget['set_y_init'], self.widget['disp_y_init'] = create_widget('labeled_button_entry',
                master=frame_provided_init, row=1, column=0, label_text='Path of initial performance values', button_text='Browse', width=30,
                valid_check=lambda x: os.path.exists(x), error_msg='file of initial performance values does not exist')

            def set_random_init():
                frame_provided_init.grid_remove()
                frame_random_init.grid()

            def set_provided_init():
                frame_random_init.grid_remove()
                frame_provided_init.grid()

            for text, button in self.widget['init_type'].widget.items():
                if text == 'Random':
                    button.configure(command=set_random_init)
                elif text == 'From file':
                    button.configure(command=set_provided_init)
                else:
                    raise NotImplementedError

            set_random_init()

        # optimization subsection
        frame_opt = tk.Frame(master=nb_cfg)
        grid_configure(frame_opt, 0, 0)
        nb_cfg.add(child=frame_opt, text='Optimization')

        self.widget['algo_name'] = create_widget('labeled_combobox', 
            master=frame_opt, row=0, column=0, text=config_map['algorithm']['name'], values=get_algorithm_list(), required=True)
        self.widget['n_process'] = create_widget('labeled_spinbox', 
            master=frame_opt, row=1, column=0, text=config_map['algorithm']['n_process'], from_=1, to=int(1e10), default=cpu_count())
        self.widget['async'] = create_widget('labeled_combobox',
            master=frame_opt, row=2, column=0, text=config_map['algorithm']['async'], default='None',
            values=get_hp_class_names('async'))
        self.widget['set_advanced'] = create_widget('button', master=frame_opt, row=3, column=0, text='Advanced Settings', sticky=None)
        
        # evaluation subsection
        frame_eval = tk.Frame(master=nb_cfg)
        grid_configure(frame_eval, 0, 0)
        nb_cfg.add(child=frame_eval, text='Evaluation')

        self.widget['n_worker'] = create_widget('labeled_spinbox',
            master=frame_eval, row=0, column=0, text=config_map['experiment']['n_worker'], from_=1, to=int(1e10))

        # load config section
        if first_time:
            self.frame['load'] = create_widget('frame', master=self.window, row=1, column=0, padx=2 * PADX)
            grid_configure(self.frame['load'], 0, 0)

            self.widget['set_cfg_path'], self.widget['disp_cfg_path'] = create_widget('labeled_button_entry',
                master=self.frame['load'], row=0, column=0, label_text='Path of config file', button_text='Browse', width=30, required=True,
                valid_check=lambda x: os.path.exists(x), error_msg='config file does not exist')

            def set_enter_input():
                self.frame['load'].grid_remove()
                self.frame['enter'].grid()
                self.widget['save'].enable()

            def set_load_input():
                self.frame['enter'].grid_remove()
                self.frame['load'].grid()
                self.widget['save'].enable()

            for text, button in self.widget['cfg_input_type'].widget.items():
                if text == 'User interface':
                    button.configure(command=set_enter_input)
                elif text == 'Loading from file':
                    button.configure(command=set_load_input)
                else:
                    raise NotImplementedError

            self.frame['enter'].grid_remove()
            self.frame['load'].grid_remove()

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=2 if first_time else 1, column=0, columnspan=3)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Create' if first_time else 'Update')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')
        
        center(self.window, self.master_window)

        self.cfg_widget = {}

        if first_time:
            self.cfg_widget.update({
                'problem': {
                    'name': self.widget['problem_name'],
                },
            })

        self.cfg_widget.update({
            'algorithm': {
                'name': self.widget['algo_name'],
                'n_process': self.widget['n_process'],
                'async': self.widget['async'],
            },
            'experiment': {
                'n_worker': self.widget['n_worker'],
            },
        })


class ExpConfigController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_cfg = {} # problem config
        self.exp_cfg = {} # experiment config (for reference point)
        self.algo_cfg = {} # advanced algorithm config
        self.algo_selected = None

        self.view = None

    def get_config(self):
        return self.root_controller.get_config()

    def build_config_window(self, first_time):
        '''
        Build configuration window (for create/change)
        '''
        self.view = ExpConfigView(self.root_view, first_time)

        if first_time:
            self.view.widget['problem_name'].widget.bind('<<ComboboxSelected>>', self.select_problem)

        self.view.widget['algo_name'].widget.bind('<<ComboboxSelected>>', self.select_algorithm)
        self.view.widget['set_advanced'].configure(command=lambda: self.set_algo_advanced(first_time))

        if first_time:
            self.view.widget['set_cfg_path'].configure(command=self.load_config_from_file)
            self.view.widget['set_x_init'].configure(command=self.set_x_init)
            self.view.widget['set_y_init'].configure(command=self.set_y_init)

        self.view.widget['save'].configure(command=lambda: self.save_config(first_time))
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        # load current config values to entry if not first time setting config
        if not first_time:
            self.load_curr_config()

        # disable widgets
        if first_time:
            self.view.widget['set_advanced'].disable()
            self.view.widget['save'].disable()

    def create_config(self):
        '''
        Create experiment configurations
        '''
        self.build_config_window(first_time=True)

    def update_config(self):
        '''
        Update experiment configurations
        '''
        self.build_config_window(first_time=False)

    def load_config_from_file(self):
        '''
        Load experiment configurations From file
        '''
        filename = tk.filedialog.askopenfilename(parent=self.root_view.root)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_cfg_path'].set(filename)
        self.view.widget['disp_cfg_path'].widget.xview_moveto(1)

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
        self.view.widget['disp_x_init'].widget.xview_moveto(1)

    def set_y_init(self):
        '''
        Set path of provided initial performance values
        '''
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_y_init'].set(filename)
        self.view.widget['disp_y_init'].widget.xview_moveto(1)

    def select_algorithm(self, event):
        '''
        Select algorithm
        '''
        self.algo_selected = event.widget.get()
        self.view.widget['set_advanced'].enable()

    def set_algo_advanced(self, first_time):
        '''
        Set advanced settings of the algorithm
        '''
        HyperparamController(self, first_time)

    def load_curr_config(self):
        '''
        Set values of widgets as current configuration values
        '''
        curr_config = self.get_config()
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                widget.enable()
                if cfg_name == 'async':
                    widget.set(get_hp_name_by_class('async', curr_config[cfg_type][cfg_name]['name'])) # TODO: support other hyperparams
                else:
                    widget.set(curr_config[cfg_type][cfg_name])
                widget.select()
        self.problem_cfg.update(curr_config['problem'])
        self.algo_cfg.update(curr_config['algorithm'])
        self.algo_cfg.pop('name')
        self.algo_cfg.pop('n_process') # TODO: check
        self.view.widget['set_advanced'].enable()

    def save_config(self, first_time):
        '''
        Save specified configuration values (TODO: clean)
        '''
        if first_time:
            try:
                exp_name = self.view.widget['exp_name'].get()
            except Exception as e:
                tk.messagebox.showinfo('Error', e, parent=self.view.window)
                return

            cfg_input_type = self.view.widget['cfg_input_type'].get()

            # if load config From file
            if cfg_input_type == 'Loading from file':

                filename = self.view.widget['disp_cfg_path'].get()
                try:
                    config = load_config(filename)
                except Exception as e:
                    tk.messagebox.showinfo('Error', 'Invalid yaml file: ' + str(e), parent=self.view.window)
                    return

                config = self.root_controller.verify_config(exp_name, config, self.view.window)
                if config is not None:
                    self.view.window.destroy()
                    self.root_controller.init_config(exp_name, config)
                else:
                    return

        # if enter config
        config = self.get_config()
        if config is None:
            config = {
                'problem': {},
                'experiment': {},
                'algorithm': {},
            }

        # specifically deal with initial samples (TODO: clean)
        if first_time:
            init_type = self.view.widget['init_type'].get()

            if init_type == 'Random':
                try:
                    config['experiment']['n_random_sample'] = self.view.widget['n_init'].get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return

            elif init_type == 'From file':
                try:
                    x_init_path = self.view.widget['disp_x_init'].get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return
                try:
                    y_init_path = self.view.widget['disp_y_init'].get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return

                assert x_init_path is not None, 'Path of initial design variables must be provided'
                if y_init_path is None: # only path of initial X is provided
                    config['experiment']['init_sample_path'] = x_init_path
                else: # both path of initial X and initial Y are provided
                    config['experiment']['init_sample_path'] = [x_init_path, y_init_path]

            else:
                raise Exception(f'Invalid initialization type {init_type}')

        # set config values from widgets
        for cfg_type, val_map in self.view.cfg_widget.items():
            for cfg_name, widget in val_map.items():
                try:
                    if cfg_name == 'async':
                        config[cfg_type][cfg_name] = {}
                        config[cfg_type][cfg_name]['name'] = get_hp_class_by_name('async', widget.get())
                    else:
                        config[cfg_type][cfg_name] = widget.get()
                except Exception as e:
                    tk.messagebox.showinfo('Error', e, parent=self.view.window)
                    return

        config['experiment'].update(self.exp_cfg)
        config['algorithm'].update(self.algo_cfg)

        if first_time: # init config
            config = self.root_controller.verify_config(exp_name, config, window=self.view.window)
            if config is not None:
                self.view.window.destroy()
                self.root_controller.init_config(exp_name, config)
            else:
                return
        else: # update config
            try:
                config = complete_config(config, check=True)
            except Exception as e:
                tk.messagebox.showinfo('Error', 'Invalid configurations: ' + str(e), parent=self.view.window)
                return
            self.view.window.destroy()
            self.root_controller.set_config(config)
