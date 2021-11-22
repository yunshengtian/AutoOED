from datetime import datetime
import tkinter as tk

from autooed.system.gui.widgets.utils.layout import grid_configure
from autooed.system.gui.widgets.factory import create_widget


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


class PanelLogController:

    def __init__(self, root_controller):
        self.root_controller = root_controller
        self.root_view = self.root_controller.view

        self.view = PanelLogView(self.root_view)

        self.view.widget['clear'].configure(command=self.clear_log)

    def log(self, string):
        '''
        Log texts to ScrolledText widget
        '''
        if string == []: return
        self.view.widget['log'].enable()
        time = datetime.now().strftime('\n%Y-%m-%d %H:%M:%S\n')
        if isinstance(string, str):
            log_str = string
        elif isinstance(string, list):
            log_str = '\n'.join(string)
        else:
            raise NotImplementedError
        self.view.widget['log'].widget.insert(tk.INSERT, time + log_str + '\n')
        self.view.widget['log'].disable()
        self.view.widget['log'].widget.yview_pickplace('end')

    def clear_log(self):
        '''
        Clear texts in GUI log
        '''
        self.view.widget['log'].enable()
        self.view.widget['log'].widget.delete('1.0', tk.END)
        self.view.widget['log'].disable()