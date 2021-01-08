import tkinter as tk
from .view import LoadTableView


class LoadTableController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.database = self.root_controller.database

        self.view = LoadTableView(self.root_view)

        self.view.widget['table_name'].widget.config(values=self.database.get_table_list())
        self.view.widget['load'].configure(command=self.load_table)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def load_table(self):
        try:
            name = self.view.widget['table_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()
        self.root_controller.after_init(name)