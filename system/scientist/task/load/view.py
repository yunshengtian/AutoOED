import tkinter as tk
from system.gui.widgets.factory import create_widget


class LoadTaskView:

    def __init__(self, root_view):
        self.window = tk.Toplevel(master=root_view)
        self.window.title('Load Task')
        self.window.resizable(False, False)
        self.widget = {}
        self.widget['table_name'] = create_widget('labeled_combobox', master=self.window, row=0, column=0, columnspan=2, 
            text='Table name', required=True)
        self.widget['load'] = create_widget('button', master=self.window, row=1, column=0, text='Load')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')