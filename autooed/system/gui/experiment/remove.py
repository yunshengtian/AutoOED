import tkinter as tk

from autooed.system.gui.widgets.factory import create_widget
from autooed.system.gui.widgets.utils.layout import center


class ExpRemoveView:

    def __init__(self, root_view):
        self.root_view = root_view
        self.master_window = self.root_view.root
        self.window = create_widget('toplevel', master=self.master_window, title='Remove Experiment')

        self.widget = {}
        self.widget['exp_name'] = create_widget('labeled_combobox', master=self.window, row=0, column=0, columnspan=2, 
            text='Experiment name', required=True)
        self.widget['remove'] = create_widget('button', master=self.window, row=1, column=0, text='Remove')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')

        center(self.window, self.master_window)


class ExpRemoveController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.database = self.root_controller.database

        self.view = ExpRemoveView(self.root_view)

        self.view.widget['exp_name'].widget.config(values=self.database.get_table_list())
        self.view.widget['remove'].configure(command=self.remove_experiment)
        self.view.widget['cancel'].configure(command=self.view.window.destroy)

    def remove_experiment(self):
        try:
            name = self.view.widget['exp_name'].get()
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return

        try:
            self.database.remove_table(name)
        except Exception as e:
            tk.messagebox.showinfo('Error', e, parent=self.view.window)
            return
        
        self.view.window.destroy()