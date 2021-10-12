import tkinter as tk

from autooed.system.gui.widgets.factory import create_widget


class RemoveExperimentView:

    def __init__(self, root_view):
        self.window = create_widget('toplevel', master=root_view.root, title='Remove Experiment')

        self.widget = {}
        self.widget['experiment_name'] = create_widget('labeled_combobox', master=self.window, row=0, column=0, columnspan=2, 
            text='Experiment name', required=True)
        self.widget['remove'] = create_widget('button', master=self.window, row=1, column=0, text='Remove')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')


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