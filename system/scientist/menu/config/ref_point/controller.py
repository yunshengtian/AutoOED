import numpy as np
import tkinter as tk
from .view import RefPointView


class RefPointController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.problem_cfg = self.root_controller.problem_cfg

        self.view = RefPointView(self.root_view, self.problem_cfg)

        self.view.widget['save'].configure(command=self.save_ref_point)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        self.load_ref_point()

    def load_ref_point(self):
        if 'ref_point' in self.problem_cfg:
            self.view.widget['excel'].set_column(1, self.problem_cfg['ref_point'])

    def save_ref_point(self):
        try:
            ref_point = self.view.widget['excel'].get_column(1)
        except Exception as e:
            tk.messagebox.showinfo('Error', str(e), parent=self.view.window)
            return

        if not self.root_controller.first_time:
            if None in ref_point:
                tk.messagebox.showinfo('Error', 'Please specify a complete reference point', parent=self.view.window)
                return

        self.problem_cfg['ref_point'] = ref_point
        self.view.window.destroy()