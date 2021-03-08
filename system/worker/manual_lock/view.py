import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.gui.widgets.excel import Excel


class ManualLockView:
    
    def __init__(self, root_view, lock):
        self.root_view = root_view

        title = 'Lock Entries' if lock else 'Release Entries'
        self.window = create_widget('toplevel', master=self.root_view.root, title=title)

        self.widget = {}

        frame_n_row = create_widget('frame', master=self.window, row=0, column=0, sticky=None, pady=0)
        self.widget['disp_n_row'] = create_widget('labeled_entry',
            master=frame_n_row, row=0, column=0, text='Number of rows', class_type='int')
        self.widget['set_n_row'] = create_widget('button', master=frame_n_row, row=0, column=1, text='Update')

        self.widget['rowid_excel'] = Excel(master=self.window, rows=1, columns=1, width=10, 
            title=['Row number'], dtype=[int], default=None, required=[True], required_mark=False)
        self.widget['rowid_excel'].grid(row=1, column=0)

        frame_action = create_widget('frame', master=self.window, row=2, column=0, sticky=None, pady=0)
        self.widget['start'] = create_widget('button', master=frame_action, row=0, column=0, text='Lock' if lock else 'Release')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')