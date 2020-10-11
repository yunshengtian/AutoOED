import tkinter as tk
from system.scientist.gui.map import config_map
from .view import DesignSpaceView


class DesignSpaceController:

    def __init__(self, root_controller, n_var):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view
        self.n_var = n_var

        self.problem_cfg = self.root_controller.problem_cfg

        self.view = DesignSpaceView(self.root_view, n_var)

        # load configured design space
        for column, key in enumerate(self.view.titles):
            if key in self.problem_cfg:
                self.view.widget['design_excel'].set_column(column, self.problem_cfg[key])

        self.view.widget['save'].configure(command=self.save_design_space)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def save_design_space(self):
        '''
        Save design space parameters
        '''
        temp_cfg = {}
        for column, key in enumerate(self.view.titles):
            try:
                temp_cfg[key] = self.view.widget['design_excel'].get_column(column)
            except:
                tk.messagebox.showinfo('Error', 'Invalid value for "' + config_map['problem'][key] + '"', parent=self.view.window)
                return

        self.view.window.destroy()

        for key, val in temp_cfg.items():
            self.problem_cfg[key] = val