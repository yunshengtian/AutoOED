import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.gui.widgets.excel import Excel


class ManualFillView:

    def __init__(self, root_view, n_obj):
        self.root_view = root_view

        self.window = create_widget('toplevel', master=self.root_view.root, title='Fill Entries')

        self.widget = {}

        frame_n_row = create_widget('frame', master=self.window, row=0, column=0, sticky=None, pady=0)
        self.widget['disp_n_row'] = create_widget('labeled_entry',
            master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int')
        self.widget['set_n_row'] = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

        self.widget['performance_excel'] = Excel(master=self.window, rows=1, columns=n_obj + 1, width=10, 
            title=['Row number'] + [f'f{i + 1}' for i in range(n_obj)], dtype=[int] + [float] * n_obj, default=None, required=[True] * (n_obj + 1), required_mark=False)
        self.widget['performance_excel'].grid(row=1, column=0)

        frame_action = create_widget('frame', master=self.window, row=2, column=0, sticky=None, pady=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')