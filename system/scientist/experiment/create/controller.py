import tkinter as tk
from .view import CreateExperimentView


class CreateExperimentController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view_init

        self.database = self.root_controller.database

        self.view = CreateExperimentView(self.root_view)

        self.view.widget['create'].configure(command=self.create_experiment)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def create_experiment(self):
        try:
            name = self.view.widget['experiment_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            self.database.create_table(name)
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()
        self.root_controller.after_init(name)