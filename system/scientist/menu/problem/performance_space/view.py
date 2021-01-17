import tkinter as tk
from system.gui.widgets.factory import create_widget
from system.gui.widgets.excel import Excel
from system.scientist.map import config_map


class PerformanceSpaceView:

    def __init__(self, root_view, n_obj):
        self.root_view = root_view
        self.n_obj = n_obj

        self.titles = ['obj_name', 'obj_type']

        self.window = tk.Toplevel(master=self.root_view.window)
        self.window.title('Configure Performance Space')
        self.window.resizable(False, False)

        self.widget = {}

        # performance space section
        frame_performance = create_widget('frame', master=self.window, row=0, column=0)
        create_widget('label', master=frame_performance, row=0, column=0, text='Enter the properties for objectives:')
        self.widget['performance_excel'] = Excel(master=frame_performance, rows=self.n_obj, columns=2, width=15,
            title=[config_map['problem'][title] for title in self.titles], dtype=[str, str], valid_check=[None, lambda x: x in ['min', 'max']])
        self.widget['performance_excel'].grid(row=1, column=0)
        self.widget['performance_excel'].set_column(0, [f'f{i + 1}' for i in range(self.n_obj)])

        # action section
        frame_action = tk.Frame(master=self.window)
        frame_action.grid(row=1, column=0)
        self.widget['save'] = create_widget('button', master=frame_action, row=0, column=0, text='Save')
        self.widget['cancel'] = create_widget('button', master=frame_action, row=0, column=1, text='Cancel')