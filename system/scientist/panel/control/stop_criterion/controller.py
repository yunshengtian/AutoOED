from time import time
import tkinter as tk
from .view import StopCriterionView


class StopCriterionController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.stop_criterion = root_controller.stop_criterion

        self.view = StopCriterionView(self.root_view)

        self.view.widget['save'].configure(command=self.save_stop_criterion)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        self.load_stop_criterion()

    def get_timestamp(self):
        return self.root_controller.get_timestamp()

    def set_timestamp(self):
        return self.root_controller.set_timestamp()

    def load_stop_criterion(self):
        '''
        Load current stopping criterion
        '''
        for key, val in self.stop_criterion.items():
            self.view.widget['var'][key].set(1)
            if key == 'time':
                val -= time() - self.get_timestamp()
                self.stop_criterion[key] = val
                self.set_timestamp()
            self.view.widget['entry'][key].set(val)

    def save_stop_criterion(self):
        '''
        Save stopping criterion
        '''
        self.stop_criterion.clear()
        for key in ['time', 'n_sample', 'hv_value', 'hv_conv']:
            if self.view.widget['var'][key].get() == 1:
                try:
                    self.stop_criterion[key] = self.view.widget['entry'][key].get()
                except:
                    error_msg = self.view.widget['entry'][key].get_error_msg()
                    error_msg = '' if error_msg is None else ': ' + error_msg
                    tk.messagebox.showinfo('Error', f'Invalid value for "{self.view.name_options[key]}"' + error_msg, parent=self.view.window)
                    return
                if key == 'time':
                    self.set_timestamp()
        self.view.window.destroy()