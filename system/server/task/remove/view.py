import tkinter as tk
from system.gui.widgets.factory import create_widget


class RemoveTaskView:

    def __init__(self, root_view):
        self.window = tk.Toplevel(master=root_view)
        self.window.title('Remove Task')
        self.window.resizable(False, False)
        self.widget = {}
        self.widget['task_name'] = create_widget('labeled_combobox', master=self.window, row=0, column=0, columnspan=2, 
            text='Task name', required=True)
        self.widget['remove'] = create_widget('button', master=self.window, row=1, column=0, text='Remove')
        self.widget['cancel'] = create_widget('button', master=self.window, row=1, column=1, text='Cancel')