import tkinter as tk
from .view import RemoveTableView


class RemoveTableController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.database = self.root_controller.database

        self.view = RemoveTableView(self.root_view)

        self.view.widget['db_name'].widget.config(values=self.database.get_all_table_list())
        self.view.widget['remove'].configure(command=self.remove_table)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def remove_table(self):
        try:
            name = self.view.widget['db_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            if self.database.check_table_exist(name):
                self.database.remove_table(name)
            elif self.database.check_empty_table_exist(name):
                self.database.remove_empty_table(name)
            else:
                raise Exception(f'Table {name} not found')
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()