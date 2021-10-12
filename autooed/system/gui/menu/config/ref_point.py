import numpy as np
import tkinter as tk

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.excel import Excel


class RefPointView:
    
    def __init__(self, root_view, problem_cfg):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.window, title='Set Reference Point')

        self.widget = {}

        frame_ref_point = create_widget('labeled_frame', master=self.window, text='Reference Point', row=0, column=0)
        frame_excel = create_widget('frame', master=frame_ref_point, row=0, column=0)
        self.widget['excel'] = Excel(master=frame_excel, rows=problem_cfg['n_obj'], columns=2, width=15,
            title=['Name', 'Reference Point'], dtype=[str, float])
        self.widget['excel'].grid(row=0, column=0)
        self.widget['excel'].set_column(0, problem_cfg['obj_name'])
        self.widget['excel'].disable_column(0)

        frame_action = create_widget('frame', master=self.window, row=1, column=0, padx=0, pady=0, sticky=None)
        self.widget['save'] = create_widget('button', master=frame_action, text='Save', row=0, column=0)
        self.widget['cancel'] = create_widget('button', master=frame_action, text='Cancel', row=0, column=1)


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