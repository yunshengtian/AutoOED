import tkinter as tk
from tkinter import ttk

from autooed.system.gui.widgets.utils.grid import grid_configure
from autooed.system.gui.widgets.factory import create_widget, show_widget_error
from autooed.system.gui.map import algo_config_map, algo_value_map, algo_value_inv_map
from autooed.system.gui.menu.config.algo_advanced.surrogate import SurrogateController
from autooed.system.gui.menu.config.algo_advanced.acquisition import AcquisitionController
from autooed.system.gui.menu.config.algo_advanced.solver import SolverController
from autooed.system.gui.menu.config.algo_advanced.selection import SelectionController


class AlgoAdvancedView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.window, title='Advanced Settings')

        self.widget = {}
        self.cfg_widget = {}

        # parameter section
        frame_param_algo = create_widget('frame', master=self.window, row=0, column=0)
        self.nb_param = ttk.Notebook(master=frame_param_algo)
        self.nb_param.grid(row=0, column=0, sticky='NSEW')
        self.frame_surrogate = tk.Frame(master=self.nb_param)
        self.frame_acquisition = tk.Frame(master=self.nb_param)
        self.frame_solver = tk.Frame(master=self.nb_param)
        self.frame_selection = tk.Frame(master=self.nb_param)
        self.nb_param.add(child=self.frame_surrogate, text='Surrogate')
        self.nb_param.add(child=self.frame_acquisition, text='Acquisition')
        self.nb_param.add(child=self.frame_solver, text='Solver')
        self.nb_param.add(child=self.frame_selection, text='Selection')
        grid_configure(self.frame_surrogate, None, 0)
        grid_configure(self.frame_acquisition, None, 0)
        grid_configure(self.frame_solver, None, 0)
        grid_configure(self.frame_selection, None, 0)

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')


class AlgoAdvancedController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.algo_cfg = self.root_controller.algo_cfg

        self.view = AlgoAdvancedView(self.root_view)

        self.controller = {
            'surrogate': SurrogateController(self),
            'acquisition': AcquisitionController(self),
            'solver': SolverController(self),
            'selection': SelectionController(self),
        }

        for key, controller in self.controller.items():
            self.view.cfg_widget[key] = controller.view.widget

        self.view.widget['save'].configure(command=self.save_config_algo)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        # load current config values to entry if not first time setting config
        curr_config = self.get_config()
        if not self.root_view.first_time and self.root_view.cfg_widget['algorithm']['name'].get() == curr_config['algorithm']['name']:
            self.load_curr_config_algo()

    def get_config(self):
        return self.root_controller.get_config()

    def load_curr_config_algo(self):
        '''
        Load advanced settings of algorithm
        '''
        if self.algo_cfg == {}:
            curr_config = self.get_config()
            self.algo_cfg.update(curr_config['algorithm'])
            self.algo_cfg.pop('name')
            self.algo_cfg.pop('n_process')
        for cfg_type, val_map in self.view.cfg_widget.items():
            # set names
            name = self.algo_cfg[cfg_type]['name']
            val_map['name'].set(algo_value_map[cfg_type]['name'][name])
            val_map['name'].select()
            # set params
            for cfg_name, widget in val_map.items():
                if cfg_name not in self.algo_cfg[cfg_type] or cfg_name == 'name': continue
                val = self.algo_cfg[cfg_type][cfg_name]
                if cfg_name in algo_value_map[cfg_type]:
                    widget.set(algo_value_map[cfg_type][cfg_name][val])
                else:
                    widget.set(val)
                if hasattr(widget, 'select'):
                    widget.select()

    def save_config_algo(self):
        '''
        Save advanced settings of algorithm
        '''
        temp_cfg = {}
        for cfg_type, val_map in self.view.cfg_widget.items():
            temp_cfg[cfg_type] = {}
            for cfg_name, widget in val_map.items():
                try:
                    val = widget.get()
                except:
                    show_widget_error(master=self.view.window, widget=widget, name=algo_config_map[cfg_type][cfg_name])
                    return
                if cfg_name in algo_value_inv_map[cfg_type]:
                    val = algo_value_inv_map[cfg_type][cfg_name][val]
                temp_cfg[cfg_type][cfg_name] = val

        self.view.window.destroy()

        for key, val in temp_cfg.items():
            self.algo_cfg[key] = val