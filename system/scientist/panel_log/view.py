import tkinter as tk
from tkinter import scrolledtext
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget


class PanelLogView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        frame_log = create_widget('labeled_frame', master=self.root_view.root, row=2, column=1, text='Log')
        grid_configure(frame_log, 0, 0)

        # log display
        self.widget['log'] = scrolledtext.ScrolledText(master=frame_log, width=10, height=10, state=tk.DISABLED)
        self.widget['log'].grid(row=0, column=0, sticky='NSEW', padx=5, pady=5)

        self.widget['clear'] = create_widget('button', master=frame_log, row=1, column=0, text='Clear')