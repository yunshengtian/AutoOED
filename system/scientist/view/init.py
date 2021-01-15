import tkinter as tk
from system.gui.widgets.factory import create_widget


class ScientistInitView:

    def __init__(self, root):
        self.root = root

        frame_init = tk.Frame(master=self.root)
        frame_init.grid(row=0, column=0, padx=20, pady=20, sticky='NSEW')

        self.widget = {}
        self.widget['create_table'] = create_widget('button', master=frame_init, row=0, column=0, text='Create Table')
        self.widget['load_table'] = create_widget('button', master=frame_init, row=1, column=0, text='Load Table')
        self.widget['remove_table'] = create_widget('button', master=frame_init, row=2, column=0, text='Remove Table')
