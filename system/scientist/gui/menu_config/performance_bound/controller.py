import tkinter as tk
from system.scientist.gui.map import config_map
from .view import PerformanceBoundView


class PerformanceBoundController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_static_cfg = self.root_controller.problem_static_cfg
        self.problem_dynamic_cfg = self.root_controller.problem_dynamic_cfg

        obj_name = self.problem_static_cfg['obj_name']
        obj_lb = self.problem_dynamic_cfg['obj_lb']
        obj_ub = self.problem_dynamic_cfg['obj_ub']

        self.view = PerformanceBoundView(self.root_view, obj_name, obj_lb, obj_ub)

        self.view.widget['performance_excel'].set_column(0, obj_name)
        self.view.widget['performance_excel'].disable_column(0)
        self.view.widget['performance_excel'].set_column(1, obj_lb)
        self.view.widget['performance_excel'].set_column(2, obj_ub)

        self.view.widget['save'].configure(command=self.save_performance_space)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def save_performance_space(self):
        '''
        Save performance space parameters
        '''
        temp_cfg = {}
        for column, key in zip([1, 2], ['obj_lb', 'obj_ub']):
            try:
                temp_cfg[key] = self.view.widget['performance_excel'].get_column(column)
            except:
                tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['problem'][key] + '"', parent=self.view.window)
                return
        for key, val in temp_cfg.items():
            self.problem_dynamic_cfg[key] = val

        self.view.window.destroy()