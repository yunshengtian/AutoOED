import tkinter as tk
from system.gui.utils.grid import grid_configure
from system.gui.widgets.factory import create_widget


class PanelLogView:

    def __init__(self, root_view):
        self.root_view = root_view

        self.widget = {}

        frame_log = create_widget('labeled_frame', master=self.root_view.root, row=2, column=1, text='Log')
        grid_configure(frame_log, 0, 0)

        # log display
        self.widget['log'] = create_widget('text', master=frame_log, row=0, column=0)
        self.widget['log'].disable()

        self.widget['clear'] = create_widget('button', master=frame_log, row=1, column=0, text='Clear')