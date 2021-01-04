import tkinter as tk
from tkinter import ttk
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget
from system.scientist.map import algo_config_map, algo_value_map


class AlgoAdvancedView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.window)
        self.window.title('Advanced Settings')
        self.window.resizable(False, False)

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
