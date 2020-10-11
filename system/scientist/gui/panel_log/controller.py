import tkinter as tk
from .view import LogView


class LogController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = LogView(self.root_view)

        self.view.widget['clear'].configure(command=self.clear_log)
        self.view.widget['clear'].configure(state=tk.DISABLED)

    def log(self, string):
        '''
        Log texts to ScrolledText widget
        '''
        if string == []: return
        self.view.widget['log'].configure(state=tk.NORMAL)
        if isinstance(string, str):
            self.view.widget['log'].insert(tk.INSERT, string + '\n')
        elif isinstance(string, list):
            self.view.widget['log'].insert(tk.INSERT, '\n'.join(string) + '\n')
        else:
            raise NotImplementedError
        self.view.widget['log'].configure(state=tk.DISABLED)
        self.view.widget['log'].yview_pickplace('end')

    def clear_log(self):
        '''
        Clear texts in GUI log
        '''
        self.view.widget['log'].configure(state=tk.NORMAL)
        self.view.widget['log'].delete('1.0', tk.END)
        self.view.widget['log'].configure(state=tk.DISABLED)