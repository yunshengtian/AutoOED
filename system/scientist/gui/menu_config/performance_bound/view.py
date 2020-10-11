import tkinter as tk
from system.gui.widgets.excel import Excel
from system.gui.widgets.factory import create_widget
from system.scientist.gui.map import config_map


class PerformanceBoundView:

    def __init__(self, root_view, obj_name, obj_lb, obj_ub):
        self.root_view = root_view

        self.titles = ['obj_name', 'obj_lb', 'obj_ub']
        n_obj = len(obj_name)

        self.window = tk.Toplevel(master=self.root_view.window)
        self.window.title('Set Performance Bounds')
        self.window.resizable(False, False)

        self.widget = {}

        # performance space section
        frame_performance = create_widget('frame', master=self.window, row=0, column=0)
        create_widget('label', master=frame_performance, row=0, column=0, text='Enter the bounds for performance values:')
        self.widget['performance_excel'] = Excel(master=frame_performance, rows=n_obj, columns=3, width=15,
            title=[config_map['problem'][title] for title in self.titles], dtype=[str, float, float])
        self.widget['performance_excel'].grid(row=1, column=0)

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')