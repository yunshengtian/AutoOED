import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.gui.widgets.excel import Excel


class StopEvalView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.window = tk.Toplevel(master=self.root_view.root)
        self.window.title('Stop Evaluation')
        self.window.resizable(False, False)

        self.widget = {}

        frame_n_row = create_widget('frame', master=self.window, row=0, column=0, sticky=None, pady=0)
        self.widget['disp_n_row'] = create_widget('labeled_entry',
            master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int')
        self.widget['disp_n_row'].set(1)
        self.widget['set_n_row'] = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

        self.widget['rowid_excel'] = Excel(master=self.window, rows=1, columns=1, width=10, 
            title=['Row number'], dtype=[int], default=None, required=[True])
        self.widget['rowid_excel'].grid(row=1, column=0)

        frame_action = create_widget('frame', master=self.window, row=2, column=0, sticky=None, pady=0)
        self.widget['stop'] = create_widget('button', master=frame_action, row=0, column=0, text='Stop')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')
