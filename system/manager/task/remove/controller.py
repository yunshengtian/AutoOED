import tkinter as tk
from .view import RemoveTaskView


class RemoveTaskController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view_init

        self.database = self.root_controller.database

        self.view = RemoveTaskView(self.root_view)

        self.view.widget['task_name'].widget.config(values=self.database.get_table_list())
        self.view.widget['remove'].configure(command=self.remove_task)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def remove_task(self):
        try:
            name = self.view.widget['task_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            self.database.remove_table(name)
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()