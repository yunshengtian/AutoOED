import tkinter as tk

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import center


class ExpLoadView:

    def __init__(self, root_view):
        self.root_view = root_view
        self.master_window = self.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title='Load Experiment')

        self.widget = {}
        self.widget['exp_name'] = create_widget('labeled_combobox', master=self.window, row=0, column=0, columnspan=2, 
            text='Experiment name', required=True)
        self.widget['load'] = create_widget('button', master=self.window, row=1, column=0, text='Load')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')

        center(self.window, self.master_window)


class ExpLoadController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.database = self.root_controller.database

        self.view = ExpLoadView(self.root_view)

        self.view.widget['exp_name'].widget.config(values=self.database.get_table_list())
        self.view.widget['load'].configure(command=self.load_experiment)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def load_experiment(self):
        try:
            exp_name = self.view.widget['exp_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()
        self.root_controller.init_config(exp_name)