import tkinter as tk
from .view import CreateTableView


class CreateTableController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.database = self.root_controller.database

        self.view = CreateTableView(self.root_view)

        self.view.widget['set_file_path'].configure(command=self.set_file_path)
        self.view.widget['create'].configure(command=self.create_table)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def set_file_path(self):
        filename = tk.filedialog.askopenfilename(parent=self.view.window)
        if not isinstance(filename, str) or filename == '': return
        self.view.widget['disp_file_path'].set(filename)

    def create_table(self):
        try:
            name = self.view.widget['db_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            file_path = self.view.widget['disp_file_path'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            if file_path is None:
                self.database.create_empty_table(name)
            else:
                self.database.import_db_from_file(name, file_path)
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()
        self.root_controller.after_init(name)