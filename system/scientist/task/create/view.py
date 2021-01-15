import tkinter as tk
from system.gui.widgets.factory import create_widget


class CreateTaskView:

    def __init__(self, root_view):
        self.window = tk.Toplevel(master=root_view)
        self.window.title('Create Task')
        self.window.resizable(False, False)
        self.widget = {}
        self.widget['task_name'] = create_widget('labeled_entry', master=self.window, row=0, column=0, columnspan=2, 
            text='Task name', class_type='string', width=10, required=True)
        self.widget['set_file_path'], self.widget['disp_file_path'] = create_widget('labeled_button_entry', master=self.window, row=1, column=0, columnspan=2,
            label_text='Existing table file location (optional)', button_text='Browse')
        self.widget['create'] = create_widget('button', master=self.window, row=2, column=0, text='Create')
        self.widget['cancel'] = create_widget('button', master=self.window, row=2, column=1, text='Cancel')