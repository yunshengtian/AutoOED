import tkinter as tk
from .view import StopCriterionView
from system.stop_criterion import get_stop_criterion, get_name


class StopCriterionController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.agent = self.root_controller.agent
        self.view = StopCriterionView(self.root_view)

        self.view.widget['save'].configure(command=self.save_stop_criterion)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

        self.load_stop_criterion()

    def save_stop_criterion(self):
        '''
        Save stopping criterion
        '''
        self.root_controller.stop_criterion.clear()

        for key in self.view.name_options.keys():
            if self.view.widget['var'][key].get() == 1:
                try:
                    value = self.view.widget['entry'][key].get()
                except:
                    error_msg = self.view.widget['entry'][key].get_error_msg()
                    error_msg = '' if error_msg is None else ': ' + error_msg
                    tk.messagebox.showinfo('Error', f'Invalid value for "{self.view.name_options[key]}"' + error_msg, parent=self.view.window)
                    return
                stop_criterion = get_stop_criterion(key)(self.agent, value)
                self.root_controller.stop_criterion.append(stop_criterion)

        self.view.window.destroy()

    def load_stop_criterion(self):
        '''
        Load stopping criterion
        '''
        for stop_criterion in self.root_controller.stop_criterion:
            if not stop_criterion.check():
                key = get_name(type(stop_criterion))
                self.view.widget['var'][key].set(1)
                self.view.widget['entry'][key].enable()
                self.view.widget['entry'][key].set(stop_criterion.load())
