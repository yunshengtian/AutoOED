import tkinter as tk
from system.scientist.map import config_map
from .view import DesignBoundView


class DesignBoundController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_static_cfg = self.root_controller.problem_static_cfg
        self.problem_dynamic_cfg = self.root_controller.problem_dynamic_cfg

        var_name = self.problem_static_cfg['var_name']
        var_lb = self.problem_dynamic_cfg['var_lb']
        var_ub = self.problem_dynamic_cfg['var_ub']

        self.view = DesignBoundView(self.root_view, var_name, var_lb, var_ub)

        self.view.widget['design_excel'].set_column(0, var_name)
        self.view.widget['design_excel'].disable_column(0)
        self.view.widget['design_excel'].set_column(1, var_lb)
        self.view.widget['design_excel'].set_column(2, var_ub)

        self.view.widget['save'].configure(command=self.save_design_space)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def save_design_space(self):
        '''
        Save design space parameters
        '''
        temp_cfg = {}
        for column, key in zip([1, 2], ['var_lb', 'var_ub']):
            try:
                temp_cfg[key] = self.view.widget['design_excel'].get_column(column)
            except:
                tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['problem'][key] + '"', parent=self.view.window)
                return
        for key, val in temp_cfg.items():
            self.problem_dynamic_cfg[key] = val

        self.view.window.destroy()