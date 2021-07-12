import tkinter as tk
from .view import RemoveExperimentView


class RemoveExperimentController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view_init

        self.database = self.root_controller.database

        self.view = RemoveExperimentView(self.root_view)

        self.view.widget['experiment_name'].widget.config(values=self.database.get_table_list())
        self.view.widget['remove'].configure(command=self.remove_experiment)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def remove_experiment(self):
        try:
            name = self.view.widget['experiment_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            self.database.remove_table(name)
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()