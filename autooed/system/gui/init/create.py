import tkinter as tk

from autooed.system.gui.widgets.factory import create_widget


class InitCreateView:

    def __init__(self, root_view):
        self.window = create_widget('toplevel', master=root_view.root, title='Create Experiment')

        self.widget = {}
        self.widget['experiment_name'] = create_widget('labeled_entry', master=self.window, row=0, column=0, columnspan=2, 
            text='Experiment name', class_type='string', width=10, required=True, 
            valid_check=lambda x: not x.startswith('sqlite_'), error_msg='experiment name cannot start with sqlite_')
        self.widget['create'] = create_widget('button', master=self.window, row=1, column=0, text='Create')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')


class InitCreateController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view_init

        self.database = self.root_controller.database

        self.view = InitCreateView(self.root_view)

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